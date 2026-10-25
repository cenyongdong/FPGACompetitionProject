"""One fresh r48 startup admission. Importing this module performs no board IO.

bootstrap(BASE, boot_id) requires verified diagnostic assets in BASE/package,
and an existing BASE/software directory. It exclusively creates BASE/startup.
No SDK, BOOT write, reboot, functional reset, load retry or command resend.
The parent owns authorization, package identity, boot installation and budgets.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ALLOWED_PC = sum(1 << bit for bit in (92, 93, 95))
FORBIDDEN_PC = ((1 << 160) - 1) ^ ALLOWED_PC


def _need(ok, why):
    if not ok:
        raise RuntimeError(why)


def _read(path):
    return json.loads(Path(path).read_text())


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    _need(spec is not None and spec.loader is not None, 'Cannot load prepared module: '+str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _guard(c, boot_id):
    _need(c.runtime() == boot_id, 'Runtime boot differs; no retry')
    _need(not c.owners(), 'Device has another owner; no retry')


def _pc(control):
    status = control['full_PC_status']
    _need(type(status) is int and 0 <= status < 1 << 160, 'Incomplete native PC160 status')
    _need(control['request'] == control['response'] and not control['error'] and
          control['PC_checker_ready'] and control['PC_system_resetn'],
          'Native checker not ready/stable or control error')
    _need(not status & FORBIDDEN_PC, 'Native PC160 contains a bit other than 92/93/95')
    return status


def _child(c, run, package, boot_id, name, script, args, collect=False):
    _guard(c, boot_id)
    out = run/name
    out.mkdir(mode=0o700)
    argv = [sys.executable, str(package/script), *map(str, args(out))]
    started = time.monotonic()
    code, error = None, None
    try:
        with (out/'stdout.log').open('xb') as stdout, (out/'stderr.log').open('xb') as stderr:
            # Native collectors have their own bounded one-write ACK waits.
            # No outer timeout kills a pending device command or restarts it.
            code = subprocess.run(argv, stdout=stdout, stderr=stderr, cwd=str(package)).returncode
    except Exception as caught:
        error = str(caught)
    c.fresh_json(out/'exit.json', dict(argv=argv, exit_code=code, error=error,
                 elapsed_seconds=time.monotonic()-started, boot_id=boot_id,
                 SDK=0, automatic_retry=False))
    _guard(c, boot_id)
    _need(error is None and code == 0, name+' collector failed; original output retained; no retry')
    value = _read(out/'capture/result.json' if collect else out/'raw.decoded.json')
    _need(value['boot_id'] == boot_id, name+' captured another boot')
    if collect:
        _need(value['valid'] is True and value['SDK'] == value['DMA'] == value['HDMI_START'] == 0,
              name+' incomplete/inconclusive or functional traffic attempted')
    return value


def _collect(c, run, package, boot_id, name, operation, extra=()):
    return _child(c, run, package, boot_id, name, 'capture_deferred.py',
                  lambda out: [operation, out/'capture', boot_id, *extra], collect=True)


def _native(c, run, package, boot_id, side):
    trace = _child(c, run, package, boot_id, 'cycletrace-'+side,
                   'capture_hp2_cycletrace.py', lambda out: [out/'raw.json', boot_id])
    protocol = _child(c, run, package, boot_id, 'protocol-'+side,
                      'capture_hp2_protocol.py', lambda out: [out/'raw.json', boot_id])
    return trace, protocol


def _protocol_view(protocol, capture):
    result = copy.deepcopy(protocol)
    result.update(valid=True, capture_HP_cycle=capture['control']['capture_HP_cycle'],
                  live_status=capture['control']['full_PC_status'])
    return result


def _trace_view(trace, after, boot_id):
    _need(trace['boot_id'] == boot_id and len(trace['banks']) == 2, 'Consumption trace boot/banks differ')
    bank = copy.deepcopy(trace['banks'][1])
    _need(bank['published'] is True and bank['count'] == len(bank['rows']) == 96+bank['trigger_index'] and
          0 <= bank['trigger_index'] <= 32, 'First-RUN consumption bank incomplete')
    arm = after['control']['arm_HP_cycle_raw']+1
    _need(bank['trigger_cycle'] == arm, 'First sampled RUN differs from raw ARM+1')
    bank.update(valid=True, boot_id=boot_id, overflow=False, arm_HP_cycle=arm)
    return bank


def _inspect(c, run, boot_id, name, generation, control=None):
    """Read held state only; no SNAP, ARM, reset or functional CSR write."""
    _guard(c, boot_id)
    out = run/name
    out.mkdir(mode=0o700)
    evidence, io = c.Evidence(out/'capture'), None
    try:
        io = c.MMIO(evidence, boot_id)
        monitor = c.header(io, c.MON)
        current = c.read_control(io, evidence)
        hdmi = {hex(off): io.read(off) for off in (0, 0x24, 0x28, 0x2c, 0x34, 0x40)}
        evidence.save('admission_held_state', monitor=monitor, control=current, HDMI_read_only=hdmi)
        _need(monitor == dict(status=0, abi=0x41495201, request=generation, response=generation),
              'Monitor is not at the required fresh generation')
        _need(hdmi['0x0'] == 0x48444d01 and hdmi['0x40'] == 0x48445301 and
              all(hdmi[key] == 0 for key in ('0x24', '0x28', '0x2c', '0x34')),
              'HDMI functional command/static pattern was already attempted')
        if control is None:
            _need(current['request'] == current['response'] == 0 and not current['error'] and
                  not any(current[key] for key in ('arm_used', 'arm_issued', 'rearm_used', 'rearm_issued')),
                  'Startup control has already been used')
        else:
            _need(current['raw'] == control['raw'], 'Final held control changed after persisted admission cut')
            _pc(current)
    finally:
        if io is not None:
            io.close()
        evidence.close()
    _guard(c, boot_id)


def _healthy(record, boot_id, generation):
    _need(record['valid'] is True and record['boot_id'] == boot_id and record['overflow'] is False and
          record['observer_generation'] == generation and
          all(record[key] == 0 for key in ('SDK', 'DMA', 'HDMI_START')),
          'Healthy capture identity/generation differs')
    _need(record['first_AR_HP_cycle'] is None and record['first_RVALID_HP_cycle'] is None,
          'Healthy capture contains startup history')
    _need(all(record['counts_lifetime'][ch][key] == 0 for ch in ('PS', 'S01') for key in ('AR', 'R')) and
          all(value == 0 for value in record['counts_lifetime']['writes'].values()),
          'Healthy lifetime has AR/return/write activity')
    for channel in ('HC0', 'HC1', 'HC2', 'HC3', 'PS', 'S01'):
        _need(all(record['counts_epoch'][channel][key] == 0 for key in
                  ('AR', 'R', 'RLAST', 'non_OKAY', 'ARVALID_cycles', 'RVALID_cycles', 'expected_R')),
              'Healthy epoch contains bus activity: '+channel)
        _need(not record['pins'][channel]['ARVALID'] and not record['pins'][channel]['RVALID'],
              'Healthy current bus pins active: '+channel)
    levels, control, drain = record['levels'], record['control'], record['drain']
    _need(levels['PS_HP2_resetn'] and levels['PL_HP2_resetn'] and not levels['HP_reset'],
          'Healthy reset boundary not released')
    _need(drain['state'] == drain['beats'] == drain['HP_cycles'] == 0 and
          not any(drain[key] for key in ('saw_RLAST', 'saw_RRESP_error', 'bad_ID', 'late_RVALID')),
          'Healthy consumer is not untouched WAIT')
    _need(not any(control[key] for key in ('arm_used', 'arm_issued', 'rearm_used', 'rearm_issued')),
          'Healthy path attempted consumption/checker rearm')
    _pc(control)


def _fresh_text(path, value):
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def bootstrap(base: Path, boot_id: str) -> dict:
    """Admit one untouched same-boot startup or raise, with no automatic retry."""
    base = Path(base)
    _need(base.is_absolute() and base.is_dir() and not base.is_symlink(), 'Absolute existing BASE required')
    _need(isinstance(boot_id, str) and boot_id, 'Expected boot_id required')
    package, software, run = base/'package', base/'software', base/'startup'
    _need(package.is_dir() and software.is_dir(), 'Prepared package/software directories required')
    required = ('capture_deferred.py', 'consume_gate.py', 'before_seed_gate.py',
                'capture_hp2_cycletrace.py', 'capture_hp2_protocol.py',
                'decode_hp2_cycletrace.py', 'decode_hp2_protocol.py', 'hp2_protocol_checks.py', 'libmmio32.so')
    _need(all((package/name).is_file() and not (package/name).is_symlink() for name in required),
          'Prepared diagnostic asset missing/unsafe')
    _need(not (base/'startup-admission.json').exists() and not (software/'startup-mode.txt').exists(),
          'Startup admission/mode already exists; no retry')
    c = _load(package/'capture_deferred.py', '_r48_capture_deferred')
    gate = _load(package/'consume_gate.py', '_r48_consume_gate')
    seed_module = _load(package/'before_seed_gate.py', '_r48_before_seed_gate')
    _guard(c, boot_id)
    run.mkdir(mode=0o700)  # A failed or interrupted attempt permanently consumes this directory.
    c.fresh_json(run/'attempt.json', dict(boot_id=boot_id, SDK=0, DMA=0, HDMI_START=0,
                 automatic_retry=False, functional_reset=False, BOOT_writes=0, reboots=0))
    previous_gate = sys.modules.get('consume_gate')
    # before_seed_gate imports this public name for its unchanged _native gate.
    # Bind it only while explicitly executing bootstrap; import itself has no IO.
    sys.modules['consume_gate'] = gate
    try:
        _inspect(c, run, boot_id, 'initial-held', 0)
        before_result = _collect(c, run, package, boot_id, 'observe-before', 'snapshot')
        before = before_result['normalized']
        _need(before['observer_generation'] == 2, 'First complete startup epoch is not generation2')
        trace_before, protocol_before_raw = _native(c, run, package, boot_id, 'before')
        protocol_before = _protocol_view(protocol_before_raw, before)
        seed = seed_module.evaluate(before, trace_before, protocol_before)
        c.fresh_json(run/'before-seed.json', seed)
        _need(seed['boot_id'] == boot_id, 'Seed gate boot differs')
        classification = seed['classification']
        if classification == 'healthy_no_target':
            _need(seed['continue_allowed'] is True and seed['eligible'] is False,
                  'Healthy seed was not safely classified')
            _healthy(before, boot_id, 2)
            after_result = _collect(c, run, package, boot_id, 'observe-healthy', 'snapshot',
                                    ('--before', run/'observe-before/capture/result.json'))
            after = after_result['normalized']
            _healthy(after, boot_id, 4)
            _need(after['HP_cycle'] > before['HP_cycle'] and
                  after['control']['request'] == before['control']['request']+1,
                  'Healthy second snapshot order/control generation differs')
            mode, control = 'healthy', after['control']
        elif classification == 'known_unmatched_return':
            _need(seed['eligible'] is True, 'Known unmatched startup return is not eligible')
            after_result = _collect(c, run, package, boot_id, 'consume', 'consume',
                                    ('--before', run/'observe-before/capture/result.json',
                                     '--seed-gate', run/'before-seed.json'))
            after = after_result['normalized']
            trace_after, protocol_after_raw = _native(c, run, package, boot_id, 'after')
            trace = _trace_view(trace_after, after, boot_id)
            protocol_after = _protocol_view(protocol_after_raw, after)
            consumption = gate.evaluate(before, after, trace, protocol_before, protocol_after)
            c.fresh_json(run/'consumed-gate.json', consumption)
            _need(consumption['eligible'] is True and consumption['boot_id'] == boot_id,
                  'Same-boot consumption proof failed: '+str(consumption.get('reasons')))
            rearmed = _collect(c, run, package, boot_id, 'checker-rearm', 'checker-rearm',
                               ('--before', run/'consume/capture/result.json',
                                '--consume-gate', run/'consumed-gate.json'))
            current = rearmed['normalized']
            _need(current['checker_ready_for_SDK'] is True and
                  current['historical_protocol_file_unchanged'] is True,
                  'Checker-only rearm did not preserve history/admit fresh state')
            mode, control = 'consumed', current['control']
            _need(control['arm_used'] and control['arm_issued'] and control['rearm_used'] and
                  control['rearm_issued'] and c.safe_terminal(c.drain(control['drain_raw'])),
                  'Consumed path does not retain safe nonzero QUIET terminal')
        else:
            raise RuntimeError('Unsafe/inconclusive startup seed: '+str(seed.get('reasons')))
        _need(after['observer_generation'] == 4, 'Final observer generation is not4')
        status = _pc(control)
        _inspect(c, run, boot_id, 'final-held', 4, control)
        receipt = dict(passed=True, valid=True, mode=mode, boot_id=boot_id,
                       observer_generation=4, observer_generation4=True, PCstatus=status,
                       PC_status_words=[(status >> (32*i)) & 0xffffffff for i in range(5)],
                       PC_status_bits=[i for i in range(160) if status >> i & 1], control=control,
                       SDK=0, DMA=0, HDMI_START=0, BOOT_writes=0, reboots=0,
                       automatic_retry=False, functional_reset=False,
                       startup_classification=classification, evidence=str(run),
                       original_startup_history_preserved=True, functional_recovery_proved=False)
        _guard(c, boot_id)
        _fresh_text(software/'startup-mode.txt', mode+'\n')
        c.fresh_json(base/'startup-admission.json', receipt)
        return receipt
    except Exception as error:
        c.fresh_json(run/'failure.json', dict(passed=False, boot_id=boot_id, error=str(error),
                     SDK=0, automatic_retry=False, original_raw_preserved=True))
        raise
    finally:
        if previous_gate is None:
            sys.modules.pop('consume_gate', None)
        else:
            sys.modules['consume_gate'] = previous_gate

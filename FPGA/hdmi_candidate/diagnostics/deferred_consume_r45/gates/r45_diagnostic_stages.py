"""r45 diagnostic stages only; parent owns authorization, identity and budgets.

diagnostic_stage(stage, run, package, boot_id, spawn) returns a JSON-compatible
result and exclusively saves run/metadata/<stage>.json. spawn(name, argv_fn)
creates run/name, executes argv_fn(out), and returns (out, exit_code).
Neither this module nor its collectors open the SDK or reboot the board.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import capture_deferred as c
import consume_gate

STAGES = ('observe-before', 'cycletrace-before', 'protocol-before', 'before-seed',
          'consume', 'cycletrace-after', 'protocol-after', 'consumed-gate',
          'checker-rearm', 'post-frame-protocol', 'post-joint-protocol')
POST_ALLOWED = (92, 93, 95)
POST_FORBIDDEN = ((1 << 160)-1) ^ sum(1 << bit for bit in POST_ALLOWED)


def _read(path):
    return json.loads(path.read_text())


def _asset(package, name, subdir):
    # Both layouts are explicit: prepared package subdirectories or flattened
    # deployment. Parent verifies the selected file identities before entry.
    for path in (package/subdir/name, package/name):
        if path.is_file():
            return path
    raise RuntimeError('Required package file missing: '+name)


def _guard(boot_id):
    c.need(c.runtime() == boot_id, 'Diagnostic stage runtime boot differs')
    c.need(not c.owners(), 'Diagnostic stage has another device owner')


def _capture(run, stage):
    value = _read(run/stage/'capture/result.json')
    c.need(value['valid'] is True, stage+' collector incomplete/inconclusive')
    return value


def _normalized(run, stage, boot_id):
    value = _capture(run, stage)['normalized']
    c.need(value['valid'] is True and value['boot_id'] == boot_id, 'Capture boot/valid differs: '+stage)
    return value


def _stage_ok(run, stage, boot_id):
    value = _read(run/'metadata'/(stage+'.json'))
    c.need(value['valid'] is True and value['boot_id'] == boot_id, 'Prior stage incomplete: '+stage)
    return value


def _protocol_view(run, side, capture, boot_id):
    _stage_ok(run,'protocol-'+side,boot_id)
    native = _read(run/('protocol-'+side)/'raw.decoded.json')
    c.need(native['boot_id'] == boot_id, 'Native protocol boot differs')
    view = copy.deepcopy(native)
    # Original decoded/raw files remain untouched. These three annotations bind
    # the native sticky history to the independently acknowledged control cut.
    view.update(valid=True, capture_HP_cycle=capture['control']['capture_HP_cycle'],
                live_status=capture['control']['full_PC_status'])
    return view


def _trace_view(run, after, boot_id):
    _stage_ok(run,'cycletrace-after',boot_id)
    native = _read(run/'cycletrace-after/raw.decoded.json')
    c.need(native['boot_id'] == boot_id and len(native['banks']) == 2, 'Consumption trace boot/banks differ')
    bank = native['banks'][1]
    c.need(bank['published'] is True and bank['count'] == len(bank['rows']) == 96+bank['trigger_index'] and
           0 <= bank['trigger_index'] <= 32, 'Consumption bank1 incomplete')
    first_run = after['control']['arm_HP_cycle_raw']+1
    c.need(bank['trigger_cycle'] == first_run, 'Bank1 does not trigger at raw ARM + 1')
    view = copy.deepcopy(bank)
    # Fixed-capacity bank stops writing after its validated published descriptor;
    # it does not have a separately invented overflow counter.
    view.update(valid=True,boot_id=boot_id,overflow=False,arm_HP_cycle=first_run)
    return view


def _post_snapshot(stage, run, boot_id):
    sdk = _read(run/'metadata/sdk-ready.json')
    c.need(sdk['valid'] is True and sdk['boot_id'] == boot_id, 'Post-SDK native check requires SDK admission')
    previous = sdk if stage == 'post-frame-protocol' else _stage_ok(run,'post-frame-protocol',boot_id)
    out = run/stage
    out.mkdir(mode=0o700)
    evidence = c.Evidence(out/'capture')
    io = None
    result = dict(valid=False,passed=False,stage=stage,boot_id=boot_id,automatic_retry=False,
                  SDK=0,monitor_commands=0,maximum_diagnostic_commands=1)
    try:
        _guard(boot_id)
        evidence.save('begin',stage=stage,boot_id=boot_id,monitor_commands=0)
        io = c.MMIO(evidence,boot_id)
        held = c.read_control(io,evidence)
        c.need(held['request'] == held['response'] == previous['control']['request'] and
               held['arm_used'] and held['rearm_used'] and not held['error'],
               'Control sequence/one-shot history differs before post-SDK SNAP')
        c.wait_command(io,c.CTRL,c.SNAP,evidence)  # Exactly one; no monitor access.
        control = c.read_control(io,evidence)
        status = control['full_PC_status']
        result.update(control=control,full_PC_status=status,
                      full_PC_words=[(status >> (32*i)) & 0xffffffff for i in range(5)],
                      status_bits=[i for i in range(160) if status >> i & 1])
        c.need(control['request'] == control['response'] == held['request']+1 and
               control['arm_used'] and control['rearm_used'] and not control['error'] and
               control['PC_checker_ready'] and control['PC_system_resetn'], 'Post-SDK checker not ready')
        c.need(not status & POST_FORBIDDEN, 'Fresh native status contains a bit other than 92/93/95')
        result.update(valid=True,passed=True)
    except Exception as error:
        result['error'] = str(error)
        evidence.save('inconclusive',error=str(error),automatic_retry=False)
    finally:
        if io is not None:
            io.close()
        evidence.close()
        c.fresh_json(out/'result.json',result)
    return result


def diagnostic_stage(stage, run, package, boot_id, spawn):
    """Execute one explicitly reserved stage; never reserve/retry another stage."""
    c.need(stage in STAGES, 'Unknown r45 diagnostic stage')
    run, package = Path(run), Path(package)
    metadata = run/'metadata'
    target = metadata/(stage+'.json')
    c.need(metadata.is_dir() and not target.exists() and not (run/stage).exists(),
           'Stage output already exists or metadata directory absent')
    _guard(boot_id)
    result = dict(valid=False,passed=False,stage=stage,boot_id=boot_id,automatic_retry=False,SDK=0)
    try:
        if stage in ('observe-before','consume','checker-rearm'):
            script = _asset(package,'capture_deferred.py','gates')
            operation = {'observe-before':'snapshot','consume':'consume','checker-rearm':'checker-rearm'}[stage]
            extra = []
            if stage == 'consume':
                _stage_ok(run,'before-seed',boot_id)
                c.need(_read(metadata/'before-seed.json')['eligible'] is True, 'No known pending seed admitted')
                extra = ['--before',str(run/'observe-before/capture/result.json'),
                         '--seed-gate',str(metadata/'before-seed.json')]
            elif stage == 'checker-rearm':
                _stage_ok(run,'consumed-gate',boot_id)
                c.need(_read(metadata/'consumed-gate.json')['eligible'] is True, 'No same-boot consumption proof')
                extra = ['--before',str(run/'consume/capture/result.json'),
                         '--consume-gate',str(metadata/'consumed-gate.json')]
            out,code = spawn(stage,lambda out:[sys.executable,str(script),operation,str(out/'capture'),boot_id]+extra)
            result.update(exit_code=code,capture=str(out/'capture/result.json'))
            c.need(code == 0,'Explicit collector failed; no command retry')
            value = _capture(run,stage)
            c.need(value['boot_id'] == boot_id,'Collector runtime identity differs')
            current = value['normalized']
            result.update(valid=True,passed=True,observer_generation=current.get('observer_generation'),
                          drain=current.get('drain'))
            if stage == 'checker-rearm':
                c.need(current['checker_ready_for_SDK'] is True,'Fresh checker not admitted')
                before = _capture(run,'observe-before')
                after = _normalized(run,'consume',boot_id)
                words = before['raw_snapshot']['words']
                c.need(len(words) == 104 and words[0] == 0x41495201,'Before source pin words incomplete')
                connected_mask = words[83] & 0x7fff9
                c.need(connected_mask != 0,'Before actual S01 source input configuration absent')
                ready = dict(valid=True,boot_id=boot_id,control=current['control'],
                             consume_gate=str(metadata/'consumed-gate.json'),
                             checker_capture=str(out/'capture/result.json'),SDK=0,
                             functional_recovery_proved=False)
                observe = dict(valid=True,boot_id=boot_id,discard_probe_admissible=True,
                               S01_source_connected_confirmed=True,S01_source_input_mask=connected_mask,
                               S01_source_evidence=str(run/'observe-before/capture/result.json'),
                               S01_source_word_index=83,drain=after['drain'],
                               startup_abnormality_retained=True,healthy_idle=False,
                               functional_recovery_proved=False,SDK=0)
                _guard(boot_id)
                c.need(not (metadata/'sdk-ready.json').exists() and not (metadata/'observe.json').exists(),
                       'SDK admission metadata already exists')
                c.fresh_json(metadata/'sdk-ready.json',ready)
                c.fresh_json(metadata/'observe.json',observe)
                result.update(control=current['control'],SDK_admitted=True)
        elif stage.startswith(('cycletrace-','protocol-')):
            name = 'capture_hp2_cycletrace.py' if stage.startswith('cycletrace-') else 'capture_hp2_protocol.py'
            script = _asset(package,name,'capture')
            out,code = spawn(stage,lambda out:[sys.executable,str(script),str(out/'raw.json'),boot_id])
            result.update(exit_code=code,raw=str(out/'raw.json'),decoded=str(out/'raw.decoded.json'))
            c.need(code == 0,'Read-only diagnostic capture failed')
            native = _read(out/'raw.decoded.json')
            c.need(native['boot_id'] == boot_id,'Native capture boot differs')
            # Published=false/status0 is valid on an untouched healthy boot.
            result.update(valid=True,passed=True,status=native['status'])
        elif stage in ('before-seed','consumed-gate'):
            out = run/stage
            out.mkdir(mode=0o700)
            before = _normalized(run,'observe-before',boot_id)
            if stage == 'before-seed':
                _stage_ok(run,'cycletrace-before',boot_id)
                trace = _read(run/'cycletrace-before/raw.decoded.json')
                protocol = _protocol_view(run,'before',before,boot_id)
                source = _asset(package,'before_seed_gate.py','gates')
                spec = importlib.util.spec_from_file_location('_r45_prepared_before_seed',str(source))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                gate = module.evaluate(before,trace,protocol)
                admissible = gate.get('classification') in ('healthy_no_target','known_unmatched_return')
            else:
                _stage_ok(run,'consume',boot_id)
                after = _normalized(run,'consume',boot_id)
                trace = _trace_view(run,after,boot_id)
                gate = consume_gate.evaluate(before,after,trace,
                       _protocol_view(run,'before',before,boot_id),_protocol_view(run,'after',after,boot_id))
                admissible = gate.get('eligible') is True
            c.need(gate['boot_id'] == boot_id,'Pure gate boot differs')
            result.update(gate)
            result.update(valid=admissible,passed=admissible)
            c.fresh_json(out/'inputs.json',dict(before=str(run/'observe-before/capture/result.json'),
                         after=str(run/'consume/capture/result.json') if stage == 'consumed-gate' else None,
                         native_files_unchanged=True,annotation_fields=['valid','capture_HP_cycle','live_status']))
        else:
            result = _post_snapshot(stage,run,boot_id)
    except Exception as error:
        result.update(valid=False,passed=False,error=str(error))
    try:
        _guard(boot_id)
    except Exception as error:
        result.update(valid=False,passed=False,error=str(error))
    c.fresh_json(target,result)
    return result

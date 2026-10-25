"""Explicit r46 diagnostic operations; native aligned MMIO32 via ctypes.

No SDK, functional reset, HDMI write, automatic consume, or command retry.
Every output directory and attempt/result file is exclusive and never replaced.
"""
import argparse
import ctypes
import errno
import json
import mmap
import os
from pathlib import Path
import stat
import time

BASE = 0x400b0000
MON, CTRL = 0x400, 0x800
CONS, SNAP, CHKR = 0x434f4e53, 0x534e4150, 0x43484b52
RECOMMENDATIONS = (20, 28, 36, 57, 67, 70, 72, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101)
MANDATORY_MASK = ((1 << 160) - 1) ^ sum(1 << i for i in RECOMMENDATIONS)
WRITES = ('legacy_AW', 'legacy_W', 'legacy_B', 'PS_AW', 'PS_W', 'PS_B')


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def runtime():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def fresh_json(path, value):
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


class Evidence:
    def __init__(self, directory):
        directory.mkdir(mode=0o700, parents=False, exist_ok=False)
        self.directory = directory
        fd = os.open(str(directory / 'raw.jsonl'), os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
        self.stream = os.fdopen(fd, 'w')

    def save(self, event, **values):
        values.update(event=event, Linux_monotonic_ns=int(time.monotonic()*1000000000))
        self.stream.write(json.dumps(values) + '\n')
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def close(self):
        self.stream.close()


def owners():
    found = []
    own = str(os.getpid())
    for process in Path('/proc').glob('[0-9]*'):
        if process.name == own:
            continue
        try:
            for fd in (process / 'fd').iterdir():
                try:
                    target = os.readlink(str(fd))
                    if target.startswith(('/dev/axi', '/dev/udmabuf', '/dev/u-dma', '/dev/video', '/dev/mem')):
                        found.append(dict(pid=process.name, fd=fd.name, target=target))
                except OSError as error:
                    if error.errno not in (errno.ENOENT, errno.ESRCH):
                        raise
        except OSError as error:
            if error.errno not in (errno.ENOENT, errno.ESRCH):
                raise RuntimeError('Cannot establish device ownership: ' + str(error))
    return found


class NativeMMIO32:
    """Only this C library touches mapped words; no Python buffer pack/unpack."""
    def __init__(self, library=None):
        path = Path(library) if library is not None else Path(__file__).resolve().with_name('libmmio32.so')
        need(path.is_absolute() and path.is_file() and not path.is_symlink(), 'Native MMIO32 library missing/unsafe')
        self.library = ctypes.CDLL(str(path))
        self.library.mmio32_abi.argtypes = []
        self.library.mmio32_abi.restype = ctypes.c_uint32
        need(self.library.mmio32_abi() == 0x4d333201, 'Native MMIO32 ABI differs')
        self.library.mmio32_read32.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        self.library.mmio32_read32.restype = ctypes.c_int
        self.library.mmio32_write32.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self.library.mmio32_write32.restype = ctypes.c_int

    def read(self, address):
        value = ctypes.c_uint32()
        code = self.library.mmio32_read32(address, ctypes.byref(value))
        need(code == 0, 'Native MMIO32 read rejected: '+str(code))
        return value.value

    def write(self, address, value):
        code = self.library.mmio32_write32(address, value)
        need(code == 0, 'Native MMIO32 write rejected: '+str(code))


class MMIO:
    def __init__(self, evidence, boot_id):
        self.evidence, self.boot_id = evidence, boot_id
        self.native = NativeMMIO32()  # Resolve ABI before opening the device.
        self.fd = os.open('/dev/mem', os.O_RDWR | os.O_SYNC | os.O_CLOEXEC)
        try:
            need(stat.S_ISCHR(os.fstat(self.fd).st_mode), 'Physical CSR character device required')
            self.page = mmap.mmap(self.fd, 4096, flags=mmap.MAP_SHARED,
                                  prot=mmap.PROT_READ | mmap.PROT_WRITE, offset=BASE)
            # from_buffer exports the writable mapping address; it performs no
            # Python value load/store. Keep it alive until after all C calls.
            self.mapping_reference = ctypes.c_uint32.from_buffer(self.page)
            self.address = ctypes.addressof(self.mapping_reference)
            need(self.address % 4 == 0, 'Mapped virtual base is not word-aligned')
        except Exception:
            if hasattr(self, 'mapping_reference'):
                del self.mapping_reference
            if hasattr(self, 'page'):
                self.page.close()
            os.close(self.fd)
            raise

    def read(self, offset):
        need(type(offset) is int and offset % 4 == 0 and 0 <= offset <= 4092, 'Unaligned/out-of-page CSR read')
        return self.native.read(self.address+offset)

    def write(self, offset, value):
        need((offset == MON and value in (1, 2)) or
             (offset == CTRL and value in (CONS, SNAP, CHKR)), 'Only explicit diagnostic CSR commands may be written')
        need(runtime() == self.boot_id, 'Boot changed before diagnostic write')
        # This fsynced event precedes the only store, including uncertain stores.
        self.evidence.save('command_attempt', offset=hex(offset), value=value, boot_id=self.boot_id)
        self.native.write(self.address+offset, value)  # One native call, never repeated.

    def close(self):
        del self.mapping_reference
        try:
            self.page.close()
        finally:
            os.close(self.fd)


def header(io, base):
    return dict(status=io.read(base), abi=io.read(base+4), request=io.read(base+8), response=io.read(base+12))


class DiagnosticCommandFailure(RuntimeError):
    def __init__(self, details):
        self.details = details
        super().__init__('Diagnostic '+details['failure_kind']+'; last_header='+
                         json.dumps(details['last_header'],sort_keys=True)+
                         '; elapsed_seconds='+str(details['elapsed_seconds'])+'; do not resend')


def wait_command(io, base, value, evidence, timeout=0.1):
    started, ack_started, last = time.monotonic(), None, None
    def fail(kind, cause=None):
        now = time.monotonic()
        details = dict(base=hex(base),command=value,failure_kind=kind,last_header=last,
                       elapsed_seconds=now-started,
                       ack_elapsed_seconds=None if ack_started is None else now-ack_started,
                       ack_deadline_seconds=timeout,automatic_retry=False)
        if cause is not None:
            details['cause'] = str(cause)
        evidence.save('command_failed',**details)
        raise DiagnosticCommandFailure(details)
    try:
        last = header(io,base)
    except Exception as error:
        fail('header_read_failure',error)
    evidence.save('command_before',base=hex(base),command=value,header=last)
    expected_abi = 0x41495201 if base == MON else 0x48444301
    if last['abi'] != expected_abi:
        fail('abi_mismatch_before_write')
    if last['status'] & 2:
        fail('command_error_before_write')
    if last['status'] & 1:
        fail('busy_before_write')
    if not last['request'] == last['response'] < 0xffffffff:
        fail('generation_invalid_before_write')
    sequence = last['request']+1
    try:
        io.write(base,value)  # One store. Timeout/error never causes a retry.
    except Exception as error:
        try:
            last = header(io,base)
        except Exception:
            pass  # Preserve the last complete header without inventing one.
        fail('native_write_failure',error)
    ack_started = time.monotonic()
    until = ack_started+timeout
    while True:
        try:
            last = header(io,base)
        except Exception as error:
            fail('header_read_failure',error)
        # Command error is an observed hardware status, even if it coincides
        # with a deadline. It must never be mislabeled as an elapsed timeout.
        if last['status'] & 2:
            fail('command_error')
        if last['abi'] != expected_abi:
            fail('abi_changed')
        if not (last['request'] in (sequence-1,sequence) and last['response'] in (sequence-1,sequence)):
            fail('generation_changed')
        if last['status'] & 3 == 0 and last['request'] == last['response'] == sequence:
            now = time.monotonic()
            evidence.save('command_ack',base=hex(base),command=value,header=last,
                          elapsed_seconds=now-started,ack_elapsed_seconds=now-ack_started)
            return last
        if time.monotonic() >= until:
            fail('ack_deadline_elapsed')
        time.sleep(0.0001)


def read_control(io, evidence):
    before = header(io, CTRL)
    words = [io.read(CTRL + off) for off in range(0x10, 0x3c, 4)]
    after = header(io, CTRL)
    raw = dict(header_before=before, words_10_to_38=words, header_after=after)
    evidence.save('control_raw', raw=raw)
    need(before == after and before['abi'] == 0x48444301 and before['status'] & 3 == 0 and
         before['request'] == before['response'], 'Control bundle not stable')
    flags = words[1]
    pc = sum(words[6+i] << (32*i) for i in range(5))
    result = dict(request=after['request'], response=after['response'],
                  arm_issued=bool(after['status'] & 4), rearm_issued=bool(after['status'] & 8),
                  arm_used=bool(flags & 1), rearm_used=bool(flags & 2), error=bool(flags & 128),
                  PC_checker_ready=bool(flags & 4), PC_system_resetn=bool(flags & 8),
                  capture_HP_cycle=words[2] | words[3] << 32,
                  arm_HP_cycle_raw=words[4] | words[5] << 32,
                  drain_raw=words[0], full_PC_status=pc, raw=raw)
    result['first_sampled_RUN_HP_cycle_derived'] = result['arm_HP_cycle_raw'] + 1 if result['arm_used'] else None
    return result


def drain(raw):
    return dict(state=raw & 7, beats=(raw >> 3) & 511, HP_cycles=(raw >> 12) & 8191,
                saw_RLAST=bool(raw & (1 << 25)), saw_RRESP_error=bool(raw & (1 << 26)),
                bad_ID=bool(raw & (1 << 27)), late_RVALID=bool(raw & (1 << 31)))


def safe_terminal(value):
    return (value['state'] == 2 and 0 < value['beats'] < 256 and 64 <= value['HP_cycles'] < 4096 and
            value['saw_RLAST'] and not any(value[k] for k in ('saw_RRESP_error', 'bad_ID', 'late_RVALID')))


def monitor_start(io, evidence):
    h = header(io, MON)
    evidence.save('monitor_initial', header=h, count=io.read(MON+0x10))
    need(h['abi'] == 0x41495201 and h['status'] == 0 and h['request'] == h['response'] and
         h['request'] % 2 == 0 and h['request'] <= 0xfffffffd and io.read(MON+0x10) == 104,
         'Monitor must be idle at a valid even generation; no reset/retry')
    return wait_command(io, MON, 1, evidence)['request'] - 1


def monitor_finish(io, evidence, initial):
    wait_command(io, MON, 2, evidence)
    h = header(io, MON)
    words = [io.read(MON+0x40+4*i) for i in range(104)]
    evidence.save('monitor_words_raw', header=h, words=words)
    boot = [io.read(MON+(0x14+4*i if i < 11 else 0x1e0+4*(i-11))) for i in range(19)]
    evidence.save('boot_words_raw', words=boot)
    release = [io.read(0x600+4*i) for i in range(128)]
    end = header(io, MON)
    evidence.save('release_words_raw', words=release, header_after=end)
    need(h == end and h['status'] == 0 and h['request'] == h['response'] == initial+2 and
         words[0] == 0x41495201 and boot[0] == 0x42545201 and boot[18] & 128 and
         release[0] == 0x50534c01 and release[1] & 3 == 3 and release[7] == 1,
         'Full raw retained; monitor/boot/release snapshot identity invalid')
    need(boot[3] == release[36] and boot[4] == release[37], 'Matched source FREEZE PS totals differ')
    return dict(initial_generation=initial, generation=h['request'], words=words,
                boot_words=boot, release_words=release, header_after=end)


def normalize(raw, control, boot_id, previous=None):
    w, b, r = raw['words'], raw['boot_words'], raw['release_words']
    need(not (b[1] & ((15 << 13) | (1 << 17))) and not (r[1] & 4) and not ((r[34] >> 4) & 255),
         'Raw counter/event overflow; do not subtract')
    need(w[1] > 0 and w[2] & 31 == 0x19 and w[3] == 0, 'Monitor reset/clock state changed')
    epoch, pins = {}, {}
    for i, name in enumerate(('HC0', 'HC1', 'HC2', 'HC3', 'S01', 'PS')):
        at = 8+16*i
        epoch[name] = dict(AR=w[at], R=w[at+1], RLAST=w[at+2], non_OKAY=w[at+3],
                           ARVALID_cycles=w[at+6], RVALID_cycles=w[at+7], expected_R=w[at+15])
        pin = w[at+11]
        pins[name] = dict(ARVALID=bool(pin & 1), ARREADY=bool(pin & 2),
                          RVALID=bool(pin & 4), RREADY=bool(pin & 8), RID=(pin >> 19) & 63,
                          RRESP=(pin >> 25) & 3, RLAST=bool(pin & (1 << 27)))
    need(all(e['AR'] == e['ARVALID_cycles'] == e['non_OKAY'] == 0 for e in epoch.values()),
         'Requests/non-OKAY observed in diagnostic epoch')
    need(all(epoch[c]['R'] == 0 and not pins[c]['RVALID'] for c in ('HC0','HC1','HC2','HC3')) and
         all(not p['ARVALID'] for p in pins.values()), 'AI return or current request')
    writes = dict(zip(WRITES, r[38:44]))
    need(all(v == 0 for v in writes.values()), 'Cumulative write activity')
    lifetime = dict(PS=dict(AR=b[3], R=b[4]), S01=dict(AR=b[5], R=b[6]), writes=writes)
    need(lifetime['PS']['AR'] == lifetime['S01']['AR'] == 0 and not (r[34] & 1), 'Cumulative AR history')
    need(control['drain_raw'] == w[4] and not control['error'],
         'Separate control SNAP and monitor FREEZE did not have stable drain state')
    levels = dict(PS_HP2_resetn=bool(r[5] & 1), PL_HP2_resetn=bool(r[5] & 2),
                  HP_reset=bool(r[5] & 8), DDR_calibrated=bool(r[5] & 64))
    for name in ('PS', 'S01', 'HC2'):
        levels[name+'_ARVALID'] = pins[name]['ARVALID']
        levels[name+'_RVALID'] = pins[name]['RVALID']
    need(levels['PS_HP2_resetn'] and levels['PL_HP2_resetn'] and not levels['HP_reset'], 'Reset not released')
    for name, rid in (('PS', 0x20), ('S01', 0)):
        need(not pins[name]['RVALID'] or (pins[name]['RID'] == rid and pins[name]['RRESP'] == 0),
             'Visible pending ID/response differs: '+name)
    if previous is not None:
        need(previous['boot_id'] == boot_id, 'Previous snapshot is from another boot')
        for name in ('PS', 'S01'):
            for key in ('AR', 'R'):
                need(previous['counts_lifetime'][name][key] + epoch[name][key] == lifetime[name][key],
                     'Before + current epoch does not equal native lifetime: '+name+'.'+key)
    return dict(valid=True, boot_id=boot_id, SDK=0, DMA=0, HDMI_START=0, overflow=False,
                observer_generation=raw['generation'],
                HP_cycle=r[32] | r[33] << 32, control_capture_HP_cycle=control['capture_HP_cycle'],
                clock_note='Control SNAP and monitor/boot FREEZE are separate cuts; native counter origins are retained, not equated.',
                counts_lifetime=lifetime, counts_epoch=epoch, pins=pins, levels=levels,
                first_RVALID_HP_cycle=(r[46] | r[47] << 32) if r[34] & 2 else None,
                first_AR_HP_cycle=(r[44] | r[45] << 32) if r[34] & 1 else None,
                drain=drain(w[4]), control=control,
                counter_note='Only PS/S01 AR/R and writes are lifetime totals. RLAST/non_OKAY/HC2 are observed epoch values; no cumulative value is invented.')


def load_record(path):
    value = json.loads(path.read_text())
    return value.get('normalized', value)


def held_matches(io, evidence, saved):
    current = read_control(io, evidence)
    need(current['raw'] == saved['control']['raw'], 'Held control snapshot changed since persisted evidence')
    h = header(io, MON)
    need(h['status'] == 0 and h['request'] == h['response'] == saved['observer_generation'],
         'Monitor generation differs from persisted evidence')
    return current


def run(args, evidence, io):
    need(runtime() == args.boot_id, 'Runtime identity changed')
    active = owners()
    evidence.save('owners', owners=active)
    need(not active, 'Device has another owner')
    old = load_record(args.before) if args.before else None
    if args.operation == 'snapshot':
        initial = monitor_start(io, evidence)
        time.sleep(args.window_ms / 1000.0)
        raw = monitor_finish(io, evidence, initial)
        wait_command(io, CTRL, SNAP, evidence)
        control = read_control(io, evidence)
        normalized = normalize(raw, control, args.boot_id, old)
    elif args.operation == 'consume':
        need(old is not None and old['valid'] is True and old['boot_id'] == args.boot_id, 'Persisted before record required')
        gate = json.loads(args.seed_gate.read_text())
        need(gate['eligible'] is True and gate['classification'] == 'known_unmatched_return' and
             gate['boot_id'] == args.boot_id and gate['PS_AR'] == 0 and
             gate['PS_R'] == old['counts_lifetime']['PS']['R'], 'Known same-boot seed gate missing/differs')
        control = held_matches(io, evidence, old)
        need(not control['arm_used'] and not control['arm_issued'] and not control['rearm_used'] and
             not control['error'] and old['drain']['state'] == 0, 'ARM already used or not WAIT')
        need(old['pins']['S01']['RVALID'] and old['pins']['S01']['RID'] == 0 and
             old['pins']['S01']['RRESP'] == 0 and not old['pins']['S01']['RREADY'], 'No held valid S01 seed')
        fresh_json(evidence.directory/'attempt.json', dict(operation='consume', boot_id=args.boot_id,
                   before=str(args.before), seed_gate=str(args.seed_gate), control_request=control['request'],
                   automatic_retry=False, SDK=0, DMA=0, HDMI_START=0))
        initial = monitor_start(io, evidence)  # Capture the complete consume delta, not a later idle epoch.
        arm_ack = wait_command(io, CTRL, CONS, evidence)
        time.sleep(0.002)  # >4096 nominal 200MHz HP cycles; no polling/repeated SNAP commands.
        snap_ack = wait_command(io, CTRL, SNAP, evidence)
        control = read_control(io, evidence)
        raw = monitor_finish(io, evidence, initial)
        normalized = normalize(raw, control, args.boot_id, old)
        normalized['control']['arm_request'] = arm_ack['request']
        normalized['control']['snapshot_request'] = snap_ack['request']
        normalized['control']['commands'] = [dict(opcode=CONS, request=arm_ack['request']),
                                             dict(opcode=SNAP, request=snap_ack['request'])]
        need(snap_ack['request'] == old['control']['request']+2 and
             arm_ack['request'] == old['control']['request']+1 and control['arm_used'] and
             safe_terminal(normalized['drain']), 'Nonzero consume not acknowledged/terminal; no second command')
    else:
        need(old is not None and old['valid'] is True and old['boot_id'] == args.boot_id, 'Persisted after-consume record required as --before')
        gate = json.loads(args.consume_gate.read_text())
        need(gate['eligible'] is True and gate['boot_id'] == args.boot_id and
             gate['protocol_history_preserved'] is True and
             gate['discard_beats'] == old['drain']['beats'], 'Same-boot consume gate missing/differs')
        control = held_matches(io, evidence, old)
        need(control['arm_used'] and not control['rearm_used'] and not control['rearm_issued'] and
             not control['error'] and safe_terminal(old['drain']) and
             not any(old['levels'][x] for x in ('PS_RVALID', 'S01_RVALID', 'HC2_RVALID')),
             'Checker rearm precondition unsafe/already used')
        fresh_json(evidence.directory/'attempt.json', dict(operation='checker-rearm', boot_id=args.boot_id,
                   after_consume=str(args.before), consume_gate=str(args.consume_gate),
                   control_request=control['request'], preserved_full_PC_status=control['full_PC_status'],
                   automatic_retry=False, functional_reset=False))
        clear_ack = wait_command(io, CTRL, CHKR, evidence)
        time.sleep(0.002)
        snap_ack = wait_command(io, CTRL, SNAP, evidence)
        control = read_control(io, evidence)
        need(control['arm_used'] and control['rearm_used'] and not control['error'] and
             control['PC_checker_ready'] and control['PC_system_resetn'] and
             not (control['full_PC_status'] & MANDATORY_MASK) and safe_terminal(drain(control['drain_raw'])),
             'Fresh post-CHKR checker not ready/has mandatory status; no retry')
        need(clear_ack['request'] == old['control']['request']+1 and
             snap_ack['request'] == old['control']['request']+2, 'CHKR/SNAP generations differ')
        normalized = dict(valid=True, boot_id=args.boot_id, checker_ready_for_SDK=True,
                          control=control, historical_protocol_file_unchanged=True,
                          input_after_consume=str(args.before), consume_gate=str(args.consume_gate),
                          SDK=0, DMA=0, HDMI_START=0, functional_recovery_proved=False)
        raw = None
    need(runtime() == args.boot_id and not owners(), 'Boot/ownership changed during capture')
    return dict(valid=True, operation=args.operation, boot_id=args.boot_id,
                raw_snapshot=raw, normalized=normalized, automatic_retry=False,
                functional_recovery_proved=False, SDK=0, DMA=0, HDMI_START=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('snapshot', 'consume', 'checker-rearm'))
    parser.add_argument('output', type=Path, help='New absolute directory, never reused')
    parser.add_argument('boot_id')
    parser.add_argument('--before', type=Path, help='Persisted result.json; for checker-rearm use the after-consume record')
    parser.add_argument('--seed-gate', type=Path)
    parser.add_argument('--consume-gate', type=Path)
    parser.add_argument('--window-ms', type=int, default=20)
    args = parser.parse_args()
    need(args.output.is_absolute() and 1 <= args.window_ms <= 1000, 'Absolute fresh output and bounded window required')
    need(args.operation != 'consume' or (args.before and args.seed_gate), 'consume requires --before and --seed-gate')
    need(args.operation != 'checker-rearm' or (args.before and args.consume_gate), 'checker-rearm requires --before and --consume-gate')
    evidence = Evidence(args.output)
    io = None
    result = dict(valid=False, inconclusive=True, operation=args.operation, boot_id=args.boot_id,
                  automatic_retry=False, SDK=0, DMA=0, HDMI_START=0, functional_recovery_proved=False)
    try:
        evidence.save('begin', operation=args.operation, expected_boot_id=args.boot_id, actual_boot_id=runtime())
        need(runtime() == args.boot_id and not owners(), 'Boot identity/device ownership differs before mapping')
        io = MMIO(evidence, args.boot_id)
        # HDMI function aperture is exclusively read-only in this program.
        evidence.save('HDMI_read_only', words={hex(i): io.read(i) for i in (0,0x10,0x24,0x28,0x2c,0x30,0x40)})
        result = run(args, evidence, io)
    except Exception as error:
        result['error'] = str(error)
        if isinstance(error, DiagnosticCommandFailure):
            result['command_failure'] = error.details
        evidence.save('inconclusive', error=str(error), automatic_retry=False)
    finally:
        if io is not None:
            io.close()
        fresh_json(args.output/'result.json', result)
        evidence.close()
    print(json.dumps({k:v for k,v in result.items() if k not in ('raw_snapshot','normalized')}))
    return 0 if result['valid'] else 2


if __name__ == '__main__':
    raise SystemExit(main())

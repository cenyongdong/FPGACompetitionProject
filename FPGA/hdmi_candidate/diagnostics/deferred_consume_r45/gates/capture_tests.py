"""Offline MMIO models only; never opens /dev/mem or claims a board pass."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import sys

sys.dont_write_bytecode = True
import capture_deferred as c

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


class Evidence:
    directory = Path('/offline-only')
    def __init__(self): self.events = []
    def save(self, event, **values): self.events.append(dict(event=event, **values))


class Input:
    def __init__(self, value): self.value = value
    def read_text(self): return json.dumps(self.value)
    def __str__(self): return 'offline-memory-input'


def bundle(after=False):
    w, b, r = [0]*104, [0]*19, [0]*128
    status = 2 | (16 << 3) | (80 << 12) | (1 << 25) if after else 0
    w[0:5] = [0x41495201, 4000, 0x19, 0, status]
    b[0], b[4], b[6], b[18] = 0x42545201, 16 if after else 6, 16 if after else 0, 128
    r[0:2] = [0x50534c01, 3]
    r[5], r[7], r[32], r[34], r[37], r[46] = 67, 1, 20000100 if after else 19999900, 2, b[4], 342533
    for at, rid, accepted in ((72, 0, 16), (88, 32, 10)):
        w[at+11] = 0 if after else 4 | (rid << 19)
        if after: w[at+1], w[at+2], w[at+7] = accepted, 1, accepted
    return dict(initial_generation=8, generation=10 if after else 8,
                words=w, boot_words=b, release_words=r, header_after={})


class IO:
    def __init__(self, fault=None):
        self.monitor_seq, self.control_seq = 8, 3
        self.consumed = self.cleared = False
        self.arm_issued = self.rearm_issued = False
        self.writes, self.fault = [], fault
        self.held = bundle(False)
        self.held_control = self.control_words()

    def control_words(self):
        after = self.consumed
        flags = 12 | int(after) | (2 if self.cleared else 0)
        cycle = 20000095 if after else 19999950
        arm = 19999999 if after else 0
        pc = 0 if self.cleared else sum(1 << bit for bit in (58, 59, 92, 93, 95))
        return [bundle(after)['words'][4], flags, cycle, 0, arm, 0] + [(pc >> (32*i)) & 0xffffffff for i in range(5)]

    def read(self, offset):
        if c.CTRL <= offset <= c.CTRL+0x38:
            off = offset-c.CTRL
            if off == 0: return int(self.arm_issued)*4 + int(self.rearm_issued)*8
            if off == 4: return 0x48444301
            if off in (8,12): return self.control_seq
            return self.held_control[(off-0x10)//4]
        if c.MON <= offset <= c.MON+0x1ff:
            off = offset-c.MON
            if off == 0: return 0
            if off == 4: return 0x41495201
            if off in (8,12): return self.monitor_seq
            if off == 0x10: return 104
            if 0x14 <= off <= 0x3c: return self.held['boot_words'][(off-0x14)//4]
            if 0x40 <= off <= 0x1dc: return self.held['words'][(off-0x40)//4]
            if 0x1e0 <= off <= 0x1fc: return self.held['boot_words'][11+(off-0x1e0)//4]
        if 0x600 <= offset < 0x800: return self.held['release_words'][(offset-0x600)//4]
        return 0

    def write(self, offset, value):
        self.writes.append((offset, value))
        if self.fault == 'timeout': return
        step = 2 if self.fault == 'jump' else 1
        if offset == c.MON:
            self.monitor_seq += step
            if value == 2: self.held = bundle(self.consumed)
        else:
            self.control_seq += step
            # A CONS/CHKR immediate ACK retains the pre-action source bundle.
            self.held_control = self.control_words()
            if value == c.CONS: self.consumed = self.arm_issued = True
            if value == c.CHKR: self.cleared = self.rearm_issued = True


def main():
    cases = []
    def check(name, action):
        try:
            action()
            cases.append(dict(name=name, passed=True))
        except Exception as error:
            cases.append(dict(name=name, passed=False, error=str(error)))
    def require(ok):
        assert ok

    c.runtime = lambda: 'offline-same-boot'
    c.owners = lambda: []
    c.time.sleep = lambda seconds: None
    saved = []
    c.fresh_json = lambda path, value: saved.append((str(path), copy.deepcopy(value)))

    def nonzero_generation():
        io, e = IO(), Evidence()
        initial = c.monitor_start(io,e)
        raw = c.monitor_finish(io,e,initial)
        require(initial == 8 and raw['generation'] == 10 and io.writes == [(c.MON,1),(c.MON,2)])
        require(len(raw['words']) == 104 and len(raw['boot_words']) == 19 and len(raw['release_words']) == 128)
    check('nonzero_even_monitor_generation_and_full_raw',nonzero_generation)

    def no_retry(fault):
        io,e = IO(fault),Evidence()
        try: c.wait_command(io,c.CTRL,c.CONS,e,timeout=0)
        except RuntimeError: pass
        else: raise AssertionError('uncertain command accepted')
        require(io.writes == [(c.CTRL,c.CONS)])
    check('timeout_never_reissues_CONS',lambda:no_retry('timeout'))
    check('unexpected_ACK_never_reissues_CONS',lambda:no_retry('jump'))

    def write_whitelist():
        fake = SimpleNamespace(page=bytearray(4096),boot_id='offline-same-boot',evidence=Evidence())
        for off,val in ((0,1),(0x10,1),(c.CTRL,0),(c.MON,c.CONS),(c.CTRL+4,c.CONS)):
            try: c.MMIO.write(fake,off,val)
            except RuntimeError: pass
            else: raise AssertionError('functional/invalid write permitted')
        require(not fake.evidence.events and not any(fake.page))
        c.MMIO.write(fake,c.CTRL,c.SNAP)
        require(fake.evidence.events[0]['event']=='command_attempt')
    check('only_diagnostic_command_writes_attempt_before_store',write_whitelist)

    io,e = IO(),Evidence()
    control = c.read_control(io,e)
    before = c.normalize(bundle(False),control,'offline-same-boot')
    seed = dict(eligible=True,classification='known_unmatched_return',boot_id='offline-same-boot',PS_AR=0,PS_R=6)
    args = SimpleNamespace(operation='consume',boot_id='offline-same-boot',before=Input(dict(normalized=before)),
                           seed_gate=Input(seed),consume_gate=None,window_ms=20)
    after_result = None
    def one_consume():
        nonlocal after_result
        after_result = c.run(args,e,io)
        a = after_result['normalized']
        require(io.writes == [(c.MON,1),(c.CTRL,c.CONS),(c.CTRL,c.SNAP),(c.MON,2)])
        require(a['control']['request']==5 and a['control']['arm_request']==4 and
                a['control']['snapshot_request']==5 and a['observer_generation']==10)
        require(a['control']['arm_HP_cycle_raw']==19999999 and
                a['control']['first_sampled_RUN_HP_cycle_derived']==20000000)
        require(a['counts_lifetime']['PS']['R']==16 and a['counts_epoch']['PS']['R']==10 and
                a['counts_epoch']['S01']['R']==a['drain']['beats']==16)
        require('RLAST' not in a['counts_lifetime']['PS'] and len(saved)==1 and saved[0][1]['automatic_retry'] is False)
        require(a['control_capture_HP_cycle']<a['HP_cycle'])
    check('single_CONS_then_SNAP_prefill6_delta10_16_separate_cuts',one_consume)

    def repeat_rejected():
        count = len(io.writes)
        again = copy.copy(args)
        again.before = Input(after_result)
        again.seed_gate = Input(dict(seed,PS_R=16))
        try:c.run(again,Evidence(),io)
        except RuntimeError:pass
        else:raise AssertionError('used ARM permitted')
        require(len(io.writes)==count)
    check('second_consume_rejected_without_write',repeat_rejected)

    def rearm():
        gate = dict(eligible=True,boot_id='offline-same-boot',protocol_history_preserved=True,discard_beats=16)
        args2 = SimpleNamespace(operation='checker-rearm',boot_id='offline-same-boot',before=Input(after_result),
                                consume_gate=Input(gate))
        result = c.run(args2,Evidence(),io)
        require(io.writes[-2:]==[(c.CTRL,c.CHKR),(c.CTRL,c.SNAP)] and
                result['normalized']['checker_ready_for_SDK'] is True and io.control_seq==7)
        require(result['normalized']['control']['full_PC_status']==0 and after_result['normalized']['control']['full_PC_status']!=0)
    check('single_CHKR_then_SNAP_keeps_historical_input',rearm)

    def prior_owner():
        c.owners = lambda:[dict(pid='example',target='/dev/axi')]
        target=IO()
        try:c.run(args,Evidence(),target)
        except RuntimeError:pass
        else:raise AssertionError('owner accepted')
        require(not target.writes)
        c.owners=lambda:[]
    check('active_owner_refused_before_commands',prior_owner)

    def missing_raw():
        raw=bundle()
        raw['boot_words']=[]
        try:c.normalize(raw,control,'offline-same-boot')
        except (IndexError,KeyError,RuntimeError):return
        raise AssertionError('missing native values guessed')
    check('missing_raw_is_inconclusive',missing_raw)

    def real_r38_raw():
        base=ROOT/'tools/pose-v1/evidence/hp2-bounded-drain-20261024-r38/board-candidate/run-1'
        legacy=json.loads((base/'legacy/trace.jsonl').read_text().splitlines()[0])
        release=[json.loads(line) for line in (base/'release/raw.jsonl').read_text().splitlines()][-1]
        # Only the control wrapper is derived: r38 predates this new CSR. The
        # real boot/release/monitor words remain untouched; no board pass claim.
        raw=dict(words=legacy['words'],boot_words=release['boot_words'],release_words=release['words'],generation=2)
        derived_control=dict(control,drain_raw=raw['words'][4])
        value=c.normalize(raw,derived_control,release['boot_id'])
        require(value['counts_lifetime']['PS']['R']==value['counts_lifetime']['S01']['R']==16)
        require('RLAST' not in value['counts_lifetime']['PS'])
    check('actual_r38_words_normalize_without_fabricated_lifetime_RLAST',real_r38_raw)

    report=dict(offline_MMIO_models_only=True,board_test_pass_claimed=False,
                total=len(cases),passed=sum(case['passed'] for case in cases),cases=cases)
    (HERE/'capture-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for case in cases:
        if not case['passed']:print(case)
    assert report['passed']==report['total']
    print('OFFLINE_COLLECTOR_TESTS',report['passed'],'/',report['total'],'NO_BOARD_PASS_CLAIM')


if __name__=='__main__':main()

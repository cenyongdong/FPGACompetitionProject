"""Actual-evidence-derived fixtures; successful synthetic gates are not board passes."""
import copy
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from consume_gate import evaluate

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
R38 = ROOT / 'tools/pose-v1/evidence/hp2-bounded-drain-20261024-r38/board-candidate/run-1'
R44 = ROOT / 'tools/pose-v1/evidence/ai-hdmi-startup-control-20261024-r44/board-candidate/seed/run-1'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def fixture(prefill=6):
    """Counterfactual deferred timeline using actual IDs/RESP/LAST and seed counts.

    It intentionally has a derived identity, never either original boot ID.
    PS/S01 event positions are a model; original captures are never rewritten.
    """
    original = load(R38 / 'cycletrace/raw.decoded.json')
    original_rows = original['banks'][1]['rows']
    ps = [r for r in original_rows if r['PS_RVALID'] and r['PS_RREADY']]
    s01 = [r for r in original_rows if r['S01_RVALID'] and r['S01_RREADY']]
    seed = load(R44 / 'metadata/observe.json')
    assert len(ps) == len(s01) == 16 and seed['decoded']['raw_HP_handshakes']['PS_R'] == 6
    arm = 20_000_000
    identity = 'derived-offline-prefill-' + str(prefill)
    counts = {ch: dict(AR=0, R=0) for ch in ('PS', 'S01')}
    counts['PS']['R'] = prefill
    counts['writes'] = {k: 0 for k in ('legacy_AW', 'legacy_W', 'legacy_B', 'PS_AW', 'PS_W', 'PS_B')}
    epoch = {ch: dict(AR=0, R=0, RLAST=0, non_OKAY=0, ARVALID_cycles=0,
                     RVALID_cycles=0, expected_R=0) for ch in ('HC0','HC1','HC2','HC3','PS','S01')}
    pins = {ch: dict(ARVALID=False, RVALID=False, RREADY=False, RID=0, RRESP=0)
            for ch in epoch}
    pins['PS'].update(RVALID=True, RID=0x20)
    pins['S01']['RVALID'] = True
    before = dict(boot_id=identity, valid=True, HP_cycle=arm-100, observer_generation=8,
                  overflow=False, SDK=0, DMA=0, HDMI_START=0,
                  first_RVALID_HP_cycle=seed['decoded']['first_raw_PS_RVALID_HP_cycle'],
                  first_AR_HP_cycle=None, counts_lifetime=counts, counts_epoch=epoch, pins=pins,
                  control_capture_HP_cycle=arm-50,
                  control=dict(request=3, response=3, arm_used=False, arm_issued=False,
                               rearm_used=False,rearm_issued=False,error=False,
                               capture_HP_cycle=arm-50, PC_checker_ready=True, PC_system_resetn=True),
                  drain=dict(state=0, beats=0, HP_cycles=0, saw_RLAST=False,
                             saw_RRESP_error=False, bad_ID=False, late_RVALID=False),
                  levels=dict(PS_HP2_resetn=True, PL_HP2_resetn=True, HP_reset=False,
                              PS_ARVALID=False, S01_ARVALID=False, HC2_ARVALID=False,
                              PS_RVALID=True, S01_RVALID=True, HC2_RVALID=False))
    rows = []
    s01_start = 0 if prefill else 4
    final_s01 = s01_start + len(s01) - 1
    quiet = final_s01 + 1 + 64
    for k in range(-8, quiet+9):
        row = {key: 0 for key in original_rows[0]}
        row.update(HP_cycle=arm+k, PS_HP2_resetn=1, PL_HP2_resetn=1, HP_reset=0,
                   HC2_RREADY=1, drain_state=0 if k < 0 else (1 if k < quiet else 2))
        if k < 0:
            row.update(PS_RVALID=1, PS_RID=0x20, S01_RVALID=int(bool(prefill)))
        for ch, data, start in [('PS', ps[prefill:], 0), ('S01', s01, s01_start)]:
            index = k-start
            if 0 <= index < len(data):
                source = data[index]
                row.update({ch+'_'+key: source[ch+'_'+key] for key in ('RID', 'RRESP', 'RLAST', 'RDATA')})
                row[ch+'_RVALID'] = row[ch+'_RREADY'] = 1
        rows.append(row)
    after = copy.deepcopy(before)
    after['HP_cycle'] = arm + quiet + 20
    after['observer_generation'] += 2
    for ch in ('PS', 'S01'):
        after['counts_lifetime'][ch].update(R=16)
        after['counts_epoch'][ch].update(R=16-prefill if ch=='PS' else 16, RLAST=1)
        after['levels'][ch+'_RVALID'] = False
        after['pins'][ch]['RVALID'] = False
    after['control'].update(request=5,response=5,arm_used=True,arm_issued=True,
                            arm_request=4,snapshot_request=5,
                            commands=[dict(opcode=0x434f4e53,request=4),dict(opcode=0x534e4150,request=5)],
                            arm_HP_cycle_raw=arm-1, first_sampled_RUN_HP_cycle_derived=arm,
                            capture_HP_cycle=arm+quiet+15)
    after['control_capture_HP_cycle'] = arm+quiet+15
    after['drain'].update(state=2, beats=16, HP_cycles=quiet, saw_RLAST=True)
    trace = dict(boot_id=identity, valid=True, published=True, overflow=False,
                 arm_HP_cycle=arm, count=len(rows), rows=rows)
    pb = load(R44 / 'protocol/raw.decoded.json')
    pb.update(boot_id=identity, valid=True, capture_HP_cycle=arm-50)
    pb['live_status'] = pb['first_status']
    before['control']['full_PC_status'] = pb['live_status']
    after['control']['full_PC_status'] = pb['live_status']
    pa = copy.deepcopy(pb)
    pa['capture_HP_cycle'] = after['control_capture_HP_cycle']
    return [before, after, trace, pb, pa]


def main():
    cases = []
    def check(name, expected, change=None, prefill=6):
        args = fixture(prefill)
        if change:
            change(*args)
        original = copy.deepcopy(args)
        result = evaluate(*args)
        passed = result['eligible'] is expected and original == args
        cases.append(dict(name=name, expected_eligible=expected, result=result,
                          input_unchanged=original == args, passed=passed))

    check('derived_prefill6_PS_delta10_S01_delta16', True)
    check('derived_prefill0_PS_delta16_S01_delta16', True, prefill=0)
    def entirely_prefilled(b,a,t,p,q):
        a['counts_epoch']['PS']['RLAST'] = 0
    check('all_PS_prefilled_S01_trace_proves_RLAST', True, entirely_prefilled, prefill=16)
    check('actual_r44_seed_vs_actual_r38_boot_cannot_be_spliced', False,
          lambda b,a,t,p,q: (b.update(boot_id=load(R44/'metadata/observe.json')['boot_id']),
                              a.update(boot_id=load(R38/'metadata/observe.json')['boot_id'])))
    check('trace_other_boot', False, lambda b,a,t,p,q: t.update(boot_id='another-boot'))
    check('counter_epoch_reset', False, lambda b,a,t,p,q: a.update(observer_generation=2))
    check('counter_decrease', False, lambda b,a,t,p,q: a['counts_lifetime']['PS'].update(R=5))
    check('forget_prefilled6', False, lambda b,a,t,p,q: a['counts_lifetime']['PS'].update(R=10))
    check('missing_one_S01_beat', False, lambda b,a,t,p,q: a['counts_lifetime']['S01'].update(R=15))
    check('new_AR', False, lambda b,a,t,p,q: a['counts_lifetime']['PS'].update(AR=1))
    check('new_write', False, lambda b,a,t,p,q: a['counts_lifetime']['writes'].update(legacy_W=1))
    check('HC2_misdelivery', False, lambda b,a,t,p,q: a['counts_epoch']['HC2'].update(R=1))
    check('HC0_misdelivery', False, lambda b,a,t,p,q: a['counts_epoch']['HC0'].update(R=1))
    check('bad_PS_RID', False, lambda b,a,t,p,q: next(r for r in t['rows'] if r['PS_RVALID']).update(PS_RID=1))
    check('bad_S01_RID', False, lambda b,a,t,p,q: next(r for r in t['rows'] if r['S01_RVALID']).update(S01_RID=1))
    check('non_OKAY', False, lambda b,a,t,p,q: next(r for r in t['rows'] if r['S01_RVALID']).update(S01_RRESP=2))
    check('missing_RLAST', False, lambda b,a,t,p,q: next(r for r in t['rows'] if r['S01_RLAST']).update(S01_RLAST=0))
    check('extra_RLAST', False, lambda b,a,t,p,q: next(r for r in t['rows'] if r['S01_RVALID'] and r['S01_RREADY']).update(S01_RLAST=1))
    check('native_capacity_bit', False, lambda b,a,t,p,q: q.update(live_status=1<<78))
    check('native_history_cleared', False, lambda b,a,t,p,q: q.update(published=False))
    check('native_history_replaced', False, lambda b,a,t,p,q: q['first_indication'].update(HP_cycle=1))
    check('third_control_command', False, lambda b,a,t,p,q: a['control'].update(request=6, response=6))
    check('missing_SNAP', False, lambda b,a,t,p,q: a['control'].update(request=4, response=4))
    check('ARM_edge_not_first_RUN', False, lambda b,a,t,p,q: a['control'].update(arm_HP_cycle_raw=t['arm_HP_cycle']))
    check('control_after_FREEZE_not_claimed_same_cut', False,
          lambda b,a,t,p,q: q.update(capture_HP_cycle=a['HP_cycle']+1))
    check('control_live_status_not_acknowledged', False, lambda b,a,t,p,q: q.update(live_status=1<<58))
    check('monitor_epoch_R_differs_lifetime_delta', False, lambda b,a,t,p,q: a['counts_epoch']['PS'].update(R=16))
    check('epoch_non_OKAY', False, lambda b,a,t,p,q: a['counts_epoch']['PS'].update(non_OKAY=1))
    check('ARM_already_used', False, lambda b,a,t,p,q: b['control'].update(arm_used=True))
    check('ABORT_terminal', False, lambda b,a,t,p,q: a['drain'].update(state=5))
    check('beat_limit', False, lambda b,a,t,p,q: a['drain'].update(beats=256))
    check('cycle_limit', False, lambda b,a,t,p,q: a['drain'].update(HP_cycles=4096))
    check('late_return', False, lambda b,a,t,p,q: a['drain'].update(late_RVALID=True))
    check('return_still_present', False, lambda b,a,t,p,q: a['levels'].update(PS_RVALID=True))
    check('trace_gap', False, lambda b,a,t,p,q: t['rows'][8].update(HP_cycle=t['arm_HP_cycle']+1))
    check('trace_count_mismatch', False, lambda b,a,t,p,q: t.update(count=t['count']-1))
    check('WAIT_ready_before_ARM', False, lambda b,a,t,p,q: t['rows'][0].update(S01_RREADY=1))
    check('RUN_duration_mismatch', False, lambda b,a,t,p,q: a['drain'].update(HP_cycles=81))
    check('counter_first_R_history_changed', False, lambda b,a,t,p,q: a.update(first_RVALID_HP_cycle=1))
    check('trace_state_rearmed', False, lambda b,a,t,p,q: t['rows'][-1].update(drain_state=1))
    check('overflow', False, lambda b,a,t,p,q: a.update(overflow=True))
    check('SDK_already_opened', False, lambda b,a,t,p,q: b.update(SDK=1))
    report = dict(derived_fixtures_only=True, board_test_pass_claimed=False,
                  sources=[str(R38/'cycletrace/raw.decoded.json'), str(R44/'metadata/observe.json'),
                           str(R44/'protocol/raw.decoded.json')],
                  total=len(cases), passed=sum(c['passed'] for c in cases), cases=cases)
    (HERE/'gate-tests.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for case in cases:
        if not case['passed']:
            print(json.dumps(case, ensure_ascii=False))
    assert report['passed'] == report['total'], 'Offline conservation gate failed'
    print('DERIVED_OFFLINE_GATE_TESTS', report['passed'], '/', report['total'], 'NO_BOARD_PASS_CLAIM')


if __name__ == '__main__':
    main()

from pathlib import Path
import json,tarfile,hashlib
W=Path(__file__).resolve().parent
E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hp2-mmio32-20261024-r46')
run=E/'board-candidate-final/run-1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
before=read(run/'observe-before/capture/result.json')['normalized']
after=read(run/'revalidate-consume/capture/result.json')['normalized']
gate=read(run/'metadata/consumed-gate.json')
ready=read(run/'metadata/sdk-ready.json')
frame=read(run/'metadata/frame-test.json')
post=read(run/'metadata/post-frame-protocol.json')
physical=read(E/'physical-screen-observation.json')
with tarfile.open(E/'recovery-metadata.tar.gz') as t:
    final=json.load(t.extractfile('metadata/final-audit.json'))
    closed=json.load(t.extractfile('metadata/closed.json'))
    stopped=json.load(t.extractfile('metadata/diagnostic-continuation-stopped.json'))
assert closed['closed'] and closed['candidate_starts']==1 and closed['original_fallbacks']==1 and closed['SDK_Open_attempts']==1
assert final['fpga_state']=='operating' and not final['device_owners'] and len(final['startup_files'])==9 and len(final['SDK'])==6
assert final['boot_id']!=before['boot_id'] and gate['eligible'] and after['drain']['beats']==16
assert ready['control']['full_PC_status']==post['full_PC_status']==0
assert physical['passed'] is False and stopped['stage']=='physical-screen-observation'
assert not (run/'metadata/joint-test.attempt.json').exists()
rows=[json.loads(x) for x in (run/'frame-test/frames/hdmi.jsonl').read_text().splitlines()]
commands=[r for r in rows if r['event']=='command']
start=next(r for r in commands if r['op']==1)
flip=next(r for r in commands if r['op']==2)
stop=next(r for r in commands if r['op']==3)
adoptions=[next(r for r in commands if r['accepted']==i) for i in (100,101)]
timeline=dict(clock='Linux CLOCK_MONOTONIC ns',START_ns=start['request_sent_ns'],
    first_adopt_observed_ns=adoptions[0]['snapshot_read_ns'],FLIP_ns=flip['request_sent_ns'],
    second_adopt_observed_ns=adoptions[1]['snapshot_read_ns'],STOP_ns=stop['request_sent_ns'],
    first_adopt_to_FLIP_seconds=(flip['request_sent_ns']-adoptions[0]['snapshot_read_ns'])/1e9,
    second_adopt_to_STOP_seconds=(stop['request_sent_ns']-adoptions[1]['snapshot_read_ns'])/1e9,
    START_to_STOP_seconds=(stop['request_sent_ns']-start['request_sent_ns'])/1e9,
    command_snapshots=len(commands),all_command_faults_zero=all(r['faults']==0 for r in commands))
regs0=read(run/'metadata/hdmi-registers-before.json')['values'];regs1=read(run/'metadata/hdmi-registers-after.json')['values']
pixel_delta=(regs1['0x38']-regs0['0x38'])&0xffffffff
csr_delta=(regs1['0x3c']-regs0['0x3c'])&0xffffffff
clock=dict(pixel_delta_u32=pixel_delta,csr_delta_u32=csr_delta,
    counter_ratio=pixel_delta/csr_delta,
    nominal_frequency_registers_are_constants=True,
    note='Endpoint counter deltas support continuing pixel/CSR activity; not a TMDS signal measurement and not proof of no transient reset.')
ram=[]
for slot in (0,1):
    a=(run/f'frame-test/frames/memory-actual-{slot}.bin').read_bytes()
    b=(run/f'frame-test/frames/memory-source-{slot}.bin').read_bytes()
    assert a==b and len(a)==4147200
    ram.append(dict(slot=slot,bytes=len(a),bitwise_equal=True))
report=dict(boot_id=before['boot_id'],same_boot_actual_consumption=True,discard_beats=16,
    initial_counts=before['counts_lifetime'],final_pre_SDK_counts=after['counts_lifetime'],
    drain=after['drain'],consume_gate=gate,
    checker_before_function_status=0,checker_after_patterns_status=0,
    software_pattern_controller_passed=frame['passed'],
    physical_HDMI_passed=False,physical_observation=physical,
    pattern_timeline=timeline,pixel_counter_observation=clock,RAM_probe=ram,
    AXI_counts=frame['AXI_counts'],
    joint_executed=False,AI_inference_executed=False,numeric_acceptance_claimed=False,
    no_functional_retry=True,original_runtime_verified=True,final_original_boot_id=final['boot_id'],
    actual=dict(candidate_starts=1,original_fallbacks=1,SDK_Open=1),remaining=closed['remaining'],
    HDMI_long_term_executed=False,AI_four_HC_unchanged=True,
    post_function_drain_bit31_set=bool(post['control']['drain_raw']>>31),
    drain_bit31_note='RTL latches any S01 RVALID in QUIET, including later legal HDMI responses; not an independent post-START malformed-return alarm.')
(E/'result-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
state=read(E/'state.json')
state.update(status='closed_display_failure_original_runtime_restored',active=False,
    actual_same_boot_consumption_admitted=True,discard_beats=16,
    software_component_passed=True,physical_HDMI_passed=False,component_passed=False,
    joint_passed=False,joint_executed=False,AI_inference_executed=False,
    stop_reason='User confirmed pattern only flashed/few seconds before black; no functional retry.',
    runs=[dict(run='run-1',boot_id=before['boot_id'],classification='known_unmatched_return',
               consume_eligible=True,discard_beats=16,fresh_checker_160_before=0,
               software_pattern_passed=True,fresh_checker_160_after=0,physical_HDMI_passed=False,
               joint_executed=False,joint_passed=False)],
    continuation_source_commit='eee67cd4',continuation_approval_commit='e244ec00',
    candidate_archive='candidate-capture-final.tar.gz',recovery_archive='recovery-metadata.tar.gz',
    UART_all_closed=all(read(d/'reader.json')['closed'] and read(d/'reader.json')['transmitted_bytes']==0
                        for d in E.glob('uart-*') if d.is_dir() and (d/'ready.json').exists()))
(E/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(timeline=timeline,clock=clock,actual=state['actual'],original_runtime_verified=True,
    physical_HDMI_passed=False,AI_inference_executed=False,UART_all_closed=state['UART_all_closed'])))

from pathlib import Path
import json, math, statistics, tarfile
e=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-long-native-20261024-r49')
with tarfile.open(e/'candidate-evidence.tar.gz') as t:
    def get(name):return json.load(t.extractfile(name))
    def rows(name):return [json.loads(x) for x in t.extractfile(name).read().decode().splitlines()]
    admission=get('startup-admission.json');seed=get('startup/before-seed.json')
    native=get('metadata/long-test.json');failure=get('software/run-long-native/results/failure.json')
    oracle=get('software/run-long-native/results/index-oracle/summary.json')
    hdmi=rows('software/run-long-native/results/hdmi.jsonl')
    frames=rows('software/run-long-native/results/hdmi-frames.jsonl')
    delivery=rows('software/run-long-native/results/delivery-timing.jsonl')
def stats(values):
    values=sorted(values)
    return dict(count=len(values),mean_ms=statistics.mean(values),
                p95_ms=values[math.ceil(.95*len(values))-1],max_ms=values[-1])
timing=dict(render=stats([x['render_rgb565_ms'] for x in frames]),
            show=stats([x['show_ms'] for x in frames]),
            board_ACK_wait=stats([(x['ack_end_ns']-x['ack_begin_ns'])/1e6 for x in delivery
                                 if x.get('ack_end_ns',0)>=x.get('ack_begin_ns',1)]))
host=json.loads((e/'host/summary.json').read_text())
analysis=json.loads((e/'host/analysis.json').read_text())
audit=json.loads((e/'final-audit.json').read_text());closed=json.loads((e/'closed.json').read_text())
summary=dict(passed=False,host_sent=host['sent'],host_confirmed=host['received'],
    full_original_records=analysis['records'],native_completed=failure['completed'],
    native_host_archived=failure['host_archived'],HDMI_adopted=native['HDMI_adopted'],
    host_errors=host['errors'],native_exit=native['native_exit'],native_seconds=native['seconds'],
    startup_mode=admission['mode'],startup_PS_AR=seed['PS_AR'],startup_PS_R=seed['PS_R'],
    protocol_snapshots=native['protocol_snapshots'],fresh_native_protocol_clean=native['all_fresh_native_protocol_checks_passed'],
    STOP_proved=any(x.get('event')=='stop_proved' for x in hdmi),
    frames_released=any(x.get('event')=='frames_released_after_stop' for x in hdmi),
    finite_identity_selection_errors=analysis['finite_and_identity_errors'],
    frozen_reference_passes=sum(x['accepted'] for x in analysis['frozen_reference_checks']),
    checked_max_joint_delta_mm=max(x['max_checked_joint_delta_mm'] for x in analysis['frozen_reference_checks']),
    index_oracle=oracle,output_hz_short_sample=host['output_rate_hz'],timing=timing,
    screen_user_report='骨架仅短暂可见，未确认连续显示',continuous_screen_verified=False,
    actual=dict(candidate_starts=1,original_fallbacks=1,SDK_Open=1),
    remaining=dict(candidate_starts=0,original_fallbacks=0,SDK_Open=0),
    original_runtime_restored=closed['closed'] and audit['boot_id']==closed['boot_id'],
    original_runtime_boot_id=audit['boot_id'],original_BOOT_sha256=audit['startup_files']['BOOT.BIN']['sha256'],
    original_files_verified=len(audit['startup_files']),SDK_files_verified=len(audit['SDK']),
    AI_four_HC_unchanged=True,hardware_rebuilt=False,automatic_retry=False,long_stability_proved=False)
(e/'result-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
state=json.loads((e/'state.json').read_text())
state.update(status='closed_throughput_backlog_failure_original_restored',active=False,
             actual=summary['actual'],remaining=summary['remaining'],
             original_runtime_restored=summary['original_runtime_restored'],
             original_runtime_boot_id=audit['boot_id'],BOOT_current_sha256=summary['original_BOOT_sha256'],
             original_BOOT_file_restored=True,HDMI_adopted=native['HDMI_adopted'],
             long_stability_proved=False,result='result-summary.json')
(e/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
pre=e/'preboot-host/actual.full'
receipt=dict(file='actual.full',bytes=pre.stat().st_size,received_records=0,
             note='Preallocated capacity from pre-BOOT host service, no inputs/results; original retained locally, not copied into Git.')
(e/'preboot-host/reservation.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))

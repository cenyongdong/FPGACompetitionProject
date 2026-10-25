from pathlib import Path
import json,math,statistics
w=Path(__file__).resolve().parent;e=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-pipeline-20261024-r53')
r=w/'unpacked/software/run-long-native/results'
read=lambda p:json.loads(p.read_text())
rows=lambda p:[json.loads(x) for x in p.read_text().splitlines()]
host=read(e/'host/summary.json');analysis=read(e/'host/analysis.json')
native=read(w/'unpacked/metadata/long-test.json');fail=read(r/'failure.json')
admission=read(w/'unpacked/startup-admission.json');seed=read(w/'unpacked/startup/before-seed.json')
audit=read(e/'final-audit.json');closed=read(e/'closed.json')
hdmi=rows(r/'hdmi.jsonl');frames=rows(r/'hdmi-frames.jsonl')
commands=[x for x in hdmi if x.get('event')=='command']
start=next(x for x in commands if x['op']==1)
stop=next(x for x in commands if x['op']==3 and x['sequence']>start['sequence'])
def stats(v):
    v=sorted(v)
    return dict(count=len(v),mean_ms=statistics.mean(v),p95_ms=v[math.ceil(.95*len(v))-1],max_ms=v[-1]) if v else None
timing={k:stats([x[k] for x in frames]) for k in ('render_rgb565_ms','prepare_background_ms','render_dynamic_ms','begin_show_ms')}
timing['write_and_later_adoption_observed']=stats([x['write_and_adopt_ms'] for x in hdmi if x.get('event')=='adopted'])
result=dict(passed=False,long_stability_proved=False,AI_four_HC_unchanged=True,hardware_rebuilt=False,
    single_SDK_thread=True,automatic_retry=False,startup_mode=admission['mode'],startup_PS_AR=seed['PS_AR'],startup_PS_R=seed['PS_R'],discard_beats=0,
    actual=dict(candidate_starts=1,original_fallbacks=1,SDK_Open=1),remaining=closed['remaining'],
    native_exit=native['native_exit'],failure=fail,index_oracle=read(r/'index-oracle/summary.json'),
    host_sent=host['sent'],host_confirmed=host['received'],full_original_records=analysis['records'],
    HDMI_adopted=native['HDMI_adopted'],short_sample_output_hz=host['output_rate_hz'],input_hz=host['input_rate_hz'],
    host_errors=host['errors'],protocol_snapshots=native['protocol_snapshots'],fresh_native_protocol_clean=native['all_fresh_native_protocol_checks_passed'],
    HDMI_commands=len(commands),HDMI_commands_with_faults=sum(bool(x['faults']) for x in commands),
    STOP_proved=any(x.get('event')=='stop_proved' for x in hdmi),frames_released=any(x.get('event')=='frames_released_after_stop' for x in hdmi),
    HDMI_START_to_STOP_seconds=(stop['request_sent_ns']-start['request_sent_ns'])/1e9,
    timing=timing,finite_identity_selection_errors=analysis['finite_and_identity_errors'],
    frozen_reference_passes=sum(x['accepted'] for x in analysis['frozen_reference_checks']),
    checked_max_joint_delta_mm=max(x['max_checked_joint_delta_mm'] for x in analysis['frozen_reference_checks']),
    full_record_count_matches_confirmed=analysis['host_count_matches'],screen_user_report='仍只闪现片刻',continuous_screen_verified=False,
    original_runtime_restored=closed['closed'] and audit['boot_id']==closed['boot_id'],original_runtime_boot_id=audit['boot_id'],
    original_BOOT_sha256=audit['startup_files']['BOOT.BIN']['sha256'],original_files_verified=len(audit['startup_files']),SDK_files_verified=len(audit['SDK']),
    candidate_archive=dict(bytes=(e/'candidate-evidence.tar.gz').stat().st_size,sha256='037422e7fdc3ab20d5b90fe326a210e86603faa3d45529fe96bc11b6cf7c2972'))
(e/'result-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
state=read(e/'state.json');state.update(status='closed_op192_first_read_mismatch_original_restored',active=False,
    BOOT_written=True,original_BOOT_file_restored=True,original_runtime_restored=result['original_runtime_restored'],
    original_runtime_boot_id=audit['boot_id'],BOOT_current_sha256=result['original_BOOT_sha256'],
    actual=result['actual'],remaining=result['remaining'],HDMI_adopted=result['HDMI_adopted'],long_stability_proved=False,result='result-summary.json')
(e/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))

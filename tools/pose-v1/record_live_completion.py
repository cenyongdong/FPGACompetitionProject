"""Record accepted stages separately from preserved harness failures and candidates."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];target=root/'tools/pose-v1/evidence/live-20261008-completion';assert not target.exists();target.mkdir()
def load(rel):return json.loads((root/rel).read_text(encoding='utf-8-sig'))
def sha(rel):return hashlib.sha256((root/rel).read_bytes()).hexdigest()
three='tools/pose-v1/evidence/live-20261008-r2/live-three.acceptance.json'
expanded='tools/pose-v1/evidence/live-20261008-r2-coordinated/live-27.acceptance.json'
negative='tools/pose-v1/evidence/rtsp-pressure-20261008-r1/completion-review.json'
normal='tools/pose-v1/evidence/guarded-normal-20261008-r1/completion-review.json'
t,e,n,c=map(load,(three,expanded,negative,normal));assert all(x['complete_online_stage_verified'] for x in (t,e))
assert n['RTP_send_error_propagated'] and c['guarded_module_same_negative'] and c['send_errors']==0
nt=load('tools/pose-v1/evidence/live-20261008-r2/three-network-review/review.json');ne=load('tools/pose-v1/evidence/live-20261008-r2-coordinated/expanded-network-review/review.json')
report=dict(status='finite_real_capture_pipeline_and_guarded_module_gates_verified',binary_sha256=t['binary_sha256'],manifest_sha256=t['package_manifest_sha256'],package_payloads=403,build_sources=34,SDK='3.39.0',sdk_headers=15,vendor_files=189,
    Host_cases=107,registry_records=12,CPU_output_values=59600,accepted_model_forwards=t['full_correct_forwards']+e['full_correct_forwards'],accepted_input_scores_poses_FP32_values=32*15100,
    accepted_real_encoded_frames=t['encoded_frames']+e['encoded_frames'],accepted_real_RTSP_decoded_frames=t['network_frames']+e['network_frames'],RTSP_actual_result_frames=t['network_frames']+e['network_frames']-nt['NoInput_frames']-ne['NoInput_frames'],video_joint_checks=t['video_joint_visibility_checks']+e['video_joint_visibility_checks'],
    model_outputs_bitwise_old_board=True,all_current_capture_network_pixels_exact=True,actual_RTP_capture_PTS=True,Engine_main_owner_held_until_workers_joined=True,source_rate_Hz=2,target_video_fps=10,repeats_not_new_inference=True,SDK_profiling=False,
    guarded_candidate=dict(negative=n,normal=c,integrated_into_pipeline_r2=False),
    preserved_failures=dict(first27=dict(model_forwards_correct=28,encoded_frames=490,network_frames=40,network_first_encoded_id=450,reason='client_started_too_late_no_full_source_gate'),short_guarded_normal=dict(producer_frames=160,received_frames=91,minimum_client_gate=100,reason='16s_window_too_short_for_tool_startup; preserved_not_accepted')),
    BOOT_model_RAW_SDK_unchanged=True,kernel_unchanged=True,all_services_and_SSH_SFTP_closed=True,user_paused=False,whole_system5Hz=False,long_run30minutes=False,HDMI=False,TCP_window_frontend_integrated_into_this_target=False,
    review_sha256={r:sha(r) for r in (three,expanded,negative,normal)},next='Freeze guarded normal/slow-peer-tested network candidate into a fresh integration target and regress Host/real source gates; then merge existing TCP complete-window interface before whole-system performance/long-run gates. HDMI配套未知不写。')
(target/'completion-review.json').write_bytes((json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode())
(target/'next-checkpoint.json').write_bytes((json.dumps(dict(status='module_validation_complete_ready_for_guarded_integration',user_paused=False,services_running=False,SSH_SFTP_closed=True,authorization='User authorized agent continuation; no new execution-party confirmation required',entry='tools/pose-v1/LIVE-RESULTS-20261008.md',completion='tools/pose-v1/evidence/live-20261008-completion/completion-review.json',accepted_program=report['binary_sha256'],build='.local/pose-v1-build/mixed-20261008-live-r2',package='.local/pose-v1-live/package-20261008-r2',board_directories=['/tmp/pose-v1-live/20261008-r2','/tmp/pose-v1-live/20261008-r2-coordinated','/tmp/pose-rtsp-pressure-20261008-r1','/tmp/pose-rtsp-guarded-normal-20261008-r1'],guarded_network_candidate_integrated=False,next=report['next'],preserve_failures=True,no_automatic_retry_compaction_reset_or_BOOT_change=True),indent=2,ensure_ascii=False)+'\n').encode())
print(json.dumps({k:report[k] for k in ('status','accepted_model_forwards','accepted_real_encoded_frames','accepted_real_RTSP_decoded_frames','RTSP_actual_result_frames','video_joint_checks')},indent=2))

"""Issue the next-stage gate only after engine, local video and network reviews."""
import argparse,hashlib,json
from pathlib import Path
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--engine',type=Path,required=True);p.add_argument('--video',type=Path,required=True);p.add_argument('--network',type=Path,required=True);p.add_argument('--input-review',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists();e,v,n=load(a.engine),load(a.video),load(a.network)
assert e['status']=='live_stage_passed' and e['stage'] in ('live-three','live-27')
assert v['status']=='resident_video_sources_and_IDs_verified' and n['status']=='real_capture_RTSP_bytes_PTS_sources_pixels_verified'
assert e['full_correct_forwards']==v['inference_sources']==n['new_inference_sources'] and e['encoded_frames']==v['decoded_frames']
assert n['all_sources_present'] and n['actual_RTP_capture_PTS'] and n['all_pixels_equal_current_capture'] and n['NoInput_frames']>0
report=dict(e,network_frames=n['network_frames'],network_all_sources=True,network_pixels_exact_current_capture=True,video_joint_visibility_checks=v['joint_visibility_checks'],evidence_reviews_sha256={str(f):sha(f) for f in (a.engine,a.video,a.network)},complete_online_stage_verified=True,whole_system_5Hz_verified=False,long_run_verified=False)
if 'TCP_complete_windows' in e:
    assert a.input_review is not None
    ingress=load(a.input_review);assert ingress['status']=='complete_CSI_sender_receiver_result_mapping_verified' and ingress['windows']==e['full_correct_forwards'] and ingress['loss_or_rejection']==0
    report.update(TCP_input_independent_mapping_verified=True,TCP_raw_bytes=ingress['raw_bytes'])
    report['evidence_reviews_sha256'][str(a.input_review)]=sha(a.input_review)
a.output.write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(report,indent=2))

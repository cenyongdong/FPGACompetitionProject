"""Review bounded numeric/local-video evidence without granting an RTSP gate."""
from pathlib import Path
import json
import numpy as np
import mixed_validation_gate as old
from review_source_r4_stage import identities,rows,sha
root=old.ROOT;e=root/'tools/pose-v1/evidence/source-readback-20261009-r4';r=e/'process-three-coordinated';out=r/'results'
package=root/'.local/pose-v1-source-readback/package-20261009-r4'
m,b,_=identities(package,root/'.local/pose-v1-build/mixed-20261009-source-readback-r4');returned=old.verify(r)
assert (r/'exit.txt').read_text().strip()=='0' and sha(r/'pose_live_pipeline_check')==b['binary_sha256'] and sha(r/'pose_display_worker')==b['display_worker_sha256']
assert sha(r/'executed-runner.sh')==sha(root/'tools/pose-v1/run-source-readback-r4.sh')
assert (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
pre=old.load(r/'preflight.json');hp=old.load(e/'host-check/preflight.json');assert all(pre[k]==hp[k] for k in ('boot_files','libraries','SDK_packages','fpga_state'))
old.registry(out/'engine/registry.jsonl');old.fusion_binding_review(out/'engine',old.load(root/'tools/pose-v1/mixed-fusion-baseline.json'))
assert old.load(r/'previous-acceptance.json')['binary_sha256']==b['binary_sha256']
calls=rows(out/'inference.jsonl');timings=rows(out/'timing.jsonl');assert len(calls)==len(timings)==4
cases=[line.split()[1] for line in (package/'cases.tsv').read_text().splitlines() if line.startswith('base')];assert len(cases)==3;cases.append(cases[0]);total=0
for i,c in enumerate(calls):
    assert c['invocation']==i and c['frame_id']==100000+i and c['case']==cases[i] and c['before_forward']==0 and c['completed_layers']==745 and c['host_callbacks']==c['zg_callbacks']==7
    for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:
        raw=(out/f'result{i}.{suffix}.f32').read_bytes();assert raw==(package/folder/(c['case']+'.'+suffix+'.f32')).read_bytes()==(out/f'presaved-results/{i}/{suffix}.f32').read_bytes() and np.isfinite(np.frombuffer(raw,'<f4')).all();total+=len(raw)//4
    assert (out/f'presaved-results/{i}/raw-payload.bin').read_bytes()==(package/'inputs'/(c['case']+'.csi')).read_bytes()[32:]
assert total==60400 and not (out/'failed-host-inputs').exists()
assert all((out/'engine'/x).stat().st_size==0 for x in ('readiness.jsonl','operator-execution.jsonl','monotonic-spans.jsonl'))
assert not old.load(out/'engine/sdk-profile-setting.json')['enabled']
ingress=old.load(out/'input-summary.json');assert ingress['received']==ingress['consumed']==4 and ingress['overwritten']==ingress['rejected']==0
assert [x['event'] for x in rows(out/'lifecycle.jsonl')]==['Engine_created','workers_joined','Engine_destroyed']
parent=rows(out/'display/parent.jsonl');child=rows(out/'display/child.jsonl');assert parent[-1]['event']=='cleanly_reaped' and parent[-1]['wait_status']==0 and child[-1]['renders']==4
display=old.load(out/'display-queue.json');assert display['published']==display['adopted']==4 and display['overwritten']==display['coalesced']==0
samples=rows(out/'samples.jsonl');packets=rows(out/'packets.jsonl');units=rows(out/'access-units.jsonl');net=rows(out/'network/events.jsonl');summary=old.load(out/'summary.json')
assert len(samples)==len(units)==summary['encoded_frames']<1000
assert set(s['invocation'] for s in samples if s['inference_result'])==set(range(4))
assert net[-1]['sources_live']==net[-1]['sources_created']==0 and not net[-1]['failed']
assert not any(x['event']=='nal_delivered' for x in net)
enc=rows(out/'encoder/events.jsonl')[-1];assert enc['event']=='encoding_complete' and enc['queued']==enc['returned']==len(samples) and enc['last']
video=old.load(e/'video-coordinated/review.json');assert video['decoded_frames']==len(samples) and video['inference_sources']==4
client=old.load(e/'client-coordinated/review.json');assert client['status']=='failed' and client['error']=='RTSP/1.0 404 Stream Not Found' and not client['frames']
sender=old.load(e/'client-coordinated/sender.json');assert len(sender['sent'])==4 and sender['status']=='sent_no_receiver_ack'
report=dict(status='bounded_numeric_and_local_video_passed_RTSP_not_verified_source_fault_not_reproduced',program_sha256=b['binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],returned_files=returned,forwards=4,full_FP32_bitwise=total,encoded=len(samples),video_joint_checks=video['joint_visibility_checks'],Source_readback_triggered=False,source_hardware_reads=0,source_fault_reproduced=False,root_cause_fixed=False,network_received_frames=0,RTSP_verified=False,client_startup_404=True,dmesg_unchanged=True,child_reaped=True,Engine_destroyed_after_workers=True,compactions=0,performance_acceptance=False)
(e/'local-result-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

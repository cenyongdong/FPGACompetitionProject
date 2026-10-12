"""Audit the finite output mismatch without turning its prefix into acceptance."""
import json,numpy as np
from pathlib import Path
import mixed_validation_gate as g
from review_combined_read_build_base import identities
root=g.ROOT;e=root/'tools/pose-v1/evidence/combined-read-20261010-r1/fps505';r=e/'load-103-return/run-load-103';o=r/'results';p=e/'failure-review.json';assert not p.exists()
m,b,n=identities(root/'.local/pose-v1-combined-read/package-20261010-r1',root/'.local/pose-v1-build/mixed-20261010-combined-read-r1');g.verify(r)
assert g.sha(r/'pose_combined_read_check')==b['combined_binary_sha256'] and (r/'exit.txt').read_text().strip()=='1'
assert (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
for line in (r/'final.processes').read_text().splitlines()[1:]:assert len(line.split())<2 or not line.split()[1].startswith('pose_')
assert not any(x in (r/'final.ports').read_text() for x in (':39001 ',':8554 '))
rows=lambda p:[json.loads(x) for x in p.read_text().splitlines()]
calls=rows(o/'inference.jsonl');assert len(calls)==33
pkg=root/'.local/pose-v1-combined-read/package-20261010-r1'
for i,c in enumerate(calls):
    assert c['call']==c['invocation']==i and c['completed_layers']==745 and c['host_callbacks']==c['zg_callbacks']==7
    for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:
        assert (o/'presaved-results'/str(i)/(suffix+'.f32')).read_bytes()==(pkg/folder/(c['case']+'.'+suffix+'.f32')).read_bytes()
bad=g.load(o/'presaved-results/33/identity.json');assert bad['saved_before_gate'] and bad['frame_id']==100033 and bad['invocation']==33 and bad['case']=='S13_07_304'
assert bad['input']['bit_mismatches']==bad['scores']['bit_mismatches']==0 and bad['poses']['bit_mismatches']==128 and bad['poses']['finite'] and bad['poses']['max_abs']==0.5546875
assert (o/'presaved-results/33/raw-payload.bin').read_bytes()==(pkg/'inputs/S13_07_304.csi').read_bytes()[32:]
for suffix,count in [('input',10800),('scores',100),('poses',4200)]:
    data=(o/'presaved-results/33'/(suffix+'.f32')).read_bytes();assert len(data)==count*4 and np.isfinite(np.frombuffer(data,'<f4')).all()
ledger=g.load(o/'persistence-ledger.json');assert len(ledger['tasks'])==8 and ledger['original_computation_failure']
assert [(x['name'],x['saved']) for x in ledger['tasks'] if not x['saved']]==[('complete-results',False)]
life=rows(o/'lifecycle.jsonl');assert [x['event'] for x in life]==['Engine_created','workers_joined','Engine_destroyed'] and [x['time_ns'] for x in life]==sorted(x['time_ns'] for x in life)
parent=rows(o/'display/parent.jsonl');assert parent[-1]['event']=='error_cleanup_reaped' and parent[-1]['wait_status']==256
events=rows(o/'encoder/events.jsonl');abort=[x for x in events if x['event']=='abort_streamoff'];assert len(abort)==2 and all(x['result']==0 for x in abort)
network=rows(o/'network/events.jsonl');assert network[-1]['event']=='completed' and network[-1]['sources_live']==0 and network[-1]['failed']
host=g.load(e/'failure-host-comparison.json');assert host['owned_inputs']==8 and host['owned_bytes']==115360
assert [(v['op_id'],v['slot'],v['changed_FP32']) for v in host['records'] if not v['bitwise_equal']]==[(582,1,128),(649,1,128)]
assert all(v['nonfinite_actual']==0 for v in host['records']) and not (o/'failed-host-inputs').exists()
video=g.load(e/'video-prefix/review.json');net=g.load(e/'network-prefix/review.json');assert video['decoded_frames']==360 and net['network_frames']==330 and video['missing_completed_sources']==net['missing_completed_sources']==[31,32]
report=dict(status='QPC_capacity_finite_pose_mismatch_preserved_not_acceptance',program_SHA256=b['combined_binary_sha256'],manifest_SHA256=b['package_manifest_sha256'],complete_correct=33,full_F32_compared=498300,owned_returned=34,failed_invocation=33,case=bad['case'],failed_frame_id=100033,failed_owned_output_bytes=60400,poses_changed_F32=128,maximum_pose_abs=0.5546875,input_and_scores_bitwise=True,all_values_finite=True,earliest_observed_bad_Host_input=dict(op=582,slot=1,changed=128),also_bad_Host_input=dict(op=649,slot=1,changed=128),Host_bytes_preserved=115360,output_gate_did_not_trigger_CPU_exception_or_late_reads=True,late_device_reads_saved=False,complete_result_flush_failed_but_all34_presaved=True,seven_other_flush_tasks_saved=True,kernel_unchanged=True,abort_STREAMOFF_succeeded=True,child_reaped=True,network_sources_released=True,Engine_destroyed_after_join=True,all_services_closed=True,video_prefix=360,network_prefix=330,uncaptured_sample_tail=3,missing_completed_video_sources=[31,32],normal_drain=False,root_cause_proven=False,capacity_5Hz_passed=False)
p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(report)

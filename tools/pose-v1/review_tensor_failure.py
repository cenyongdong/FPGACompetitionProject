"""Validate the observed stopped run without hardcoding an old invocation."""
import argparse,json
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
from review_tensor_identity_r3_stage import identities,rows
def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path,required=True);p.add_argument('--gold-review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    m,b,n=identities(a.package,a.build);r=a.results;out=r/'results';verified=g.verify(r)
    assert (r/'exit.txt').read_text().strip()=='1' and g.sha(r/'pose_live_pipeline_check')==b['binary_sha256'] and g.sha(r/'executed-runner.sh')==g.sha(g.ROOT/'tools/pose-v1/run-tensor-identity.sh')
    assert (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
    fail=g.load(out/'failed-host-inputs/failure.json');idx=g.load(out/'failed-invocation-inputs/index.json');gold=g.load(a.gold_review)
    assert fail['op_id']==192 and fail['invocation']==idx['invocation']==gold['invocation'] and fail['frame_id']==idx['frame_id']==gold['frame_id']
    inv=idx['invocation'];calls=rows(out/'inference.jsonl');timing=rows(out/'timing.jsonl');assert len(calls)==len(timing)==inv
    for i,c in enumerate(calls):
        assert c['call']==c['invocation']==i and c['before_forward']==0 and c['completed_layers']==745 and c['host_callbacks']==c['zg_callbacks']==7
        for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:
            blob=(out/f'result{i}.{suffix}.f32').read_bytes();assert blob==(a.package/folder/(c['case']+'.'+suffix+'.f32')).read_bytes()==(out/f'presaved-results/{i}/{suffix}.f32').read_bytes() and np.isfinite(np.frombuffer(blob,'<f4')).all()
        assert (out/f'presaved-results/{i}/raw-payload.bin').read_bytes()==(a.package/'inputs'/(c['case']+'.csi')).read_bytes()[32:]
    assert all(v['bitwise_equal'] for v in gold['records'][:-1]);bad=gold['records'][-1];assert bad['op_id']==192 and bad['slot']==1 and not bad['bitwise_equal']
    actual=np.frombuffer((out/'failed-invocation-inputs/op192.slot1.f32').read_bytes(),'<f4');noninteger=int((~np.isfinite(actual)|(actual!=np.trunc(actual))).sum())
    for slot in (0,1):
        early=(out/'failed-invocation-inputs'/f'op192.slot{slot}.f32').read_bytes();assert early==(out/'failed-host-inputs/post-copy'/f'input{slot}.f32').read_bytes()==(out/'failed-host-inputs'/f'input{slot}.f32').read_bytes()
        reference=g.ROOT/gold['records'][slot+1]['golden_path']
        for k in (0,1):assert (out/'failed-host-inputs/source-readback'/f'round{k}.input{slot}.f32').read_bytes()==reference.read_bytes()
    ingress=g.load(out/'input-summary.json');assert ingress['consumed']==inv+1 and ingress['returned']==inv and ingress['overwritten']==0 and ingress['final_after_join'] and ingress['failure_path']
    ledger=g.load(out/'persistence-ledger.json');assert ledger['original_computation_failure'] and len(ledger['tasks'])==8 and all(v['saved'] for v in ledger['tasks'])
    life=rows(out/'lifecycle.jsonl');assert [v['event'] for v in life]==['Engine_created','workers_joined','Engine_destroyed']
    net=rows(out/'network/events.jsonl');assert net[-1]['event']=='completed' and net[-1]['sources_live']==0
    child=rows(out/'display/parent.jsonl');assert child[-1]['event']=='error_cleanup_reaped' and child[-1]['wait_status']==256
    off=[v for v in rows(out/'encoder/events.jsonl') if v['event']=='abort_streamoff'];assert len(off)==2 and {v['type'] for v in off}=={9,10} and all(v['result']==0 for v in off)
    metadata=rows(out/'copy-observations/metadata.jsonl');counts=rows(out/'producer-counts/counts.jsonl');fc=[v for v in counts if v['invocation']==inv];assert len(fc)==8 and all(v['count']==234 and not v['error'] for v in fc)
    objects=rows(out/'tensor-identities/objects.jsonl');fo=[v for v in objects if v['invocation']==inv and v['op_id']==192 and v['point']=='after_copy'];assert len(fo)==2
    for role in ('source','destination'):
        x,y=[v[role] for v in fo];assert x['region_object']==y['region_object'] and x['chunk_object']!=y['chunk_object']
        assert x['address_identity']+x['bytes']<=y['address_identity'] or y['address_identity']+y['bytes']<=x['address_identity']
    report=dict(status='failed_model_prefix_and_owned_identity_evidence_verified',binary_sha256=b['binary_sha256'],manifest_sha256=b['package_manifest_sha256'],returned_files=verified,correct_prefix=inv,correct_prefix_FP32=inv*15100,failed_invocation=inv,failed_frame=idx['frame_id'],failed_case=gold['case'],failed_op=192,changed_FP32=bad['changed_FP32'],noninteger_FP32=noninteger,nonfinite_FP32=bad['nonfinite_actual'],Host_owned_bytes=idx['owned_bytes'],late_device_source_bytes=94080,both_late_sources_gold=True,all_eight_tasks_saved=True,object_changed_across_copy=False,failed_same_region_per_domain=True,failed_source_ranges_overlap=False,failed_Host_ranges_overlap=False,failed_objects=fo,failed192_counts=[v['count'] for v in fc],shadow_rows=sum(v['kind']=='post_copy_Host_shadow' for v in metadata),metadata_rows=len(metadata),object_rows=len(objects),all192_query_rows=len(counts),ingress=ingress,kernel_unchanged=True,normal_device_reads_added=0,cleanup=dict(Engine_destroyed_after_join=True,network_sources_live=0,display_reaped=True,abort_STREAMOFF_results=[0,0]),root_cause_proven=False,full_load_accepted=False,performance_accepted=False)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('status','correct_prefix','failed_invocation','failed_case','changed_FP32','noninteger_FP32','object_changed_across_copy','both_late_sources_gold')}))
if __name__=='__main__':main()

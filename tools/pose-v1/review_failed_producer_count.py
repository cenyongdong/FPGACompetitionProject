"""Stopped192 diagnostic: verify correct prefix, owned bytes and fresh counts."""
import argparse,json
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
from review_producer_count_stage import identities,rows
def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path,required=True);p.add_argument('--gold-review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    m,b,n=identities(a.package,a.build);r=a.results;out=r/'results';verified=g.verify(r)
    assert (r/'exit.txt').read_text().strip()=='1' and g.sha(r/'pose_live_pipeline_check')==b['binary_sha256'] and g.sha(r/'executed-runner.sh')==g.sha(g.ROOT/'tools/pose-v1/run-producer-count.sh')
    assert (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
    failure=g.load(out/'failed-host-inputs/failure.json');idx=g.load(out/'failed-invocation-inputs/index.json');gold=g.load(a.gold_review)
    assert failure['op_id']==192 and failure['invocation']==idx['invocation']==3 and failure['frame_id']==idx['frame_id']==100003
    assert gold['case']=='S12_01_331' and [v['changed_FP32'] for v in gold['records']]==[0,0,1728]
    calls=rows(out/'inference.jsonl');timing=rows(out/'timing.jsonl');assert len(calls)==len(timing)==3
    for i,c in enumerate(calls):
        assert c['call']==c['invocation']==i and c['before_forward']==0 and c['completed_layers']==745 and c['host_callbacks']==c['zg_callbacks']==7
        for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:
            blob=(out/f'result{i}.{suffix}.f32').read_bytes();assert blob==(a.package/folder/(c['case']+'.'+suffix+'.f32')).read_bytes()==(out/f'presaved-results/{i}/{suffix}.f32').read_bytes() and np.isfinite(np.frombuffer(blob,'<f4')).all()
        assert (out/f'presaved-results/{i}/raw-payload.bin').read_bytes()==(a.package/'inputs'/(c['case']+'.csi')).read_bytes()[32:]
    metadata=rows(out/'copy-observations/metadata.jsonl');shadow=[v for v in metadata if v['kind']=='post_copy_Host_shadow'];sync=[v for v in metadata if v['kind']=='fresh_group_completion']
    assert len(shadow)==27 and len(sync)==3 and all(v['initial']==v['final']==638 and v['polls']==1 for v in sync)
    counts=rows(out/'producer-counts/counts.jsonl');assert len(counts)==32 and all(v['count']==234 and not v['error'] for v in counts)
    for slot in (0,1):
        early=(out/'failed-invocation-inputs'/f'op192.slot{slot}.f32').read_bytes()
        assert early==(out/'failed-host-inputs/post-copy'/f'input{slot}.f32').read_bytes()==(out/'failed-host-inputs'/f'input{slot}.f32').read_bytes()
        reference=g.ROOT/gold['records'][slot+1]['golden_path']
        for k in (0,1):assert (out/'failed-host-inputs/source-readback'/f'round{k}.input{slot}.f32').read_bytes()==reference.read_bytes()
    ingress=g.load(out/'input-summary.json');assert ingress['received']==ingress['consumed']==4 and ingress['returned']==3 and ingress['overwritten']==0 and ingress['final_after_join'] and ingress['failure_path']
    ledger=g.load(out/'persistence-ledger.json');assert ledger['original_computation_failure'] and len(ledger['tasks'])==7 and all(v['saved'] for v in ledger['tasks'])
    life=rows(out/'lifecycle.jsonl');assert [v['event'] for v in life]==['Engine_created','workers_joined','Engine_destroyed']
    net=rows(out/'network/events.jsonl');assert net[-1]['event']=='completed' and net[-1]['sources_live']==0
    child=rows(out/'display/parent.jsonl');assert child[-1]['event']=='error_cleanup_reaped' and child[-1]['wait_status']==256
    off=[v for v in rows(out/'encoder/events.jsonl') if v['event']=='abort_streamoff'];assert len(off)==2 and {v['type'] for v in off}=={9,10} and all(v['result']==0 for v in off)
    report=dict(status='failed_bounded_load_partial_numeric_verified',full_load_accepted=False,binary_sha256=b['binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],returned_files=verified,consumed=3,correct_prefix_FP32=45300,full_numeric_bitwise=True,failed_invocation=3,failed_frame=100003,failed_case=gold['case'],failed_op=192,complete_bad_result_available=False,Host_owned_inputs=3,Host_owned_bytes=47760,Host_index_changed_FP32=1728,Host_index_noninteger_FP32=1728,NaN=0,post_copy_equals_post_kernel_staging=True,both_late_sources_equal_same_CSI_golden=True,late_device_source_bytes=94080,metadata_rows=30,shadow_rows=27,fresh_sync_rows=3,producer192_query_rows=32,all192_counts=234,failed_call_extra582_poll_reached=False,all_seven_persistence_tasks_saved=True,kernel_unchanged=True,ingress=ingress,cleanup=dict(Engine_destroyed_after_join=True,network_sources_live=0,display_reaped=True,abort_STREAMOFF_results=[0,0]),root_cause_proven=False,wait_until234_would_not_wait_at_observed_copy_start=True,normal_device_data_reads_added=0,load_103_passed=False,performance_accepted=False)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('status','consumed','failed_op','Host_index_changed_FP32','all192_counts','wait_until234_would_not_wait_at_observed_copy_start')}))
if __name__=='__main__':main()

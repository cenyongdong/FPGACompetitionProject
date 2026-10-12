"""Public192 count evidence, source association and bounded persistence review."""
import argparse,json,struct
from pathlib import Path
import mixed_validation_gate as g
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path);p.add_argument('--native',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    b=g.load(a.build/'build-result.json');binary=a.build/'pose_producer_count_selftest';assert g.sha(binary)==b['producer_selftest_sha256'] and struct.unpack_from('<H',binary.read_bytes(),18)[0]==183
    report=dict(status='producer_counter_identity_checked',selftest_SHA=b['producer_selftest_sha256'],target=234,wait_added=False,normal_device_data_reads_added=0,DMA_cache_fence_proven=False)
    expected=dict(status='passed',refusals=16,queries_per_call=8,maximum_rows=824,below_target_before_copy_allowed=True,query_error_preserved=True,SDK_device=False)
    if a.native:
        assert g.load(a.native/'stdout.json')==expected
        normal=rows(a.native/'tests/observations/counts.jsonl');assert [v['count'] for v in normal]==[223,233,233,234,234,234,234,234]
        error=rows(a.native/'tests/query-error/counts.jsonl');assert len(error)==1 and error[0]['error']=='Original query error' and not error[0]['read_completed'] and error[0]['count'] is None
        regression=rows(a.native/'tests/regression/counts.jsonl');assert regression[-1]['count']==233 and regression[-1]['error']=='Producer count range/regression'
        report['Native_refusals']=16
    if a.results:
        r=a.results;out=r/'results'
        if (r/'producer-contracts.stdout.log').exists():
            assert g.load(r/'producer-contracts.stdout.log')==expected and (r/'producer-contracts.exit.txt').read_text().strip()=='0' and not (r/'producer-contracts.stderr.log').read_bytes()
            assert g.sha(r/'pose_producer_count_selftest')==b['producer_selftest_sha256'] and not (out/'producer-counts').exists()
            report.update(status='Host_producer_contracts_passed',ARM_refusals=16)
        else:
            counts=rows(out/'producer-counts/counts.jsonl');assert counts and len(counts)<=824
            meta=rows(out/'copy-observations/metadata.jsonl');shadows=[v for v in meta if v['kind']=='post_copy_Host_shadow' and v['op_id']==192]
            ledger=g.load(out/'persistence-ledger.json');assert len(ledger['tasks'])==8 and any(v['name']=='192-producer-counts' and v['saved'] for v in ledger['tasks'])
            groups={};points=['before_wait','after_wait','before_copy','after_copy'];below=[];errors=[]
            for v in counts:
                assert v['op_id']==192 and v['slot'] in (0,1) and v['producer']==[8629,8631][v['slot']] and v['group']==9186 and v['target']==234 and v['maximum']==745
                assert v['bytes']==[30240,16800][v['slot']] and v['source_offset']+v['bytes']<=v['source_capacity'] and v['begin_ns']<=v['end_ns']
                assert not v['wait_added'] and not v['device_data_read_added'] and not v['DMA_cache_fence_proven']
                group=groups.setdefault(v['invocation'],[]);assert len(group)==v['slot']*4+points.index(v['point'])
                if group: assert v['frame_id']==group[0]['frame_id'] and v['begin_ns']>=group[-1]['end_ns']
                if not v['error']:
                    assert v['read_completed'] and 0<=v['count']<=745
                    if group:assert v['count']>=group[-1]['count']
                    if v['count']<234:below.append(dict(invocation=v['invocation'],slot=v['slot'],point=v['point'],count=v['count']))
                else:errors.append(v)
                group.append(v)
            complete=0
            for inv,group in groups.items():
                if len(group)==8 and not any(v['error'] for v in group):
                    complete+=1
                    for slot in (0,1):
                        observed=[v for v in group if v['slot']==slot];shadow=next(v for v in shadows if v['invocation']==inv and v['slot']==slot)
                        for v in observed:
                            assert v['frame_id']==shadow['frame_id'] and all(v[k]==shadow[k] for k in ('source_kind','source_region','source_address','source_offset','source_capacity','bytes'))
                        assert observed[0]['end_ns']<=shadow['wait_begin_ns'] and observed[1]['begin_ns']>=shadow['wait_end_ns']
                        assert observed[2]['end_ns']<=shadow['copy_begin_ns'] and observed[3]['begin_ns']>=shadow['copy_end_ns'] and observed[3]['end_ns']<=shadow['shadow_begin_ns']
            report.update(status='public192_counts_source_and_copy_timing_checked',query_rows=len(counts),complete_observed_calls=complete,metadata_rows=len(meta),combined_rows=len(counts)+len(meta),below234=below,query_errors=errors,copy_before_below234=sum(v['point']=='before_copy' for v in below),all_persistence_tasks_saved=all(v['saved'] for v in ledger['tasks']),diagnostic_not_performance_acceptance=True)
            assert report['combined_rows']<=2048
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('below234','query_errors')}))
if __name__=='__main__':main()

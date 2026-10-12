"""Additional mandatory observer/lifetime/persistence evidence review."""
import argparse, json, hashlib, struct
from pathlib import Path
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p): return [json.loads(x) for x in p.read_text().splitlines()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    b=load(a.build/'build-result.json');blob=(a.build/'pose_invocation_evidence_selftest').read_bytes()
    assert sha(a.build/'pose_invocation_evidence_selftest')==b['invocation_selftest_sha256'] and struct.unpack_from('<H',blob,18)[0]==183
    report=dict(status='invocation_integration_identity_checked',selftest_SHA=b['invocation_selftest_sha256'],normal_device_reads_added=0)
    if a.results:
        r=a.results;out=r/'results';meta=rows(out/'copy-observations/metadata.jsonl');shadows=[x for x in meta if x['kind']=='post_copy_Host_shadow']
        for x in shadows:
            assert x['bytes']>0 and x['bytes']%4==x['Host_CPTR']%4==0
            assert x['Host_offset']+x['bytes']<=x['Host_capacity'] and x['source_offset']+x['bytes']<=x['source_capacity']
            keys=('wait_begin_ns','wait_end_ns','copy_begin_ns','copy_end_ns','shadow_begin_ns','shadow_end_ns')
            assert [x[k] for k in keys]==sorted(x[k] for k in keys)
        if (r/'invocation-contracts.stdout.log').exists():
            assert load(r/'invocation-contracts.stdout.log')==dict(status='passed',refusals=12,owned_bytes_after_producer_release=16,all_tasks_after_comparison_error=True,original_error_preserved=True,SDK_device=False)
            assert (r/'invocation-contracts.exit.txt').read_text().strip()=='0' and not (r/'invocation-contracts.stderr.log').read_bytes()
            assert sha(r/'pose_invocation_evidence_selftest')==b['invocation_selftest_sha256']
            assert len(shadows)==4 and {(x['frame_id'],x['invocation']) for x in shadows}=={(42,0),(43,1)}
            index=load(out/'finite-output-probe/index.json');assert index['frame_id']==43 and index['invocation']==1 and index['owned_bytes']==47040 and not index['source_device_read'] and len(index['inputs'])==2
            for x in index['inputs']:
                actual=(out/'finite-output-probe'/x['file']).read_bytes();assert len(actual)==x['bytes'] and actual==bytes(x['bytes'])
            ledger=load(out/'finite-output-ledger.json');assert ledger['original_computation_failure'] and [t['saved'] for t in ledger['tasks']]==[False,True,True,True]
            assert load(out/'finite-output-probe.json')==dict(status='passed',Host_forward_completed=True,owned_inputs=2,owned_bytes=47040,original_error_preserved=True,source_device_read=False)
            # Old CPU exception and both later source reads remain available.
            old=out/'failed-host-inputs';idx=load(old/'post-copy/shadow.json');assert len(idx['inputs'])==2
            for x in idx['inputs']:
                value=(old/f"input{x['slot']}.f32").read_bytes();assert value==(old/'post-copy'/f"input{x['slot']}.f32").read_bytes()
                for k in range(2): assert value==(old/'source-readback'/f"round{k}.input{x['slot']}.f32").read_bytes()
            report.update(status='Host_lifetime_and_independent_persistence_passed',Host_refusals=12,finite_Host_forward=True,owned_bytes=47040,old_CPU_exception_source_rounds=2)
        else:
            ledger=load(out/'persistence-ledger.json');assert len(ledger['tasks'])==7
            assert [x['name'] for x in ledger['tasks']]==['complete-results','copy-metadata','192-producer-counts','Engine-evidence','failed-Host-frame','warmup','ARM-frame-references']
            failed=(out/'failed-invocation-inputs').exists()
            if failed:
                index=load(out/'failed-invocation-inputs/index.json');assert ledger['original_computation_failure']
                records=[x for x in shadows if x['invocation']==index['invocation']];assert len(records)==len(index['inputs']) and not index['source_device_read']
                for x in index['inputs']:
                    assert len((out/'failed-invocation-inputs'/x['file']).read_bytes())==x['bytes']
                    record=next(v for v in records if (v['op_id'],v['slot'])==(x['op_id'],x['slot']))
                    assert record['bytes']==x['bytes'] and record['frame_id']==index['frame_id']
                report.update(status='failed_frame_persistence_checked',frame_id=index['frame_id'],invocation=index['invocation'],owned_inputs=len(index['inputs']),owned_bytes=index['owned_bytes'],ledger=ledger)
            else:
                assert not ledger['original_computation_failure'] and all(x['saved'] for x in ledger['tasks'])
                calls=rows(out/'inference.jsonl');assert len(shadows)==len(calls)*8
                for i in range(len(calls)):
                    record=[x for x in shadows if x['invocation']==i];assert sum(x['bytes'] for x in record)==115360
                report.update(status='normal_independent_persistence_passed',calls=len(calls),shadow_records=len(shadows),single_frame_bytes=115360)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()

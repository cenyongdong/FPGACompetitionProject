"""Independent snapshot/sync/accounting evidence gate; no device access."""
import argparse,json,hashlib,struct
from pathlib import Path
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path);p.add_argument('--native',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    b=load(a.build/'build-result.json');binary=a.build/'pose_stage_observation_selftest';data=binary.read_bytes();assert sha(binary)==b['stage_selftest_sha256'] and struct.unpack_from('<H',data,18)[0]==183
    report=dict(status='stage_guard_identity_checked',selftest_SHA=sha(binary),DMA_cache_fence_proven=False,zero_copy=False)
    if a.native:
        assert (a.native/'saved-host/post-copy/input0.f32').read_bytes()==struct.pack('<4I',0xffffffff,0x80000000,0x3f800000,0x40000000)
        sync=rows(a.native/'observations/metadata.jsonl')[0];assert (sync['initial'],sync['final'],sync['polls'])==(481,638,3)
        report['native_shadow_bytes_owned']=16
    if a.results:
        r=a.results;out=r/'results';metadata=rows(out/'copy-observations/metadata.jsonl');shadows=[x for x in metadata if x['kind']=='post_copy_Host_shadow'];sync=[x for x in metadata if x['kind']=='fresh_group_completion']
        for x in shadows:
            assert x['Host_CPTR']%4==x['bytes']%4==0 and x['bytes']>0
            assert x['Host_offset']+x['bytes']<=x['Host_capacity'] and x['source_offset']+x['bytes']<=x['source_capacity']
            assert [x[k] for k in ('wait_begin_ns','wait_end_ns','copy_begin_ns','copy_end_ns','shadow_begin_ns','shadow_end_ns')]==sorted(x[k] for k in ('wait_begin_ns','wait_end_ns','copy_begin_ns','copy_end_ns','shadow_begin_ns','shadow_end_ns'))
            assert x['mod64']==x['Host_CPTR']%64 and x['mod128']==x['Host_CPTR']%128 and x['mod256']==x['Host_CPTR']%256
        for x in sync:
            assert x['op_id']==582 and x['target']==638 and x['initial']<=x['final']<=745 and x['final']>=638 and x['polls']>=1 and x['end_ns']>=x['begin_ns'] and not x['DMA_cache_fence_proven']
        if (r/'stage-contracts.stdout.log').exists():
            assert load(r/'stage-contracts.stdout.log')==dict(status='passed',refusals=11,owned_bytes=16,fresh_counter_polls=3,SDK_device=False)
            assert (r/'stage-contracts.exit.txt').read_text().strip()=='0' and not (r/'stage-contracts.stderr.log').read_bytes()
            assert sha(r/'pose_stage_observation_selftest')==b['stage_selftest_sha256']
            failure=out/'failed-host-inputs';index=load(failure/'post-copy/shadow.json');assert len(index['inputs'])==2 and not sync
            assert len(shadows)==2 and index['op_id']==192
            for x in index['inputs']:
                assert (failure/'post-copy'/f"input{x['slot']}.f32").read_bytes()==(failure/f"input{x['slot']}.f32").read_bytes()
            report.update(status='Host_snapshot_sync_negative_tests_passed',ARM_refusals=11,Host_probe_shadow_bytes=sum(x['bytes'] for x in index['inputs']),Host_source_rounds=2)
        else:
            assert not any(x['kind']=='completion_wait_failed' for x in metadata)
            calls=rows(out/'inference.jsonl');assert len(sync)==len(calls) and len(shadows)==8*len(calls)
            assert [x['invocation'] for x in sync]==list(range(len(calls)))
            ingress=load(out/'input-summary.json');assert ingress['final_after_join'] and not ingress['failure_path'] and ingress['returned']==ingress['consumed']==len(calls)
            report.update(status='normal_snapshot_sync_accounting_passed',calls=len(calls),snapshot_rows=len(shadows),fresh_sync_rows=len(sync),sync_actual_waited=sum(x['initial']<638 for x in sync),sync_max_ms=max((x['end_ns']-x['begin_ns'])/1e6 for x in sync),metadata_rows=len(metadata))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()

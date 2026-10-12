"""Compare preserved invocation shadow against frozen same-CSI N1 inputs."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    out=a.results;index=g.load(out/'failed-invocation-inputs/index.json');identity_file=out/'presaved-results'/str(index['invocation'])/'identity.json'
    if identity_file.exists(): identity=g.load(identity_file);case=identity['case']
    else:
        identity=g.load(out/'failed-host-inputs/failure.json')
        catalog=[line.split()[1] for line in (a.package/'cases.tsv').read_text().splitlines() if line.split()[0]=='expanded']
        assert len(catalog)==27 and index['frame_id']==100000+index['invocation']
        case=catalog[(index['frame_id']-100000)%27]
    assert identity['frame_id']==index['frame_id'] and identity['invocation']==index['invocation']
    gold=g.ROOT/'tools/pose-v1/evidence/runtime-20261007-r2/n1';verified=g.verify(gold)
    captures=[json.loads(x) for x in (gold/'results/content/index.jsonl').read_text().splitlines()]
    records=[]
    for x in index['inputs']:
        candidates=[v for v in captures if v['case']==case and v['kind']=='bridge_input' and (v['op_id'],v['slot'])==(x['op_id'],x['slot'])]
        assert candidates and all(v['tensor']['pointer']=='CPTR' and v['bytes']==x['bytes'] for v in candidates)
        for v in candidates:
            inv=v['invocation']
            for suffix in ('scores','poses'):
                assert (gold/f'results/call{inv}.{suffix}.f32').read_bytes()==(a.package/'r6-reference'/f'{case}.{suffix}.f32').read_bytes()
            assert (gold/f'results/content/call{inv}.caller_input.op0.slot0.f32').read_bytes()==(a.package/'reference'/f'{case}.input.f32').read_bytes()
        ref=gold/'results/content'/candidates[0]['file'];actual=out/'failed-invocation-inputs'/x['file']
        blob=actual.read_bytes();baseline=ref.read_bytes();assert len(blob)==len(baseline)==x['bytes']
        for v in candidates: assert (gold/'results/content'/v['file']).read_bytes()==baseline
        aa=np.frombuffer(blob,'<f4');bb=np.frombuffer(baseline,'<f4');changed=np.flatnonzero(aa.view('<u4')!=bb.view('<u4'))
        finite=np.isfinite(aa)&np.isfinite(bb);delta=aa[finite].astype(float)-bb[finite].astype(float)
        records.append(dict(op_id=x['op_id'],slot=x['slot'],bytes=x['bytes'],actual_sha256=g.sha(actual),golden_sha256=g.sha(ref),golden_path=str(ref.relative_to(g.ROOT)),changed_FP32=len(changed),changed_first64=changed[:64].tolist(),nonfinite_actual=int((~np.isfinite(aa)).sum()),finite_max_abs=float(np.abs(delta).max()) if len(delta) else None,bitwise_equal=blob==baseline))
    report=dict(status='failed_Host_frame_same_CSI_reference_compared_not_acceptance',case=case,invocation=index['invocation'],frame_id=index['frame_id'],owned_inputs=len(records),owned_bytes=index['owned_bytes'],all_Host_inputs_bitwise=all(v['bitwise_equal'] for v in records),golden_files_verified=verified,golden_file_list_sha256=g.sha(gold/'files.sha256'),source_device_read=False,root_cause_proven=False,records=records)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='records'}))
if __name__=='__main__':main()

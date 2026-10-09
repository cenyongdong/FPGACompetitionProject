"""Independent byte-level classification; does not repair indices or relax gates."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
def main():
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    metadata=json.loads((a.directory/'failure.json').read_text());assert metadata['status']=='captured_after_CPU_exception' and not metadata['device_read']
    result=[]
    for item in metadata['inputs']:
        raw=(a.directory/item['file']).read_bytes();v=np.frombuffer(raw,'<f4');bits=np.frombuffer(raw,'<u4')
        assert len(raw)==item['bytes']==int(np.prod(item['shape']))*4
        assert item['pointer']=='CPTR' and item['dtype']=='FP32' and item['offset']+item['bytes']<=item['chunk_bytes']
        finite=np.isfinite(v);integer=np.zeros(len(v),bool);integer[finite]=v[finite]==np.trunc(v[finite])
        report=dict(slot=item['slot'],shape=item['shape'],bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),NaN=int(np.isnan(v).sum()),positive_Inf=int(np.isposinf(v).sum()),negative_Inf=int(np.isneginf(v).sum()),finite_noninteger=int((finite&~integer).sum()),dtype_layout=item['layout'])
        if metadata['op_id']==192 and item['slot']==1:
            extent=metadata['inputs'][0]['shape'][1];valid=finite&integer&(v>=-extent)&(v<extent)
            bad=np.flatnonzero(~valid);report.update(axis=1,axis_extent=extent,outside_Numpy_index_bounds=int((finite&integer&((v<-extent)|(v>=extent))).sum()),invalid_indices=len(bad),first_invalid=[dict(flat=int(i),coordinate=list(map(int,np.unravel_index(i,item['shape']))),fp32_hex=f'{int(bits[i]):08x}',value=float(v[i]) if finite[i] else str(v[i])) for i in bad[:32]])
        result.append(report)
    report=dict(status='failure_Host_bytes_classified_no_fix',frame_id=metadata['frame_id'],invocation=metadata['invocation'],op_id=metadata['op_id'],original_error=metadata['error'],phase=metadata['input_phase'],inputs=result,upstream_origin_proven=False)
    a.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

"""Compare original staged bytes and two SDK source reads without repairing data."""
import argparse,json
from pathlib import Path
import numpy as np
import mixed_validation_gate as old
def contiguous(values):
    groups=[]
    for v in map(int,values):
        if groups and groups[-1][1]==v:groups[-1][1]+=1
        else:groups.append([v,v+1])
    return groups
def main():
    p=argparse.ArgumentParser();p.add_argument('--failure',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path);a=p.parse_args();assert not a.output.exists()
    meta=old.load(a.failure/'failure.json');rd=a.failure/'source-readback';reads=old.load(rd/'readback.json')
    assert all(meta[k]==reads[k] for k in ('frame_id','invocation','op_id')) and reads['status']=='two_SDK_source_reads_completed' and reads['rounds']==2
    assert not reads['direct_device_dereference'] and not reads['explicit_wait_or_reset']
    assert len(meta['inputs'])==len(reads['sources']);total=0;comparisons=[]
    for expected,source in zip(meta['inputs'],reads['sources']):
        assert expected['slot']==source['slot'] and expected['shape']==source['shape'] and expected['bytes']==source['bytes']
        assert source['offset']+source['bytes']<=source['chunk_bytes']
        staging=(a.failure/expected['file']).read_bytes();total+=len(staging)
        blobs=[];durations=[];per=[]
        for rr in source['reads']:
            raw=(rd/rr['file']).read_bytes();assert len(raw)==len(staging) and rr['begin_ns']<=rr['end_ns'];blobs.append(raw);durations.append((rr['end_ns']-rr['begin_ns'])/1e6)
        assert len(blobs)==2 and source['reads'][0]['round']==0 and source['reads'][1]['round']==1
        vals=[np.frombuffer(x,'<f4') for x in [staging]+blobs];bits=[x.view('<u4') for x in vals]
        for name,v,raw in zip(['original_staging','source_round0','source_round1'],vals,[staging]+blobs):
            per.append(dict(name=name,sha256=old.sha(a.failure/expected['file']) if name=='original_staging' else old.sha(rd/source['reads'][int(name[-1])]['file']),NaN=int(np.isnan(v).sum()),Inf=int(np.isinf(v).sum()),zeros=int((v==0).sum())))
        result=dict(slot=source['slot'],shape=source['shape'],pointer=source['pointer'],region=source['region'],source_address=source['address'],source_chunk=source['chunk_identity'],source_offset=source['offset'],source_capacity=source['chunk_bytes'],read_ms=durations,classification=per,staging_to_round0_changed_FP32=int((bits[0]!=bits[1]).sum()),staging_to_round1_changed_FP32=int((bits[0]!=bits[2]).sum()),round0_to_round1_changed_FP32=int((bits[1]!=bits[2]).sum()),staging_to_round0_changed_ranges_FP32=contiguous(np.flatnonzero(bits[0]!=bits[1])))
        if a.reference and source['slot']==0:
            gold=np.frombuffer(a.reference.read_bytes(),'<u4');assert len(gold)==len(bits[0]);result.update(reference_sha256=old.sha(a.reference),reference_changed_FP32=[int((v!=gold).sum()) for v in bits])
        comparisons.append(result)
    assert total==reads['single_round_bytes']<=1024*1024
    if all(x['round0_to_round1_changed_FP32']==0 and x['staging_to_round0_changed_FP32']==0 for x in comparisons):scope='Both later source reads match original staged bytes; anomaly also observed through source-read path, origin remains unresolved.'
    elif any(x['round0_to_round1_changed_FP32'] for x in comparisons):scope='Source-read results changed between rounds; investigate completion, lifetime and read visibility.'
    else:scope='Later source reads differ from original staging; investigate copy/storage visibility or source completion after original copy. This does not prove which operation caused the difference.'
    report=dict(status='two_source_reads_and_original_staging_compared',frame_id=meta['frame_id'],invocation=meta['invocation'],op_id=meta['op_id'],original_error=meta['error'],single_round_bytes=total,additional_source_read_bytes=2*total,comparisons=comparisons,inference=scope,root_cause_proven=False,reads_are_later_than_original_copy=True,source_hardware_read=any(x['device'] for x in reads['sources']))
    a.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

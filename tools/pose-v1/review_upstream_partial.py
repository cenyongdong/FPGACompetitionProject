"""Public boundary observations; complete owned frames and independent Gather oracle."""
import argparse,json
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--synthetic',action='store_true');a=p.parse_args();assert not a.output.exists()
root=a.evidence;rows=[json.loads(x) for x in (root/'metadata.jsonl').read_text(encoding='utf-8').splitlines()];summary=g.load(root/'summary.json');assert len(rows)==summary['rows']<=824
spec={'topk_indices':(1137,400),'zg_input_data':(4406,16800),'gather_pre_data':(4406,16800),'gather_pre_indices':(1137,400),'gather_post':(1148,16800),'zg_pre_gather':(1148,16800),'zg_post_base':(4414,16800),'zg_post_update':(4418,16800)}
group={}
for x in rows:
    assert x['point'] in spec and x['value']==spec[x['point']][0] and x['bytes']==spec[x['point']][1] and not x['error']
    assert 0<x['wait_begin_ns']<=x['wait_end_ns']<=x['read_begin_ns']<=x['read_end_ns']
    s=x['storage'];assert s['bytes']==x['bytes'] and s['offset']+s['bytes']<=s['capacity'] and s['kind'] in ['CPTR','ADDR','BOTH']
    group.setdefault(x['invocation'],[]).append(x)
assert all(len(v)==8 and len({x['point'] for x in v})==8 for v in group.values())
if a.synthetic:assert len(rows)==8 and all(x['count_before']==x['count_after']==0 and x['storage']['kind']=='CPTR' for x in rows)
def compare(a,b):
    assert a.shape==b.shape;changed=int((a.view('<u4')!=b.view('<u4')).sum());finite=np.isfinite(a)&np.isfinite(b)
    return dict(changed_FP32=changed,bitwise_equal=changed==0,finite_max_abs=float(np.abs(a[finite].astype(float)-b[finite].astype(float)).max()) if finite.any() else None)
frames=[]
for directory in sorted(root.glob('frame*'),key=lambda p:int(p.name[5:])):
    idx=g.load(directory/'index.json')
    if not idx['samples']:
        assert idx['invocation']==summary['last_invocation'] and idx['invocation'] not in group;continue
    assert set(idx['samples'])==set(spec)
    blobs={k:(directory/(k+'.f32')).read_bytes() for k in spec}
    arrays={k:np.frombuffer(v,'<f4') for k,v in blobs.items()};assert all(len(blobs[k])==n for k,(_,n) in spec.items())
    for x in group[idx['invocation']]:
        h=14695981039346656037
        for byte in blobs[x['point']]:h=((h^byte)*1099511628211)&((1<<64)-1)
        assert h==x['FNV64_diagnostic_only']
    index=arrays['gather_pre_indices'];assert np.isfinite(index).all() and np.array_equal(index,np.trunc(index)) and ((index>=0)&(index<100)).all()
    expected=arrays['gather_pre_data'].reshape(100,42)[index.astype(np.int64)].reshape(-1)
    result=dict(invocation=idx['invocation'],frame=idx['frame'],Gather_from_observed_retained_pre=compare(arrays['gather_post'],expected),producer_data_to_pre=compare(arrays['gather_pre_data'],arrays['zg_input_data']),TopK_indices_to_pre=compare(arrays['gather_pre_indices'],arrays['topk_indices']),Gather_post_to_ZG_pre=compare(arrays['zg_pre_gather'],arrays['gather_post']))
    if a.synthetic:
        assert np.array_equal(arrays['zg_input_data'],np.arange(4200,dtype='<f4')) and np.array_equal(index,np.arange(99,-1,-1,dtype='<f4'))
        assert all(result[k]['bitwise_equal'] for k in ['Gather_from_observed_retained_pre','producer_data_to_pre','TopK_indices_to_pre','Gather_post_to_ZG_pre'])
    frames.append(result)
report=dict(status='synthetic_original_Gather_and_public_Host_boundary_passed' if a.synthetic else 'public_boundaries_compared_not_internal_Session_arguments_proof',rows=len(rows),invocations=len(group),complete_owned_frames=len(frames),per_frame_owned_bytes=101600,frames=frames,pre_vector_not_read_as_inputs=True,private_tmap_access=False,physical_reuse_possible=True,shared_SDK_read_path=True,root_cause_proven=False)
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(report['status'],len(rows),'rows',len(frames),'complete frames')

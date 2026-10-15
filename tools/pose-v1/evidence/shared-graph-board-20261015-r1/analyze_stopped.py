"""Analyze the saved first inference without relaxing or rerunning its failed gate."""
import ast,hashlib,json
from pathlib import Path
import statistics,shutil
import numpy as np
import torch
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
RUN=E/'returned/run-wall';D=RUN/'results';OLD=R/'.local/noscatter-delivery-20261015-r1/fixtures'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_bytes((json.dumps(v,indent=2,allow_nan=False)+'\n').encode())
assert (RUN/'exit.txt').read_text().strip()=='1'
failure=load(D/'failure.json')
assert failure['error']=='Complete output differs; stop without retry' and failure['completed_frames']==0
assert not (RUN/'wrapper-failure.json').exists() and not (RUN/'timeout.json').exists()
for n,h in load(RUN/'evidence-files.json').items():assert sha(RUN/n)==h,n
assert (RUN/'before.dmesg.txt').read_bytes()==(RUN/'after.dmesg.txt').read_bytes()
frames=lines(D/'frames.jsonl');assert len(frames)==1 and not frames[0]['matched']
f=frames[0];assert f['case']=='S11_01_308' and f['invocation']==0
binding=load(D/'engine/binding-summary.json');assert binding['coverage_complete'] and binding['original_hardops']==1021
assert f['completed_layers']==binding['validated_runtime_final_count']
graph=load(R/'model/piw24_shared-20261015-r1/piw24_shared_ZG.json')
actual_hard={o['op_id'] for o in graph['ops'] if o['_type_key']=='icraft::xir::HardOp'}
bound=lines(D/'engine/after-apply.all-bindings.jsonl')
host={r['binding_key'] for r in bound if r['backend']=='icraft::xrt::HostBackendNode'}
zg={r['binding_key'] for r in bound if 'ZG330BackendNode' in r['backend']}
assert host=={0,188,192,437,442,565} and len(zg)==binding['effective_zg_groups']
metadata={r['op_id']:r for r in lines(D/'engine/after-apply.zg-hardop-map.jsonl')}
members=[n for group in zg for n in metadata[group]['merge_from']]
assert len(members)==len(set(members))==1021 and set(members)==actual_hard
sync=sorted((metadata[g]['sync_index'],metadata[g]['layer_count'],g) for g in zg)
end=0
for start,count,g in sync:assert start==end;end+=count
assert end==binding['validated_runtime_final_count']==612
assert f['host_callbacks']==5 and f['zg_callbacks']==len(zg)
arrays={};values={}
for name,size in [('input',10800),('scores',100),('poses',4200)]:
    a=np.fromfile(D/'frame-0'/(name+'.f32'),dtype='<f4')
    b=np.fromfile(OLD/(f['case']+'.'+name+'.f32'),dtype='<f4')
    assert len(a)==len(b)==size and np.isfinite(a).all() and np.isfinite(b).all()
    delta=a.astype('f8')-b.astype('f8')
    arrays[name]=dict(count=size,finite=True,bitwise_equal=a.tobytes()==b.tobytes(),
        changed_values=int(np.count_nonzero(a.view('u4')!=b.view('u4'))),
        max_abs_model_units=float(np.abs(delta).max()),mean_abs_model_units=float(np.abs(delta).mean()),
        actual_sha256=sha(D/'frame-0'/(name+'.f32')))
    values[name]=(b,a)
    if name=='poses':
        p=delta.reshape(100,14,3)
        arrays[name].update(max_coordinate_delta_mm=float(np.abs(delta).max()*1000),
            max_joint_delta_mm=float(np.linalg.norm(p,axis=-1).max()*1000),
            highest_score_candidate_max_joint_delta_mm=float(np.linalg.norm(p[0],axis=-1).max()*1000),
            both_exactly_FP16_representable=bool(np.array_equal(a,a.astype('f2').astype('f4')) and np.array_equal(b,b.astype('f2').astype('f4'))))
assert arrays['input']['bitwise_equal'] and arrays['scores']['bitwise_equal']
assert arrays['poses']['changed_values']>0
source=E/'metric-source.verified-server.py';assert sha(source)=='52b603525b351b25e16f00237c787ea65d6957dbed0535899007d3fcfaafdb31'
tree=ast.parse(source.read_text(encoding='utf-8'));cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='WifiPoseDataset')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='calc_mpjpe')
ns=dict(torch=torch,np=np);exec(compile(ast.Module(body=[method],type_ignores=[]),str(source),'exec'),ns)
torch.set_num_threads(1)
gt_source=R/'tools/pose-v1/evidence/noscatter-board-20261015-r1/ground-truth'/('S11_01_308.npy')
assert sha(gt_source)=='3b2cbcd55f90c3cd0b23e8670cbff2ea73eb2549f01786756374058160d871cf'
(E/'ground-truth').mkdir();shutil.copyfile(gt_source,E/'ground-truth'/gt_source.name)
gt=torch.tensor(np.load(gt_source,allow_pickle=False),dtype=torch.float32);metrics={};matching={}
for mode,pred in zip(('noscatter','shared'),values['poses']):
    pred=torch.tensor(pred.reshape(100,14,3).copy())
    metrics[mode]=[float(v) for v in ns['calc_mpjpe'](None,gt,pred,'S11_01_308',root=[5,7])]
    assert len(gt)==1
    matching[mode]=int(torch.norm(gt[0]-pred,p=2,dim=-1).mean(-1).argmin())
rows=lines(D/'monotonic-spans.jsonl');assert all(not r['failed'] and r['end_ns']>=r['begin_ns']>=0 for r in rows)
INIT=(1<<64)-1;rs=[r for r in rows if r['invocation']==0]
def duration(r):return r['end_ns']-r['begin_ns']
def one(k):
    found=[r for r in rs if r['kind']==k];assert len(found)==1,k;return found[0]
def union(items):
    result=0;end=None
    for a,b in sorted(items):
        if end is None or a>=end:result+=b-a;end=b
        elif b>end:result+=b-end;end=b
    return result
forward=one('runtime.forward');wait=one('runtime.final_wait')
calls=[r for r in rs if r['kind'] in ('op.host','op.zg')]
assert {r['op_id'] for r in calls if r['kind']=='op.host'}=={0,188,192,437,442}
assert {r['op_id'] for r in calls if r['kind']=='op.zg'}==zg
assert len(calls)==5+len(zg)
assert union((r['begin_ns'],r['end_ns']) for r in calls)==sum(duration(r) for r in calls)
assert all(forward['begin_ns']<=r['begin_ns']<=r['end_ns']<=forward['end_ns'] for r in calls)
assert all(r['op_id'] not in (582,649) and r['kind']!='bridge.counter_wait' for r in rs)
bridge=[r for r in rs if r['kind'].startswith('bridge.')]
operators=[]
for call in sorted(calls,key=lambda r:r['begin_ns']):
    ch=[r for r in bridge if r['op_id']==call['op_id']]
    assert all(call['begin_ns']<=r['begin_ns']<=r['end_ns']<=call['end_ns'] for r in ch)
    operators.append(dict(op_id=call['op_id'],kind=call['kind'],inclusive_ms=duration(call)/1e6,
        thread_cpu_ms=call['thread_cpu_ns']/1e6,phases_ms={k:sum(duration(r) for r in ch if r['kind']==k)/1e6 for k in sorted({r['kind'] for r in ch})}))
phase={k:sum(duration(r) for r in bridge if r['kind']==k)/1e6 for k in sorted({r['kind'] for r in bridge})}
remainder=sum(duration(c)-union((r['begin_ns'],r['end_ns']) for r in bridge if r['op_id']==c['op_id']) for c in calls if c['kind']=='op.host')/1e6
zg_ms=sum(duration(c) for c in calls if c['kind']=='op.zg')/1e6
outside_ms=(duration(forward)-sum(duration(c) for c in calls))/1e6
assert abs(sum(phase.values())+remainder+zg_ms+outside_ms-duration(forward)/1e6)<1e-10
transfers=lines(D/'transfers.jsonl');assert len(transfers)==4 and sum(t['logical_bytes'] for t in transfers)==48160
previous=load(R/'tools/pose-v1/evidence/noscatter-board-20261015-r1/analysis.json')
before308=lines(R/'tools/pose-v1/evidence/noscatter-board-20261015-r1/returned/run-wall/results/frames.jsonl')[0]
report=dict(status='first_inference_saved_but_strict_numeric_gate_failed',planned_frames=3,
    actual_inferences=1,accepted_frames=0,unexecuted_frames=2,retry=False,gate_relaxed=False,
    board_exit=1,stop_reason=failure['error'],binding=binding,
    actual_fused_groups=[dict(op_id=g,start=start,layers=count,original_members=len(metadata[g]['merge_from'])) for start,count,g in sync],
    arrays=arrays,case=f['case'],single_frame_timing_ms={k:v for k,v in f.items() if k.endswith('_ms')},
    inference_to_ready_ms=(wait['end_ns']-forward['begin_ns'])/1e6,
    forward_partition_ms=dict(phases=phase,host_callback_other=remainder,zg_submit_callbacks=zg_ms,uncovered=outside_ms),
    operators=operators,initialization_phases_ms={r['kind']:duration(r)/1e6 for r in rows if r['invocation']==INIT},
    MPJPE=dict(case=f['case'],persons=len(gt),metric_mm=metrics,matched_candidate_indices=matching,
               delta_mm=metrics['shared'][0]-metrics['noscatter'][0]),
    timing_comparison=dict(previous_noscatter_same_case_ms=before308['process_ms'],
        current_shared_single_case_ms=f['process_ms'],speedup_observed_same_case=before308['process_ms']/f['process_ms'],
        previous_noscatter_three_frame_mean_ms=previous['frame_means_ms']['process_ms'],
        same_session_AB=False,accepted_speedup_claim=False),
    hardware_counter_or_SDK_error_observed=False,kernel_log_changed=False,
    limits=['Numerical gate failed; this is not a passed three-frame benchmark or a deployment acceptance',
            'Only one completed inference timing sample; no warmup, long run or VPU/TCP',
            'Scores and inputs bitwise unchanged; pose change is measured, its exact FP16 compiler origin not established',
            'Pure NPU arithmetic, DDR stalls and exact SDK dispatch are unavailable'])
save(E/'stopped-analysis.json',report)
print(json.dumps({k:v for k,v in report.items() if k not in ('operators','initialization_phases_ms','actual_fused_groups')},indent=2))

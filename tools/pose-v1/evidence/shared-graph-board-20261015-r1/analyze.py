"""Independently audit the actual fusion, full outputs and nested wall-clock spans."""
import ast
import hashlib
import json
from pathlib import Path
import statistics
import shutil
import numpy as np
import torch

R=Path(r'D:\FPGACompetitionProject')
E=R/'tools/pose-v1/evidence/shared-graph-board-20261015-r1'
RUN=E/'returned/run-wall'
D=RUN/'results'
OLD=R/'.local/engine-timing-delivery-20261013-r3'
ALG=Path(r'D:\Person-in-WIFI-3D\Person-in-WiFi-3D-repo')
torch.set_num_threads(1)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def save(p,v):p.write_bytes((json.dumps(v,indent=2,allow_nan=False)+'\n').encode())
assert (RUN/'exit.txt').read_text().strip()=='0'
assert not (RUN/'wrapper-failure.json').exists() and not (D/'failure.json').exists()
for name,h in load(RUN/'evidence-files.json').items():assert sha(RUN/name)==h,name
assert (RUN/'before.dmesg.txt').read_bytes()==(RUN/'after.dmesg.txt').read_bytes()
summary=load(D/'summary.json'); frames=lines(D/'frames.jsonl')
assert summary['completed_frames']==summary['planned_frames']==len(frames)==3
binding=load(D/'engine/binding-summary.json'); assert binding['coverage_complete']
assert binding['original_ops']==1027 and binding['original_hardops']==1021 and binding['direct_host_ops']==6
all_bind=lines(D/'engine/after-apply.all-bindings.jsonl')
host={r['binding_key'] for r in all_bind if r['backend']=='icraft::xrt::HostBackendNode'}
zg={r['binding_key'] for r in all_bind if 'ZG330BackendNode' in r['backend']}
assert host=={0,188,192,437,442,565} and len(zg)==binding['effective_zg_groups']
maps={r['op_id']:r for r in lines(D/'engine/after-apply.zg-hardop-map.jsonl')}
members={g:maps[g]['merge_from'] for g in zg}
flat=[i for v in members.values() for i in v]
assert len(flat)==len(set(flat))==1021
graph=load(R/'model/piw24_shared-20261015-r1/piw24_shared_ZG.json')
assert set(flat)=={o['op_id'] for o in graph['ops'] if o['_type_key']=='icraft::xir::HardOp'}
sync=sorted((maps[g]['sync_index'],maps[g]['layer_count'],g) for g in zg)
next_count=0
for start,count,g in sync:assert start==next_count;next_count+=count
assert next_count==binding['validated_runtime_final_count']
assert all(f['completed_layers']==next_count and f['host_callbacks']==5 and f['zg_callbacks']==len(zg) for f in frames)
assert all(r['op_id'] not in (582,649) for r in lines(D/'engine/registry.jsonl'))
rows=lines(D/'monotonic-spans.jsonl')
INIT=(1<<64)-1
assert all(r['end_ns']>=r['begin_ns']>=0 and not r['failed'] for r in rows)
def dur(r):return r['end_ns']-r['begin_ns']
def one(rs,k):
    found=[r for r in rs if r['kind']==k];assert len(found)==1,k;return found[0]
def union(items):
    total=0;end=None
    for a,b in sorted(items):
        assert b>=a
        if end is None or a>=end:total+=b-a;end=b
        elif b>end:total+=b-end;end=b
    return total
parts=[]; array_checks=[]; transfers=lines(D/'transfers.jsonl')
for f in frames:
    i=f['invocation'];rs=[r for r in rows if r['invocation']==i]
    forward=one(rs,'runtime.forward'); final=one(rs,'runtime.final_wait')
    calls=[r for r in rs if r['kind'] in ('op.host','op.zg')]
    assert {r['op_id'] for r in calls if r['kind']=='op.host'}=={0,188,192,437,442}
    assert {r['op_id'] for r in calls if r['kind']=='op.zg'}==zg
    assert len(calls)==5+len(zg)
    assert all(forward['begin_ns']<=r['begin_ns']<=r['end_ns']<=forward['end_ns'] for r in calls)
    call_union=union((r['begin_ns'],r['end_ns']) for r in calls)
    assert call_union==sum(dur(r) for r in calls)
    assert not any(r['op_id'] in (582,649) or r['kind']=='bridge.counter_wait' for r in rs)
    bridge=[r for r in rs if r['kind'].startswith('bridge.')]
    by_op=[]
    for call in calls:
        ch=[r for r in bridge if r['op_id']==call['op_id']]
        assert all(call['begin_ns']<=r['begin_ns']<=r['end_ns']<=call['end_ns'] for r in ch)
        by_op.append(dict(op_id=call['op_id'],kind=call['kind'],inclusive_ns=dur(call),
            thread_cpu_ns=call['thread_cpu_ns'],bridge_union_ns=union((r['begin_ns'],r['end_ns']) for r in ch),
            phases_ns={k:sum(dur(r) for r in ch if r['kind']==k) for k in sorted({r['kind'] for r in ch})}))
    part=dict(invocation=i,forward_ns=dur(forward),final_wait_ns=dur(final),
        inference_to_ready_ns=final['end_ns']-forward['begin_ns'],
        inference_thread_cpu_ns=None,  # these two manual wall spans have no CPU probe
        input_ready_wait_ns=sum(dur(r) for r in bridge if r['kind']=='bridge.wait'),
        cpu_kernel_ns=sum(dur(r) for r in bridge if r['kind']=='bridge.cpu'),
        copy_api_ns=sum(dur(r) for r in bridge if r['kind']=='bridge.copy'),
        allocation_ns=sum(dur(r) for r in bridge if r['kind']=='bridge.allocate'),
        spec_ns=sum(dur(r) for r in bridge if r['kind']=='bridge.spec'),
        writeback_ns=sum(dur(r) for r in bridge if r['kind']=='bridge.writeback'),
        callback_remainder_ns=sum(dur(c)-union((r['begin_ns'],r['end_ns']) for r in bridge if r['op_id']==c['op_id']) for c in calls if c['kind']=='op.host'),
        zg_submit_callback_ns=sum(dur(c) for c in calls if c['kind']=='op.zg'),
        forward_outside_callback_ns=dur(forward)-call_union,operators=by_op)
    assert sum(part[k] for k in ('input_ready_wait_ns','cpu_kernel_ns','copy_api_ns','allocation_ns','spec_ns',
                                'writeback_ns','callback_remainder_ns','zg_submit_callback_ns','forward_outside_callback_ns'))==dur(forward)
    parts.append(part)
    checks={}
    for kind,n,ref in [('input',10800,'input'),('scores',100,'scores'),('poses',4200,'poses')]:
        actual=D/('frame-'+str(i))/(kind+'.f32'); gold=OLD/'fixtures'/(f['case']+'.'+ref+'.f32')
        assert actual.stat().st_size==gold.stat().st_size==4*n
        a=np.fromfile(actual,dtype='<f4');b=np.fromfile(gold,dtype='<f4')
        assert np.isfinite(a).all() and a.tobytes()==b.tobytes()
        checks[kind]=dict(FP32=n,bitwise_equal=True,sha256=sha(actual),max_abs=0.)
    copy_rows=[r for r in transfers if r['invocation']==i]
    assert len(copy_rows)==4 and sum(r['logical_bytes'] for r in copy_rows)==48160
    array_checks.append(dict(case=f['case'],checks=checks))
metric_source=E/'metric-source.verified-server.py'
assert sha(metric_source)=='52b603525b351b25e16f00237c787ea65d6957dbed0535899007d3fcfaafdb31'
shutil.copyfile(metric_source,E/'metric-source.py')
tree=ast.parse(metric_source.read_text(encoding='utf-8'))
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='WifiPoseDataset')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='calc_mpjpe')
ns=dict(torch=torch,np=np)
exec(compile(ast.Module(body=[method],type_ignores=[]),str(metric_source),'exec'),ns)
mpjpe=[]
(E/'ground-truth').mkdir()
prior_gt={}
for line in (R/'tools/pose-v1/evidence/shared-refine-20261014-r1/frames.jsonl').read_text(encoding='utf-8').splitlines():
    row=json.loads(line)
    if row['sample'] in {f['case'] for f in frames}:prior_gt[row['sample']]=row['gt_sha256']
for f in frames:
    gt_path=ALG/'data/wifipose/test_data/keypoint'/(f['case']+'.npy')
    assert sha(gt_path)==prior_gt[f['case']], 'Ground truth differs from full-test corpus'
    shutil.copyfile(gt_path,E/'ground-truth'/gt_path.name)
    gt=torch.tensor(np.load(gt_path,allow_pickle=False),dtype=torch.float32)
    scores={}
    for mode,path in [('before',OLD/'fixtures'/(f['case']+'.poses.f32')),('after',D/('frame-'+str(f['invocation']))/'poses.f32')]:
        pred=torch.tensor(np.fromfile(path,dtype='<f4').reshape(100,14,3).copy())
        scores[mode]=[float(v) for v in ns['calc_mpjpe'](None,gt,pred,f['case'],root=[5,7])]
    assert scores['before']==scores['after']
    mpjpe.append(dict(case=f['case'],persons=len(gt),gt_sha256=sha(gt_path),metric_mm=scores))
phase_names=[k for k in parts[0] if k.endswith('_ns')]
mean_phase={k:(statistics.mean(p[k] for p in parts)/1e6 if all(p[k] is not None for p in parts) else None) for k in phase_names}
frame_fields=[k for k in frames[0] if k.endswith('_ms')]
frame_mean={k:statistics.mean(f[k] for f in frames) for k in frame_fields}
init_rows=[r for r in rows if r['invocation']==INIT]
old=load(R/'tools/pose-v1/evidence/engine-timing-board-20261013-r2/timing-summary.json')
old_mean=old['frame_metric_ms']['process_ms']['mean']
operators=[]
for op in [0,188,192,437,442]+[g for _,_,g in sync]:
    samples=[next(o for o in p['operators'] if o['op_id']==op) for p in parts]
    operators.append(dict(op_id=op,kind=samples[0]['kind'],
         inclusive_ms=statistics.mean(o['inclusive_ns'] for o in samples)/1e6,
         thread_cpu_ms=statistics.mean(o['thread_cpu_ns'] for o in samples)/1e6,
         phases_ms={k:statistics.mean(o['phases_ns'].get(k,0) for o in samples)/1e6
                    for k in sorted({k for o in samples for k in o['phases_ns']})}))
report=dict(status='three_frame_bitwise_and_timing_verified',frames=3,output_FP32=12900,
   inputs_FP32=32400,all_outputs_bitwise=True,max_output_abs=0.,binding=binding,
   fused_groups=[dict(op_id=g,sync_start=a,layer_count=b,members=len(members[g])) for a,b,g in sync],
   initialized_ms=summary['init_ms'],frame_means_ms=frame_mean,forward_partition_ms=mean_phase,
   initialization_phases_ms={r['kind']:dur(r)/1e6 for r in init_rows},operators=operators,
   arrays=array_checks,per_frame_partitions=parts,MPJPE=mpjpe,
   mean_three_frame_mpjpe_mm=statistics.mean(m['metric_mm']['after'][0] for m in mpjpe),
   reference_comparison=dict(historical_date='2026-10-13',historical_engine_ms=old_mean,
       current_engine_ms=frame_mean['process_ms'],difference_ms=frame_mean['process_ms']-old_mean,
       reduction_percent=(1-frame_mean['process_ms']/old_mean)*100,
       same_windows_sdk_boot_kernel=True,controlled_same_session_AB=False),
   transfers_per_frame=4,transfer_bytes_per_frame=48160,ScatterND_callbacks=0,ScatterND_counter_waits=0,
   pure_NPU_compute_ms=None,DDR_stall_ms=None,exact_SDK_dispatch_ms=None,
   lifetime='single Engine; three frames; no retry/reset0/VPU/TCP/compaction/reboot',
   limits=['3 samples only, first frame cold preprocessing differs; historical comparison is not controlled same-run AB',
           'Report final ready wait as well as Session.forward; neither isolated callback submission nor static layer count measures whole inference',
           'ready wait and thread CPU are host observations, not pure NPU/DDR time',
           'MPJPE uses unchanged GT-assisted all100 greedy matching, not confidence detection accuracy',
           'Shared refinement graph tested; full-dataset board MPJPE, long run and GUI/video remain unverified'])
save(E/'analysis.json',report)
print(json.dumps({k:v for k,v in report.items() if k not in ('arrays','per_frame_partitions','initialization_phases_ms','operators')},indent=2))

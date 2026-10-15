"""Audit all saved outputs, including the third frame rejected by the 3 mm policy."""
import ast,hashlib,json,shutil,statistics,tarfile
from pathlib import Path
import numpy as np
import torch
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
OLD=R/'tools/pose-v1/evidence/noscatter-board-20261015-r1'
PREV=R/'tools/pose-v1/evidence/shared-graph-board-20261015-r1'
RUN=E/'returned/run-wall';D=RUN/'results';FIX=R/'.local/shared-gate-delivery-20261015-r1/fixtures'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
assert (RUN/'exit.txt').read_text().strip()=='1'
failure=load(D/'failure.json');assert failure['completed_frames']==2 and not failure['diagnostic_error']
assert failure['error']=='Output exceeds approved shared 3mm gate or score/finite check failed; stop without retry'
assert not (RUN/'wrapper-failure.json').exists() and not (RUN/'timeout.json').exists()
for n,h in load(RUN/'evidence-files.json').items():assert sha(RUN/n)==h,n
assert (RUN/'before.dmesg.txt').read_bytes()==(RUN/'after.dmesg.txt').read_bytes()
before=load(RUN/'preflight.json');after=load(E/'final-preflight.json')
for k in ('boot_files','libraries','SDK_packages','fpga_state'):assert before[k]==after[k],k
assert after['fpga_state']=='operating' and 'pose_shared_timing' not in after['processes']
assert (E/'docker-final-state.txt').read_text(encoding='utf-8-sig').strip()=='exited'
M=R/'model/piw24_shared-20261015-r1';policy=load(E/'policy.json')
for ext,key in [('json','graph_json_sha256'),('raw','graph_raw_sha256')]:
    assert sha(M/('piw24_shared_ZG.'+ext))==policy[key]
assert policy['max_joint_euclidean_delta_mm']==3
S=R/'.local/shared-gate-source-20261015-r1'
for n,h in load(E/'source-manifest.json')['files'].items():assert sha(S/n)==h,n
assert sha(S/'shared_output_gate.hpp')==sha(R/'tools/pose-v1/shared-output-gate/shared_output_gate.hpp')

binding=load(D/'engine/binding-summary.json')
assert binding['original_hardops']==1021 and binding['coverage_complete'] and binding['validated_runtime_final_count']==612
graph=load(M/'piw24_shared_ZG.json');hard={o['op_id'] for o in graph['ops'] if o['_type_key']=='icraft::xir::HardOp'}
bound=lines(D/'engine/after-apply.all-bindings.jsonl')
hosts={r['binding_key'] for r in bound if r['backend']=='icraft::xrt::HostBackendNode'}
zg={r['binding_key'] for r in bound if 'ZG330BackendNode' in r['backend']}
assert hosts=={0,188,192,437,442,565} and len(zg)==5
metadata={r['op_id']:r for r in lines(D/'engine/after-apply.zg-hardop-map.jsonl')}
members=[i for g in zg for i in metadata[g]['merge_from']]
assert len(members)==len(set(members))==1021 and set(members)==hard
sync=sorted((metadata[g]['sync_index'],metadata[g]['layer_count'],g) for g in zg);end=0
for start,count,g in sync:assert start==end;end+=count
assert end==612

source=PREV/'metric-source.verified-server.py'
assert sha(source)=='52b603525b351b25e16f00237c787ea65d6957dbed0535899007d3fcfaafdb31'
shutil.copyfile(source,E/source.name)
cls=next(n for n in ast.parse(source.read_text(encoding='utf-8')).body if isinstance(n,ast.ClassDef) and n.name=='WifiPoseDataset')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='calc_mpjpe')
ns=dict(torch=torch,np=np);exec(compile(ast.Module(body=[method],type_ignores=[]),str(source),'exec'),ns)
torch.set_num_threads(1)
gt_pins={r['case']:r['gt_sha256'] for r in load(OLD/'analysis.json')['MPJPE']}
frames=lines(D/'frames.jsonl');assert len(frames)==3 and [f['matched'] for f in frames]==[True,True,False]
assert [f['case'] for f in frames]==['S11_01_308','S11_01_309','S11_01_310']
(E/'ground-truth').mkdir()
rows=lines(D/'monotonic-spans.jsonl');assert all(not r['failed'] and r['end_ns']>=r['begin_ns'] for r in rows)
def duration(r):return (r['end_ns']-r['begin_ns'])/1e6
details=[]
for i,f in enumerate(frames):
    arrays={};values={}
    for name,count in [('input',10800),('scores',100),('poses',4200)]:
        actual=D/('frame-'+str(i))/(name+'.f32');reference=FIX/(f['case']+'.'+name+'.f32')
        a=np.fromfile(actual,dtype='<f4');b=np.fromfile(reference,dtype='<f4')
        assert a.size==b.size==count and np.isfinite(a).all() and np.isfinite(b).all()
        diff=a.astype('f8')-b.astype('f8')
        arrays[name]=dict(count=count,finite=True,bitwise_equal=a.tobytes()==b.tobytes(),
            changed_values=int(np.count_nonzero(a.view('u4')!=b.view('u4'))),actual_sha256=sha(actual))
        values[name]=(b,a)
        if name=='poses':
            delta=diff.reshape(100,14,3)*1000.0;norm=np.linalg.norm(delta,axis=-1)
            over=np.argwhere(norm>3.0)
            arrays[name].update(max_coordinate_delta_mm=float(np.abs(delta).max()),max_joint_delta_mm=float(norm.max()),
                highest_score_candidate_max_joint_delta_mm=float(norm[0].max()),
                over_limit_joints=len(over),over_limit_candidate_ids=sorted({int(v[0]) for v in over}),
                over_limit_positions=over.tolist())
            assert abs(float(norm.max())-f['max_joint_delta_mm'])<1e-12
            assert arrays[name]['changed_values']==f['changed_pose_values']
    assert arrays['input']['bitwise_equal'] and arrays['scores']['bitwise_equal']
    assert f['finite'] and f['scores_bitwise_equal'] and not f['poses_bitwise_equal']
    assert f['matched']==(arrays['poses']['max_joint_delta_mm']<=3)
    assert f['completed_layers']==612 and f['host_callbacks']==5 and f['zg_callbacks']==5
    gtpath=OLD/'ground-truth'/(f['case']+'.npy');assert sha(gtpath)==gt_pins[f['case']]
    shutil.copyfile(gtpath,E/'ground-truth'/gtpath.name)
    gt=torch.tensor(np.load(gtpath,allow_pickle=False),dtype=torch.float32);metrics={};matching={}
    for name,pred in zip(('noscatter','shared'),values['poses']):
        pred=torch.tensor(pred.reshape(100,14,3).copy())
        metrics[name]=[float(v) for v in ns['calc_mpjpe'](None,gt,pred,f['case'],root=[5,7])]
        matching[name]=int(torch.norm(gt[0]-pred,p=2,dim=-1).mean(-1).argmin())
    spans=[r for r in rows if r['invocation']==i]
    calls=[r for r in spans if r['kind'] in ('op.host','op.zg')]
    assert len(calls)==10
    assert {r['op_id'] for r in calls if r['kind']=='op.zg'}==zg
    assert {r['op_id'] for r in calls if r['kind']=='op.host'}=={0,188,192,437,442}
    assert not any(r['op_id'] in (582,649) or r['kind']=='bridge.counter_wait' for r in spans)
    phases={k:sum(duration(r) for r in spans if r['kind']==k) for k in sorted({r['kind'] for r in spans if r['kind'].startswith('bridge.')})}
    transfers=[r for r in lines(D/'transfers.jsonl') if r['invocation']==i]
    assert len(transfers)==4 and sum(t['logical_bytes'] for t in transfers)==48160
    details.append(dict(case=f['case'],accepted=f['matched'],arrays=arrays,
        timing_ms={k:v for k,v in f.items() if k.endswith('_ms')},bridge_phases_ms=phases,
        MPJPE_mm=metrics,MPJPE_delta_mm=metrics['shared'][0]-metrics['noscatter'][0],
        matched_candidate_indices=matching))

repeat=all((D/'frame-0'/(n+'.f32')).read_bytes()==(PREV/'returned/run-wall/results/frame-0'/(n+'.f32')).read_bytes()
           for n in ('input','scores','poses'))
source_archive=E/'source.tar.gz';assert not source_archive.exists()
with tarfile.open(source_archive,'x:gz') as t:
    for p in sorted(S.rglob('*')):
        if p.is_file():t.add(p,arcname=p.relative_to(S).as_posix(),recursive=False)
means={k:statistics.mean(f[k] for f in frames) for k in frames[0] if k.endswith('_ms')}
report=dict(status='3mm_policy_implemented_third_frame_rejected',board_exit=1,
    planned_frames=3,actual_inferences=3,accepted_frames=2,rejected_frames=1,
    policy=policy,binding=binding,failure=failure,frames=details,
    all_inputs_bitwise=True,all_scores_bitwise=True,all_outputs_finite=True,
    max_joint_delta_mm=max(d['arrays']['poses']['max_joint_delta_mm'] for d in details),
    changed_pose_values=sum(d['arrays']['poses']['changed_values'] for d in details),
    mean_all_three_measured_frames_ms=means,accepted_three_frame_benchmark=False,
    mean_three_frame_MPJPE_mm={k:statistics.mean(d['MPJPE_mm'][k][0] for d in details) for k in ('noscatter','shared')},
    mean_MPJPE_delta_mm=statistics.mean(d['MPJPE_delta_mm'] for d in details),
    first_frame_repeat_bitwise_same_as_previous_shared_run=repeat,
    initialization_phases_ms={r['kind']:duration(r) for r in rows if r['invocation']==(1<<64)-1},
    source_archive_sha256=sha(source_archive),original_failure_and_models_unchanged=True,
    kernel_logs_unchanged=True,SDK_BOOT_after_identity_unchanged=True,
    no_task_process_remains=True,FPGA_state=after['fpga_state'],FPAI_final_status='exited',
    physical_bias_cause_proven=False,automatic_retry=False,
    unrelated_background_load='MobaXterm monitor and apt/unattended-upgrade observed; not modified; no controlled A/B')
save(E/'analysis.json',report)
print(json.dumps(dict(status=report['status'],accepted=2,rejected=1,
    cases=[dict(case=d['case'],max_joint_delta_mm=d['arrays']['poses']['max_joint_delta_mm'],
        over_limit_joints=d['arrays']['poses']['over_limit_joints'],MPJPE_delta_mm=d['MPJPE_delta_mm'],
        engine_ms=d['timing_ms']['process_ms']) for d in details],
    measured_mean_ms=means['process_ms'],mean_MPJPE_delta_mm=report['mean_MPJPE_delta_mm']),indent=2))

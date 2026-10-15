"""Independent complete-array audit and finite memory observations; no board retry."""
from pathlib import Path
import hashlib,json,statistics,sys
import numpy as np
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
D=R/'.local/shared-stability-delivery-20261015-r2'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def lines(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
stage=sys.argv[1];assert stage in ('basic','short','stress')
run=E/('returned-'+stage)/('run-'+stage);out=run/'results'
exit_code=int((run/'exit.txt').read_text());assert exit_code==0,load(run/'controller-summary.json')
for n,h in load(run/'evidence-files.json').items():assert sha(run/n)==h,n
assert not (out/'failure.json').exists() and not (run/'monitor-failure.json').exists()
assert not (run/'stderr.txt').read_bytes()
assert (run/'before.dmesg.txt').read_bytes()==(run/'after.dmesg.txt').read_bytes()
pre,post=load(run/'preflight.json'),load(run/'post-preflight.json')
for k in ('boot_files','libraries','SDK_packages','fpga_state'):assert pre[k]==post[k],k
assert post['fpga_state']=='operating' and 'pose_shared_' not in post['processes']
binding=load(out/'engine/binding-summary.json')
assert binding['coverage_complete'] and binding['original_hardops']==1021 and binding['validated_runtime_final_count']==612
graph=load(D/'models/piw24_shared_ZG.json');hard={o['op_id'] for o in graph['ops'] if o['_type_key']=='icraft::xir::HardOp'}
bound=lines(out/'engine/after-apply.all-bindings.jsonl')
hosts={r['binding_key'] for r in bound if r['backend']=='icraft::xrt::HostBackendNode'}
zg={r['binding_key'] for r in bound if 'ZG330BackendNode' in r['backend']}
assert hosts=={0,188,192,437,442,565} and len(zg)==5
metadata={r['op_id']:r for r in lines(out/'engine/after-apply.zg-hardop-map.jsonl')}
members=[i for g in zg for i in metadata[g]['merge_from']]
assert len(members)==len(set(members))==1021 and set(members)==hard
end=0
for start,count in sorted((metadata[g]['sync_index'],metadata[g]['layer_count']) for g in zg):
    assert start==end;end+=count
assert end==612
f=lines(out/'frames.jsonl');n=len(f);assert n>0 and all(x['matched'] for x in f)
assert all(x['completed_layers']==612 and x['host_callbacks']==5 and x['zg_callbacks']==5 for x in f)
names=['S11_01_308','S11_01_309','S11_01_310']
refs={key:np.stack([np.fromfile(D/'fixtures'/(name+'.'+key+'.f32'),dtype='<f4') for name in names])
      for key in ('input','scores','poses')}
keys=('input','scores','poses');counts={'input':10800,'scores':100,'poses':4200}
actual={}
if stage=='basic':
    assert n==3
    for key in keys:actual[key]=np.stack([np.fromfile(out/('frame-'+str(i))/(key+'.f32'),dtype='<f4') for i in range(n)])
else:
    summary=load(out/'summary.json');assert summary['status']=='resident_duration_completed'
    assert summary['completed']==summary['saved']==n
    assert summary['actual_duration_ms']>=summary['seconds_budget']*1000
    assert summary['max_frames']<=90000 and n<=summary['max_frames']
    for key in keys:
        path=out/(key+'s.f32' if key=='input' else key+'.f32')
        # Input stream is inputs.f32; scores and poses names already plural.
        assert path.stat().st_size==n*counts[key]*4,(path,path.stat().st_size,n)
        actual[key]=np.memmap(path,dtype='<f4',mode='r',shape=(n,counts[key]))
max_checked=0.;max_all=0.;excluded_above=0;repeat_changed_frames=0;repeat_max_coordinate_mm=0
first_shared_poses=np.array(actual['poses'][:3],copy=True)
for start in range(0,n,128):
    stop=min(n,start+128);indices=np.arange(start,stop)%3
    for key in keys:assert np.isfinite(actual[key][start:stop]).all(),(key,start)
    for key in ('input','scores'):
        assert np.array_equal(actual[key][start:stop].view('u4'),refs[key][indices].view('u4')),(key,start)
    repeated=first_shared_poses[indices]
    repeat_changed_frames+=int(np.count_nonzero(np.any(actual['poses'][start:stop].view('u4')!=repeated.view('u4'),axis=1)))
    repeat_max_coordinate_mm=max(repeat_max_coordinate_mm,float(np.abs(actual['poses'][start:stop].astype('f8')-repeated).max()*1000))
    delta=(actual['poses'][start:stop].astype('f8')-refs['poses'][indices].astype('f8')).reshape(-1,100,14,3)*1000
    norms=np.linalg.norm(delta,axis=-1);mask=refs['scores'][indices]>np.float32(.2)
    fore=norms[mask];back=norms[~mask]
    if fore.size:max_checked=max(max_checked,float(fore.max()))
    max_all=max(max_all,float(norms.max()));excluded_above+=int(np.count_nonzero(back>3))
    assert not fore.size or fore.max()<=3,(start,fore.max())
    for i in range(start,stop):
        assert f[i]['invocation']==i and f[i]['case']==names[i%3]
        assert abs(f[i]['max_checked_joint_delta_mm']-float(norms[i-start][mask[i-start]].max()))<1e-10

resources=lines(run/'resources.jsonl')
steady=[r for r in resources if r.get('inference_elapsed_s') is not None and
        r['inference_elapsed_s']>=load(D/'plan.json')[stage]['memory_warmup_seconds']]
memory=dict(samples=len(resources),steady_samples=len(steady),peak_RSS_KiB=max(r['status_kb'].get('VmRSS',0) for r in resources),
            minimum_MemAvailable_KiB=min(r['meminfo_kb']['MemAvailable'] for r in resources),
            children_optional_interface_missing=any(not r.get('children_observation_supported',True) for r in resources))
leak_screen=None
if stage!='basic':
    assert len(steady)>=10,'Insufficient steady memory samples'
    times=np.array([r['monotonic_s'] for r in steady]);times-=times[0]
    for key,src in [('RSS','status_kb'),('Pss','smaps_kb'),('Private_Dirty','smaps_kb'),('VmSize','status_kb'),('VmData','status_kb')]:
        field='VmRSS' if key=='RSS' else key;values=np.array([r[src].get(field,0) for r in steady],dtype='f8')
        slope=float(np.polyfit(times,values,1)[0]*60) if times[-1]>0 else 0
        memory[key]=dict(first_median_KiB=float(np.median(values[:5])),last_median_KiB=float(np.median(values[-5:])),
            change_KiB=float(np.median(values[-5:])-np.median(values[:5])),min_KiB=float(values.min()),
            max_KiB=float(values.max()),linear_slope_KiB_per_minute=slope)
    for key,src in [('fd_count',None),('Threads','status_kb'),('map_count',None)]:
        values=[r[src][key] if src else r[key] for r in steady]
        memory[key]=dict(first_median=float(statistics.median(values[:5])),last_median=float(statistics.median(values[-5:])),
            min=min(values),max=max(values))
    cap=4096 if stage=='short' else 8192;slope_cap=1024 if stage=='short' else 64
    leak_screen=(memory['Pss']['change_KiB']<=cap and memory['RSS']['change_KiB']<=cap and memory['VmData']['change_KiB']<=cap and
        memory['Pss']['linear_slope_KiB_per_minute']<=slope_cap and
        memory['fd_count']['last_median']<=memory['fd_count']['first_median']+1 and
        memory['Threads']['last_median']<=memory['Threads']['first_median'] and
        memory['map_count']['last_median']<=memory['map_count']['first_median']+2)
    metadata=lines(out/'copy-observations/metadata.jsonl');assert metadata and max(r['invocation'] for r in metadata)<=2
    identity=lines(out/'tensor-identities/objects.jsonl');assert identity and max(r['invocation'] for r in identity)<=2
    spans=lines(out/'monotonic-spans.jsonl');assert all(not r['failed'] for r in spans)
    assert {r['invocation'] for r in spans if r['invocation']!=2**64-1}=={0,1,2}
    # No inference-path source read, mathematical change, or growing diagnostics is introduced.
    memory['regular_copy_metadata_rows']=len(metadata)
    memory['regular_identity_rows']=len(identity)
    memory['timing_record_rows']=len(spans)
    memory['CmaFree_KiB_range']=[min(r['meminfo_kb']['CmaFree'] for r in steady),max(r['meminfo_kb']['CmaFree'] for r in steady)]
    assert n>=300

stats={}
for key in ('process_ms','preprocess_ms','forward_ms','final_wait_ms','output_read_ms'):
    v=np.array([r[key] for r in f]);stats[key]=dict(mean=float(v.mean()),median=float(np.median(v)),p95=float(np.percentile(v,95)),max=float(v.max()))
report=dict(status='passed' if leak_screen is not False else 'memory_growth_screen_not_passed',stage=stage,
    exit=0,inferences=n,unique_input_sources=3,all_input_and_scores_bitwise=True,all_outputs_finite=True,
    max_checked_joint_delta_mm=max_checked,max_all_joint_delta_mm=max_all,
    excluded_background_overlimit_joints=excluded_above,memory=memory,memory_growth_screen_passed=leak_screen,
    timing_ms=stats,SDK_BOOT_kernel_unchanged=True,no_task_process_remains=True,
    binding=binding,complete_HardOp_union_verified=True,
    same_graph_repeat_pose_changed_frames=repeat_changed_frames,same_graph_repeat_max_coordinate_mm=repeat_max_coordinate_mm,
    complete_saved_actual_outputs=True,graceful_engine_cleanup=True,
    duration=load(out/'summary.json') if stage!='basic' else None,
    leak_limit='Finite observation cannot prove absence of leaks in all inputs, paths, or indefinitely')
save(E/(stage+'-analysis.json'),report)
print(json.dumps(dict(status=report['status'],stage=stage,inferences=n,memory=memory,Engine_ms=stats['process_ms']),indent=2))
if stage=='short':
    save(E/'short-reviewed.json',dict(approved_to_start_stress=bool(leak_screen),source_report_sha256=sha(E/'short-analysis.json'),
        inferences=n,package_sha256=sha(D/'package.json'),memory_screen=memory))
if leak_screen is False:raise SystemExit(2)

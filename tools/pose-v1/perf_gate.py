"""Profiling-off independent package and review. Frozen r2 sources stay unchanged."""
import argparse,json,shutil,sys
from pathlib import Path
import numpy as np
import mixed_validation_gate as old
from runtime_gate import captures
ROOT=old.ROOT;R6=ROOT/'tools/pose-v1/evidence/mixed-20261006-frame-state-r6/mixed-three/results'
sha,load,save,verify,need,lines=old.sha,old.load,old.save,old.verify,old.need,old.lines

def prepare(a):
    base=ROOT/'.local/pose-v1-runtime/package-20261007-e0-n1-p1-r2';verify(base);m=load(base/'manifest.json')
    for rel,h in m['sources'].items():need(sha(ROOT/rel)==h,'Frozen r2 changed: '+rel)
    need(not a.package.exists(),'Preserve package');shutil.copytree(base,a.package)
    replacements={
      'software/pose_v1/src/runtime_core.cpp':('software/pose_v1/src/timed_runtime_core.cpp','runtime_core.cpp'),
      'software/pose_v1/src/runtime_check.cpp':('software/pose_v1/src/timed_runtime_check.cpp','runtime_check.cpp'),
      'software/pose_v1/src/mixed_bridge.cpp':('software/pose_v1/src/timed_mixed_bridge.cpp','mixed_bridge.cpp')}
    for previous,(rel,dest) in replacements.items():
        m['build_files'].pop(previous);m['build_files'][rel]=dict(destination=dest,sha256=sha(ROOT/rel));m['sources'][rel]=sha(ROOT/rel)
    rel='software/pose_v1/include/forward_clock.hpp';m['build_files'][rel]=dict(destination='forward_clock.hpp',sha256=sha(ROOT/rel));m['sources'][rel]=sha(ROOT/rel)
    for rel in ['tools/pose-v1/perf_gate.py','tools/pose-v1/run-perf-validation.sh']:m['sources'][rel]=sha(ROOT/rel)
    m['profile_enabled']=False;m['parent_r2_manifest_sha256']=sha(base/'manifest.json');m['stage']='profile_off_single_clock_prepared_not_executed'
    (a.package/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode())
    shutil.copyfile(ROOT/'tools/pose-v1/run-perf-validation.sh',a.package/'run-perf-validation.sh');old.checksum(a.package);print('Profiling-off package prepared:',verify(a.package))

def review(a):
    if a.stage=='host-check':return old.stage_review(a)
    verify(a.package);count=verify(a.results);m=load(a.package/'manifest.json');b=load(a.build/'build-result.json');out=a.results/'results'
    for r,h in m['sources'].items():need(sha(ROOT/r)==h,'Source changed after preparation: '+r)
    need((a.results/'exit.txt').read_text().strip()=='0' and (a.results/'run.stderr.log').stat().st_size==0 and not(out/'failure.json').exists(),'Runtime failure; stop')
    need(sha(a.results/'pose_mixed_check')==b['binary_sha256'] and b['package_manifest_sha256']==sha(a.package/'manifest.json'),'Binary/package mismatch')
    old.sdk(load(a.results/'sdk-audit.json'),m)
    identity=load(a.results/'run-identity.json');prev=load(a.results/'previous-acceptance.json');expected_prev={'e0':'host-check','p1':'e0'}[a.stage]
    need(identity==dict(stage=a.stage,package_manifest_sha256=b['package_manifest_sha256'],binary_sha256=b['binary_sha256'],previous_stage=expected_prev),'Run identity')
    need(prev['status']=='stage_engineering_review_passed' and prev['stage']==expected_prev and prev['binary_sha256']==b['binary_sha256'] and prev['package_manifest_sha256']==b['package_manifest_sha256'],'Prior gate')
    need((a.results/'dmesg.before.log').read_bytes()==(a.results/'dmesg.after.log').read_bytes(),'New kernel messages require review')
    need('not found' not in (a.results/'ldd.txt').read_text(),'Library unresolved')
    config=load(out/'run-config.json');need(config==dict(mode=a.stage,device_init_allowed=True,content_capture=a.stage!='p1',sdk_profiling=False,frame_state_reset_level=1,sdk_wait_ms=10000,minimal_log=a.stage=='p1'),'Scope differs')
    versions=load(out/'device-version.json')['versions'];need(versions['device']=='25122301' and versions['icore']=='FMSHZGV3TECH-AID - 24160628','FPGA baseline changed')
    old.registry(out/'registry.jsonl');old.fusion_binding_review(out,load(a.package/'mixed-fusion-baseline.json'))
    for p in lines(out/'host-parameters.jsonl'):
        path=f"op{p['op_id']}.param{p['input']}.f32";need((out/path).read_bytes()==(R6/path).read_bytes() and p['loaded_from_real_RAW'],'Real RAW parameters changed')
    need(len(lines(out/'host-parameters.jsonl'))==4,'Parameter count')
    cases=m['expanded_cases'] if a.stage=='n1' else m['cases']
    calls=[cases[i%3] for i in range(33)] if a.stage=='p1' else cases+[cases[0]]
    rows=lines(out/'results.jsonl');need(len(rows)==len(calls),'Call count')
    execution=lines(out/'operator-execution.jsonl');state=lines(out/'readiness.jsonl')
    signatures=set()
    for inv,(r,c) in enumerate(zip(rows,calls)):
        need(all(r[k]==c[k] for k in ('case','frame_id','source_time_ns')) and r['invocation']==inv and r['output_stem']==f'call{inv}','Call identity')
        need(r['before_clear']==(0 if inv==0 else 745) and r['before_forward']==0 and r['completed_layers']==745,'Completion protocol')
        need(r['host_callbacks']==r['zg_callbacks']==7 and r['measured']==(a.stage=='p1' and inv>=3),'Callback/timing scope')
        for k in ('preprocess_ms','prepare_ms','state_clear_ms','forward_ms','final_wait_ms','output_ms','selection_ms','process_ms','cpu_ms'):
            need(np.isfinite(r[k]) and r[k]>=0,'Timing invalid')
        need(type(r['rss_kib']) is int and r['rss_kib']>0,'RSS invalid')
        ex=[e for e in execution if e['invocation']==inv];need(len(ex)==14 and all(e['frame_id']==c['frame_id'] for e in ex),'Execution count/identity')
        need({e['op_id'] for e in ex if 'HostBackend' in e['backend']}=={0,*old.HOST_IDS},'Host coverage')
        need({e['op_id'] for e in ex if 'ZG330Backend' in e['backend']}==set(range(9185,9192)),'ZG coverage')
        states=[e for e in state if e['invocation']==inv];need(len(states)==(5 if a.stage=='p1' else 19),'State coverage')
        for where,count_value in [('before_frame_state_clear',0 if inv==0 else 745),('before_forward',0),('outputs_completed',745),('after_dump',745)]:
            found=[s for s in states if s['where']==where];need(len(found)==1 and found[0]['layer_count']==count_value and all(found[0]['ready']),'Frame readiness')
        pending=[s for s in states if s['where']=='after_forward']
        need(len(pending)==1 and 0<=pending[0]['layer_count']<=745 and len(pending[0]['ready'])==2,'Invalid asynchronous return observation')
        for s in states:
            if s['where']=='post_callback' and 9185<=s['op_id']<=9191:
                minimum={9185:223,9186:234,9187:477,9188:481,9189:638,9190:720,9191:745}[s['op_id']]
                need(0<=s['layer_count']<=745,'Fused group readiness')
        output_bytes=[]
        for suffix,size in [('scores',100),('poses',4200)]:
            raw=(out/f'call{inv}.{suffix}.f32').read_bytes();v=np.frombuffer(raw,dtype='<f4');need(v.size==size and np.isfinite(v).all(),'Model output invalid');output_bytes.append(raw)
            if a.stage in ('e0','p1'):need(raw==(R6/(c['case']+'.'+suffix+'.f32')).read_bytes(),'Output differs from frozen r6')
            if a.stage!='p1' and inv==len(cases):need(raw==(out/f'call0.{suffix}.f32').read_bytes(),'Same-session repeat differs')
        need(r['top_index']==int(np.argmax(np.frombuffer(output_bytes[0],dtype='<f4'))),'Selection differs')
        signatures.add(tuple(hashlib.sha256(x).hexdigest() for x in output_bytes))
        need((out/(c['case']+'.input.f32')).read_bytes()==(a.package/'reference'/(c['case']+'.input.f32')).read_bytes(),'PS input differs')
    need(len(signatures)>1,'No input response');summary=load(out/'summary.json')
    need(summary['forward_calls']==len(calls) and summary['case_count']==len(cases) and summary['sdk_profiling'] is False,'Summary mismatch')
    report=dict(status='stage_engineering_review_passed',stage=a.stage,binary_sha256=b['binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],returned_files_verified=count,
                calls=len(calls),different_outputs=len(signatures),session_init_ms=summary['session_init_ms'],numerical_accepted=False,performance_accepted=False)
    if a.stage!='p1':report['content']=captures(out,a.package,calls)
    else:
        need(not(out/'content').exists() and (out/'bridge.jsonl').stat().st_size==0,'Minimal IO scope')
        stages=[s['stage'] for s in lines(out/'stages.jsonl')]
        need(stages.count('warmup_three_r6_verified_before_measurement')==1,'Missing pre-measurement r6 gate')
        gate_index=stages.index('warmup_three_r6_verified_before_measurement')
        need(stages[:gate_index].count('forward_started')==3 and stages[gate_index:].count('forward_started')==30,'Warmup gate order differs')
        measured=rows[3:];metrics={}
        for k in ('preprocess_ms','prepare_ms','state_clear_ms','forward_ms','final_wait_ms','output_ms','selection_ms','process_ms','cpu_ms'):
            v=np.array([r[k] for r in measured]);metrics[k]=dict(min=float(v.min()),median=float(np.median(v)),p95=float(np.percentile(v,95)),max=float(v.max()),mean=float(v.mean()))
        report['performance']=dict(warmup=3,measured=30,metrics=metrics,processing_throughput_hz=30000/sum(r['process_ms'] for r in measured),
            rss_kib_min=min(r['rss_kib'] for r in rows),rss_kib_max=max(r['rss_kib'] for r in rows),sdk_profiling=False,
            excludes='Session initialization, input file/network IO, batched evidence IO and hashes; includes PS preprocessing/state clear/forward/wait/readout/finite/selection',
            full_system_5Hz_accepted=False)
    report['monotonic_breakdown']=timing_review(out,calls,rows)
    need(load(out/'sdk-profile-setting.json')==dict(enabled=False,wall_clock='std::chrono::steady_clock',unit='ns'),'Profiling-off identity')
    save(a.output,report);print('Reviewed:',a.stage)

def timing_review(out,calls,rows):
    spans=lines(out/'monotonic-spans.jsonl');by_call=[]
    def duration(r):return (r['end_ns']-r['begin_ns'])/1e6
    for inv,c in enumerate(calls):
        found=[r for r in spans if r['invocation']==inv]
        need(all(r['frame_id']==c['frame_id'] and type(r['begin_ns']) is int and type(r['end_ns']) is int and 0<=r['begin_ns']<=r['end_ns'] for r in found),'Clock/case identity')
        total=[r for r in found if r['kind']=='runtime.total'];forward=[r for r in found if r['kind']=='runtime.forward']
        need(len(total)==len(forward)==1 and abs(duration(total[0])-rows[inv]['process_ms'])<1,'Process timing identity')
        op=[r for r in found if r['kind'] in ('op.host','op.zg')]
        need(len(op)==14 and {r['op_id'] for r in op if r['kind']=='op.host'}=={0,*old.HOST_IDS} and {r['op_id'] for r in op if r['kind']=='op.zg'}==set(range(9185,9192)),'Timed callback coverage')
        ordered=sorted(op,key=lambda r:r['begin_ns'])
        need(all(a['end_ns']<=b['begin_ns'] for a,b in zip(ordered,ordered[1:])),'Overlapping backend spans; cannot partition')
        for r in op:need(forward[0]['begin_ns']<=r['begin_ns']<=r['end_ns']<=forward[0]['end_ns'],'Callback outside forward')
        bridge=[r for r in found if r['kind'].startswith('bridge.')]
        for kind,count in [('bridge.wait',8),('bridge.allocate',8),('bridge.copy',8),('bridge.cpu',5),('bridge.spec',5)]:
            need(sum(r['kind']==kind for r in bridge)==count,'Timed bridge coverage: '+kind)
        for r in bridge:
            enclosing=[o for o in op if o['op_id']==r['op_id']]
            need(len(enclosing)==1 and enclosing[0]['begin_ns']<=r['begin_ns']<=r['end_ns']<=enclosing[0]['end_ns'],'Bridge span outside Host operation')
        values={kind:sum(duration(r) for r in found if r['kind']==kind) for kind in {r['kind'] for r in found}}
        residual=duration(forward[0])-sum(duration(o) for o in op)
        need(residual>=0,'Negative forward residual')
        by_call.append(dict(invocation=inv,case=c['case'],values_ms=values,forward_unattributed_ms=residual,per_op_ms={str(r['op_id']):duration(r) for r in op}))
    selected=by_call[3:] if len(calls)==33 else by_call
    keys=set().union(*(r['values_ms'] for r in selected))
    def stats(v):return dict(mean=float(np.mean(v)),median=float(np.median(v)),p95=float(np.percentile(v,95)),max=float(max(v)))
    return dict(clock='std::chrono::steady_clock',raw_unit='ns',callback_spans_are_backend_wall_not_pure_NPU=True,nested_bridge_times_not_added_again_to_forward=True,
        aggregate_ms={k:stats([r['values_ms'].get(k,0) for r in selected]) for k in sorted(keys)},per_op_ms={str(i):stats([r['per_op_ms'][str(i)] for r in selected]) for i in sorted({0,*old.HOST_IDS,*range(9185,9192)})},
        forward_unattributed_ms=stats([r['forward_unattributed_ms'] for r in selected]),calls=by_call)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    q=s.add_parser('prepare');q.add_argument('--package',type=Path,required=True);q.set_defaults(func=prepare)
    q=s.add_parser('review-build')
    for k in ('package','build','output'):q.add_argument('--'+k,type=Path,required=True)
    q.set_defaults(func=old.build_review)
    q=s.add_parser('review-stage');q.add_argument('--stage',choices=['host-check','e0','p1'],required=True)
    for k in ('package','build','results','output'):q.add_argument('--'+k,type=Path,required=True)
    q.set_defaults(func=review)
    a=p.parse_args();a.func(a)

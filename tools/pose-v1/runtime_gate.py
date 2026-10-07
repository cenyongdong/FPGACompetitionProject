"""Isolated E0/N1/P1 packaging and offline evidence review; never accesses hardware."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
from types import SimpleNamespace
import numpy as np
import mixed_validation_gate as old
from host_content_review import INPUT_SIZES, RESULT_SIZES

ROOT=old.ROOT
BASE=ROOT/'.local/pose-v1-mixed-validation/package-20261006-frame-state-r6'
R6=ROOT/'tools/pose-v1/evidence/mixed-20261006-frame-state-r6/mixed-three/results'
sha,load,save,verify,need,lines=old.sha,old.load,old.save,old.verify,old.need,old.lines
NEW={
 'software/pose_v1/include/runtime_core.hpp':'runtime_core.hpp',
 'software/pose_v1/include/runtime_validation.hpp':'runtime_validation.hpp',
 'software/pose_v1/src/runtime_core.cpp':'runtime_core.cpp',
 'software/pose_v1/src/runtime_check.cpp':'runtime_check.cpp',
 'tools/pose-v1/runtime-CMakeLists.txt':'CMakeLists.txt',
}

def prepare(a):
    verify(BASE);m=load(BASE/'manifest.json')
    for rel,h in m['sources'].items():need(sha(ROOT/rel)==h,'Frozen r6 source changed: '+rel)
    selection=ROOT/'tools/pose-v1/evidence/next-phase-20261006/proposed-27-cases.json'
    expanded=load(selection)['cases'];need(len(expanded)==27,'Wrong selection')
    need(not a.package.exists(),'Preserve package');shutil.copytree(BASE,a.package)
    for c in expanded:
        for field,suffix,folder in [('raw','.csi','inputs'),('reference','.input.f32','reference')]:
            p=ROOT/c[field+'_path'];need(sha(p)==c[field+'_sha256'],'Selected source changed')
            dest=a.package/folder/(c['case']+suffix)
            if dest.exists():need(sha(dest)==sha(p),'Shared input identity differs')
            else:shutil.copyfile(p,dest)
    (a.package/'cases.tsv').write_bytes((''.join(f"base\t{c['case']}\t{c['frame_id']}\t{c['source_time_ns']}\n" for c in m['cases'])+
        ''.join(f"expanded\t{c['case']}\t{c['frame_id']}\t{c['source_time_ns']}\n" for c in expanded)).encode())
    m['expanded_cases']=expanded;m['selection_sha256']=sha(selection)
    m['r6_manifest_sha256']=sha(BASE/'manifest.json');m['r6_binary_sha256']='f826fc31441caf09ef22d94561672023737ab4c330ba22ec0159ecf7f77e144a'
    verify(R6.parent)
    need(sha(R6.parent/'pose_mixed_check')==m['r6_binary_sha256'],'r6 evidence binary differs')
    (a.package/'r6-reference').mkdir()
    m['r6_output_sha256']={}
    for c in m['cases']:
        for suffix in ('scores','poses'):
            name=c['case']+'.'+suffix+'.f32'
            shutil.copyfile(R6/name,a.package/'r6-reference'/name)
            m['r6_output_sha256'][name]=sha(R6/name)
    m['build_files'].pop('software/pose_v1/src/mixed_check.cpp');m['build_files'].pop('tools/pose-v1/mixed-validation-CMakeLists.txt')
    m['build_files'].update({r:dict(destination=d,sha256=sha(ROOT/r)) for r,d in NEW.items()})
    for rel in (*NEW,'tools/pose-v1/runtime_gate.py','tools/pose-v1/run-runtime-validation.sh','tools/pose-v1/runtime_onnx_reference.py'):
        m['sources'][rel]=sha(ROOT/rel)
    m['stage']='E0_N1_P1_prepared_not_executed'
    (a.package/'manifest.json').write_bytes((json.dumps(m,indent=2,ensure_ascii=False)+'\n').encode())
    shutil.copyfile(ROOT/'tools/pose-v1/run-runtime-validation.sh',a.package/'run-runtime-validation.sh')
    old.checksum(a.package);print('Runtime package prepared:',verify(a.package))

def captures(out,package,calls):
    rows=lines(out/'content/index.jsonl');need(len(rows)==17*len(calls),'Capture count')
    expected_keys={('caller_input',0,0),('input0_output',0,0)}|{('bridge_input',*x) for x in INPUT_SIZES}|{('bridge_result',*x) for x in RESULT_SIZES}
    raw={};seen=set()
    for inv,c in enumerate(calls):
        found=[r for r in rows if r['invocation']==inv]
        need(len(found)==17 and {(r['kind'],r['op_id'],r['slot']) for r in found}==expected_keys,'Capture coverage')
        for r in found:
            need(r['case']==c['case'] and r['frame_id']==c['frame_id'],'Capture case identity')
            for key in ('invocation','frame_id','op_id','slot','bytes'):need(type(r[key]) is int and r[key]>=0,'Capture integer')
            name=f"call{inv}.{r['kind']}.op{r['op_id']}.slot{r['slot']}.f32"
            need(r['file']==name and name not in seen,'Capture filename');seen.add(name)
            data=(out/'content'/name).read_bytes();meta=r['tensor']
            need(meta['allocated'] is True and meta['pointer']=='CPTR' and meta['region']=='icraft::xrt::HostMemRegionNode' and meta['bytes']==len(data)==r['bytes'],'Capture storage')
            need(type(meta['offset']) is int and type(meta['chunk_bytes']) is int and 0<=meta['offset']<=meta['chunk_bytes'] and len(data)<=meta['chunk_bytes']-meta['offset'],'Capture bounds')
            need(np.isfinite(np.frombuffer(data,dtype='<f4')).all(),'Capture finite')
            if r['kind'] in ('caller_input','input0_output'):
                need(r.get('matches_expected') is True and data==(package/'reference'/(c['case']+'.input.f32')).read_bytes(),'Actual PS/Input0 differs')
                need(type(r.get('same_handle_as_caller')) is bool and type(r.get('same_chunk_as_caller')) is bool,'Caller metadata')
            else:
                sizes=INPUT_SIZES if r['kind']=='bridge_input' else RESULT_SIZES
                need(len(data)==sizes[r['op_id'],r['slot']],'Bridge size')
            raw[(inv,r['kind'],r['op_id'],r['slot'])]=data
    need({p.name for p in (out/'content').iterdir()}==seen|{'index.jsonl'},'Extra capture')
    # Every captured value, not just final output, must repeat.
    for key,value in raw.items():
        if key[0]==len(calls)-1:need(value==raw[(0,)+key[1:]],'Repeated capture differs')
    ops={o['op_id']:o for o in load(package/'graph/piw24_ZG.json')['ops']};total=0
    for inv in range(len(calls)):
        for opid in (188,192,437,582,649):
            op=ops[opid];args=[];slot=0
            for i,v in enumerate(op['inputs']):
                if v['_type_key'].endswith('Params'):data=(out/f'op{opid}.param{i}.f32').read_bytes()
                else:data=raw[inv,'bridge_input',opid,slot];slot+=1
                args.append(np.frombuffer(data,dtype='<f4').reshape(v['dtype']['shape']))
            if opid in (188,437):
                idx=np.argsort(-args[0],axis=op['axis'],kind='stable');sel=[slice(None)]*idx.ndim;sel[op['axis']]=slice(0,int(args[1].flat[0]));idx=idx[tuple(sel)]
                expect=[np.take_along_axis(args[0],idx,axis=op['axis']),idx.astype('<f4')]
            elif opid==192:
                need(np.array_equal(args[1],np.trunc(args[1])),'Noninteger Gather indices');expect=[np.take_along_axis(args[0],args[1].astype(np.int64),axis=op['axis'])]
            else:
                need(np.array_equal(args[1],np.trunc(args[1])),'Noninteger Scatter indices');idx=args[1].astype(np.int64);value=args[0].copy()
                need(np.unique(idx.reshape(-1,3),axis=0).shape[0]==4200,'Scatter full grid differs')
                value[tuple(idx[...,j] for j in range(3))]=args[2];expect=[value]
            for slot,value in enumerate(expect):
                need(value.astype('<f4').tobytes()==raw[inv,'bridge_result',opid,slot],'Real CPU NumPy mismatch');total+=value.size
    return dict(records=len(rows),real_CPU_values_bitwise_equal=total,Gather_content_verified=False,provided_output_writeback_verified=False)

def review(a):
    if a.stage=='host-check':return old.stage_review(a)
    verify(a.package);count=verify(a.results);m=load(a.package/'manifest.json');b=load(a.build/'build-result.json');out=a.results/'results'
    for r,h in m['sources'].items():need(sha(ROOT/r)==h,'Source changed after preparation: '+r)
    need((a.results/'exit.txt').read_text().strip()=='0' and (a.results/'run.stderr.log').stat().st_size==0 and not(out/'failure.json').exists(),'Runtime failure; stop')
    need(sha(a.results/'pose_mixed_check')==b['binary_sha256'] and b['package_manifest_sha256']==sha(a.package/'manifest.json'),'Binary/package mismatch')
    old.sdk(load(a.results/'sdk-audit.json'),m)
    identity=load(a.results/'run-identity.json');prev=load(a.results/'previous-acceptance.json');expected_prev={'e0':'host-check','n1':'e0','p1':'n1'}[a.stage]
    need(identity==dict(stage=a.stage,package_manifest_sha256=b['package_manifest_sha256'],binary_sha256=b['binary_sha256'],previous_stage=expected_prev),'Run identity')
    need(prev['status']=='stage_engineering_review_passed' and prev['stage']==expected_prev and prev['binary_sha256']==b['binary_sha256'] and prev['package_manifest_sha256']==b['package_manifest_sha256'],'Prior gate')
    need((a.results/'dmesg.before.log').read_bytes()==(a.results/'dmesg.after.log').read_bytes(),'New kernel messages require review')
    need('not found' not in (a.results/'ldd.txt').read_text(),'Library unresolved')
    config=load(out/'run-config.json');need(config==dict(mode=a.stage,device_init_allowed=True,content_capture=a.stage!='p1',sdk_profiling=True,frame_state_reset_level=1,sdk_wait_ms=10000,minimal_log=a.stage=='p1'),'Scope differs')
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
        for where,count_value in [('before_frame_state_clear',0 if inv==0 else 745),('before_forward',0),('after_forward',745),('outputs_completed',745),('after_dump',745)]:
            found=[s for s in states if s['where']==where];need(len(found)==1 and found[0]['layer_count']==count_value and all(found[0]['ready']),'Frame readiness')
        for s in states:
            if s['where']=='post_callback' and 9185<=s['op_id']<=9191:
                minimum={9185:223,9186:234,9187:477,9188:481,9189:638,9190:720,9191:745}[s['op_id']]
                need(minimum<=s['layer_count']<=745 and all(s['ready']),'Fused group readiness')
        output_bytes=[]
        for suffix,size in [('scores',100),('poses',4200)]:
            raw=(out/f'call{inv}.{suffix}.f32').read_bytes();v=np.frombuffer(raw,dtype='<f4');need(v.size==size and np.isfinite(v).all(),'Model output invalid');output_bytes.append(raw)
            if a.stage in ('e0','p1'):need(raw==(R6/(c['case']+'.'+suffix+'.f32')).read_bytes(),'Output differs from frozen r6')
            if a.stage!='p1' and inv==len(cases):need(raw==(out/f'call0.{suffix}.f32').read_bytes(),'Same-session repeat differs')
        need(r['top_index']==int(np.argmax(np.frombuffer(output_bytes[0],dtype='<f4'))),'Selection differs')
        signatures.add(tuple(hashlib.sha256(x).hexdigest() for x in output_bytes))
        need((out/(c['case']+'.input.f32')).read_bytes()==(a.package/'reference'/(c['case']+'.input.f32')).read_bytes(),'PS input differs')
    need(len(signatures)>1,'No input response');summary=load(out/'summary.json')
    need(summary['forward_calls']==len(calls) and summary['case_count']==len(cases) and summary['sdk_profiling'] is True,'Summary mismatch')
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
            rss_kib_min=min(r['rss_kib'] for r in rows),rss_kib_max=max(r['rss_kib'] for r in rows),sdk_profiling=True,
            excludes='Session initialization, input file/network IO, batched evidence IO and hashes; includes PS preprocessing/state clear/forward/wait/readout/finite/selection',
            full_system_5Hz_accepted=False)
    save(a.output,report);print('Reviewed:',a.stage)

def compare(a):
    verify(a.package);verify(a.reference);verify(a.results);ref=a.reference;out=a.results/'results';m=load(a.package/'manifest.json');cases=m['expanded_cases']
    approval=load(a.acceptance);need(approval['stage']=='n1' and approval['status']=='stage_engineering_review_passed' and approval['binary_sha256']==sha(a.results/'pose_mixed_check'),'N1 engineering review required')
    need(approval['package_manifest_sha256']==sha(a.package/'manifest.json')==load(a.results/'run-identity.json')['package_manifest_sha256'],'Comparison package mismatch')
    env=load(ref/'environment.json');need(env['model_sha256']=='7b04090e374e31e016d5703bbcf1d0a561d0b98f268fde984b0bf0461598bd21' and env['providers']==['CPUExecutionProvider'],'ORT identity')
    need(load(ref/'summary.json')['repeated_first_bitwise_equal'],'ORT repeat')
    ref_rows=lines(ref/'results.jsonl');board_rows=lines(out/'results.jsonl')
    need(len(ref_rows)==len(board_rows)==28,'Comparison call count')
    for inv,c in enumerate(cases+[cases[0]]):
        need(all(ref_rows[inv][k]==board_rows[inv][k]==c[k] for k in ('case','frame_id','source_time_ns')) and ref_rows[inv]['invocation']==board_rows[inv]['invocation']==inv,'Comparison frame mismatch')
    def stats(x,y):
        d=y.astype('f8')-x.astype('f8');v=np.abs(d)
        return dict(max_abs=float(v.max()),mean_abs=float(v.mean()),rms=float(np.sqrt(np.mean(d*d))),p95_abs=float(np.percentile(v,95)),bitwise_equal=x.tobytes()==y.tobytes())
    report=dict(status='deployment_errors_reported_tolerance_pending',coordinate_units='model_raw',same_slot_is_not_candidate_identity=True,MPJPE_evaluated=False,cases=[])
    aggregate={'scores':([],[]),'poses':([],[]),'selected_best_coordinates':([],[])}
    for inv,c in enumerate(cases):
        name=c['case'];need((ref/(name+'.input.f32')).read_bytes()==(out/(name+'.input.f32')).read_bytes(),'Comparison inputs differ');arrays={};entry=dict(case=name,group=c['group'],frame_id=c['frame_id'])
        for kind,shape in [('scores',(100,)),('poses',(100,14,3))]:
            x=np.frombuffer((ref/(name+'.'+kind+'.f32')).read_bytes(),dtype='<f4').reshape(shape);y=np.frombuffer((out/f'call{inv}.{kind}.f32').read_bytes(),dtype='<f4').reshape(shape)
            need(np.isfinite(x).all() and np.isfinite(y).all(),'Finite comparison');arrays[kind]=(x,y);entry[kind]=stats(x,y);aggregate[kind][0].append(x.ravel());aggregate[kind][1].append(y.ravel())
        i,j=map(lambda x:int(np.argmax(x)),arrays['scores']);x,y=arrays['poses'];entry.update(reference_top_index=i,board_top_index=j,top_slot_changed=i!=j,selected_best_coordinates=stats(x[i],y[j]))
        aggregate['selected_best_coordinates'][0].append(x[i].ravel());aggregate['selected_best_coordinates'][1].append(y[j].ravel());report['cases'].append(entry)
    report['aggregate']={k:stats(np.concatenate(x),np.concatenate(y)) for k,(x,y) in aggregate.items()}
    report['top_slot_switch_count']=sum(r['top_slot_changed'] for r in report['cases']);report['numerical_accepted']=False;save(a.output,report)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    q=s.add_parser('prepare');q.add_argument('--package',type=Path,required=True);q.set_defaults(func=prepare)
    q=s.add_parser('review-build')
    for k in ('package','build','output'):q.add_argument('--'+k,type=Path,required=True)
    q.set_defaults(func=old.build_review)
    q=s.add_parser('review-stage');q.add_argument('--stage',choices=['host-check','e0','n1','p1'],required=True)
    for k in ('package','build','results','output'):q.add_argument('--'+k,type=Path,required=True)
    q.set_defaults(func=review)
    q=s.add_parser('compare')
    for k in ('package','reference','results','acceptance','output'):q.add_argument('--'+k,type=Path,required=True)
    q.set_defaults(func=compare)
    a=p.parse_args();a.func(a)

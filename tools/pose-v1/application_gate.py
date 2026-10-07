"""Prepare/review isolated E1-A/B application; no devices are opened here."""
import argparse,hashlib,json,shutil,struct
from pathlib import Path
import numpy as np
import mixed_validation_gate as old
ROOT=old.ROOT
sha,load,save,verify,need,lines=old.sha,old.load,old.save,old.verify,old.need,old.lines

def prepare(a):
    parent=ROOT/'.local/pose-v1-perf/package-20261007-lazy-r4';verify(parent);m=load(parent/'manifest.json')
    for rel,h in m['sources'].items():need(sha(ROOT/rel)==h,'Frozen baseline changed: '+rel)
    need(not a.package.exists(),'Preserve package');shutil.copytree(parent,a.package)
    replacements={
      'software/pose_v1/include/runtime_core.hpp':('software/pose_v1/include/application_core.hpp','application_core.hpp'),
      'software/pose_v1/src/timed_runtime_core.cpp':('software/pose_v1/src/application_core.cpp','application_core.cpp'),
      'software/pose_v1/src/timed_runtime_check.cpp':('software/pose_v1/src/application_check.cpp','application_check.cpp'),
      'software/pose_v1/src/timed_mixed_bridge.cpp':('software/pose_v1/src/application_bridge.cpp','application_bridge.cpp'),
      'software/pose_v1/include/forward_clock.hpp':('software/pose_v1/include/application_clock.hpp','application_clock.hpp'),
      'tools/pose-v1/runtime-CMakeLists.txt':('tools/pose-v1/application-CMakeLists.txt','CMakeLists.txt')}
    for previous,(rel,dest) in replacements.items():m['build_files'].pop(previous);m['build_files'][rel]=dict(destination=dest,sha256=sha(ROOT/rel))
    m['build_files']['software/pose_v1/include/lazy_runtime_validation.hpp']['destination']='lazy_runtime_validation.hpp'
    for rel in ['software/pose_v1/include/tcp_receiver.hpp','software/pose_v1/src/tcp_receiver.cpp','software/pose_v1/src/tcp_transport_check.cpp']:
        m['build_files'][rel]=dict(destination=Path(rel).name,sha256=sha(ROOT/rel))
    for rel in [*m['build_files'],'tools/pose-v1/Build-Application.ps1','tools/pose-v1/application_gate.py','tools/pose-v1/run-application.sh','tools/pose-v1/send_application_cases.py']:
        m['sources'][rel]=sha(ROOT/rel)
    m['parent_lazy_r4_manifest_sha256']=sha(parent/'manifest.json');m['stage']='production_interface_and_TCP_prepared_not_executed';m['binary_name']='pose_application_check'
    # Original board outputs, never ONNX-rematched outputs, are the network oracle.
    (a.package/'board-reference').mkdir()
    prior=ROOT/'tools/pose-v1/evidence/runtime-20261007-r2/n1/results'
    refs={}
    for i,c in enumerate(m['expanded_cases']):
        for suffix in ['scores','poses']:
            src=prior/f'call{i}.{suffix}.f32';dest=a.package/'board-reference'/(c['case']+'.'+suffix+'.f32');shutil.copyfile(src,dest);refs[dest.name]=sha(src)
    for c in m['cases']:
        for suffix in ['scores','poses']:
            src=a.package/'r6-reference'/(c['case']+'.'+suffix+'.f32');dest=a.package/'board-reference'/src.name
            if dest.exists():need(dest.read_bytes()==src.read_bytes(),'Base/N1 reference differs')
            else:shutil.copyfile(src,dest)
            refs[dest.name]=sha(src)
    m['board_reference_sha256']=refs
    for c in m['cases']+m['expanded_cases']:c['raw_sha256']=sha(a.package/'inputs'/(c['case']+'.csi'))
    shutil.copyfile(ROOT/'tools/pose-v1/run-application.sh',a.package/'run-application.sh')
    (a.package/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode());old.checksum(a.package)
    print('Prepared application package:',verify(a.package))

def build(a):
    verify(a.package);m=load(a.package/'manifest.json');b=load(a.build/'build-result.json')
    need(b['stage']=='compiled_not_executed' and not b['device_accessed'],'Build scope')
    need(b['package_manifest_sha256']==sha(a.package/'manifest.json'),'Package differs')
    need(b['build_script_sha256']==sha(ROOT/'tools/pose-v1/Build-Application.ps1'),'Builder changed')
    for rel,h in m['sources'].items():need(sha(ROOT/rel)==h,'Source changed: '+rel)
    for rel,v in m['build_files'].items():need(sha(a.build/'source'/v['destination'])==v['sha256']==b['source_sha256'][rel],'Build source differs')
    old.sdk(load(a.build/'sdk-audit.json'),m)
    for rel,h in m['sdk_headers_normalized_sha256'].items():need(hashlib.sha256((a.build/'sdk-snapshot'/rel).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h,'SDK header differs')
    for filename,key in [('libicraft_hostbackend.so','host_library_sha256'),('libicraft_zg330backend.so','zg_library_sha256')]:need(sha(a.build/'sdk-snapshot'/filename)==m[key],'SDK backend differs')
    for name,key in [('pose_application_check','binary_sha256'),('pose_transport_check','transport_binary_sha256')]:
        p=a.build/(name+'.arm64');raw=p.read_bytes();need(sha(p)==b[key] and raw[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',raw,18)[0]==183,'ARM program identity')
    raw=(a.build/'build.log').read_bytes();log=raw.decode('utf-16' if raw[:2] in [b'\xff\xfe',b'\xfe\xff'] else 'utf-8-sig')
    need('Built target pose_application_check' in log and 'Built target pose_transport_check' in log and '9.4.0' in log and 'cmake version 3.24.2' in log,'Build incomplete/toolchain changed')
    need('error:' not in log and 'RPATH' not in log and 'RUNPATH' not in log,'Build errors/runtime path')
    need('[libicraft_hostbackend.so]' in log and '[libicraft_zg330backend.so]' in log,'Direct backends absent')
    save(a.output,dict(status='application_build_reviewed',stage='build',binary_sha256=b['binary_sha256'],transport_binary_sha256=b['transport_binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],source_files=len(m['build_files'])))

def review(a):
    verify(a.package);count=verify(a.results);m=load(a.package/'manifest.json');b=load(a.build/'build-result.json');out=a.results/'results'
    for rel,h in m['sources'].items():need(sha(ROOT/rel)==h,'Source changed: '+rel)
    need((a.results/'exit.txt').read_text().strip()=='0' and (a.results/'run.stderr.log').stat().st_size==0 and not(out/'failure.json').exists(),'Stage failure; stop')
    need(sha(a.results/'pose_application_check')==b['binary_sha256'] and b['package_manifest_sha256']==sha(a.package/'manifest.json'),'Program/package differs')
    old.sdk(load(a.results/'sdk-audit.json'),m)
    previous={'host-check':'build','regression':'host-check','net-three':'regression','net-27':'net-three'}[a.stage]
    prev=load(a.results/'previous-acceptance.json');ident=load(a.results/'run-identity.json')
    need(prev['stage']==previous and prev['status']==('application_build_reviewed' if previous=='build' else 'application_stage_passed') and prev['binary_sha256']==b['binary_sha256'] and prev['package_manifest_sha256']==b['package_manifest_sha256'],'Previous stage identity')
    need(ident==dict(stage=a.stage,previous_stage=previous,binary_sha256=b['binary_sha256'],package_manifest_sha256=b['package_manifest_sha256']),'Run identity')
    need((a.results/'dmesg.before.log').read_bytes()==(a.results/'dmesg.after.log').read_bytes(),'Kernel changed, review before proceeding')
    need('not found' not in (a.results/'ldd.txt').read_text(),'Library unresolved')
    mode='serve' if a.stage.startswith('net-') else a.stage
    need(load(out/'run-config.json')==dict(mode=mode,device_init_allowed=a.stage!='host-check',content_capture=a.stage=='host-check',sdk_profiling=False),'Scope changed')
    report=dict(status='application_stage_passed',stage=a.stage,binary_sha256=b['binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],returned_files=count,video_initialized=False)
    if a.stage=='host-check':
        fixture=load(a.package/'cpu-fixture-manifest.json');rows=lines(out/'host/cases.jsonl');need(len(rows)==len(fixture['cases'])==107,'Host case count');old.registry(out/'host/registry.jsonl')
        floats=0
        for expected,got in zip(fixture['cases'],rows):
            need(all(got[k]==expected[k] for k in ['case_id','op_id','expected']) and got['passed'] and got['rejection']==('' if expected['expected']=='PASS' else expected['expected']),'Host rejection/identity')
            for i in range(expected['outputs']):
                raw=(out/'host'/expected['case_id']/f'output{i}.f32').read_bytes();need(raw==(a.package/'fixtures'/expected['case_id']/f'expected{i}.f32').read_bytes(),'Host math differs');floats+=len(raw)//4
        from host_content_review import review_host
        review_host(out);need(floats==59600,'Host output count');report.update(cases=107,FP32_values=floats,device_opened=False)
    else:
        old.registry(out/'registry.jsonl');old.fusion_binding_review(out,load(a.package/'mixed-fusion-baseline.json'))
        need(load(out/'device-version.json')['versions']==dict(device='25122301',icore='FMSHZGV3TECH-AID - 24160628'),'Device changed')
        params=lines(out/'host-parameters.jsonl');need(len(params)==4,'RAW parameter count')
        for p in params:
            name=f"op{p['op_id']}.param{p['input']}.f32";need(p['loaded_from_real_RAW'] and (out/name).read_bytes()==(old.ROOT/'tools/pose-v1/evidence/mixed-20261006-frame-state-r6/mixed-three/results'/name).read_bytes(),'RAW changed')
        cases=m['expanded_cases'] if a.stage=='net-27' else m['cases'];calls=[cases[j%3] for j in range(4) for _ in range(2)] if a.stage=='regression' else cases
        rows=lines(out/'results.jsonl');need(len(rows)==len(calls),'Forward count')
        for i,(row,case) in enumerate(zip(rows,calls)):
            need(row['frame_id']==case['frame_id'] and row['source_time_ns']==case['source_time_ns'] and row['call']==row['invocation']==i,'Frame mapping')
            need(row['frozen_reference_checked']==(a.stage=='regression' and i%2==0),'Production path required')
            need(row['before_clear']==(0 if i==0 else 745) and row['before_forward']==0 and row['completed_layers']==745 and row['host_callbacks']==row['zg_callbacks']==7,'Completion/callback protocol')
            need(all(np.isfinite(row[k]) and row[k]>=0 for k in ['process_ms','preprocess_ms','forward_ms','final_wait_ms','queue_ms','arrival_to_result_ms']),'Timing invalid')
            need((out/f'call{i}.input.f32').read_bytes()==(a.package/'reference'/(case['case']+'.input.f32')).read_bytes(),'PS input changed')
            for suffix,n in [('scores',100),('poses',4200)]:
                raw=(out/f'call{i}.{suffix}.f32').read_bytes();need(len(raw)==n*4 and np.isfinite(np.frombuffer(raw,dtype='<f4')).all(),'Output invalid')
                need(raw==(a.package/'board-reference'/(case['case']+'.'+suffix+'.f32')).read_bytes(),'Output differs from prior board')
            need(row['top_index']==int(np.argmax(np.fromfile(out/f'call{i}.scores.f32',dtype='<f4'))),'Selection changed')
        summary=load(out/'summary.json');need(summary['forward_calls']==len(calls) and summary['sdk_profiling'] is False and summary['video_initialized'] is False,'Summary scope')
        # Full callbacks for sampled frames only; execution coverage for every frame is checked in the core and rows.
        limit=8 if a.stage=='regression' else 4;executions=lines(out/'operator-execution.jsonl')
        need(len(executions)==14*min(len(calls),limit),'Bounded diagnostic coverage')
        for i in range(min(len(calls),limit)):
            ex=[v for v in executions if v['invocation']==i];need({v['op_id'] for v in ex}=={0,*old.HOST_IDS,*range(9185,9192)},'Sample callback coverage')
        spans=lines(out/'monotonic-spans.jsonl');need(len(spans)<=8192 and all(0<=s['begin_ns']<=s['end_ns'] and s['invocation']<limit for s in spans),'Bounded single clock evidence')
        if a.stage.startswith('net-'):
            network=load(out/'network.json');need(network==dict(sessions=1,received=len(calls),rejected=0,overwritten=0,reconnect_discarded=0,consumed=len(calls)),'Network loss/rejection')
            need(all(row['session']==1 and not row['frozen_reference_checked'] for row in rows),'Network used reference')
            report['arrival_to_result_ms']=dict(mean=float(np.mean([r['arrival_to_result_ms'] for r in rows])),p95=float(np.percentile([r['arrival_to_result_ms'] for r in rows],95)))
        report.update(calls=len(calls),outputs_bitwise_prior_board=True,production_requires_frozen_reference=False,telemetry_bounded=True)
    save(a.output,report);print('Reviewed application stage:',a.stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('prepare');q.add_argument('--package',type=Path,required=True);q.set_defaults(func=prepare)
    for cmd,fun in [('review-build',build),('review-stage',review)]:
        q=sub.add_parser(cmd)
        if cmd=='review-stage':q.add_argument('--stage',choices=['host-check','regression','net-three','net-27'],required=True)
        for k in ['package','build','output']:q.add_argument('--'+k,type=Path,required=True)
        if cmd=='review-stage':q.add_argument('--results',type=Path,required=True)
        q.set_defaults(func=fun)
    a=p.parse_args();a.func(a)

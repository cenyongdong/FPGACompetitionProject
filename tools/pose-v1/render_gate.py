"""Isolated E1-C review: frozen inference sources, CPU raster and real three-frame hook."""
import argparse,json,hashlib,struct,sys
from pathlib import Path
import numpy as np
import mixed_validation_gate as old
from review_skeleton_render import review as render_review
ROOT=old.ROOT;sha,load,save,need,verify,lines=old.sha,old.load,old.save,old.need,old.verify,old.lines
def freeze(a):
    m=load(a.package/'manifest.json')
    for rel in ['tools/pose-v1/run-render-validation.sh','tools/pose-v1/render_gate.py']:m['sources'][rel]=sha(ROOT/rel)
    import shutil
    shutil.copyfile(ROOT/'tools/pose-v1/run-render-validation.sh',a.package/'run-render-validation.sh')
    (a.package/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode());old.checksum(a.package);print('Render package frozen:',verify(a.package))
def build(a):
    verify(a.package);m=load(a.package/'manifest.json');b=load(a.build/'build-result.json')
    need(b['package_manifest_sha256']==sha(a.package/'manifest.json') and b['stage']=='compiled_not_executed' and not b['device_accessed'],'Build scope/identity')
    need(b['build_script_sha256']==sha(ROOT/'tools/pose-v1/Build-Render.ps1'),'Builder identity')
    for rel,h in m['sources'].items():need(sha(ROOT/rel)==h,'Source changed: '+rel)
    for rel,v in m['build_files'].items():need(sha(a.build/'source'/v['destination'])==v['sha256']==b['source_sha256'][rel],'Copied source differs')
    old.sdk(load(a.build/'sdk-audit.json'),m)
    for rel,h in m['sdk_headers_normalized_sha256'].items():need(hashlib.sha256((a.build/'sdk-snapshot'/rel).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h,'SDK header')
    for name,key in [('libicraft_hostbackend.so','host_library_sha256'),('libicraft_zg330backend.so','zg_library_sha256')]:need(sha(a.build/'sdk-snapshot'/name)==m[key],'SDK backend')
    for name,key in [('pose_application_render_check','binary_sha256'),('pose_skeleton_render_check','renderer_binary_sha256'),('pose_video_capability_probe','video_probe_sha256')]:
        p=a.build/(name+'.arm64');raw=p.read_bytes();need(sha(p)==b[key] and raw[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',raw,18)[0]==183,'ARM ELF identity')
    raw=(a.build/'build.log').read_bytes();log=raw.decode('utf-16' if raw[:2] in [b'\xff\xfe',b'\xfe\xff'] else 'utf-8-sig')
    need(all('Built target '+s in log for s in ['pose_application_render_check','pose_skeleton_render_check','pose_video_capability_probe']) and 'error:' not in log,'Compile failure')
    need('9.4.0' in log and 'cmake version 3.24.2' in log and 'RPATH' not in log and 'RUNPATH' not in log,'Toolchain/runtime path')
    save(a.output,dict(status='render_build_reviewed',stage='build',binary_sha256=b['binary_sha256'],renderer_binary_sha256=b['renderer_binary_sha256'],video_probe_sha256=b['video_probe_sha256'],package_manifest_sha256=b['package_manifest_sha256'],sources=len(m['build_files'])))
def stage(a):
    count=verify(a.results);verify(a.package);m=load(a.package/'manifest.json');b=load(a.build/'build-result.json')
    need((a.results/'exit.txt').read_text().strip()=='0' and (a.results/'run.stderr.log').stat().st_size==0,'Render stage failure')
    need(sha(a.results/'pose_application_render_check')==b['binary_sha256'],'Returned program')
    old.sdk(load(a.results/'sdk-audit.json'),m)
    for rel,h in m['sources'].items():need(sha(ROOT/rel)==h,'Source changed')
    previous={'cpu-render':'build','host-check':'cpu-render','net-render-three':'host-check'}[a.stage];prev=load(a.results/'previous-acceptance.json')
    need(prev['stage']==previous and prev['status']==('render_build_reviewed' if previous=='build' else 'render_stage_passed') and prev['binary_sha256']==b['binary_sha256'] and prev['package_manifest_sha256']==b['package_manifest_sha256'],'Prior gate')
    need(load(a.results/'run-identity.json')==dict(stage=a.stage,previous_stage=previous,binary_sha256=b['binary_sha256'],package_manifest_sha256=b['package_manifest_sha256']),'Run identity')
    need((a.results/'dmesg.before.log').read_bytes()==(a.results/'dmesg.after.log').read_bytes(),'Kernel change requires review')
    report=dict(status='render_stage_passed',stage=a.stage,binary_sha256=b['binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],returned_files=count,HDMI_VPU_streamed=False)
    if a.stage=='cpu-render':
        need(sha(a.results/'pose_skeleton_render_check')==b['renderer_binary_sha256'],'CPU renderer binary')
        self_test=render_review(a.results/'self-test',None,None);frames=render_review(a.results/'frames',a.package/'render-input',a.package/'render-cases.tsv')
        native=ROOT/'.local/pose-v1-render/native-20261007-r1/frames'
        for row in frames['frames']:
            for suffix in ['.ppm','.rgb565le','.nv12','.nv21']:need((a.results/'frames'/(row['stem']+suffix)).read_bytes()==(native/(row['stem']+suffix)).read_bytes(),'ARM/native raster differs')
        report.update(device_opened=False,self_test=self_test,render=frames,ARM_native_all_rasters_bitwise=True)
    elif a.stage=='host-check':
        out=a.results/'results';rows=lines(out/'host/cases.jsonl');fixture=load(a.package/'cpu-fixture-manifest.json');need(len(rows)==len(fixture['cases'])==107,'Host case count');old.registry(out/'host/registry.jsonl')
        total=0
        for expected,got in zip(fixture['cases'],rows):
            need(all(expected[k]==got[k] for k in ['case_id','op_id','expected']) and got['passed'] and got['rejection']==('' if expected['expected']=='PASS' else expected['expected']),'Host case identity/rejection')
            for i in range(expected['outputs']):
                raw=(out/'host'/expected['case_id']/f'output{i}.f32').read_bytes();need(raw==(a.package/'fixtures'/expected['case_id']/f'expected{i}.f32').read_bytes(),'Host numeric mismatch');total+=len(raw)//4
        from host_content_review import review_host
        review_host(out);need(total==59600,'Output count');report.update(cases=107,FP32_values=total,device_opened=False)
    else:
        out=a.results/'results';need(not(out/'failure.json').exists(),'Network/render failed');old.registry(out/'registry.jsonl');old.fusion_binding_review(out,load(a.package/'mixed-fusion-baseline.json'))
        need(load(out/'device-version.json')['versions']==dict(device='25122301',icore='FMSHZGV3TECH-AID - 24160628'),'Device identity')
        rows=lines(out/'results.jsonl');need(len(rows)==3,'Call count')
        cat=a.results/'review-render-cases.tsv'
        # Keep generated review catalog outside returned-checksum root.
        cat=a.output.parent/(a.stage+'.review-cases.tsv');need(not cat.exists(),'Preserve review catalog')
        cat.write_bytes(''.join(f"call{i}\t{c['frame_id']}\n" for i,c in enumerate(m['cases'])).encode())
        for i,(row,c) in enumerate(zip(rows,m['cases'])):
            need(row['frame_id']==c['frame_id'] and row['invocation']==i and not row['frozen_reference_checked'],'Production identity')
            need(row['before_forward']==0 and row['completed_layers']==745 and row['host_callbacks']==row['zg_callbacks']==7,'Frame protocol')
            need((out/f'call{i}.input.f32').read_bytes()==(a.package/'reference'/(c['case']+'.input.f32')).read_bytes(),'Input differs')
            for suffix in ['scores','poses']:need((out/f'call{i}.{suffix}.f32').read_bytes()==(a.package/'board-reference'/(c['case']+'.'+suffix+'.f32')).read_bytes(),'Model output changed')
        network=load(out/'network.json');need(network==dict(sessions=1,received=3,rejected=0,overwritten=0,reconnect_discarded=0,consumed=3),'Network loss')
        rr=render_review(out,out,cat);report.update(calls=3,outputs_bitwise_prior=True,render=rr,device_opened=True)
        params=lines(out/'host-parameters.jsonl');need(len(params)==4 and all(p['loaded_from_real_RAW'] for p in params),'Real parameters')
    save(a.output,report);print('Reviewed renderer stage:',a.stage)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('freeze');q.add_argument('--package',type=Path,required=True);q.set_defaults(func=freeze)
    for cmd,fn in [('review-build',build),('review-stage',stage)]:
        q=sub.add_parser(cmd)
        for k in ['package','build','output']:q.add_argument('--'+k,type=Path,required=True)
        if cmd=='review-stage':q.add_argument('--stage',choices=['cpu-render','host-check','net-render-three'],required=True);q.add_argument('--results',type=Path,required=True)
        q.set_defaults(func=fn)
    a=p.parse_args();a.func(a)

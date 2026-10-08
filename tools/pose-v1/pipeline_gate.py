"""Independent identity/Host and real finite pipeline review; never runs hardware."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
import mixed_validation_gate as old
ROOT=old.ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def save(p,obj):assert not p.exists();p.write_bytes((json.dumps(obj,indent=2)+'\n').encode())

def identities(package,build,target='pose_pipeline_encode_check',builder='tools/pose-v1/Build-Pipeline.ps1'):
    assert (target,builder) in [('pose_pipeline_encode_check','tools/pose-v1/Build-Pipeline.ps1'),('pose_resident_check','tools/pose-v1/Build-Resident.ps1')]
    count=old.verify(package);m=load(package/'manifest.json');b=load(build/'build-result.json')
    assert b['stage']=='compiled_not_executed' and not b['device_accessed']
    assert b['package_manifest_sha256']==sha(package/'manifest.json')
    assert b['build_script_sha256']==sha(ROOT/builder)
    for rel,h in m['sources'].items():assert sha(ROOT/rel)==h
    for rel,item in m['build_files'].items():assert sha(ROOT/rel)==sha(build/'source'/item['destination'])==item['sha256']==b['source_sha256'][rel]
    assert sha(ROOT/'software/pose_v1/src/vpu_encoder.cpp')==m['frozen_vpu_r5_sha256']
    old.sdk(load(build/'sdk-audit.json'),m)
    for rel,h in m['sdk_headers_normalized_sha256'].items():assert hashlib.sha256((build/'sdk-snapshot'/rel).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h
    for name,key in [('libicraft_hostbackend.so','host_library_sha256'),('libicraft_zg330backend.so','zg_library_sha256')]:assert sha(build/'sdk-snapshot'/name)==m[key]
    blob=(build/(target+'.arm64')).read_bytes()
    assert sha(build/(target+'.arm64'))==b['binary_sha256'] and blob[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',blob,18)[0]==183
    raw=(build/'build.log').read_bytes();log=raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
    assert 'Built target '+target in log and 'error:' not in log and '9.4.0' in log and 'cmake version 3.24.2' in log
    assert 'RPATH' not in log and 'RUNPATH' not in log
    warnings=[x for x in log.splitlines() if 'warning:' in x]
    assert len(warnings)==3 and all('lazy_runtime_validation.hpp:123:' in x or 'host_cpu_adapter.cpp:18:' in x for x in warnings)
    return m,b,count

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','host-check','combined']);p.add_argument('--package',type=Path,required=True)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    m,b,count=identities(a.package,a.build)
    report=dict(status='pipeline_build_reviewed' if a.mode=='build' else 'pipeline_stage_passed',stage=a.mode,binary_sha256=b['binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],package_payloads=count,build_sources=len(m['build_files']),sdk_headers=len(m['sdk_headers_normalized_sha256']))
    if a.mode=='build':save(a.output,report);print('F0 build identities reviewed');return
    r=a.results;report['returned_hashed_files']=old.verify(r)
    assert sha(r/'pose_pipeline_encode_check')==b['binary_sha256']
    assert (r/'exit.txt').read_text().strip()=='0' and not (r/'stderr.log').read_bytes()
    assert (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
    identity=load(r/'preflight.json');reference=load(ROOT/'tools/pose-v1/evidence/video-descriptor-20261007-r5/encode/preflight.json')
    assert identity['boot_files']==reference['boot_files'] and identity['libraries']==reference['libraries'] and identity['SDK_packages']==reference['SDK_packages']
    prev=load(r/'previous-acceptance.json');assert prev['stage']==('build' if a.mode=='host-check' else 'host-check') and prev['binary_sha256']==b['binary_sha256'] and prev['package_manifest_sha256']==b['package_manifest_sha256']
    out=r/'results';assert load(out/'contracts.json')==dict(status='passed',frame_rejections=5,missing_callbacks_rejected_before_device=True,packet_owned_after_capture_reuse=True)
    if a.mode=='host-check':
        expected=load(a.package/'cpu-fixture-manifest.json')['cases'];got=rows(out/'host/cases.jsonl');assert len(expected)==len(got)==107
        old.registry(out/'host/registry.jsonl');total=0
        for e,g in zip(expected,got):
            assert all(e[k]==g[k] for k in ('case_id','op_id','expected')) and g['passed']
            assert g['rejection']==('' if e['expected']=='PASS' else e['expected'])
            for i in range(e['outputs']):
                raw=(out/'host'/e['case_id']/f'output{i}.f32').read_bytes();assert raw==(a.package/'fixtures'/e['case_id']/f'expected{i}.f32').read_bytes()
                assert np.isfinite(np.frombuffer(raw,dtype='<f4')).all();total+=len(raw)//4
        assert total==59600
        assert load(out/'summary.json')==dict(stage='host-check',cases=107,device_opened=False,VPU_streamed=False)
        report.update(Host_cases=107,CPU_output_values=total,registry_records=12,contract_negative_cases=6,device_opened=False,VPU_streamed=False)
    else:
        expected=m['fixed_cases'];records=rows(out/'inference.jsonl');assert len(records)==8
        for i,row in enumerate(records):
            name=expected[i%4];stem=('regression' if i<4 else 'production')+str(i%4)
            assert row['case']==name and row['stem']==stem and row['invocation']==i
            assert row['before_clear']==(0 if i==0 else 745) and row['before_forward']==0 and row['completed_layers']==745
            assert row['host_callbacks']==row['zg_callbacks']==7 and row['checked_reference']==(i<4)
            for suffix,folder,ref_suffix in [('input','reference','input'),('scores','r6-reference','scores'),('poses','r6-reference','poses')]:
                raw=(out/f'{stem}.{suffix}.f32').read_bytes();assert raw==(a.package/folder/f'{name}.{ref_suffix}.f32').read_bytes()
                assert np.isfinite(np.frombuffer(raw,dtype='<f4')).all()
        baseline=ROOT/'tools/pose-v1/mixed-fusion-baseline.json'
        assert sha(baseline)==sha(ROOT/'.local/pose-v1-render/package-20261007-r1/mixed-fusion-baseline.json')
        old.registry(out/'engine/registry.jsonl');old.fusion_binding_review(out/'engine',load(baseline))
        events=rows(out/'encoder/events.jsonl');final=events[-1]
        assert final['event']=='encoding_complete' and final['queued']==final['returned']==10 and final['last']
        assert final['npu_owned_by_caller'] and not final['hdmi']
        enters=[x for x in events if x['event']=='producer_enter'];assert len(enters)==10
        assert [x['VPU_streaming'] for x in enters]==[False]*2+[True]*8
        durations=[x for x in events if x['event']=='producer_duration'];assert [x['frame'] for x in durations]==list(range(10))
        assert all(0<=x['nanoseconds']<60000000000 for x in durations)
        assert sum(x['nanoseconds'] for x in durations[2:])==final['producer_paused_ns']
        expected_buffers=m.get('requested_queue_buffers',6)
        assert expected_buffers in (2,6)
        assert next(x for x in events if x['event']=='input_prime_policy')==dict(event='input_prime_policy',allocated_buffers=expected_buffers,prime_count=2)
        if expected_buffers==2:
            mapped=[x for x in events if x['event']=='mapped_total']
            assert mapped==[dict(event='mapped_total',type=10,bytes=2764800,buffers=2),dict(event='mapped_total',type=9,bytes=4194304,buffers=2)]
            report['requested_and_returned_queue_buffers']=2
        lifecycle=rows(out/'lifecycle.jsonl');assert [x['event'] for x in lifecycle]==['VPU_capture_before_Engine','Engine_created']
        assert lifecycle[0]['packet_count']>0 and lifecycle[0]['time_ns']<lifecycle[1]['time_ns']
        source=[x for x in events if x['event']=='source_frame'];assert len(source)==10
        for i,row in enumerate(source):
            assert row['encoded_id']==i and row['repeated_source']==bool(i%2)
            if i<2:assert row['source_frame_id']==0 and not row['inference_result']
            else:assert row['source_frame_id']==(6,7,8,6)[(i-2)//2] and row['invocation']==4+(i-2)//2 and row['inference_result']
        assert all(x['equal'] for x in events if x['event']=='host_copy_check')
        packets=rows(out/'packets.jsonl');capture=[x for x in events if x['event']=='capture'];assert len(packets)==len(capture)
        copied=b''
        for i,(row,cap) in enumerate(zip(packets,capture)):
            raw=(out/f'packet{i}.h264').read_bytes();assert row['packet']==i and len(raw)==row['bytes']==cap['bytes'] and row['pts_us']==cap['pts_us'] and row['flags']==cap['flags']
            copied+=raw
        assert copied==(out/'encoder/video.h264').read_bytes() and len(copied)==final['bytes']
        raw=(out/'encoder/submitted.nv12').read_bytes();assert len(raw)==10*1280*720*3//2
        frames=rows(out/'frames.jsonl');assert len(frames)==4
        from review_skeleton_render import ppm
        # Verify the explicitly non-inference startup pixels separately.
        warmrgb=ppm(out/'frames/warmup.ppm')
        ar,ag,ab=np.moveaxis(warmrgb.astype(np.int32),-1,0)
        warmY=((66*ar+129*ag+25*ab+128)//256+16).clip(0,255).astype(np.uint8)
        avg=(warmrgb.astype(np.int32).reshape(360,2,640,2,3).sum(axis=(1,3))+2)//4;ar,ag,ab=np.moveaxis(avg,-1,0)
        warmU=((-38*ar-74*ag+112*ab+128)//256+128).clip(0,255).astype(np.uint8);warmV=((112*ar-94*ag-18*ab+128)//256+128).clip(0,255).astype(np.uint8)
        for i in (0,1):
            wy=warmY.copy();wuv=np.stack((warmU,warmV),axis=-1).reshape(360,1280)
            wuv[300:340,40:1240]=128;wy[600:680,40:1240]=16
            for bit in range(6):wy[600:632,40+bit*64:88+bit*64]=235 if i&(1<<bit) else 16
            wy[640:680,40+i*21:64+i*21]=235
            assert raw[i*1382400:(i+1)*1382400]==wy.tobytes()+wuv.tobytes()
        for source_id,frame in enumerate(frames):
            assert frame['source_index']==source_id and frame['frame_id']==(6,7,8,6)[source_id]
            points=np.fromfile(out/f'production{source_id}.poses.f32',dtype='<f4').reshape(100,14,3)[frame['top_index']].astype(np.float64)
            x,y,z=(points-np.array([1.75,1.75,3.4])).T;z=-z
            cy,sy=np.cos(np.pi/6),np.sin(np.pi/6);ce,se=np.cos(np.pi/9),np.sin(np.pi/9)
            projected=np.stack((460+220*(cy*x-sy*y),355-220*(ce*z-se*(sy*x+cy*y))),axis=-1)
            assert np.allclose(projected,frame['projected'],rtol=1e-14,atol=1e-9)
            rgb=ppm(out/'frames'/f'source{source_id}.ppm');r0,g0,b0=np.moveaxis(rgb.astype(np.int32),-1,0)
            Y=((66*r0+129*g0+25*b0+128)//256+16).clip(0,255).astype(np.uint8)
            mean=(rgb.astype(np.int32).reshape(360,2,640,2,3).sum(axis=(1,3))+2)//4;r0,g0,b0=np.moveaxis(mean,-1,0)
            U=((-38*r0-74*g0+112*b0+128)//256+128).clip(0,255).astype(np.uint8);V=((112*r0-94*g0-18*b0+128)//256+128).clip(0,255).astype(np.uint8)
            for i in (2+source_id*2,3+source_id*2):
                yb=Y.copy();uv=np.stack((U,V),axis=-1).reshape(360,1280);uv[300:340,40:1240]=128;yb[600:680,40:1240]=16
                for bit in range(6):yb[600:632,40+bit*64:88+bit*64]=235 if i&(1<<bit) else 16
                yb[640:680,40+i*21:64+i*21]=235
                assert raw[i*1382400:(i+1)*1382400]==yb.tobytes()+uv.tobytes()
        assert (out/'frames/source0.ppm').read_bytes()==(out/'frames/source3.ppm').read_bytes()
        assert len({(out/'frames'/f'source{i}.ppm').read_bytes() for i in range(3)})==3
        assert load(out/'summary.json')==dict(stage='combined',regression_forward_calls=4,production_forward_calls=4,encoded_frames=10,warmup_frames=2,device_opened=True,VPU_streamed=True,RTSP_initialized=False,HDMI_initialized=False,realtime_throughput_verified=False)
        report.update(full_forward_calls=8,production_new_results=4,encoded_frames=10,warmup_frames=2,VPU_capture_before_Engine=True,producer_after_VPU_streamon=True,owned_capture_matches_stream=True,NV12_bitwise_numpy=True,kernel_unchanged=True,throughput_verified=False)
    report.update(exit=0,stderr_empty=True,BOOT_SDK_preserved=True)
    save(a.output,report);print(json.dumps(report,indent=2))

if __name__=='__main__':main()

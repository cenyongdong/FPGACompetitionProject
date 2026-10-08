"""Strict identity, CPU regression and real-capture lifecycle review; no hardware calls."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
import mixed_validation_gate as old

ROOT=old.ROOT
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(line) for line in p.read_text().splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identities(package,build):
    count=old.verify(package);m=load(package/'manifest.json');b=load(build/'build-result.json')
    assert b['stage']=='compiled_not_executed' and not b['device_accessed'] and b['package_manifest_sha256']==sha(package/'manifest.json')
    builder=m.get('build_script','tools/pose-v1/Build-LivePipeline.ps1')
    assert builder in ('tools/pose-v1/Build-LivePipeline.ps1','tools/pose-v1/Build-GuardedLive.ps1','tools/pose-v1/Build-TcpLive.ps1','tools/pose-v1/Build-TcpEvidence.ps1','tools/pose-v1/Build-TcpPresaved.ps1')
    assert b['build_script_sha256']==sha(ROOT/builder)
    if m.get('guarded_network'):
        expected_builder='tools/pose-v1/Build-TcpPresaved.ps1' if m.get('presave_all_results') else ('tools/pose-v1/Build-TcpEvidence.ps1' if m.get('failed_output_capture') else ('tools/pose-v1/Build-TcpLive.ps1' if m.get('tcp_window_input') else 'tools/pose-v1/Build-GuardedLive.ps1'))
        assert builder==expected_builder
        baseline=load(ROOT/'.local/pose-v1-build/guarded-normal-20261008-r1/build-result.json')
        for rel in ('software/pose_v1/include/guarded_rtsp.hpp','software/pose_v1/src/guarded_rtsp.cpp'):
            assert m['build_files'][rel]['sha256']==baseline['sources'][rel]
        assert 'software/pose_v1/src/online_rtsp.cpp' not in m['build_files']
        for rel,digest in m['frozen_live_sources'].items():assert sha(ROOT/rel)==digest
    for rel,digest in m['sources'].items():assert sha(ROOT/rel)==digest
    for rel,item in m['build_files'].items():assert sha(ROOT/rel)==sha(build/'source'/item['destination'])==item['sha256']==b['source_sha256'][rel]
    assert load(build/'vendor-files.json')==m['vendor_files']
    assert sha(ROOT/'software/pose_v1/src/vpu_encoder.cpp')==m['frozen_vpu_r5_sha256']
    for rel,digest in m['frozen_resident_module_sources'].items():assert sha(ROOT/rel)==digest
    old.sdk(load(build/'sdk-audit.json'),m)
    for rel,digest in m['sdk_headers_normalized_sha256'].items():assert hashlib.sha256((build/'sdk-snapshot'/rel).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest
    for name,key in [('libicraft_hostbackend.so','host_library_sha256'),('libicraft_zg330backend.so','zg_library_sha256')]:assert sha(build/'sdk-snapshot'/name)==m[key]
    for name,key in [('pose_live_pipeline_check.arm64','binary_sha256'),('pose_access_unit_selftest','au_selftest_sha256')]:
        blob=(build/name).read_bytes();assert sha(build/name)==b[key] and blob[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',blob,18)[0]==183
    if m.get('tcp_window_input'):
        blob=(build/'pose_tcp_transport_check').read_bytes();assert sha(build/'pose_tcp_transport_check')==b['tcp_selftest_sha256'] and blob[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',blob,18)[0]==183
    if m.get('failed_output_capture'):
        blob=(build/'pose_failed_result_selftest').read_bytes();assert sha(build/'pose_failed_result_selftest')==b['failed_selftest_sha256'] and blob[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',blob,18)[0]==183
    log=(build/'build.log').read_text(encoding='utf-8-sig')
    assert 'Built target pose_live_pipeline_check' in log and 'Built target pose_access_unit_selftest' in log and 'error:' not in log
    assert 'RPATH' not in log and 'RUNPATH' not in log and '9.4.0' in log and 'cmake version 3.24.2' in log
    warnings=[line for line in log.splitlines() if 'warning:' in line]
    assert len(warnings)==3 and all('lazy_runtime_validation.hpp:123:' in line or 'host_cpu_adapter.cpp:18:' in line for line in warnings)
    return m,b,count

def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['build','host-check','live-three','live-27']);p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();m,b,count=identities(a.package,a.build)
    report=dict(status='live_build_reviewed' if a.stage=='build' else 'live_stage_passed',stage=a.stage,binary_sha256=b['binary_sha256'],package_manifest_sha256=sha(a.package/'manifest.json'),package_payloads=count,build_sources=len(m['build_files']),sdk_headers=len(m['sdk_headers_normalized_sha256']),vendor_files=len(m['vendor_files']))
    if a.stage!='build':
        r=a.results;report['returned_hashed_files']=old.verify(r)
        runner_names=('run-tcp-evidence.sh',) if m.get('failed_output_capture') else (('run-tcp-live.sh',) if m.get('tcp_window_input') else ('run-live-stage.sh','run-live-coordinated.sh'))
        executed=sha(r/'executed-runner.sh');allowed={sha(ROOT/'tools/pose-v1'/name) for name in runner_names}
        assert executed in allowed;report['executed_runner_sha256']=executed
        assert sha(r/'pose_live_pipeline_check')==b['binary_sha256'] and (r/'exit.txt').read_text().strip()=='0'
        assert (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
        baseline=load(ROOT/'tools/pose-v1/evidence/resident-20261008-r6/resident-three/preflight.json');preflight=load(r/'preflight.json')
        assert all(preflight[k]==baseline[k] for k in ('boot_files','libraries','SDK_packages','fpga_state'))
        identity=load(r/'run-identity.json');assert identity['program_sha256']==b['binary_sha256'] and identity['package_manifest_sha256']==report['package_manifest_sha256']
        previous=load(r/'previous-acceptance.json');assert previous['stage']=={'host-check':'build','live-three':'host-check','live-27':'live-three'}[a.stage]
        assert previous['binary_sha256']==b['binary_sha256'] and previous['package_manifest_sha256']==report['package_manifest_sha256']
        out=r/'results'
        if a.stage=='host-check':
            assert not (r/'stderr.log').read_bytes() and not (r/'AU.stderr.log').read_bytes() and (r/'AU.exit.txt').read_text().strip()=='0'
            assert sha(r/'pose_access_unit_selftest')==b['au_selftest_sha256']
            assert load(r/'AU.stdout.log')==dict(status='passed',rejections=17,threaded_units=2000,capacity=8,no_device=True)
            records=rows(out/'host/cases.jsonl');expected=load(a.package/'cpu-fixture-manifest.json')['cases'];assert len(records)==len(expected)==107
            old.registry(out/'host/registry.jsonl');total=0
            for actual,wanted in zip(records,expected):
                assert actual['passed'] and all(actual[k]==wanted[k] for k in ('case_id','op_id','expected'))
                assert actual['rejection']==('' if wanted['expected']=='PASS' else wanted['expected'])
                for i in range(wanted['outputs']):
                    data=(out/'host'/wanted['case_id']/f'output{i}.f32').read_bytes();assert data==(a.package/'fixtures'/wanted['case_id']/f'expected{i}.f32').read_bytes()
                    assert np.isfinite(np.frombuffer(data,dtype='<f4')).all();total+=len(data)//4
            assert total==59600
            assert load(out/'queue-contracts.json')==dict(capacity=2,overwrite_oldest=True,popLatest=True,immutable_bytes=True,stop_refused=True)
            if m.get('tcp_window_input'):
                assert sha(r/'pose_tcp_transport_check')==b['tcp_selftest_sha256'] and not (r/'TCP.stderr.log').read_bytes() and (r/'TCP.exit.txt').read_text().strip()=='0'
                assert load(r/'TCP.stdout.log')==dict(self_test='passed',malformed_cases=7,raw_bits=True,bounded_slot=True,loopback_fragmented=True,partial_disconnect=True,duplicate_rejected=True,idle_timeout=True)
                report.update(TCP_protocol_selftest=True)
            if m.get('failed_output_capture'):
                assert sha(r/'pose_failed_result_selftest')==b['failed_selftest_sha256'] and not (r/'failure-contracts.stderr.log').read_bytes() and (r/'failure-contracts.exit.txt').read_text().strip()=='0'
                contract=dict(status='passed',positive=1,failure_preserved=2,original_exception=True,SDK_device=False)
                if m.get('presave_all_results'):contract['all_presaved']=3
                assert load(r/'failure-contracts.stdout.log')==contract
                for i in (1,2):
                    folder='presaved-results/0' if m.get('presave_all_results') else 'failed-result'
                    rejected=r/f'failure-contracts/{i}'/folder;scores=np.fromfile(rejected/'scores.f32',dtype='<f4');poses=np.fromfile(rejected/'poses.f32',dtype='<f4')
                    assert len(scores)==100 and len(poses)==4200 and poses[2]==-.5 and np.count_nonzero(poses)==1
                    assert (scores[0]==.125 if i==1 else np.isnan(scores[0])) and np.count_nonzero(scores[1:])==0
                    assert load(rejected/'identity.json')['scores']['finite']==(i==1)
                report.update(failure_capture_contracts=True)
            report.update(Host_cases=107,registry_records=12,CPU_output_values=total,AU_rejections=17,AU_threaded_units=2000,device_opened=False)
        else:
            stderr=(r/'stderr.log').read_text();assert len(stderr.splitlines())>=1 and all('CJN-Trace>>' in line and 'maxRTCPPacketSize' in line for line in stderr.splitlines())
            calls=rows(out/'inference.jsonl');n=4 if a.stage=='live-three' else 28;assert len(calls)==n
            old.registry(out/'engine/registry.jsonl');old.fusion_binding_review(out/'engine',load(ROOT/'tools/pose-v1/mixed-fusion-baseline.json'))
            for i,record in enumerate(calls):
                assert record['call']==record['invocation']==i and record['before_forward']==0 and record['completed_layers']==745 and record['host_callbacks']==record['zg_callbacks']==7
                for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:
                    data=(out/f'result{i}.{suffix}.f32').read_bytes();assert data==(a.package/folder/f"{record['case']}.{suffix}.f32").read_bytes() and np.isfinite(np.frombuffer(data,dtype='<f4')).all()
                    if m.get('presave_all_results'):assert data==(out/f'presaved-results/{i}/{suffix}.f32').read_bytes()
                if m.get('presave_all_results'):
                    assert load(out/f'presaved-results/{i}/identity.json')['saved_before_gate']
                    assert (out/f'presaved-results/{i}/raw-payload.bin').read_bytes()==(a.package/'inputs'/f"{record['case']}.csi").read_bytes()[32:]
            assert calls[0]['case']==calls[-1]['case'] and (out/'frames/result0.nv12').read_bytes()==(out/'frames'/f'result{n-1}.nv12').read_bytes()
            if m.get('tcp_window_input'):
                ingress=rows(out/'tcp-input/received.jsonl');assert len(ingress)==n
                for i,record in enumerate(ingress):
                    assert record['call']==record['sequence']==i and record['session']==(2 if i==n-1 else 1) and record['frame_id']==calls[i]['frame_id']
                    assert record['source_time_ns']==0
                assert load(out/'tcp-input/summary.json')==dict(sessions=2,received=n,consumed=n,rejected=0,overwritten=0,reconnect_discarded=0)
                report.update(TCP_complete_windows=n,TCP_capacity=1,TCP_session_repeat=True,TCP_lost_or_rejected=0)
            samples=rows(out/'samples.jsonl');events=rows(out/'encoder/events.jsonl');clocks=[e for e in events if e['event']=='sample_clock']
            aus=rows(out/'access-units.jsonl');net=rows(out/'network/events.jsonl');received=[e for e in net if e['event']=='au_received']
            assert len(samples)==len(clocks)==len(aus)==len(received) and 2<=len(samples)<1000
            assert [s['encoded_id'] for s in samples]==list(range(len(samples)))
            assert all(x['sample_ns']<y['sample_ns'] for x,y in zip(samples,samples[1:])) and all(x['pts_us']<y['pts_us'] for x,y in zip(aus,aus[1:]))
            epoch=[s['sample_ns']-c['pts_us']*1000 for s,c in zip(samples,clocks)];assert max(epoch)-min(epoch)<1000
            assert all(s['generated_ns']<=s['sample_ns'] for s in samples)
            assert {s['invocation'] for s in samples if s['inference_result']}==set(range(n))
            for s in samples:
                if s['inference_result']:assert s['source_frame_id']==calls[s['invocation']]['frame_id']
            assert all(all(x[k]==y[k] for k in ('encoded_id','pts_us','idr')) for x,y in zip(aus,received))
            assert all(x['pts_us']==y['pts_us'] for x,y in zip(aus,clocks))
            assert [e['buffers'] for e in events if e['event']=='mapped_total']==[2,2] and all(e['equal'] for e in events if e['event']=='host_copy_check')
            final=events[-1];assert final['event']=='encoding_complete' and final['queued']==final['returned']==len(samples) and final['last']
            q=load(out/'queue-stats.json');assert q['published']==q['consumed']==n and q['overwritten']==q['coalesced']==0 and q['high_water']<=2 and q['AU_high_water']<=8
            life=rows(out/'lifecycle.jsonl');assert [e['event'] for e in life]==['Engine_created','workers_joined','Engine_destroyed']
            assert life[0]['time_ns']<samples[-1]['sample_ns']<life[1]['time_ns']<=life[2]['time_ns'] and life[0]['init_ms']<60000
            assert 19000000000<=samples[-1]['sample_ns']-life[0]['time_ns']<21000000000
            assert net[-1]['event']=='completed' and not net[-1]['failed'] and net[-1]['sources_live']==0 and net[-1]['pictures']==len(samples)
            if m.get('guarded_network'):
                bounds=[e for e in net if e['event']=='TCP_buffer_bound']
                assert len(bounds)==1 and bounds[0]['requested']==65536 and bounds[0]['actual']==131072
                assert not any(e['event']=='rtp_send_error' for e in net)
                report.update(guarded_network_integrated=True,TCP_send_buffer_actual=131072,send_errors=0)
            summary=load(out/'summary.json');assert summary['forward_calls']==n and summary['encoded_frames']==summary['access_units']==len(samples)
            assert summary['RTSP'] and not summary['HDMI'] and summary['Engine_alive_until_workers_joined'] and not summary['sdk_profiling']
            report.update(full_correct_forwards=n,encoded_frames=len(samples),real_capture_AU_bridge=True,actual_clock_PTS=True,Engine_main_owner_alive_until_workers_joined=True,AU_high_water=q['AU_high_water'])
        report.update(exit=0,kernel_unchanged=True)
    a.output.write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(report,indent=2))
if __name__=='__main__':main()

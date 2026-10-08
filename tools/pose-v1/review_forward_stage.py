"""Independent source/identity, full numeric and single-clock review. No hardware calls."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
import mixed_validation_gate as old

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(values):
    v=np.asarray(values,dtype=np.float64);assert len(v) and np.isfinite(v).all() and (v>=0).all()
    return dict(count=len(v),mean=float(v.mean()),P95=float(np.percentile(v,95)),maximum=float(v.max()))

def identities(package,build):
    n=old.verify(package);m=load(package/'manifest.json');b=load(build/'build-result.json');root=old.ROOT
    assert b['stage']=='compiled_not_executed' and not b['device_accessed']
    assert b['package_manifest_sha256']==sha(package/'manifest.json') and b['build_script_sha256']==sha(root/m['build_script'])
    assert m['build_script']=='tools/pose-v1/Build-ForwardTrace.ps1'
    for rel,digest in m['sources'].items():assert sha(root/rel)==digest
    for rel,item in m['build_files'].items():assert sha(root/rel)==sha(build/'source'/item['destination'])==b['source_sha256'][rel]==item['sha256']
    for key in ('timing_frozen_parent','display_frozen_parent'):
        for rel,digest in m[key].items():assert sha(root/rel)==digest
    for key in ('frozen_live_sources','frozen_resident_module_sources'):
        for rel,digest in m[key].items():assert sha(root/rel)==digest
    assert load(build/'vendor-files.json')==m['vendor_files'];old.sdk(load(build/'sdk-audit.json'),m)
    for rel,digest in m['sdk_headers_normalized_sha256'].items():assert hashlib.sha256((build/'sdk-snapshot'/rel).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest
    for file,key in [('pose_live_pipeline_check.arm64','binary_sha256'),('pose_system_timing_selftest','timing_selftest_sha256'),('pose_access_unit_selftest','au_selftest_sha256'),('pose_tcp_transport_check','tcp_selftest_sha256'),('pose_failed_result_selftest','failed_selftest_sha256'),('pose_display_worker','display_worker_sha256'),('pose_display_process_selftest','display_selftest_sha256')]:
        blob=(build/file).read_bytes();assert sha(build/file)==b[key] and blob[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',blob,18)[0]==183
    log=(build/'build.log').read_text(encoding='utf-8-sig');assert 'error:' not in log and 'RPATH' not in log and 'RUNPATH' not in log
    assert 'Built target pose_system_timing_selftest' in log and '9.4.0' in log and 'cmake version 3.24.2' in log
    warnings=[x for x in log.splitlines() if 'warning:' in x];assert all('lazy_runtime_validation.hpp:123:' in x or 'host_cpu_adapter.cpp:18:' in x for x in warnings),warnings
    child_dynamic=log.rsplit('Dynamic section',1)[-1];assert 'icraft' not in child_dynamic and 'libssl' not in child_dynamic and 'libcrypto' not in child_dynamic
    # Exact structural equivalence of the two log-only copies.
    vpu=(root/'software/pose_v1/src/vpu_resident_encoder.cpp').read_text().replace('<<std::endl',"<<'\\n'")
    assert vpu==(root/'software/pose_v1/src/timed_resident_encoder.cpp').read_text()
    return m,b,n

def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['build','host-check','process-three','measure-2hz','measure-5hz','trace-5hz']);p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    m,b,n=identities(a.package,a.build);report=dict(status='live_build_reviewed' if a.stage=='build' else 'live_stage_passed',stage=a.stage,binary_sha256=b['binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],payloads=n,build_sources=len(m['build_files']))
    if a.stage!='build':
        r=a.results;report['returned_files']=old.verify(r)
        assert sha(r/'pose_live_pipeline_check')==b['binary_sha256'] and sha(r/'executed-runner.sh')==sha(old.ROOT/'tools/pose-v1/run-forward-trace.sh')
        assert (r/'exit.txt').read_text().strip()=='0' and (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
        pre=load(r/'preflight.json');baseline=load(old.ROOT/'tools/pose-v1/evidence/resident-20261008-r6/resident-three/preflight.json')
        assert all(pre[k]==baseline[k] for k in ('boot_files','libraries','SDK_packages','fpga_state'))
        g=load(r/'previous-acceptance.json');assert g['stage']=={'host-check':'build','process-three':'host-check','measure-2hz':'process-three','measure-5hz':'measure-2hz','trace-5hz':'process-three'}[a.stage] and g['binary_sha256']==b['binary_sha256'] and g['package_manifest_sha256']==b['package_manifest_sha256']
        out=r/'results'
        if a.stage=='host-check':
            actual=rows(out/'host/cases.jsonl');wanted=load(a.package/'cpu-fixture-manifest.json')['cases'];assert len(actual)==len(wanted)==107;old.registry(out/'host/registry.jsonl');total=0
            for x,y in zip(actual,wanted):
                assert x['passed'] and all(x[k]==y[k] for k in ('case_id','op_id','expected')) and x['rejection']==('' if y['expected']=='PASS' else y['expected'])
                for i in range(y['outputs']):
                    blob=(out/'host'/y['case_id']/f'output{i}.f32').read_bytes();assert blob==(a.package/'fixtures'/y['case_id']/f'expected{i}.f32').read_bytes() and np.isfinite(np.frombuffer(blob,'<f4')).all();total+=len(blob)//4
            assert total==59600
            for prefix in ('AU','TCP','failure-contracts','timing-contracts','display-contracts'):
                assert (r/(prefix+'.exit.txt')).read_text().strip()=='0' and not (r/(prefix+'.stderr.log')).read_bytes()
            assert load(r/'timing-contracts.stdout.log')==dict(status='passed',rejections=7,transport_fixture_separate=True,device=False)
            assert load(r/'AU.stdout.log')==dict(status='passed',rejections=17,threaded_units=2000,capacity=8,no_device=True)
            assert load(r/'display-contracts.stdout.log')==dict(status='passed',rejections=9,IPC_NV12_bytes=6912000,capacity=2,one_request_credit=True,owned_bytes=True,reaped=True,SDK_device=False)
            assert sha(r/'pose_display_worker')==b['display_worker_sha256'] and sha(r/'pose_display_process_selftest')==b['display_selftest_sha256']
            assert not (r/'display-contracts/normal/child.stderr.log').read_bytes()
            assert not (r/'stderr.log').read_bytes();report.update(Host_cases=107,CPU_FP32=total,registry_records=12,transport_fixture_tests=True)
        else:
            assert all('CJN-Trace>>' in x and 'maxRTCPPacketSize' in x for x in (r/'stderr.log').read_text().splitlines())
            calls=rows(out/'inference.jsonl');timings=rows(out/'timing.jsonl');ingress=load(out/'input-summary.json');summary=load(out/'summary.json');queue=load(out/'queue-stats.json')
            assert 4<=len(calls)<=33 and len(calls)==len(timings)==summary['forward_calls']
            expected=4 if a.stage=='process-three' else 33
            assert ingress['sessions']==1 and ingress['received']==expected and ingress['consumed']==len(calls) and ingress['overwritten']==expected-len(calls) and ingress['rejected']==ingress['reconnect_discarded']==0
            if a.stage in ('measure-2hz','process-three'):assert len(calls)==expected and queue['consumed']==expected and not queue['overwritten'] and not queue['coalesced']
            old.registry(out/'engine/registry.jsonl');old.fusion_binding_review(out/'engine',load(old.ROOT/'tools/pose-v1/mixed-fusion-baseline.json'))
            assert not load(out/'engine/sdk-profile-setting.json')['enabled'];catalog=[line.split()[1] for line in (a.package/'cases.tsv').read_text().splitlines() if line.split()[0]==('base' if a.stage=='process-three' else 'expanded')];assert len(catalog)==(3 if a.stage=='process-three' else 27)
            if a.stage=='process-three':catalog.append(catalog[0])
            for i,(c,t) in enumerate(zip(calls,timings)):
                assert c['call']==c['invocation']==i and c['frame_id']==t['transport_id']==100000+t['sequence'] and c['case']==t['case']==catalog[t['sequence']%len(catalog)]
                assert c['before_forward']==0 and c['completed_layers']==745 and c['host_callbacks']==c['zg_callbacks']==7
                for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:
                    blob=(out/f'result{i}.{suffix}.f32').read_bytes();assert blob==(a.package/folder/(c['case']+'.'+suffix+'.f32')).read_bytes()==(out/f'presaved-results/{i}/{suffix}.f32').read_bytes() and np.isfinite(np.frombuffer(blob,'<f4')).all()
                assert (out/f'presaved-results/{i}/raw-payload.bin').read_bytes()==(a.package/'inputs'/(c['case']+'.csi')).read_bytes()[32:]
                keys=['arrived_ns','dequeued_ns','process_begin_ns','process_end_ns','verify_end_ns','draw_end_ns','convert_end_ns','published_ns'];assert [t[k] for k in keys]==sorted(t[k] for k in keys)
            lifecycle=rows(out/'lifecycle.jsonl');assert [x['event'] for x in lifecycle]==['Engine_created','workers_joined','Engine_destroyed']
            samples=rows(out/'samples.jsonl');aus=rows(out/'access-units.jsonl');packets=rows(out/'packets.jsonl');network=rows(out/'network/events.jsonl');nals=[x for x in network if x['event']=='nal_delivered' and x['type'] in (1,5)];received=[x for x in network if x['event']=='au_received']
            assert len(samples)==len(aus)==len(received)==summary['encoded_frames']<1000 and queue['AU_high_water']<=8
            assert [s['encoded_id'] for s in samples]==list(range(len(samples)))
            assert network[-1]['event']=='completed' and not network[-1]['failed'] and network[-1]['sources_live']==0
            enc=rows(out/'encoder/events.jsonl');assert enc[-1]['event']=='encoding_complete' and enc[-1]['queued']==enc[-1]['returned']==len(samples) and enc[-1]['last']
            warmups=0 if a.stage=='process-three' else 3
            completed=[t for t in timings if t['invocation']>=warmups];pairs=dict(queue_ms=('arrived_ns','dequeued_ns'),process_ms=('process_begin_ns','process_end_ns'),oracle_ms=('process_end_ns','verify_end_ns'),draw_ms=('verify_end_ns','draw_end_ns'),NV12_ms=('draw_end_ns','convert_end_ns'),publish_ms=('convert_end_ns','published_ns'),arrival_to_picture_ms=('arrived_ns','convert_end_ns'))
            metrics={name:stats([(t[z]-t[y])/1e6 for t in completed]) for name,(y,z) in pairs.items()}
            for key in ('preprocess_ms','prepare_ms','state_clear_ms','forward_ms','final_wait_ms','output_ms','selection_ms'):metrics[key]=stats([t[key] for t in completed])
            adoptions=[];captures=[];handoffs=[];seen=set()
            for s in samples:
                if not s['inference_result'] or s['invocation'] in seen:continue
                seen.add(s['invocation']);t=timings[s['invocation']];assert s['source_frame_id']==t['transport_id'] and s['generated_ns']==t['convert_end_ns']
                if s['invocation']<warmups:continue
                au=aus[s['encoded_id']];packet=next(x for x in packets if x['pts_us']==au['pts_us'] and x['bytes']>0);nal=next((x for x in nals if x['encoded_id']==s['encoded_id']),None)
                adoptions.append((s['adopt_ns']-t['convert_end_ns'])/1e6);captures.append((packet['capture_ns']-t['arrived_ns'])/1e6)
                if nal:handoffs.append((nal['handoff_ns']-t['arrived_ns'])/1e6)
            assert seen==set(range(len(calls)))
            metrics['picture_to_first_adopt_ms']=stats(adoptions);metrics['arrival_to_first_capture_callback_ms']=stats(captures);metrics['arrival_to_RTSP_handoff_ms']=stats(handoffs)
            dt=(completed[-1]['convert_end_ns']-completed[0]['convert_end_ns'])/1e9;rate=(len(completed)-1)/dt
            display=rows(out/'display-timing.jsonl');dq=load(out/'display-queue.json');assert len(display)==len(calls)==dq['adopted']==dq['published'] and dq['overwritten']==dq['coalesced']==0 and dq['high_water']<=2 and dq['IPC_inflight_limit']==1
            child=rows(out/'display/child.jsonl');parent=rows(out/'display/parent.jsonl');assert child[-1]['event']=='stopped' and child[-1]['renders']==len(calls) and not child[-1]['SDK'] and not child[-1]['VPU']
            assert [x['event'] for x in parent]==['spawned','cleanly_reaped'] and parent[0]['pid']!=parent[0]['parent_pid'] and parent[-1]['wait_status']==0 and not (out/'display/child.stderr.log').read_bytes()
            assert sha(r/'pose_display_worker')==b['display_worker_sha256'];fds=(out/'display/child-fds.txt').read_text();assert '/dev/video' not in fds and '/dev/mem' not in fds and 'udmabuf' not in fds
            for d,t,c in zip(display,timings,child[:-1]):
                assert d['invocation']==t['invocation']==c['invocation'] and d['frame_id']==t['transport_id']==c['frame_id']
                ordered=[t['verify_end_ns'],d['request_ns'],d['dispatch_ns'],d['render_begin_ns'],d['draw_end_ns'],d['convert_end_ns'],d['receive_end_ns'],d['published_ns']];assert ordered==sorted(ordered)
                assert all(d[x]==c[x] for x in ('draw_end_ns','convert_end_ns')) and d['render_begin_ns']==c['begin_ns']
            active=[d for d in display if d['invocation']>=warmups]
            metrics['draw_ms']=stats([(d['draw_end_ns']-d['render_begin_ns'])/1e6 for d in active])
            metrics['display_queue_IPC_request_ms']=stats([(d['render_begin_ns']-d['request_ns'])/1e6 for d in active])
            metrics['IPC_reply_ms']=stats([(d['receive_end_ns']-d['convert_end_ns'])/1e6 for d in active])
            metrics['parent_result_handoff_ms']=stats([(d['request_ns']-timings[d['invocation']]['verify_end_ns'])/1e6 for d in active])
            report.update(display_subprocess=True,child_sdk_dependencies=False,child_reaped=True,display_covered=len(display),parent_forward_display_overlap=sum(timings[i+1]['process_begin_ns']<display[i]['convert_end_ns'] for i in range(len(timings)-1)))
            report.update(measured_consumed=len(completed),warmups=warmups,sent=expected,consumed=len(calls),overwritten=ingress['overwritten'],encoded=len(samples),repeated_video_frames=sum(x['repeated_source'] for x in samples),new_pose_completion_interval_Hz=rate,metrics=metrics,full_numeric_bitwise=True,steady_clock_only=True,whole_5Hz_threshold_met=bool(a.stage!='trace-5hz' and rate>=5 and metrics['arrival_to_picture_ms']['P95']<=500 and ingress['overwritten']==0),PC_presentation_measured=False,nested_spans_not_summed=True)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

"""Offline resident identity/Host/clock/source review; never runs hardware."""
import argparse,json
import numpy as np
from pipeline_gate import identities,sha,load,rows,save,ROOT
import mixed_validation_gate as old

p=argparse.ArgumentParser();p.add_argument('stage',choices=['build','host-check','resident-three','resident-27'])
p.add_argument('--package',type=__import__('pathlib').Path,required=True);p.add_argument('--build',type=__import__('pathlib').Path,required=True)
p.add_argument('--results',type=__import__('pathlib').Path);p.add_argument('--output',type=__import__('pathlib').Path,required=True);a=p.parse_args()
m,b,count=identities(a.package,a.build,'pose_resident_check','tools/pose-v1/Build-Resident.ps1')
report=dict(status='pipeline_build_reviewed' if a.stage=='build' else 'pipeline_stage_passed',stage=a.stage,
    binary_sha256=b['binary_sha256'],package_manifest_sha256=sha(a.package/'manifest.json'),package_payloads=count,build_sources=len(m['build_files']))
if a.stage!='build':
    r=a.results;report['returned_hashed_files']=old.verify(r)
    assert sha(r/'pose_resident_check')==b['binary_sha256']
    assert (r/'exit.txt').read_text().strip()=='0' and not (r/'stderr.log').read_bytes()
    assert (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
    # Compare actual BOOT/SDK identities with the immediately preceding gate run.
    identity=load(r/'run-identity.json');assert identity['program_sha256']==b['binary_sha256'] and identity['package_manifest_sha256']==report['package_manifest_sha256']
    preflight=load(r/'preflight.json');reference=load(ROOT/'tools/pose-v1/evidence/video-descriptor-20261007-r5/encode/preflight.json')
    assert all(preflight[k]==reference[k] for k in ('boot_files','libraries','SDK_packages'))
    previous=load(r/'previous-acceptance.json');assert previous['binary_sha256']==b['binary_sha256'] and previous['package_manifest_sha256']==report['package_manifest_sha256']
    assert previous['stage']=={'host-check':'build','resident-three':'host-check','resident-27':'resident-three'}[a.stage]
    assert load(r/'results/queue-contracts.json')==dict(status='passed',capacity=2,overwrite_oldest=True,immutable_repeat=True,stop_rejected=True,failure_paths=3)
    out=r/'results'
    if a.stage=='host-check':
        cases=rows(out/'host/cases.jsonl');expected=load(a.package/'cpu-fixture-manifest.json')['cases']
        assert len(cases)==len(expected)==107 and all(x['passed'] for x in cases)
        old.registry(out/'host/registry.jsonl')
        total=0
        for item,wanted in zip(cases,expected):
            assert all(item[k]==wanted[k] for k in ('case_id','op_id','expected'))
            assert item['rejection']==('' if wanted['expected']=='PASS' else wanted['expected'])
            for i in range(wanted['outputs']):
                actual=(out/'host'/item['case_id']/f'output{i}.f32').read_bytes()
                assert actual==(a.package/'fixtures'/item['case_id']/f'expected{i}.f32').read_bytes()
                assert np.isfinite(np.frombuffer(actual,dtype='<f4')).all();total+=len(actual)//4
        assert total==59600
        report.update(Host_cases=107,registry_records=12,CPU_output_values=total,device_opened=False)
    else:
        records=rows(out/'inference.jsonl');n=4 if a.stage=='resident-three' else 28;assert len(records)==n
        old.registry(out/'engine/registry.jsonl');old.fusion_binding_review(out/'engine',load(ROOT/'tools/pose-v1/mixed-fusion-baseline.json'))
        for i,record in enumerate(records):
            assert record['call']==i and record['invocation']==i and record['before_forward']==0 and record['completed_layers']==745
            assert record['host_callbacks']==7 and record['zg_callbacks']==7
            for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:
                actual=(out/f'result{i}.{suffix}.f32').read_bytes();assert actual==(a.package/folder/f"{record['case']}.{suffix}.f32").read_bytes()
                assert np.isfinite(np.frombuffer(actual,dtype='<f4')).all()
        assert records[0]['case']==records[-1]['case']
        assert (out/'frames/result0.nv12').read_bytes()==(out/'frames'/f'result{n-1}.nv12').read_bytes()
        samples=rows(out/'samples.jsonl');events=rows(out/'encoder/events.jsonl')
        clocks=[e for e in events if e['event']=='sample_clock'];assert 2<=len(samples)==len(clocks)<=1000
        assert [e['encoded_id'] for e in samples]==list(range(len(samples)))
        assert all(x['sample_ns']<y['sample_ns'] for x,y in zip(samples,samples[1:]))
        assert all(x['pts_us']<y['pts_us'] for x,y in zip(clocks,clocks[1:]))
        epoch=[s['sample_ns']-c['pts_us']*1000 for s,c in zip(samples,clocks)];assert max(epoch)-min(epoch)<1000
        assert {s['invocation'] for s in samples if s['inference_result']}==set(range(n))
        for sample in samples:
            assert sample['generated_ns']<=sample['sample_ns']
            if sample['inference_result']:
                assert sample['source_frame_id']==records[sample['invocation']]['frame_id']
        assert all(e['equal'] for e in events if e['event']=='host_copy_check')
        assert [e['buffers'] for e in events if e['event']=='mapped_total']==[2,2]
        final=events[-1];assert final['event']=='encoding_complete' and final['queued']==final['returned']==len(samples) and final['last']
        summary=load(out/'summary.json');assert summary['forward_calls']==summary['published']==summary['consumed']==n
        qstats=load(out/'queue-stats.json');assert qstats['published']==qstats['consumed']==n and qstats['coalesced']==qstats['overwritten']==0
        assert summary['contexts_opened']==1 and summary['overwritten']==0 and summary['queue_capacity']==2
        assert summary['queue_high_water']<=2 and not summary['RTSP'] and not summary['HDMI']
        ready=rows(out/'lifecycle.jsonl');assert len(ready)==1 and ready[0]['event']=='Engine_created' and ready[0]['init_ms']<60000
        assert 19000000000<=samples[-1]['sample_ns']-ready[0]['time_ns']<21000000000
        report.update(full_correct_forwards=n,encoded_frames=len(samples),actual_clock_PTS=True,contexts=1,realtime_throughput_verified=False)
    report.update(exit=0,kernel_unchanged=True,stderr_empty=True)
save(a.output,report);print(json.dumps(report,indent=2))

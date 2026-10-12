"""Strict complete-output evidence review; failed prefix never yields a gate."""
import argparse,json,struct
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
from review_model_only_build_base import identities,rows
EXPECTED=dict(status='passed',refusals=9,scheduled_windows=103,owned_values=True,no_calls_after_error=True,no_burst_catchup=True,independent_flush=True,SDK_device=False)
def contract(p):
    assert (p/'owned.f32').read_bytes()==np.asarray([3]+[0]*99,dtype='<f4').tobytes()
    ledger=g.load(p/'ledger.json');assert ledger['original_computation_failure'] and [x['saved'] for x in ledger['tasks']]==[False,True] and ledger['tasks'][0]['error']=='storage error'
def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['baseline','contracts','three','load-103']);p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path);p.add_argument('--native',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    m,b,n=identities(a.package,a.build);report=dict(status='model_only_stage_passed',stage=a.stage,binary_sha256=b['binary_sha256'],model_only_binary_sha256=b['model_only_binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],payloads=n,build_sources=len(m['build_files']),video=False,network=False,normal_source_reads_added=0)
    for name,key in [('pose_model_only_check','model_only_binary_sha256'),('pose_model_only_selftest','model_only_selftest_sha256')]:
        blob=(a.build/name).read_bytes();assert g.sha(a.build/name)==b[key] and struct.unpack_from('<H',blob,18)[0]==183
    log=(a.build/'build.log').read_text(encoding='utf-8-sig');needed=log.split('Dynamic section')[-1];assert all(lib in needed for lib in ['libicraft_hostbackend.so','libicraft_zg330backend.so','libicraft_xrt.so']) and all(lib not in needed for lib in ['liveMedia','libssl','libcrypto'])
    if a.native:
        assert g.load(a.native/'stdout.json')==EXPECTED and (a.native/'exit.txt').read_text().strip()=='0' and not (a.native/'stderr.log').read_bytes();contract(a.native/'results');report['Native_refusals']=9
    if a.stage=='baseline':
        previous=g.ROOT/'tools/pose-v1/evidence/tensor-identity-20261010-r3';oldpackage=g.ROOT/'.local/pose-v1-plddr-position/package-20261010-r1';oldbuild=g.ROOT/'.local/pose-v1-build/mixed-20261010-plddr-position-r1';g.verify(oldpackage);gate=g.load(previous/'host-check.acceptance.json')
        assert gate['Host_cases']==107 and gate['registry_records']==12 and gate['CPU_FP32']==59600 and gate['binary_sha256']==b['binary_sha256']==g.sha(oldbuild/'pose_live_pipeline_check.arm64')
        assert g.load(previous/'host.invocation.json')['status']=='Host_lifetime_and_independent_persistence_passed'
        preserved=0
        for item in oldpackage.rglob('*'):
            if item.is_file() and item.name not in ('files.sha256','manifest.json'):assert item.read_bytes()==(a.package/item.relative_to(oldpackage)).read_bytes();preserved+=1
        assert preserved==402
        old=g.load(oldpackage/'manifest.json')
        for rel,item in old['build_files'].items():
            if rel=='tools/pose-v1/plddr-position-CMakeLists.txt':continue
            assert m['build_files'][rel]==item
        report.update(status='model_only_baseline_exact_main_Host107_reused',Host107_new_run=False,Host107_reused=107,registry_reused=12,CPU_FP32_reused=59600,old_Host_gate_sha256=g.sha(previous/'host-check.acceptance.json'),old_failure_contract_sha256=g.sha(previous/'host.invocation.json'),new_Engine_entry_not_Host107_executed=True,preserved_payloads=402)
    if a.results:
        r=a.results;out=r/'results';report['returned_files']=g.verify(r);code=int((r/'exit.txt').read_text());assert code in (0,1) and (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
        assert g.sha(r/'executed-runner.sh')==g.sha(g.ROOT/'tools/pose-v1/run-model-only.sh')
        if a.stage=='contracts':
            assert code==0 and g.load(r/'stdout.log')==EXPECTED and not (r/'stderr.log').read_bytes() and g.sha(r/'pose_model_only_selftest')==b['model_only_selftest_sha256'];contract(out);report.update(ARM_refusals=9,NPU_forward=False)
        else:
            assert g.sha(r/'pose_model_only_check')==b['model_only_binary_sha256'];summary=g.load(out/'summary.json');limit=4 if a.stage=='three' else 103;period=500000000 if a.stage=='three' else 200000000
            assert summary['mode']==a.stage and summary['expected']==limit and summary['period_ns']==period and not any(summary[k] for k in ['sdk_profiling','VPU','display','network','HDMI']) and summary['NPU_forward']
            g.registry(out/'engine/registry.jsonl');g.fusion_binding_review(out/'engine',g.load(g.ROOT/'tools/pose-v1/mixed-fusion-baseline.json'))
            index=rows(out/'returned-index.jsonl');calls=rows(out/'inference.jsonl');timing=rows(out/'timing.jsonl');assert len(index)==summary['returned'] and len(calls)==summary['correct'] and len(timing)==summary['attempted']<=limit
            names=[line.split()[1] for line in (a.package/'cases.tsv').read_text().splitlines() if line.split()[0]==('base' if a.stage=='three' else 'expanded')]
            if a.stage=='three':assert len(names)==3;names.append(names[0])
            else:assert len(names)==27
            for i,t in enumerate(timing):
                assert t['invocation']==i and t['process_begin_ns']>=t['scheduled_ns'] and t['scheduled_ns']>0
                if i:assert t['process_begin_ns']>=timing[i-1]['process_begin_ns']+period
                if t['process_end_ns']:assert t['process_end_ns']>=t['process_begin_ns']
                if t['verify_end_ns']:assert t['verify_end_ns']>=t['process_end_ns']>0
            total=0;differences=[]
            for i,x in enumerate(index):
                name=names[i%len(names)];blob=(a.package/'inputs'/(name+'.csi')).read_bytes();header=struct.unpack('<8sIIQQ',blob[:32]);assert header[0]==b'PIWCSI1\0' and header[1:3]==(1,86400)
                assert x['invocation']==i and x['frame_id']==100000+i and x['fixture_frame_id']==header[3] and x['case']==name
                directory=out/'presaved-results'/str(i);identity=g.load(directory/'identity.json');assert identity['saved_before_gate'] and identity['call']==identity['invocation']==i and identity['frame_id']==100000+i and identity['case']==name
                assert (directory/'raw-payload.bin').read_bytes()==blob[32:]
                for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:
                    actual=(directory/(suffix+'.f32')).read_bytes();wanted=(a.package/folder/(name+'.'+suffix+'.f32')).read_bytes();assert len(actual)==len(wanted);aa=np.frombuffer(actual,'<f4');bb=np.frombuffer(wanted,'<f4');same=actual==wanted
                    if x['verified']:assert same and np.isfinite(aa).all();assert actual==(out/f'result{i}.{suffix}.f32').read_bytes();total+=len(aa)
                    elif not same: differences.append(dict(invocation=i,case=name,output=suffix,changed_FP32=int((aa.view('<u4')!=bb.view('<u4')).sum()),nonfinite=int((~np.isfinite(aa)).sum())))
                if x['verified']:
                    c=calls[i];assert c['call']==c['invocation']==i and c['case']==name and c['before_forward']==0 and c['completed_layers']==745 and c['host_callbacks']==c['zg_callbacks']==7
            ledger=g.load(out/'persistence-ledger.json');assert [x['name'] for x in ledger['tasks']]==['returned-owned','timing-and-attempt','copy-metadata','192-producer-counts','tensor-object-identities','Engine-evidence','failed-Host-frame'] and all(x['saved'] for x in ledger['tasks'])
            life=rows(out/'lifecycle.jsonl');assert [x['event'] for x in life]==['Engine_created','Engine_destroyed'] and life[1]['time_ns']>life[0]['time_ns'] and life[0]['init_ms']<60000
            if code==0:
                assert summary['passed'] and summary['returned']==summary['attempted']==summary['correct']==limit and total==15100*limit and not summary['Engine_stopped_after_error'] and not (out/'failed-invocation-inputs').exists() and not (out/'failed-host-inputs/failure.json').exists() and not (r/'stderr.log').read_bytes()
            else:
                assert not summary['passed'] and summary['Engine_stopped_after_error'] and ledger['original_computation_failure'];report['status']='model_only_stage_failed_preserved_not_acceptance'
                assert (out/'failed-attempt/identity.json').exists();report['failed_attempt']=g.load(out/'failed-attempt/identity.json');report['failure_stderr']=(r/'stderr.log').read_text(errors='replace')
            report.update(expected_calls=limit,attempted=summary['attempted'],returned=summary['returned'],correct=summary['correct'],FP32_compared=total,full_outputs_differences=differences,save_before_gate=True,single_main_Engine=True,NPU_forward=True,metadata_persistence_tasks=7,root_cause_fixed=False,performance_accepted=False,kernel_unchanged=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()

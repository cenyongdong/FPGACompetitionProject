"""Review first startup separately from resident content and preserve any failure."""
import argparse,json,struct
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
from review_resident_sequence_build_base import identities,rows
SEQUENCE=dict(status='passed',refusals=13,calls=107,unique_invocations=True,load_starts=1,load_joins=1,no_boundary_resource_restart=True,failure_stops_next_stage=True,SDK_device=False)
PRODUCER=dict(status='passed',refusals=16,queries_per_call=8,maximum_rows=856,below_target_before_copy_allowed=True,query_error_preserved=True,SDK_device=False)
LOAD=dict(status='passed',refusals=6,normal_join_before_engine_release=True,disabled_hooks_not_called=True,partial_start_cleanup=True,original_error_preserved=True,all_cleanup_hooks_attempted=True,SDK_device=False)
RUN=dict(status='passed',refusals=9,scheduled_windows=103,owned_values=True,no_calls_after_error=True,no_burst_catchup=True,independent_flush=True,SDK_device=False)
TESTS=[('sequence','pose_resident_sequence_selftest','resident_selftest_sha256',SEQUENCE),('producer','pose_resident_producer_selftest','resident_producer_selftest_sha256',PRODUCER),('load','pose_model_load_selftest','load_selftest_sha256',LOAD),('run','pose_model_only_selftest','model_only_selftest_sha256',RUN)]
def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['baseline','contracts','resident']);p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--results',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    m,b,n=identities(a.package,a.build);report=dict(stage=a.stage,status='resident_stage_passed',resident_binary_sha256=b['resident_binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],payloads=n,build_sources=len(m['build_files']),Host107_new_run=False,normal_source_reads_added=0,root_cause_fixed=False,performance_accepted=False)
    for file,key in [('pose_resident_sequence_check','resident_binary_sha256')]+[(v[1],v[2]) for v in TESTS]:assert g.sha(a.build/file)==b[key] and struct.unpack_from('<H',(a.build/file).read_bytes(),18)[0]==183
    frozen=(g.ROOT/'software/pose_v1/src/producer_count_observation.cpp').read_text();current=(g.ROOT/'software/pose_v1/src/resident_producer_count_observation.cpp').read_text();assert current.replace('rows_.size()<856','rows_.size()<824')==frozen
    for label,file,key,expected in TESTS:
        d=a.evidence/('native-'+label);assert g.load(d/'stdout.json')==expected and (d/'exit.txt').read_text().strip()=='0' and not (d/'stderr.log').read_bytes()
    report['Native_contracts']={label:v['refusals'] for label,_,_,v in TESTS}
    if a.stage=='baseline':
        old=g.ROOT/'.local/pose-v1-model-vpu/package-20261010-r2';oldbuild=g.ROOT/'.local/pose-v1-build/mixed-20261010-model-vpu-r2';gate=g.load(g.ROOT/'tools/pose-v1/evidence/tensor-identity-20261010-r3/host-check.acceptance.json')
        assert gate['Host_cases']==107 and gate['registry_records']==12 and gate['CPU_FP32']==59600 and gate['binary_sha256']==b['binary_sha256']==g.sha(oldbuild/'pose_live_pipeline_check.arm64')
        preserved=0
        for item in old.rglob('*'):
            if item.is_file() and item.name not in ('manifest.json','files.sha256'):assert item.read_bytes()==(a.package/item.relative_to(old)).read_bytes();preserved+=1
        assert preserved==402 and b['model_vpu_binary_sha256']==g.sha(oldbuild/'pose_model_vpu_check')
        report.update(status='resident_baseline_exact_main_Host107_reused',Host107_reused=107,registry_reused=12,CPU_FP32_reused=59600,preserved_payloads=402,original_main_sha256=b['binary_sha256'])
    if a.results:
        r=a.results;report['returned_files']=g.verify(r);code=int((r/'exit.txt').read_text());assert code in (0,1)
        assert g.sha(r/'executed-runner.sh')==g.sha(g.ROOT/'tools/pose-v1/run-resident-sequence.sh')
        before=(r/'dmesg.before.log').read_bytes();after=(r/'dmesg.after.log').read_bytes();report['kernel_unchanged']=before==after
        assert not any(line.split(maxsplit=2)[1].startswith('pose_') for line in (r/'final.processes').read_text().splitlines()[1:])
        assert all(port not in (r/'final.ports').read_text() for port in (':39001 ',':8554 '))
        if a.stage=='contracts':
            assert code==0 and before==after
            for label,file,key,expected in TESTS:
                assert g.sha(r/file)==b[key] and g.load(r/(file+'.stdout.json'))==expected and (r/(file+'.exit.txt')).read_text().strip()=='0' and not (r/(file+'.stderr.log')).read_bytes()
            assert (r/'run-tests/owned.f32').read_bytes()==np.asarray([3]+[0]*99,dtype='<f4').tobytes()
            report.update(status='resident_contracts_passed',ARM_contracts={label:v['refusals'] for label,_,_,v in TESTS},NPU_forward=False)
        else:
            out=r/'results';summary=g.load(out/'summary.json');life=rows(out/'lifecycle.jsonl');stages=rows(out/'stages.jsonl');timing=rows(out/'timing.jsonl');index=rows(out/'returned-index.jsonl');calls=rows(out/'inference.jsonl');v=g.load(out/'vpu/summary.json');events=rows(out/'vpu/encoder/events.jsonl')
            assert g.sha(r/'pose_resident_sequence_check')==b['resident_binary_sha256'] and summary['mode']=='resident-three-103' and summary['expected']==107 and summary['load_joined'] and v['joined'] and not any(summary[k] for k in ('sdk_profiling','display','network','HDMI'))
            assert len(index)==summary['returned'] and len(timing)==summary['attempted']<=107 and len(calls)==summary['correct']
            ledger=g.load(out/'persistence-ledger.json');assert len(ledger['tasks'])==7 and all(x['saved'] for x in ledger['tasks'])
            assert len([x for x in events if x['event']=='identity'])==1
            if not summary['Engine_created']:
                assert code==1 and summary['attempted']==summary['returned']==summary['correct']==0 and not v['first_capture_ns'] and not stages and not (out/'vpu/encoder/video.h264').read_bytes()
                assert [x['event'] for x in life]==['load_joined','Engine_not_created_cleanup'] and after.startswith(before)
                added=after[len(before):].decode(errors='replace');assert 'page allocation failure: order:7' in added and 'mvx_mmu_alloc_contiguous_pages' in added
                abort=[x for x in events if x['event']=='abort_streamoff'];assert len(abort)==2 and all(x['result']==0 for x in abort)
                report.update(status='resident_first_startup_failed_not_acceptance',first_capture=False,Engine_created=False,NPU_forward_executed=False,correct=0,FP32_compared=0,new_kernel_events=added,worker_joined=True,abort_STREAMOFF_succeeded=True)
            else:
                assert life[0]['event']=='VPU_actual_capture' and life[1]['event']=='Engine_created' and life[-2]['event']=='load_joined' and life[-1]['event']=='Engine_destroyed'
                assert [x['time_ns'] for x in life]==sorted(x['time_ns'] for x in life) and life[1]['init_ms']<60000
                starts=[x for x in stages if x['event']=='stage_started'];assert 1<=len(starts)<=2 and len({x['Engine_object'] for x in starts})==len({x['VPU_object'] for x in starts})==1 and starts[0]['Engine_object']==life[1]['Engine_object']
                names=[]
                for group in ('base','expanded'):
                    ns=[line.split()[1] for line in (a.package/'cases.tsv').read_text().splitlines() if line.split()[0]==group];assert len(ns)==(3 if group=='base' else 27);names.append(ns+[ns[0]] if group=='base' else ns)
                total=0
                for i,x in enumerate(index):
                    phase=int(i>=4);local=i-(4 if phase else 0);name=names[phase][local%len(names[phase])]
                    assert x['invocation']==i and x['phase']==phase and x['local_index']==local and x['frame_id']==100000+i and x['case']==name
                    d=out/'presaved-results'/str(i);identity=g.load(d/'identity.json');assert identity['saved_before_gate'] and identity['call']==identity['invocation']==i and identity['frame_id']==100000+i
                    assert (d/'raw-payload.bin').read_bytes()==(a.package/'inputs'/(name+'.csi')).read_bytes()[32:]
                    for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:
                        data=(d/(suffix+'.f32')).read_bytes();wanted=(a.package/folder/(name+'.'+suffix+'.f32')).read_bytes()
                        if x['verified']:assert data==wanted==(out/f'result{i}.{suffix}.f32').read_bytes() and np.isfinite(np.frombuffer(data,'<f4')).all();total+=len(data)//4
                for i,t in enumerate(timing):
                    phase=int(i>=4);local=i-(4 if phase else 0);assert t['invocation']==i and t['phase']==phase and t['local_index']==local and t['process_begin_ns']>=t['scheduled_ns']
                    if local:assert t['process_begin_ns']>=timing[i-1]['process_begin_ns']+(200000000 if phase else 500000000)
                g.registry(out/'engine/registry.jsonl');g.fusion_binding_review(out/'engine',g.load(g.ROOT/'tools/pose-v1/mixed-fusion-baseline.json'))
                for i,c in enumerate(calls):assert c['call']==c['invocation']==i and c['before_forward']==0 and c['completed_layers']==745 and c['host_callbacks']==c['zg_callbacks']==7
                if code==0:
                    assert before==after and summary['passed'] and summary['correct']==summary['attempted']==summary['returned']==107 and total==1615700
                    assert [x['event'] for x in stages]==['stage_started','stage_completed','stage_started','stage_completed'] and [(x['offset'],x['count']) for x in starts]==[(0,4),(4,103)]
                    assert v['drained'] and v['submitted']==v['returned']<1000 and v['last_capture_ns']>=timing[-1]['process_end_ns'] and events[-1]['event']=='encoding_complete'
                    assert not any(x['event']=='abort_streamoff' for x in events) and not (r/'stderr.log').read_bytes()
                else:assert not summary['passed'] and ledger['original_computation_failure'];report['status']='resident_content_failed_preserved_not_acceptance'
                report.update(first_capture=True,Engine_created=True,correct=summary['correct'],attempted=summary['attempted'],FP32_compared=total,stage_records=stages,single_Engine_and_VPU_objects=True,worker_joined=True,first_ready_precedes_Engine=True,synthetic_VPU_only=True,VPU_images=v['submitted'],VPU_drained=v['drained'])
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k not in ('stage_records','new_kernel_events')}))
if __name__=='__main__':main()

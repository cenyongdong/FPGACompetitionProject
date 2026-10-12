"""Independently regenerate101 patterns, inspect real type and bind each gate."""
import argparse,json,struct
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
from review_typed_build import identities,rows
def pattern(slot,index):
    assert slot in (0,1) and 0<=index<=100
    return (np.arange([7560,4200][slot],dtype=np.float32)+np.float32(index*8192)+np.float32(100000 if slot else .25)).tobytes()
def fnv(blob):
    value=14695981039346656037
    for x in blob:value=((value^x)*1099511628211)&((1<<64)-1)
    return value
def contract(directory):
    for index in (0,100):
        for slot,name in enumerate(('a.f32','b.f32')):assert (directory/f'pattern{index}'/name).read_bytes()==pattern(slot,index)
    assert (directory/'partial/a.f32').read_bytes()==pattern(0,100) and not (directory/'partial/b.f32').exists()
    bad=pattern(1,100);previous=(directory/'previous-copy-block/b.f32').read_bytes();assert previous[:256]==bad[:256] and previous[256:384]==pattern(0,0)[256:384] and previous[384:]==bad[384:]
def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['baseline','contracts','static','dynamic','vpu']);p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path);p.add_argument('--native',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    m,b,n=identities(a.package,a.build);report=dict(status='typed_stage_passed',stage=a.stage,package_manifest_sha256=b['package_manifest_sha256'],typed_binary_sha256=b['typed_binary_sha256'],binary_sha256=b['binary_sha256'],payloads=n,build_sources=len(m['build_files']),full_model_Session=False,NPU_forward=False)
    for name,key in [('pose_typed_scratch_check','typed_binary_sha256'),('pose_typed_scratch_selftest','typed_selftest_sha256')]:
        raw=(a.build/name).read_bytes();assert g.sha(a.build/name)==b[key] and struct.unpack_from('<H',raw,18)[0]==183
    expected=dict(status='passed',refusals=8,patterns=101,unique_slot_fingerprints=202,FP32_exact=True,partial_saved=True,stale_generation_rejected=True,SDK_device=False)
    if a.native:
        assert g.load(a.native/'stdout.json')==expected and not (a.native/'stderr.log').read_bytes() and (a.native/'exit.txt').read_text().strip()=='0';contract(a.native/'results');report['Native_refusals']=8
    if a.stage=='baseline':
        previous=g.ROOT/'tools/pose-v1/evidence/tensor-identity-20261010-r3';oldpackage=g.ROOT/'.local/pose-v1-tensor-identity/package-20261010-r3';oldbuild=g.ROOT/'.local/pose-v1-build/mixed-20261010-tensor-identity-r3'
        g.verify(oldpackage);g.verify(previous/'host-return/run-host-check');gate=g.load(previous/'host-check.acceptance.json');old=g.load(oldpackage/'manifest.json')
        assert gate['Host_cases']==107 and gate['registry_records']==12 and gate['CPU_FP32']==59600 and gate['binary_sha256']==b['binary_sha256']==g.sha(oldbuild/'pose_live_pipeline_check.arm64')
        assert g.load(previous/'host.invocation.json')['status']=='Host_lifetime_and_independent_persistence_passed'
        preserved=0
        for item in oldpackage.rglob('*'):
            if item.is_file() and item.name not in ('files.sha256','manifest.json'):
                assert item.read_bytes()==(a.package/item.relative_to(oldpackage)).read_bytes();preserved+=1
        assert preserved==402
        for rel,item in old['build_files'].items():
            if rel=='tools/pose-v1/tensor-identity-CMakeLists.txt':continue
            assert m['build_files'][rel]==item
        report.update(status='typed_baseline_exact_main_Host107_reused',Host107_new_run=False,Host107_reused=107,registry_reused=12,CPU_FP32_reused=59600,preserved_payloads=402,old_Host_gate_sha256=g.sha(previous/'host-check.acceptance.json'),old_failure_contract_sha256=g.sha(previous/'host.invocation.json'))
    if a.results:
        r=a.results;report['returned_files']=g.verify(r);assert (r/'exit.txt').read_text().strip()=='0' and (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
        assert g.sha(r/'executed-runner.sh')==g.sha(g.ROOT/'tools/pose-v1/run-typed-scratch.sh')
        if a.stage=='contracts':
            assert g.load(r/'stdout.log')==expected and not (r/'stderr.log').read_bytes() and g.sha(r/'pose_typed_scratch_selftest')==b['typed_selftest_sha256'];contract(r/'results');report.update(ARM_refusals=8,SDK_device=False)
        else:
            assert g.sha(r/'pose_typed_scratch_check')==b['typed_binary_sha256'];out=r/'results';summary=g.load(out/'summary.json');data=rows(out/'pairs.jsonl');changing=a.stage!='static'
            assert summary['mode']==a.stage and summary['completed_pairs']==len(data)==100 and summary['all_bitwise'] and summary['actual_model_types'] and summary['dynamic_writes']==changing and summary['normal_source_read_pairs']==1 and not summary['pacing_inside_pair'] and not summary['NPU_forward'] and not summary['full_model_Session']
            assert summary['pacing_between_pairs_ms']==(200 if a.stage=='vpu' else 0)
            for i,x in enumerate(data):
                index=i+1 if changing else 0;assert x['pair']==i and x['pattern_index']==index and x['previous_pattern_index']==max(0,index-1) and x['matched']
                assert [x['fnv_a'],x['fnv_b']]==[fnv(pattern(s,index)) for s in (0,1)]
                names=['copy_a_begin_ns','copy_a_end_ns','shadow_a_begin_ns','shadow_a_end_ns','copy_b_begin_ns','copy_b_end_ns','shadow_b_begin_ns','shadow_b_end_ns'];times=[x[k] for k in names];assert times==sorted(times)
                writes=[x[k] for k in ['write_a_begin_ns','write_a_end_ns','write_b_begin_ns','write_b_end_ns']]
                assert writes==sorted(writes) and (0<writes[0]<=writes[-1]<=times[0] if changing else writes==[0]*4)
            for folder,index in [('preload',0),('first-pair',1 if changing else 0),('last-pair',100 if changing else 0)]:
                for slot,name in enumerate(('a.f32','b.f32')):assert (out/folder/name).read_bytes()==pattern(slot,index)
            assert not (out/'failed-pair').exists() and all(x['saved'] for x in g.load(out/'persistence-ledger.json')['tasks'])
            meta=g.load(out/'sdk/regions.json');assert meta['device']=='25122301' and meta['icore']=='FMSHZGV3TECH-AID - 24160628' and meta['dtype_source_op']==192 and meta['source_values']==[4386,4390] and not meta['NPU_forward'] and not meta['full_model_Session']
            for slot,x in enumerate(meta['sources']):
                assert x['slot']==slot and x['pointer'] in ('ADDR','BOTH') and x['region']=='AXIZG330AIPLDDRMemRegionNode' and x['region_identity']==meta['region_identity'] and x['offset']+x['bytes']<=x['capacity'] and x['address']%64==0
                typ=x['actual_type'];assert typ==dict(FP32=True,bytes=[30240,16800][slot],shape=[1,[180,100][slot],42],layout='**C',merged_axis=[2],uvalue=0,valid_mask='1'*42)
            x,y=meta['sources'];assert x['chunk_identity']!=y['chunk_identity'] and (x['address']+x['bytes']<=y['address'] or y['address']+y['bytes']<=x['address'])
            pad=meta['padding_address'];assert meta['padding_bytes']==32
            for x in meta['sources']:assert pad+32<=x['address'] or x['address']+x['bytes']<=pad
            life=rows(out/'lifecycle.jsonl');assert [v['event'] for v in life]==(['VPU_actual_capture'] if a.stage=='vpu' else [])+['SDK_opened','workers_joined','SDK_destroyed']
            if a.stage=='vpu':
                video=g.load(out/'vpu/summary.json');events=rows(out/'vpu/encoder/events.jsonl');assert video['joined'] and video['drained'] and not video['SDK_on_encoder_thread'] and video['submitted']==video['returned']<1000 and events[-1]['event']=='encoding_complete'
                assert video['first_capture_ns']<=life[1]['time_ns'] and video['last_capture_ns']>=data[-1]['shadow_b_end_ns'] and video['packets']>100
                assert data[-1]['shadow_b_end_ns']-data[0]['write_a_begin_ns']>=19000000000
                report.update(VPU_packets=video['packets'],VPU_submitted=video['submitted'],VPU_drained=True,VPU_context_overlapped_all_pairs=True)
            report.update(pairs=100,FP32_compared=1194000,model_types=True,dynamic_writes=changing,normal_reads_between_pairs=0,copy_span_ms=(data[-1]['shadow_b_end_ns']-data[0]['copy_a_begin_ns'])/1e6,write_pairs=100 if changing else 0,pattern_fingerprints_unique=len(set((x['fnv_a'],x['fnv_b']) for x in data)),not_model_fix_or_performance_acceptance=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()

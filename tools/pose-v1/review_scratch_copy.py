"""Independent patterns, identities and preserved Host contracts; no board calls."""
import argparse,json,struct
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
from review_scratch_host import identities,rows
def patterns():return [(np.arange(7560,dtype=np.float32)+np.float32(.25)).tobytes(),(np.arange(4200,dtype=np.float32)+np.float32(100000)).tobytes()]
def fnv(blob):
    h=14695981039346656037
    for x in blob:h=((h^x)*1099511628211)&((1<<64)-1)
    return h
def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['baseline','contracts','memory','vpu']);p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path);p.add_argument('--native',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    m,b,n=identities(a.package,a.build);want=patterns();report=dict(status='scratch_stage_passed',stage=a.stage,package_manifest_sha256=b['package_manifest_sha256'],scratch_binary_sha256=b['scratch_binary_sha256'],binary_sha256=b['binary_sha256'],payloads=n,build_sources=len(m['build_files']),full_model_Session=False,NPU_forward=False)
    for name,key in [('pose_scratch_copy_check','scratch_binary_sha256'),('pose_scratch_copy_selftest','scratch_selftest_sha256')]:
        raw=(a.build/name).read_bytes();assert g.sha(a.build/name)==b[key] and struct.unpack_from('<H',raw,18)[0]==183
    if a.stage=='baseline':
        old=g.ROOT/'tools/pose-v1/evidence/producer-count-20261009-r2';oldbuild=g.ROOT/'.local/pose-v1-build/mixed-20261009-producer-count-r2';oldpackage=g.ROOT/'.local/pose-v1-producer-count/package-20261009-r2';g.verify(oldpackage);g.verify(old/'host-return/run-host-check')
        oldm=g.load(oldpackage/'manifest.json');oldb=g.load(oldbuild/'build-result.json');oldgate=g.load(old/'host-check.acceptance.json');assert oldgate['Host_cases']==107 and oldgate['registry_records']==12 and oldgate['CPU_FP32']==59600 and oldb['binary_sha256']==b['binary_sha256']==g.sha(old/'host-return/run-host-check/pose_live_pipeline_check')
        preserved=0
        for item in oldpackage.rglob('*'):
            if item.is_file() and item.name not in ('files.sha256','manifest.json'):
                assert item.read_bytes()==(a.package/item.relative_to(oldpackage)).read_bytes();preserved+=1
        assert preserved==402
        for rel,item in oldm['build_files'].items():
            if rel=='tools/pose-v1/producer-count-CMakeLists.txt':continue
            assert m['build_files'][rel]==item and g.sha(a.build/'source'/item['destination'])==item['sha256']
        assert g.load(old/'host.invocation.json')['status']=='Host_lifetime_and_independent_persistence_passed'
        report.update(status='scratch_baseline_Host107_reused_exact_main_and_payload',Host_cases_reused=107,registry_records_reused=12,CPU_FP32_reused=59600,Host107_new_run=False,preserved_payloads=402,original_main_ELF_bitwise=True,old_Host_gate_sha256=g.sha(old/'host-check.acceptance.json'),old_Host_source_read_contract_sha256=g.sha(old/'host.invocation.json'))
    if a.native:
        assert g.load(a.native/'stdout.json')==dict(status='passed',refusals=8,owned_bytes=47760,bit_mismatch_detected=True,previous_copy_block_detected=True,SDK_device=False)
        for i,name in enumerate(('a.f32','b.f32')):assert (a.native/'tests/owned'/name).read_bytes()==want[i]
        assert (a.native/'tests/previous-copy-block/b.f32').read_bytes()!=want[1]
        report['Native_pattern_refusals']=8
    if a.results:
        r=a.results;report['returned_files']=g.verify(r);assert (r/'exit.txt').read_text().strip()=='0' and (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
        if a.stage=='contracts':
            assert g.load(r/'stdout.log')==dict(status='passed',refusals=8,owned_bytes=47760,bit_mismatch_detected=True,previous_copy_block_detected=True,SDK_device=False) and not (r/'stderr.log').read_bytes();assert g.sha(r/'pose_scratch_copy_selftest')==b['scratch_selftest_sha256']
            for i,name in enumerate(('a.f32','b.f32')):assert (r/'results/owned'/name).read_bytes()==want[i]
            report.update(ARM_pattern_refusals=8,SDK_device=False)
        else:
            out=r/'results';assert g.sha(r/'pose_scratch_copy_check')==b['scratch_binary_sha256'];summary=g.load(out/'summary.json');assert summary['mode']==a.stage and summary['completed_pairs']==100 and summary['all_bitwise'] and not summary['NPU_forward'] and not summary['full_model_Session'] and not summary['pacing_inside_pair']
            records=rows(out/'pairs.jsonl');assert len(records)==100
            for i,record in enumerate(records):
                assert record['pair']==i and record['matched'] and record['fnv_a']==fnv(want[0]) and record['fnv_b']==fnv(want[1])
                ordered=[record[k] for k in ('copy_a_begin_ns','copy_a_end_ns','shadow_a_begin_ns','shadow_a_end_ns','copy_b_begin_ns','copy_b_end_ns','shadow_b_begin_ns','shadow_b_end_ns')];assert ordered==sorted(ordered)
            for folder in ('preload','first-pair','last-pair'):
                for i,name in enumerate(('a.f32','b.f32')):assert (out/folder/name).read_bytes()==want[i]
            assert not (out/'failed-pair').exists() and all(v['saved'] for v in g.load(out/'persistence-ledger.json')['tasks'])
            meta=g.load(out/'sdk/regions.json');assert meta['device']=='25122301' and meta['icore']=='FMSHZGV3TECH-AID - 24160628' and not meta['full_model_Session'] and not meta['NPU_forward']
            for i,v in enumerate(meta['sources']):assert v['slot']==i and v['bytes']==len(want[i]) and v['offset']+v['bytes']<=v['capacity'] and v['pointer'] in ('ADDR','BOTH') and v['region']=='AXIZG330AIPLDDRMemRegionNode' and v['region_identity']==meta['region_identity']
            x,y=meta['sources'];assert x['address']!=y['address'] and (y['address']-x['address']>=x['bytes'] if x['address']<y['address'] else x['address']-y['address']>=y['bytes'])
            life=rows(out/'lifecycle.jsonl');assert [v['event'] for v in life]==(['VPU_actual_capture'] if a.stage=='vpu' else [])+['SDK_opened','workers_joined','SDK_destroyed']
            if a.stage=='vpu':
                video=g.load(out/'vpu/summary.json');events=rows(out/'vpu/encoder/events.jsonl');assert video['joined'] and not video['SDK_on_encoder_thread'] and video['drained'] and video['submitted']==video['returned']<1000 and events[-1]['event']=='encoding_complete'
                assert video['first_capture_ns']<=life[1]['time_ns'] and video['last_capture_ns']>=records[-1]['shadow_b_end_ns']
                assert records[-1]['shadow_b_end_ns']-records[0]['copy_a_begin_ns']>=19000000000 and video['packets']>100
                report.update(VPU_first_capture_before_SDK=True,VPU_packets=video['packets'],VPU_submitted=video['submitted'],VPU_overlapped_all_copies=True,VPU_drained=True)
            report.update(pairs=100,FP32_compared=1194000,first_last_bitwise=True,all_actual_fingerprints_match_independent_expected=True,copy_span_ms=(records[-1]['shadow_b_end_ns']-records[0]['copy_a_begin_ns'])/1e6,not_model_fix_or_performance_acceptance=True)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()

"""Preserve strict whole-output rules; add the explicit VPU lifecycle gates."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];s=(root/'tools/pose-v1/review_model_only.py').read_text(encoding='utf-8')
def change(a,b):
    global s
    assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
s=s.replace('from review_model_only_build_base import','from review_model_vpu_build_base import')
change("choices=['baseline','contracts','three','load-103']","choices=['baseline','contracts','model-three','vpu-three','model-103','vpu-103']")
change("p.add_argument('--native',type=Path);","p.add_argument('--native',type=Path);p.add_argument('--load-native',type=Path);")
s=s.replace("status='model_only_stage_passed'","status='model_vpu_stage_passed'").replace("'model_only_baseline_exact_main_Host107_reused'","'model_vpu_baseline_exact_main_Host107_reused'").replace("'model_only_stage_failed_preserved_not_acceptance'","'model_vpu_stage_failed_preserved_not_acceptance'")
change("model_only_binary_sha256=b['model_only_binary_sha256']","model_only_binary_sha256=b['model_only_binary_sha256'],model_vpu_binary_sha256=b['model_vpu_binary_sha256']")
change("('pose_model_only_check','model_only_binary_sha256')","('pose_model_vpu_check','model_vpu_binary_sha256'),('pose_model_load_selftest','load_selftest_sha256')")
change("    if a.stage=='baseline':","""    assert g.sha(g.ROOT/'software/pose_v1/src/model_vpu_check_r1.cpp')==m['model_vpu_r1_frozen_sources']['software/pose_v1/src/model_vpu_check_r1.cpp']
    r1=(g.ROOT/'software/pose_v1/src/model_vpu_check_r1.cpp').read_text();r2=(g.ROOT/'software/pose_v1/src/model_vpu_check_r2.cpp').read_text()
    assert r2.replace('            load.check();\\n            const auto begin=now();','            const auto begin=now();')==r1
    load_expected=dict(status='passed',refusals=6,normal_join_before_engine_release=True,disabled_hooks_not_called=True,partial_start_cleanup=True,original_error_preserved=True,all_cleanup_hooks_attempted=True,SDK_device=False)
    if a.load_native:
        assert g.load(a.load_native/'stdout.json')==load_expected and not (a.load_native/'stderr.log').read_bytes() and (a.load_native/'exit.txt').read_text().strip()=='0';report['Native_load_refusals']=6
    if a.stage=='baseline':""")
s=s.replace("'tools/pose-v1/run-model-only.sh'","'tools/pose-v1/run-model-vpu.sh'")
change("contract(out);report.update(ARM_refusals=9,NPU_forward=False)","contract(out);report.update(ARM_refusals=9,NPU_forward=False)\n            assert g.load(r/'load.stdout.json')==load_expected and not (r/'load.stderr.log').read_bytes() and (r/'load.exit.txt').read_text().strip()=='0' and g.sha(r/'pose_model_load_selftest')==b['load_selftest_sha256'];report['ARM_load_refusals']=6")
change("assert g.sha(r/'pose_model_only_check')==b['model_only_binary_sha256'];summary=g.load(out/'summary.json');limit=4 if a.stage=='three' else 103;period=500000000 if a.stage=='three' else 200000000","assert g.sha(r/'pose_model_vpu_check')==b['model_vpu_binary_sha256'];summary=g.load(out/'summary.json');short=a.stage.endswith('three');video=a.stage.startswith('vpu-');limit=4 if short else 103;period=500000000 if short else 200000000;report['video']=video")
change("assert summary['mode']==a.stage and summary['expected']==limit and summary['period_ns']==period and not any(summary[k] for k in ['sdk_profiling','VPU','display','network','HDMI']) and summary['NPU_forward']","assert summary['mode']==('three' if short else 'load-103') and summary['expected']==limit and summary['period_ns']==period and not any(summary[k] for k in ['sdk_profiling','display','network','HDMI']) and summary['NPU_forward'] and summary['VPU']==video and summary['load_joined']")
s=s.replace("a.stage=='three'","short")
change("life=rows(out/'lifecycle.jsonl');assert [x['event'] for x in life]==['Engine_created','Engine_destroyed'] and life[1]['time_ns']>life[0]['time_ns'] and life[0]['init_ms']<60000","""life=rows(out/'lifecycle.jsonl');assert [x['event'] for x in life]==(['VPU_actual_capture'] if video else [])+['Engine_created','load_joined','Engine_destroyed']
            assert [x['time_ns'] for x in life]==sorted(x['time_ns'] for x in life) and life[1 if video else 0]['init_ms']<60000
            if video and code==0:
                v=g.load(out/'vpu/summary.json');events=rows(out/'vpu/encoder/events.jsonl');assert v['joined'] and v['drained'] and v['submitted']==v['returned']<1000 and not v['SDK_on_encoder_thread'] and events[-1]['event']=='encoding_complete'
                assert v['first_capture_ns']<=life[0]['time_ns']<life[1]['time_ns'] and v['last_capture_ns']>=timing[-1]['process_end_ns'] and not any(x['event']=='abort_streamoff' for x in events)
                report.update(VPU_submitted=v['submitted'],VPU_packets=v['packets'],VPU_drained=True,VPU_overlapped_all_forward_calls=True,synthetic_NoInput=True)
            elif not video:assert not (out/'vpu').exists()""")
out=root/'tools/pose-v1/review_model_vpu.py';assert not out.exists();out.write_text(s,encoding='utf-8',newline='\n')

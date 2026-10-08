"""Audit the failed diagnostic without fabricating an acceptance gate."""
import json,re
from pathlib import Path
import numpy as np
import mixed_validation_gate as old
from review_forward_stage import identities,rows,sha
root=old.ROOT;e=root/'tools/pose-v1/evidence/forward-trace-20261008-r1';r=e/'trace-5hz';out=r/'results'
m,b,_=identities(root/'.local/pose-v1-forward-trace/package-20261008-r1',root/'.local/pose-v1-build/mixed-20261008-forward-trace-r1')
returned=old.verify(r);assert (r/'exit.txt').read_text().strip()=='1'
assert sha(r/'pose_live_pipeline_check')==b['binary_sha256'] and sha(r/'pose_display_worker')==b['display_worker_sha256']
assert sha(r/'executed-runner.sh')==sha(root/'tools/pose-v1/run-forward-trace.sh')
assert (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
baseline=json.loads((e/'process-three/preflight.json').read_text());pre=json.loads((r/'preflight.json').read_text())
assert all(pre[k]==baseline[k] for k in ('boot_files','libraries','SDK_packages','fpga_state'))
old.registry(out/'engine/registry.jsonl');old.fusion_binding_review(out/'engine',old.load(root/'tools/pose-v1/mixed-fusion-baseline.json'))
calls=rows(out/'inference.jsonl');assert len(calls)==3;total=0
package=root/'.local/pose-v1-forward-trace/package-20261008-r1'
for i,c in enumerate(calls):
    assert c['invocation']==i and c['before_forward']==0 and c['completed_layers']==745 and c['host_callbacks']==c['zg_callbacks']==7
    for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:
        blob=(out/f'result{i}.{suffix}.f32').read_bytes()
        assert blob==(package/folder/(c['case']+'.'+suffix+'.f32')).read_bytes()==(out/f'presaved-results/{i}/{suffix}.f32').read_bytes()
        assert np.isfinite(np.frombuffer(blob,'<f4')).all();total+=len(blob)//4
assert total==45300
spans=rows(out/'engine/monotonic-spans.jsonl');failed=[s for s in spans if s['invocation']==3]
assert [s['slot'] for s in failed if s['op_id']==192 and s['kind']=='bridge.copy']==[0,1]
assert not any(s['kind']=='bridge.cpu' and s['op_id']==192 for s in failed)
assert 'CPU_CANDIDATE[kernel]: floating-point index is not a finite integer' in (r/'stderr.log').read_text()
assert not (out/'summary.json').exists()
parent=rows(out/'display/parent.jsonl');assert parent[-1]['event']=='error_cleanup_reaped'
encoder=rows(out/'encoder/events.jsonl');streamoffs=[s for s in encoder if s['event']=='abort_streamoff'];assert len(streamoffs)==2 and all(s['result']==0 for s in streamoffs)
assert [x['event'] for x in rows(out/'lifecycle.jsonl')]==['Engine_created','workers_joined','Engine_destroyed']
assert rows(out/'network/events.jsonl')[-1]['sources_live']==0
final=e/'final-audit';old.verify(final);listeners=(final/'listeners.txt').read_text();assert ':8554' not in listeners and ':39001' not in listeners
processes=(final/'processes.txt').read_text();assert not any('pose_live_pipeline_check' in x or 'pose_display_worker' in x for x in processes.splitlines())
comp=e/'compaction-before-regression';old.verify(comp);assert (comp/'before.dmesg.log').read_bytes()==(comp/'after.dmesg.log').read_bytes()
def ordinary_units(label):
    n=0
    for line in (comp/(label+'.pagetypeinfo.txt')).read_text().splitlines():
        if line.startswith('Node') and re.search(r'type\s+(Unmovable|Movable|Reclaimable)\s',line):
            values=list(map(int,line.split()[-11:]));n+=sum(values[i]*(1<<(i-7)) for i in range(7,11))
    return n
report=dict(status='diagnostic_failed_inputs_uncaptured_root_cause_pending',returned_files=returned,program_sha256=b['binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],completed_forwards=3,completed_FP32_bitwise=total,failed_invocation=3,failed_transport_id=100003,failed_op_id=192,failure='GatherElements kernel rejects non-finite or non-integer FP32 index',failed_staged_input_bytes_saved=False,SDK_profile=False,dmesg_unchanged=True,child_reaped=True,both_VPU_streamoff_success=True,network_sources_live=0,ports_released=True,Engine_destroyed_after_join=True,compaction_count=1,compaction_ms=old.load(comp/'action.json')['elapsed_ns']/1e6,ordinary_512KiB_units_before=ordinary_units('before'),ordinary_512KiB_units_after=ordinary_units('after'),compaction_necessity_proven=False,old_invocation28_reached=False,whole5Hz_verified=False,all_sessions_closed=True,bounded_schedule_prepared_not_executed=True)
(e/'failure-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

"""Independent complete fixed100 payload/output/pacing/lifecycle review."""
from pathlib import Path
import json,hashlib,sys,numpy as np
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-phase-20261011-r1';mode=sys.argv[1];assert mode in ('off','on')
D=E/(mode+'-return')/('run-'+mode);P=D/'results';ref=R/'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (D/'exit.txt').read_text().strip()=='0' and not (D/'stderr.txt').read_bytes()
assert (D/'before.dmesg.txt').read_bytes()==(D/'after.dmesg.txt').read_bytes()
summary=json.loads((P/'summary.json').read_text());assert summary['completed']==100 and summary['all_bitwise']
assert json.loads((P/'release.json').read_text())['remaining_sdk_chunks']==0
assert (P/'deployment.ready').read_bytes()==(P/'forward.allow').read_bytes()
deploy=json.loads((P/'deployment.json').read_text());assert deploy['sync_start']==0 and deploy['layers']==11 and deploy['member_count']==19
assert json.loads((E/(mode+'-deployment.review.json')).read_text())['sha256']==sha(P/'deployment.json')
rows=[];count=0;epoch=None
for i in range(100):
    d=P/('call-'+str(i));identity=json.loads((d/'identity.json').read_text());assert identity['invocation']==i and identity['pattern']==i%2 and identity['no_catch_up']
    if epoch is None:epoch=identity['epoch_ns']
    assert identity['epoch_ns']==epoch and identity['planned_ns']==epoch+20000000000*i//101
    assert 0<=identity['actual_start_ns']-identity['planned_ns']<20000000000//101
    pattern=ref/('pattern-'+str(i%2));metrics=[]
    for name in ('input-486.f32','input-478.f16'):assert (d/name).read_bytes()==(pattern/name).read_bytes()
    t=json.loads((d/'trace.json').read_text());assert t['before_forward_count']==0 and t['after_ready_count']==11 and t['invocation']==i
    assert identity['actual_start_ns']<=t['reset_begin_ns']<=t['forward_begin_ns']<=t['forward_return_ns']
    for value,n,read in zip((4386,4390),(7560,4200),t['reads']):
        a=d/('output-'+str(value)+'.f32');assert a.read_bytes()==(pattern/a.name).read_bytes();data=np.fromfile(a,dtype='<f4');assert data.size==n and np.isfinite(data).all();count+=n
        assert read['value']==value and read['source_ready'] and read['source_address']==next(x['physical'] for x in deploy['boundary'] if x['value']==value)
        assert t['forward_return_ns']<=read['wait_begin_ns']<=read['wait_end_ns']<=read['copy_begin_ns']<=read['copy_end_ns']<=read['owned_end_ns']
        metrics.append({'value':value,'FP32':n,'sha256':sha(a),'copy_begin_ns':read['copy_begin_ns'],'copy_end_ns':read['copy_end_ns'],'wait_us':(read['wait_end_ns']-read['wait_begin_ns'])/1000,'copy_us':(read['copy_end_ns']-read['copy_begin_ns'])/1000})
    assert t['reads'][0]['owned_end_ns']<=t['reads'][1]['wait_begin_ns']
    assert t['reads'][-1]['owned_end_ns']-identity['actual_start_ns']<20000000000//101
    assert json.loads((d/'comparison.json').read_text())['saved_before_compare']
    rows.append({'invocation':i,'pattern':i%2,'planned_ns':identity['planned_ns'],'actual_start_ns':identity['actual_start_ns'],'lateness_ns':identity['actual_start_ns']-identity['planned_ns'],'reset_begin_ns':t['reset_begin_ns'],'owned_end_ns':t['reads'][-1]['owned_end_ns'],'forward_us':(t['forward_return_ns']-t['forward_begin_ns'])/1000,'outputs':metrics})
assert count==1176000
events=[json.loads(x) for x in (P/'lifecycle.jsonl').read_text().splitlines()];names=[x['event'] for x in events]
assert names==(['VPU_actual_capture'] if mode=='on' else [])+['SDK_initialized','fixed_sequence_started','fixed_sequence_completed','workers_joined','SDK_destroyed']
assert all(a['time_ns']<=b['time_ns'] for a,b in zip(events,events[1:]))
if mode=='on':assert (P/'vpu/summary.json').is_file() and (P/'vpu-ioctl.jsonl').is_file()
else:assert not (P/'vpu').exists() and not (P/'vpu-ioctl.jsonl').exists()
for i in range(2):
    d=P/('memory-pattern-'+str(i));assert json.loads((d/'memory.json').read_text())['bitwise_equal']
    for v,e in ((486,'f32'),(478,'f16')):assert (d/('input-'+str(v)+'.roundtrip')).read_bytes()==(ref/('pattern-'+str(i))/('input-'+str(v)+'.'+e)).read_bytes()
report={'status':'fixed100_outputs_and_lifecycle_verified','mode':mode,'calls':100,'FP32_values':count,'bitwise_reference':True,'all_finite':True,'missed_slots':0,'pacing_target_hz':'5.05','stage_kernel_unchanged':True,'SDK_chunks_after_release':0,'frames':rows,'lifecycle':events,'root_cause_resolved':False,'VPU_content_and_overlap_review_pending':mode=='on','archive_sha256':sha(E/('return-'+mode+'.tar')),'performance_acceptance':False}
(E/(mode+'.data-review.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(mode,'fixed100:',count,'FP32 bitwise; pacing/lifecycle/release verified')

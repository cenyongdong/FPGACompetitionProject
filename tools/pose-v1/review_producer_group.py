"""Independent post-save NumPy review of the one fixed physical A/B/A/B run."""
from pathlib import Path
import json,hashlib,numpy as np
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-group-20261011-r2';D=E/'physical-return/run-physical';M=E/'mock-return/run-mock'
ref=R/'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert np.__version__=='2.2.5' and (D/'exit.txt').read_text().strip()=='0' and not (D/'stderr.txt').read_bytes()
assert (D/'before.dmesg.txt').read_bytes()==(D/'after.dmesg.txt').read_bytes()==(M/'before.dmesg.txt').read_bytes()
assert not any(s.split()[1].startswith('pose_') for s in (D/'processes.txt').read_text().splitlines()[1:] if len(s.split())>1)
assert json.loads((D/'results/release.json').read_text())['remaining_sdk_chunks']==0
assert json.loads((D/'budget.json').read_text())['reason']=='program_exit'
assert json.loads((D/'results/summary.json').read_text())['NPU_calls']==4
deployed=json.loads((D/'results/deployment.json').read_text());gate=json.loads((E/'deployment.review.json').read_text())
assert sha(D/'results/deployment.json')==gate['deployment_sha256']
assert (D/'results/deployment.ready').read_bytes()==(D/'results/forward.allow').read_bytes()
for pattern in range(2):
    folder=D/('results/memory-pattern-'+str(pattern));memory=json.loads((folder/'memory.json').read_text());assert memory['region']=='physicalSDKownedPLDDR' and memory['bitwise_equal'] and not memory['forward_called']
    for value,ext in ((486,'f32'),(478,'f16')):assert (folder/('input-'+str(value)+'.roundtrip')).read_bytes()==(ref/('pattern-'+str(pattern))/('input-'+str(value)+'.'+ext)).read_bytes()
rows=[];FP32=0
for i in range(4):
    p=D/('results/call-'+str(i));pattern=ref/('pattern-'+str(i%2));identity=json.loads((p/'identity.json').read_text());assert identity=={'invocation':i,'pattern':i%2}
    for n in ('input-486.f32','input-478.f16'):assert (p/n).read_bytes()==(pattern/n).read_bytes()
    trace=json.loads((p/'trace.json').read_text());assert trace['invocation']==i and trace['before_forward_count']==0 and trace['after_ready_count']==11
    assert trace['reset_begin_ns']<=trace['forward_begin_ns']<=trace['forward_return_ns']
    metrics=[]
    for value,size,shape,r in zip((4386,4390),(30240,16800),((1,180,42),(1,100,42)),trace['reads']):
        actual=p/('output-'+str(value)+'.f32');expected=pattern/actual.name
        assert actual.stat().st_size==size and actual.read_bytes()==expected.read_bytes()
        a=np.fromfile(actual,dtype='<f4').reshape(shape);b=np.fromfile(expected,dtype='<f4').reshape(shape)
        assert np.isfinite(a).all();FP32+=a.size
        assert r['value']==value and r['source_ready'] and r['source_offset']<=r['source_capacity'] and size<=r['source_capacity']-r['source_offset']
        assert r['source_address']==next(x['physical'] for x in deployed['boundary'] if x['value']==value)
        assert trace['forward_return_ns']<=r['wait_begin_ns']<=r['wait_end_ns']<=r['copy_begin_ns']<=r['copy_end_ns']<=r['owned_end_ns']
        diff=a.astype('f8')-b.astype('f8');metrics.append({'value':value,'FP32_values':a.size,'shape':shape,'bitwise_equal':True,'max_abs':float(abs(diff).max()),'rms':float(np.sqrt(np.mean(diff*diff))),'sha256':sha(actual),'wait_us':(r['wait_end_ns']-r['wait_begin_ns'])/1000,'copy_us':(r['copy_end_ns']-r['copy_begin_ns'])/1000})
    assert trace['reads'][0]['owned_end_ns']<=trace['reads'][1]['wait_begin_ns']
    stages=[json.loads(x) for x in (p/'stages.jsonl').read_text().splitlines()]
    assert [(s['stage'],s['value']) for s in stages]==[('before_reset',-1),('before_forward',-1)]+[(name,v) for v in (4386,4390) for name in ('before_wait','after_wait','before_copy','after_copy','output_saved')]
    assert all(a['time_ns']<=b['time_ns'] for a,b in zip(stages,stages[1:]))
    assert json.loads((p/'comparison.json').read_text())['saved_before_compare']
    rows.append({'invocation':i,'pattern':i%2,'before_count':0,'after_count':11,'forward_call_us':(trace['forward_return_ns']-trace['forward_begin_ns'])/1000,'outputs':metrics})
assert FP32==47040
for value in (4386,4390):
    n='output-'+str(value)+'.f32'
    assert (D/'results/call-0'/n).read_bytes()==(D/'results/call-2'/n).read_bytes()
    assert (D/'results/call-1'/n).read_bytes()==(D/'results/call-3'/n).read_bytes()
    assert (D/'results/call-0'/n).read_bytes()!=(D/'results/call-1'/n).read_bytes()
result={'status':'independent_physical_group_four_calls_passed_not_concurrency_fix','FP32_values':FP32,'sequence':['A','B','A','B'],'frames':rows,'independent_counter':[0,11],'physical_memory_roundtrip_bytes':35360,'kernel_unchanged':True,'release_chunks':0,'NPU_calls':4,'VPU_used':False,'original_failure_reproduced':False,'root_cause_resolved':False,'formal_final745_protocol_changed':False,'no_performance_acceptance':True,'archives':{'return-physical.tar':sha(E/'return-physical.tar'),'return-mock.tar':sha(E/'return-mock.tar')},'gate_review_sha256':sha(E/'deployment.review.json')}
(E/'data-review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Independent saved 47040 FP32, A/B/A/B, counter0→11, roundtrip and release verified; root unresolved')

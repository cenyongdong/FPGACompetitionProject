"""Audit existing failed r4 return; never issues stage acceptance or accesses hardware."""
from pathlib import Path
import hashlib, json, sys
import numpy as np

base=Path(__file__).resolve().parent
root=base.parents[3]
sys.path.insert(0,str(root/'tools/pose-v1'))
import mixed_validation_gate as gate
import host_content_review as content
package=root/'.local/pose-v1-mixed-validation/package-20261006-content-r4-final'
build=root/'.local/pose-v1-build/mixed-20261006-content-r4-final'
run=base/'mixed-three'; out=run/'results'
report_path=base/'mixed-three-failure-review.json'
assert not report_path.exists()
sha=gate.sha; load=gate.load; rows=gate.lines
package_count=gate.verify(package); returned_count=gate.verify(run)
m=load(package/'manifest.json'); b=load(build/'build-result.json')
assert b['package_manifest_sha256']==sha(package/'manifest.json')
assert sha(run/'pose_mixed_check')==b['binary_sha256']
gate.sdk(load(run/'sdk-audit.json'),m)
identity=load(run/'run-identity.json')
assert identity['stage']=='mixed-three' and identity['binary_sha256']==b['binary_sha256']
assert identity['package_manifest_sha256']==sha(package/'manifest.json')
assert (run/'previous-acceptance.json').read_bytes()==(base/'mixed-one.acceptance.json').read_bytes()
assert (run/'exit.txt').read_text().strip()=='1'
failure=load(out/'failure.json')
assert failure['error']=='All outputs identical for distinct CSI; review needed'
assert (run/'run.stderr.log').read_text().strip()=='STOP: '+failure['error']
assert not (out/'summary.json').exists() and not (base/'mixed-three.acceptance.json').exists()
gate.registry(out/'registry.jsonl')
gate.fusion_binding_review(out,load(package/'mixed-fusion-baseline.json'))
assert load(out/'device-version.json')['versions']=={'device':'25122301','icore':'FMSHZGV3TECH-AID - 24160628'}
records=content.review_mixed(out,package/'reference',[(f'S11_01_{n}',f) for n,f in [(308,6),(309,7),(310,8),(308,6)]])
raw={ (r['invocation'],r['kind'],r['op_id'],r['slot']):(out/'content'/r['file']).read_bytes() for r in records}
graph=load(package/'graph/piw24_ZG.json'); ops={o['op_id']:o for o in graph['ops']}
producer={v['v_id']:o['op_id'] for o in graph['ops'] for v in o['outputs']}
group={i:r['op_id'] for r in rows(out/'after-apply.zg-hardop-map.jsonl') if r['op_id']>=9185 for i in r['merge_from']}
input_edges=[]
for opid in (188,192,437,442,582,649,672):
    op=ops[opid]
    for i,v in enumerate(op['inputs']):
        if v['_type_key'].endswith('Params'): continue
        p=producer[v['v_id']]
        input_edges.append(dict(consumer=opid,model_slot=i,value_id=v['v_id'],producer=p,zg_group=group.get(p),shape=v['dtype']['shape']))
calls=[]; cpu_checks=[]
for invocation,name in enumerate(['S11_01_308','S11_01_309','S11_01_310','S11_01_308']):
    events=[r for r in rows(out/'operator-execution.jsonl') if r['invocation']==invocation]
    assert len(events)==14
    assert sorted(r['op_id'] for r in events if 'ZG330Backend' in r['backend'])==list(range(9185,9192))
    assert sorted(r['op_id'] for r in events if 'HostBackend' in r['backend'])==[0,188,192,437,442,582,649]
    moves=[r for r in rows(out/'bridge.jsonl') if r['invocation']==invocation]
    assert len(moves)==8 and sum(r['bytes'] for r in moves)==115360
    assert all(r['source']['pointer']=='ADDR' and r['destination']['pointer']=='CPTR' and r['action']=='input_to_host' for r in moves)
    changes=[]
    for r in [r for r in records if r['invocation']==invocation]:
        key=(r['kind'],r['op_id'],r['slot']); value=raw[(invocation,)+key]
        first=raw[(0,)+key]; prior=raw[(max(0,invocation-1),)+key]
        changes.append(dict(kind=key[0],op_id=key[1],slot=key[2],
            changed_vs_first=int(np.count_nonzero(np.frombuffer(value,dtype='<u4')!=np.frombuffer(first,dtype='<u4'))),
            equal_previous=value==prior,sha256=hashlib.sha256(value).hexdigest()))
    calls.append(dict(invocation=invocation,case=name,content=changes))
    for opid in (188,192,437,582,649):
        op=ops[opid]
        staged=[]; slot=0
        for i,v in enumerate(op['inputs']):
            if v['_type_key'].endswith('Params'):
                value=(out/f'op{opid}.param{i}.f32').read_bytes()
            else:
                value=raw[invocation,'bridge_input',opid,slot]; slot+=1
            staged.append(np.frombuffer(value,dtype='<f4').reshape(v['dtype']['shape']))
        if opid in (188,437):
            index=np.argsort(-staged[0],axis=op['axis'],kind='stable')
            selection=[slice(None)]*index.ndim;selection[op['axis']]=slice(0,int(staged[1].flat[0]))
            index=index[tuple(selection)]
            expected=[np.take_along_axis(staged[0],index,axis=op['axis']),index.astype('<f4')]
        elif opid==192:
            idx=staged[1]; assert np.array_equal(idx,np.trunc(idx))
            expected=[np.take_along_axis(staged[0],idx.astype(np.int64),axis=op['axis'])]
        else:
            idx=staged[1];assert np.array_equal(idx,np.trunc(idx))
            actual=staged[0].copy();idx=idx.astype(np.int64)
            assert np.unique(idx.reshape(-1,3),axis=0).shape[0]==4200
            actual[tuple(idx[...,axis] for axis in range(3))]=staged[2]
            expected=[actual]
        for slot,value in enumerate(expected):
            captured=raw[invocation,'bridge_result',opid,slot]
            assert value.astype('<f4').tobytes()==captured, (invocation,opid,slot)
            cpu_checks.append(dict(invocation=invocation,op_id=opid,slot=slot,elements=value.size,bitwise_equal=True))
outputs=[]
for name in ['S11_01_308','S11_01_309','S11_01_310','S11_01_308.repeat']:
    for suffix,count in [('scores',100),('poses',4200)]:
        p=out/f'{name}.{suffix}.f32';value=p.read_bytes()
        assert np.frombuffer(value,dtype='<f4').size==count and np.isfinite(np.frombuffer(value,dtype='<f4')).all()
        assert value==(out/f'S11_01_308.{suffix}.f32').read_bytes()
        assert value==(base/'mixed-one/results'/f'S11_01_308.{suffix}.f32').read_bytes()
        outputs.append(dict(case=name,kind=suffix,sha256=sha(p),equal_first=True))
for name in ['S11_01_308','S11_01_309','S11_01_310']:
    assert (out/f'{name}.input.f32').read_bytes()==(package/'reference'/f'{name}.input.f32').read_bytes()
for p in out.glob('op*.param*.f32'):
    assert p.read_bytes()==(base/'offline-check/results'/p.name).read_bytes()
assert (run/'dmesg.before.log').read_bytes()==(run/'dmesg.after.log').read_bytes()
report=dict(status='failed_r4_three_content_reviewed_no_acceptance',failure=failure,exit=1,
    returned_files_verified=returned_count,package_files_verified=package_count,
    binary_sha256=b['binary_sha256'],sdk=load(run/'sdk-audit.json'),device=load(out/'device-version.json'),
    binding_coverage_verified=True,real_parameters_match_offline=True,all_fixed_inputs_match=True,
    content_records=len(records),content_bytes=sum(r['bytes'] for r in records),caller_Input0_all_match_current=True,
    calls=calls,graph_input_producers=input_edges,cpu_reference_checks=cpu_checks,
    cpu_reference_values=sum(r['elements'] for r in cpu_checks),outputs=outputs,
    timing=rows(out/'results.jsonl')+[load(out/'repeat-first.json')],
    dmesg_unchanged=True,memory_before=(run/'memory.before.txt').read_text(),memory_after=(run/'memory.after.txt').read_text(),
    earliest_observed_nonresponse='invocation1: Input0 changed 10431 FP32, but group9185->TopK188 staged input stayed bitwise equal to invocation0',
    later_observation='invocation2/3: TopK188/GatherElements192/TopK437 content changes, but ScatterND582/649 staged inputs and complete model outputs remain equal to first',
    root_cause_proven=False,numerical_accepted=False,performance_accepted=False,stage_acceptance_generated=False,
    agent_activity='Local file and SDK documentation audit only; no model rerun, device access or runtime source change.')
report_path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['returned_files_verified','package_files_verified','content_records','content_bytes','cpu_reference_values','earliest_observed_nonresponse','later_observation']},indent=2))

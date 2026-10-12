"""Independent restricted NumPy reference from unchanged adapted attributes/RAW.

Only exactly representable finite FP16/TF32 inputs are supported. This does not
emulate undocumented NPU rounding, instructions, MMU, or DMA completion.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-reference-20261011-r2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert np.__version__=='2.2.5' and sys.version_info[:2]==(3,10)
b=json.loads((E/'transfer/build-result.json').read_text());models=E/'transfer/models'
for name,x in b['models'].items():assert sha(models/name)==x['sha256']
graphs={n:json.loads((models/('piw24_'+n+'.json')).read_text()) for n in ('ZG','adapted','optimized')}
hard={o['op_id']:o for o in graphs['ZG']['ops']};adapt={o['op_id']:o for o in graphs['adapted']['ops']};opt={o['op_id']:o for o in graphs['optimized']['ops']}
baseline=json.loads((R/'tools/pose-v1/mixed-fusion-baseline.json').read_text())
members=[8174,8507,8626,8627,8628,8629,8630,8631,8655,8656,8797,8798,8799,8800,8801,8802,9074,9126,9127]
assert next(g['members'] for g in baseline['groups'] if g['effective_op_id']==9186)==members
assert b['models']['piw24_ZG.json']['sha256']==baseline['graph_sha256'] and b['models']['piw24_ZG.raw']['sha256']==baseline['raw_sha256']
assert len(members)==19 and sum(hard[i]['layer_count'] for i in members)==11
order=[o['op_id'] for o in graphs['ZG']['ops'] if o['op_id'] in members]
soft=[adapt[hard[i]['origin_ops_id'][0]] for i in order]
mapping=[]
def signature(v):return {k:v[k] for k in ('v_id','dtype')}
for i,o in zip(order,soft):
    h=hard[i];assert len(h['origin_ops_id'])==1 and h['name']==o['_type_key']+'Node'
    assert [signature(v) for v in h['outputs']]==[signature(v) for v in o['outputs']]
    assert [signature(v) for v in h['inputs']+h['params']]==[signature(v) for v in o['inputs']]
    mapping.append({'HardOp':i,'adapted_op':o['op_id'],'type':o['_type_key'],'layers':h['layer_count']})
root=E/'raw-return/run-raw';p=root/'parameters'
rows=[json.loads(x) for x in (root/'parameters.jsonl').read_text().splitlines()]
assert rows[-1]['md5_checked'] and len(rows)==23
for x in rows[:-1]:
    kind='ZG' if x['file'].startswith('ZG-') else x['file'].split('-')[0]
    contents=(p/x['file']).read_bytes();assert len(contents)==x['bytes']
    if x['bytes']:
        raw=models/('piw24_'+kind+'.raw')
        with raw.open('rb') as f:f.seek(x['lazy_offset']);assert f.read(x['bytes'])==contents
    x['sha256']=sha(p/x['file'])
weight=np.fromfile(p/'ZG-8507-weight-0.bin',dtype='<f2').reshape(1,3,16,1)
assert (p/'ZG-8507-weight-0.bin').read_bytes()==(p/'adapted-weight.bin').read_bytes()
assert np.array_equal(weight.reshape(48),np.r_[np.ones(42,dtype='<f2'),np.zeros(6,dtype='<f2')])
plain_weight=np.fromfile(p/'optimized-weight.bin',dtype='<f4').reshape(1,1,42)
assert np.array_equal(plain_weight,np.ones((1,1,42),dtype='<f4'))
assert opt[189]['shape']==[1,100,1] and opt[673]['inputs'][0]['v_id']==488 and opt[673]['outputs'][0]['v_id']==1786
assert opt[192]['axis']==1 and [v['v_id'] for v in opt[192]['inputs']]==[478,1786]
assert adapt[3414]['cut_scale']=='@scales([axis=-1])'
assert adapt[3406]['aligned_units']==[{'_type_key':'icraft::xir::AlignedUnit','index':[1],'unit':[112]}]
assert adapt[3410]['begin']==[0,0,0] and adapt[3410]['end']==[1,100,1] and adapt[3410]['stride']==[1,1,1]
assert all(adapt[i]['dims']==[0,2,1,3] for i in (3416,3422))
assert all(adapt[i]['index']==[-1] for i in (3418,3424))
assert hard[8507]['params'][0]['dtype']['layout']=='@layout(IOo16i1)'
assert hard[8628]['inputs'][0]['dtype']['layout']=='@layout(*C*c16)'
header=(R/'.local/pose-v1-build/producer-raw-20261011-r2/data_type.h').read_text(encoding='utf-8')
assert 'TF32_SEM = { 127, -126, 11, 19 }' in header and 'FP16_SEM = { 15, -14, 11, 16 }' in header
assert sys.argv[1:] in ([],['--replay'])
replay=bool(sys.argv[1:]);out=E/('patterns-replay' if replay else 'patterns');assert not out.exists();out.mkdir()
def bit_equal(a,b):return a.shape==b.shape and a.dtype==b.dtype and a.tobytes()==b.tobytes()
def exact_cast(a,dtype):
    e=dtype['element_dtype'];storage=e if isinstance(e,str) else e['storage_dtype']
    if isinstance(e,dict):assert e['scale']=='@scales([axis=-1])' and e['zero_points']==[]
    if storage=='@fp(16)':
        z=a.astype('<f2');assert np.array_equal(z.astype('<f4'),a.astype('<f4'));return z
    assert storage in ('@fp(32)','@tf(32)')
    z=a.astype('<f4')
    if storage=='@tf(32)':assert np.all((z.view('<u4') & 0x1fff)==0),'Only TF32-exact patterns accepted'
    return z
def evaluate(index,data):
    values={486:index.copy(),478:data.copy(),8458:weight.copy()};trace=[]
    for o in soft:
        inputs=[values[v['v_id']] for v in o['inputs']];kind=o['_type_key'].split('::')[-1];dt=o['outputs'][0]['dtype']
        if kind=='Cast':z=exact_cast(inputs[0],dt)
        elif kind=='AlignAxis':z=np.pad(inputs[0],((0,0),(0,12)))
        elif kind=='Reshape':z=inputs[0].reshape(o['shape'])
        elif kind=='Slice':z=inputs[0][tuple(slice(a,b,c) for a,b,c in zip(o['begin'],o['end'],o['stride']))]
        elif kind=='Matmul':
            # IOo16i1 declares [input_outer,output_outer,output_inner,input_inner].
            k=inputs[1].transpose(0,3,1,2).reshape(1,1,48)
            z=np.matmul(inputs[0].astype('<f4'),k.astype('<f4')).astype('<f2')
            z=z.reshape(1,100,3,16).transpose(0,2,1,3).reshape(3,100,16)
        elif kind=='Transpose':z=inputs[0].transpose(o['dims'])
        elif kind=='PruneAxis':
            assert o['inputs'][0]['dtype']['merged_distrs']==['@merged_distr([2]^ZERO:{v:[0, 42), u:[42, 48)})']
            z=inputs[0][:,:,:42].copy()
        else:raise AssertionError('Unsupported actual op '+kind)
        assert list(z.shape)==dt['shape'] and np.isfinite(z).all()
        values[o['outputs'][0]['v_id']]=z
        trace.append({'op':o['op_id'],'shape':list(z.shape),'logical_numpy_dtype':str(z.dtype),'bytes_sha256':hashlib.sha256(z.tobytes()).hexdigest()})
    return values[4386],values[4390],trace
reports=[]
for n in range(2):
    case=out/('pattern-'+str(n));case.mkdir()
    indices=(np.arange(100) if n==0 else 179-np.arange(100)).astype('<f4').reshape(1,100)
    data=np.empty((1,3,180,16),dtype='<f2')
    for block in range(3):
        for row in range(180):
            for lane in range(16):
                channel=block*16+lane
                value=((row*13+channel*7+n*101)%701+1)/8
                data[0,block,row,lane]=value if channel<42 else 200+lane/8
    a,bout,trace=evaluate(indices,data)
    # Separate scalar address walk and original optimized Matmul as two oracles.
    scalar=np.empty((1,180,42),dtype='<f4')
    for row in range(180):
        for channel in range(42):scalar[0,row,channel]=data[0,channel//16,row,channel%16]
    original=np.matmul(indices.reshape(1,100,1),plain_weight)
    assert bit_equal(a,scalar) and bit_equal(bout,original)
    assert np.array_equal(bout,np.repeat(indices[:,:,None],42,axis=2))
    for name,arr in [('input-486.f32',indices),('input-478.f16',data),('output-4386.f32',a),('output-4390.f32',bout)]:arr.tofile(case/name)
    reports.append({'pattern':n,'FP32_output_values':a.size+bout.size,'oracle_bitwise_equal':True,'files':{f.name:{'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(case.iterdir())},'logical_trace':trace})
assert (out/'pattern-0/output-4386.f32').read_bytes()!=(out/'pattern-1/output-4386.f32').read_bytes()
assert (out/'pattern-0/output-4390.f32').read_bytes()!=(out/'pattern-1/output-4390.f32').read_bytes()
result={'status':'restricted_original_group_math_reference_closed_hardware_contract_pending','mapping':mapping,'parameters':rows[:-1],'patterns':reports,'FP32_values_verified':23520,'python':sys.version,'numpy':np.__version__,'actual_weight_valid_ones':42,'actual_weight_padding_zeros':6,'instruction_bytes':sum(x['bytes'] for x in rows[:-1] if x['role']=='instr'),'models':b['models'],'raw_review_sha256':sha(E/'raw.review.json'),'SDK_semantics_header_sha256':sha(R/'.local/pose-v1-build/producer-raw-20261011-r2/data_type.h'),'reference_scope':'two exactly representable patterns; TF32 intermediate arrays are logical FP32, not physical encoded TF32 storage','independent_MMU_sync_contract_closed':False,'NPU_executed':False,'root_cause_resolved':False}
if replay:
    for f in out.rglob('*'):
        if f.is_file():assert f.read_bytes()==(E/'patterns'/f.relative_to(out)).read_bytes()
    result['replay_bitwise_equal']=True
(E/('reference-replay.json' if replay else 'reference-review.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print('19 mapped ops, true weight verified, two patterns:',result['FP32_values_verified'],'FP32 oracle values bitwise; NPU not executed')

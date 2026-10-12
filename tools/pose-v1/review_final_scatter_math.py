"""Independent NumPy NONE oracle from real RAW and actual failed Host inputs; no device."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
o=a.results;source=o/'final-output-source-readback';idx=g.load(source/'index.json');inv=idx['invocation'];gold=g.ROOT/'tools/pose-v1/evidence/runtime-20261007-r2/n1';g.verify(gold);records=[]
loaded=[json.loads(x) for x in (o/'engine/host-parameters.jsonl').read_text().splitlines()]
for op in [582,649]:
    parameter=o/f'engine/op{op}.param1.f32';blob=parameter.read_bytes();assert len(blob)==50400 and blob==(gold/f'results/op{op}.param1.f32').read_bytes()
    assert next(x for x in loaded if x['op_id']==op)['loaded_from_real_RAW']
    raw=np.frombuffer(blob,dtype='<f4').reshape(-1,3);assert np.isfinite(raw).all() and np.array_equal(raw,np.trunc(raw));indices=raw.astype(np.int64);assert ((indices>=0)&(indices<np.array([100,14,3]))).all()
    data=np.fromfile(source/f'host.{op}.0.f32',dtype='<f4').reshape(100,14,3);updates=np.fromfile(source/f'host.{op}.1.f32',dtype='<f4');assert len(updates)==4200
    expected=data.copy()
    for position,value in zip(indices,updates):expected[tuple(position)]=value
    target=source/'cpu.582.0.f32' if op==582 else o/f'result{inv}.poses.f32';actual=np.fromfile(target,dtype='<f4').reshape(100,14,3)
    assert np.array_equal(expected.view('<u4'),actual.view('<u4'))
    records.append(dict(op=op,parameter_SHA256=hashlib.sha256(blob).hexdigest(),real_RAW_dump_bytes=len(blob),golden_parameter_identical=True,indices_finite_integer_in_bounds=True,unique_coordinate_count=len(set(map(tuple,indices))),FP32_compared=4200,NumPy_FROM_ACTUAL_bad_inputs_bitwise=True,comparison_target='owned CPU output before writeback' if op==582 else 'final poses; not a separately captured649 CPU output'))
a.output.write_text(json.dumps(dict(status='independent_ScatterND_NONE_from_actual_bad_inputs_passed_not_deployment_acceptance',invocation=inv,records=records,SDK_math_not_reimplemented_in_product=True,root_cause_proven=False),indent=2)+'\n',encoding='utf-8',newline='\n');print('Actual bad inputs and real RAW: 8400 FP32 independently match')

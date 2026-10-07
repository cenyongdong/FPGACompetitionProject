"""Compare captured real Host inputs/results with independent NumPy operations."""
import argparse
from pathlib import Path
import numpy as np
from mixed_validation_gate import verify,load,save
from host_content_review import review_mixed

def review(results,package):
    verify(results);verify(package)
    out=results/'results';config=load(out/'run-config.json')
    calls=[('S11_01_308',6)] if config['cases']=='one' else [
        ('S11_01_308',6),('S11_01_309',7),('S11_01_310',8),('S11_01_308',6)]
    records=review_mixed(out,package/'reference',calls)
    raw={(r['invocation'],r['kind'],r['op_id'],r['slot']):(out/'content'/r['file']).read_bytes() for r in records}
    ops={op['op_id']:op for op in load(package/'graph/piw24_ZG.json')['ops']}
    checks=[]
    for inv in range(len(calls)):
        for opid in (188,192,437,582,649):
            op=ops[opid];args=[];runtime_slot=0
            for i,v in enumerate(op['inputs']):
                if v['_type_key'].endswith('Params'):
                    value=(out/f'op{opid}.param{i}.f32').read_bytes()
                else:
                    value=raw[inv,'bridge_input',opid,runtime_slot];runtime_slot+=1
                args.append(np.frombuffer(value,dtype='<f4').reshape(v['dtype']['shape']))
            if opid in (188,437):
                idx=np.argsort(-args[0],axis=op['axis'],kind='stable')
                selection=[slice(None)]*idx.ndim;selection[op['axis']]=slice(0,int(args[1].flat[0]))
                idx=idx[tuple(selection)]
                expected=[np.take_along_axis(args[0],idx,axis=op['axis']),idx.astype('<f4')]
            elif opid==192:
                assert np.array_equal(args[1],np.trunc(args[1]))
                expected=[np.take_along_axis(args[0],args[1].astype(np.int64),axis=op['axis'])]
            else:
                assert np.array_equal(args[1],np.trunc(args[1]))
                idx=args[1].astype(np.int64);actual=args[0].copy()
                assert np.unique(idx.reshape(-1,3),axis=0).shape[0]==4200
                actual[tuple(idx[...,axis] for axis in range(3))]=args[2]
                expected=[actual]
            for slot,value in enumerate(expected):
                assert value.astype('<f4').tobytes()==raw[inv,'bridge_result',opid,slot],(inv,opid,slot)
                checks.append(dict(invocation=inv,op_id=opid,slot=slot,elements=value.size,bitwise_equal=True))
    return dict(status='real_captured_CPU_results_match_NumPy',checks=checks,
                total_values=sum(x['elements'] for x in checks),Gather442_content_verified=False,
                full_model_numerical_accepted=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('results','package','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();save(a.output,review(a.results,a.package))
    print('Actual captured Host results are bitwise equal to independent NumPy reference.')

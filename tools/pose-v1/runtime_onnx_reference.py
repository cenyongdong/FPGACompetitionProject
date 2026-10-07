"""27 locked real inputs and first repeat in the existing CPU ORT environment."""
import argparse
import platform
from pathlib import Path
import shutil
import sys
import time
import numpy as np
import onnxruntime as ort
from mixed_validation_gate import verify,load,save,sha,checksum,need

def run(a):
    verify(a.package);m=load(a.package/'manifest.json');cases=m['expanded_cases']
    need(len(cases)==27 and platform.python_version()=='3.10.21' and np.__version__=='2.2.5' and ort.__version__=='1.23.2','Locked environment changed')
    need(Path(sys.prefix).resolve()==Path('.local/pose-v1-onnx-conda').resolve(),'Wrong Conda environment')
    need(sha(a.model)=='7b04090e374e31e016d5703bbcf1d0a561d0b98f268fde984b0bf0461598bd21','ONNX changed')
    options=ort.SessionOptions();options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
    options.intra_op_num_threads=1;options.inter_op_num_threads=1;options.graph_optimization_level=ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    begin=time.perf_counter();session=ort.InferenceSession(str(a.model),sess_options=options,providers=['CPUExecutionProvider']);init=(time.perf_counter()-begin)*1000
    need(session.get_providers()==['CPUExecutionProvider'],'Unexpected provider')
    inputs=session.get_inputs();outputs=session.get_outputs()
    need(len(inputs)==1 and inputs[0].shape==[1,180,60] and inputs[0].type=='tensor(float)' and len(outputs)==2,'ORT interface')
    score=[o for o in outputs if o.shape==[1,100] and o.type=='tensor(float)'];pose=[o for o in outputs if o.shape==[1,100,14,3] and o.type=='tensor(float)']
    need(len(score)==len(pose)==1,'ORT output order/shape')
    need(not a.output.exists(),'Preserve ONNX outputs');a.output.mkdir(parents=True)
    rows=[];first=None
    for inv,c in enumerate(cases+[cases[0]]):
        name=c['case'];src=a.package/'reference'/(name+'.input.f32');raw=src.read_bytes()
        need(sha(src)==c['reference_sha256'],'Fixed input differs');tokens=np.frombuffer(raw,dtype='<f4').reshape(1,180,60);need(np.isfinite(tokens).all(),'Input finite')
        begin=time.perf_counter();s,p=session.run([score[0].name,pose[0].name],{inputs[0].name:tokens});elapsed=(time.perf_counter()-begin)*1000
        need(s.shape==(1,100) and p.shape==(1,100,14,3) and np.isfinite(s).all() and np.isfinite(p).all(),'ORT output finite/shape')
        data=(s.astype('<f4').tobytes(),p.astype('<f4').tobytes())
        if inv==0:first=data
        repeat=inv==27
        if repeat:need(data==first,'ORT first repeat is not bitwise reproducible')
        stem=name+('.repeat' if repeat else '')
        for kind,b in zip(('scores','poses'),data):(a.output/(stem+'.'+kind+'.f32')).write_bytes(b)
        if not repeat:shutil.copyfile(src,a.output/(name+'.input.f32'))
        rows.append(dict(case=name,frame_id=c['frame_id'],source_time_ns=c['source_time_ns'],invocation=inv,repeat=repeat,forward_ms=elapsed,top_index=int(np.argmax(s)),top_score=float(s.max())))
    import json
    (a.output/'results.jsonl').write_bytes(''.join(json.dumps(r,allow_nan=False)+'\n' for r in rows).encode())
    save(a.output/'environment.json',dict(python=platform.python_version(),numpy=np.__version__,onnxruntime=ort.__version__,prefix=sys.prefix,providers=session.get_providers(),
        execution_mode='ORT_SEQUENTIAL',intra_op_threads=1,inter_op_threads=1,graph_optimization='ORT_ENABLE_ALL',model_sha256=sha(a.model),
        package_manifest_sha256=sha(a.package/'manifest.json'),runner_sha256=sha(Path(__file__)),session_init_ms=init))
    save(a.output/'summary.json',dict(unique_cases=27,forward_calls=28,finite_FP32_values=116100,repeated_first_bitwise_equal=True,numerical_accepted=False,ground_truth_evaluated=False))
    checksum(a.output);print('ORT27 and repeat completed:',verify(a.output))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('package','model','output'):p.add_argument('--'+k,type=Path,required=True)
    run(p.parse_args())

"""Independent offline review of existing ORT27 and association to a new package."""
import argparse
from pathlib import Path
import platform
import struct
import sys
import numpy as np
import onnxruntime as ort
from mixed_validation_gate import load,lines,verify,sha,save,need

def review(a):
    files=verify(a.reference);verify(a.package);env=load(a.reference/'environment.json');m=load(a.package/'manifest.json')
    original=Path('.local/pose-v1-runtime/package-20261006-e0-n1-p1-r1');verify(original)
    need(env['package_manifest_sha256']==sha(original/'manifest.json'),'Original reference package identity')
    expected=dict(python='3.10.21',numpy='2.2.5',onnxruntime='1.23.2',providers=['CPUExecutionProvider'],execution_mode='ORT_SEQUENTIAL',intra_op_threads=1,inter_op_threads=1,graph_optimization='ORT_ENABLE_ALL',model_sha256='7b04090e374e31e016d5703bbcf1d0a561d0b98f268fde984b0bf0461598bd21')
    need(all(env.get(k)==v for k,v in expected.items()),'ORT settings changed')
    need(platform.python_version()==expected['python'] and np.__version__==expected['numpy'] and ort.__version__==expected['onnxruntime'],'Current versions')
    prefix=Path('.local/pose-v1-onnx-conda').resolve()
    need(Path(sys.prefix).resolve()==Path(env['prefix']).resolve()==prefix and all(Path(v.__file__).resolve().is_relative_to(prefix) for v in (np,ort)),'Environment leakage')
    cases=m['expanded_cases'];need(cases==load(original/'manifest.json')['expanded_cases'] and len(cases)==27,'Selection changed')
    rows=lines(a.reference/'results.jsonl');need(len(rows)==28,'ORT calls')
    totals=0;signatures=set()
    for inv,c in enumerate(cases+[cases[0]]):
        r=rows[inv];need(all(r[k]==c[k] for k in ('case','frame_id','source_time_ns')) and r['invocation']==inv and r['repeat']==(inv==27),'ORT frame labels')
        need(np.isfinite(r['forward_ms']) and r['forward_ms']>=0,'ORT timing')
        name=c['case'];raw=a.package/'inputs'/(name+'.csi');gold=a.package/'reference'/(name+'.input.f32')
        need(sha(raw)==c['raw_sha256'] and sha(gold)==c['reference_sha256'],'New package input identity')
        header=raw.read_bytes()[:32];need(struct.unpack('<8sIIQQ',header)==(b'PIWCSI1\0',1,86400,c['frame_id'],c['source_time_ns']),'CSI header')
        need((a.reference/(name+'.input.f32')).read_bytes()==gold.read_bytes()==(original/'reference'/(name+'.input.f32')).read_bytes(),'ORT/new/old input equality')
        stem=name+('.repeat' if inv==27 else '');output=[]
        for kind,size in [('scores',100),('poses',4200)]:
            raw=(a.reference/(stem+'.'+kind+'.f32')).read_bytes();v=np.frombuffer(raw,dtype='<f4')
            need(v.size==size and np.isfinite(v).all(),'Output shape/finite');output.append(sha(a.reference/(stem+'.'+kind+'.f32')))
            if inv==27:need(raw==(a.reference/(name+'.'+kind+'.f32')).read_bytes(),'ORT repeat bytes')
            if inv<27:totals+=v.size
        scores=np.frombuffer((a.reference/(stem+'.scores.f32')).read_bytes(),dtype='<f4')
        need(r['top_index']==int(np.argmax(scores)) and r['top_score']==float(scores.max()),'ORT selection metadata');signatures.add(tuple(output))
    for kind in ('input','scores','poses'):
        need((a.reference/('S11_01_308.'+kind+'.f32')).read_bytes()==(Path('.local/pose-v1-mixed-validation/onnx-20261006')/('S11_01_308.'+kind+'.f32')).read_bytes(),'Existing independent308 reference differs')
    need(totals==116100 and len(signatures)>1 and files==86,'Reference scope')
    save(a.output,dict(status='existing_ORT27_independently_verified',reference_files_verified=files,unique_cases=27,forward_calls=28,finite_values=totals,distinct_output_count=len(signatures),
        old_package_manifest_sha256=sha(original/'manifest.json'),new_package_manifest_sha256=sha(a.package/'manifest.json'),reference_environment_sha256=sha(a.reference/'environment.json'),
        reference_reused_without_rerun_or_metadata_change=True,repeated_first_bitwise_equal=True,existing308_bitwise_equal=True,current_module_paths={x.__name__:x.__file__ for x in (np,ort)},numerical_board_accepted=False))
    print('ORT27 independently reviewed; unchanged inputs/model allow reference reuse.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('reference','package','output'):p.add_argument('--'+k,type=Path,required=True)
    review(p.parse_args())

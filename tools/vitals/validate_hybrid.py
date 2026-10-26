"""Independent receiver math and fixed-ACF regressions; no device operations."""
import argparse,json,subprocess
from pathlib import Path
import numpy as np
from align_nexmon_phase import align_phase
from signal_fixtures import cases
from run_receiver_vitals import export_raw

def run(binaries,reference,output):
    output.mkdir(parents=True,exist_ok=False);suffix='.exe' if (binaries/'vitals_offline.exe').exists() else ''
    def call(name,args,label):
        command=[str((binaries/(name+suffix)).resolve()),*map(str,args)]
        p=subprocess.run(command,capture_output=True,text=True,timeout=120)
        (output/(label+'-process.json')).write_text(json.dumps(dict(command=command,exit=p.returncode,stdout=p.stdout if name!='vitals_receiver_vectors' else 'saved in receiver-vectors.csv',stderr=p.stderr),indent=2))
        if p.returncode:raise RuntimeError(label+' failed')
        return p.stdout
    comparisons=[]
    for name,_,expected in cases():
        result=output/(name+'.json');call('vitals_offline',['--input',reference/(name+'.csv'),'--output',result,'--correlation-backend','fixed-reference'],name)
        a=json.loads((reference/(name+'.json')).read_text());b=json.loads(result.read_text())
        same=a['status']==b['status']
        difference={}
        for part in ('heart','breath'):
            same &= (a[part] is None)==(b[part] is None)
            if a[part] and b[part]:
                difference[part]=abs(a[part]['bpm']-b[part]['bpm']);same &= difference[part]<.01
        comparisons.append(dict(name=name,passed=bool(same),difference_bpm=difference))
    trace=call('vitals_receiver_vectors',[],'receiver-vectors');(output/'receiver-vectors.csv').write_text(trace)
    raw=np.asarray([[float(v) for v in line.split(',')[1:]] for line in trace.splitlines() if line.startswith('R,')])
    native=np.asarray([[float(v) for v in line.split(',')[1:]] for line in trace.splitlines() if line.startswith('P,')])
    times=raw[:,0].astype(np.int64);arrays,quality=align_phase(times,raw[:,1:]);error=float(np.max(abs(native[:,1:]-arrays['phase'])))
    math=dict(samples=len(native),max_phase_error_rad=error,passed=bool(np.array_equal(native[:,0].astype(np.int64)-times[0],arrays['grid_ns']) and arrays['valid'].all() and error<5e-9))
    # Exercise real CLI, provenance, backend choice, source end and CSV portability.
    pairs=np.stack([np.exp(1j*raw[:,1:]),np.ones_like(raw[:,1:])],axis=-1)
    csv=output/'raw.csv';export_raw(csv,times,pairs,origin='synthetic')
    csv.write_bytes(b'\xef\xbb\xbf'+csv.read_bytes().replace(b'\n',b'\r\n'))
    rows_by_backend={};stream_checks=[]
    for backend in ('cpu','fixed-reference'):
        path=output/(backend+'-stream.jsonl');call('vitals_phase_stream',['--input',csv,'--output',path,'--backend',backend],backend+'-stream')
        rows=[json.loads(line) for line in path.read_text().splitlines()];hr=[r for r in rows if r['heart_bpm'] is not None];rows_by_backend[backend]=hr
        stream_checks.append(dict(backend=backend,candidates=len(hr),passed=bool(len(hr)==2 and all(abs(r['heart_bpm']-72)<1 for r in hr) and rows[-1]['status']=='source_ended' and rows[-1]['buffered']==0 and rows[-1]['heart_bpm'] is None)))
    result=dict(fixed_pipeline=comparisons,independent_resampler=math,raw_cli=stream_checks,
        passed=bool(all(r['passed'] for r in comparisons+stream_checks) and math['passed']),hardware_accessed=False)
    (output/'summary.json').write_text(json.dumps(result,indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binaries',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=run(a.binaries,a.reference,a.output);print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)

"""Archived NMD2/3 -> explicit derived phase -> bounded C++ vitals stream.

Reuses the established decoder, pairing, source quality and anti-alias adapter.
No fake IQ, clock certification, sample padding, radio changes or board access.
"""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np
from align_nexmon_phase import run as align

def export_phase(arrays, destination, origin='real_capture'):
    clock='derived_relative_rx' if origin=='real_capture' else 'synthetic_uniform'
    with Path(destination).open('x',encoding='utf-8',newline='\n') as out:
        out.write(f'# origin={origin}\n# clock={clock}\n')
        out.write('# clock_evidence=NMD relative RX time; interpolation plus measured FIR support; not RF certification\n')
        out.write('session,time_ns,sequence,source_support_valid,p0,p1,p2,p3\n')
        for i,(stamp,phase,valid) in enumerate(zip(arrays['grid_ns'],arrays['phase'],arrays['valid'])):
            out.write(f'1,{int(stamp)},{i+1},{int(np.all(valid))},'+','.join(format(float(v),'.17g') for v in phase)+'\n')

def run(pcap, output, executable, backend='cpu'):
    report=align(pcap,output)
    with np.load(output/'phase-arrays.npz') as arrays:export_phase(arrays,output/'derived-phase.csv')
    command=[str(executable.resolve()),'--input',str((output/'derived-phase.csv').resolve()),'--output',str((output/'vitals.jsonl').resolve()),'--backend',backend]
    proc=subprocess.run(command,capture_output=True,text=True,timeout=120)
    (output/'native-process.json').write_text(json.dumps(dict(command=command,exit=proc.returncode,stdout=proc.stdout,stderr=proc.stderr),indent=2))
    if proc.returncode:raise RuntimeError('Native stream failed; preserved process result')
    rows=[json.loads(s) for s in (output/'vitals.jsonl').read_text().splitlines()]
    candidates=[r for r in rows if r['heart_bpm'] is not None]
    result=dict(schema=1,source=str(pcap.resolve()),hardware_accessed=False,backend=backend,
                source_events=report['source_events'],source_seconds=report['source_relative_rx_span_seconds'],
                emitted_states=len(rows),candidate_windows=len(candidates),
                candidates_are_verified_measurements=False,synchronized_reference=False,
                final_state=rows[-1],quality=report['alignment']['windows'])
    (output/'vitals-summary.json').write_text(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pcap',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--executable',type=Path,required=True)
    p.add_argument('--backend',choices=['cpu','fixed-reference'],default='cpu');a=p.parse_args()
    print(json.dumps(run(a.pcap,a.output,a.executable,a.backend),indent=2))

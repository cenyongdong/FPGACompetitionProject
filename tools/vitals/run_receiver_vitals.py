"""One archived NMD capture -> same-packet raw pairs -> bounded native receiver.

Uses the existing first-valid decoder and a single physical RX clock segment.
Never joins segments, invents IQ, certifies a sampling clock, or repairs jumps.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import numpy as np
from audit_nexmon_vitals import CARRIERS, PAIRS, load_segment, save, describe
from native_carriers import decode_selected


def export_raw(path, times, pairs, sequences=None, session=1, origin='real_capture'):
    clock='relative_rx' if origin=='real_capture' else 'synthetic_uniform'
    if sequences is None:sequences=np.arange(1,len(times)+1)
    with Path(path).open('x',encoding='utf-8',newline='\n') as out:
        out.write(f'# origin={origin}\n# clock={clock}\n')
        out.write('# clock_evidence=source relative RX timestamps; not uniform RF sampling certification\n')
        out.write('session,time_ns,sequence,valid'+''.join(f',{p}{c}' for c in range(4) for p in ('ia','qa','ib','qb'))+'\n')
        for stamp,seq,row in zip(times,sequences,pairs):
            values=[]
            for a,b in row:values.extend((a.real,a.imag,b.real,b.imag))
            valid=int(np.isfinite(row).all() and (np.abs(row)>1e-12).all())
            out.write(f'{session},{int(stamp)},{int(seq)},{valid},'+','.join(format(float(v),'.17g') for v in values)+'\n')


def select_features(events,calibration_seconds):
    """Freeze four unique features using only prefix stability, never target HR.

    This is an experimental source-quality selector, not a physiological rank.
    The calibration prefix is excluded from the subsequent estimation history.
    """
    words=np.asarray([e.words for e in events]).copy()
    if any(e.original_words is None for e in events):raise ValueError('NMD originals required for occupied carriers')
    words[:,:,28:31]=np.asarray([e.original_words for e in events])
    bins=np.r_[np.arange(-28,0),np.arange(1,29)]%64
    iq=decode_selected(words[:,:,bins]);t=np.asarray([e.time_us-events[0].time_us for e in events])/1e6
    end=int(np.searchsorted(t,calibration_seconds))
    if end<100 or end==len(events):raise ValueError('Insufficient measured calibration/evaluation context')
    features=[]
    for a,b in ((0,1),(0,2),(1,2)):
        wrapped=np.angle(iq[:end,a]*iq[:end,b].conj())
        steps=abs(np.angle(np.exp(1j*np.diff(wrapped,axis=0))))
        for index,carrier in enumerate(bins):
            prefix=iq[:end,[a,b],index]
            if not np.isfinite(prefix).all() or (abs(prefix)<1e-12).any():continue
            features.append(dict(pair=[a,b],carrier=int(carrier),index=index,
                jumps=int((steps[:,index]>.25).sum()),step_p95_rad=float(np.percentile(steps[:,index],95))))
    features.sort(key=lambda f:(f['jumps'],f['step_p95_rad'],f['pair'],f['carrier']))
    if len(features)<4:raise ValueError('Insufficient valid source features')
    chosen=features[:4]
    pairs=np.stack([iq[end:,[*f['pair']],f['index']] for f in chosen],axis=1)
    profile=dict(calibration_seconds=calibration_seconds,calibration_events=end,
        evaluation_start_seconds=float(t[end]),carriers=[f['carrier'] for f in chosen],
        pairs=[f['pair'] for f in chosen],ranking=chosen,
        selection='prefix-only jump count then step p95; frozen; no HR or reference used',
        physiological_sensitivity_validated=False)
    return events[end:],pairs,profile


def run(pcap,output,executable,backend='cpu',calibration_seconds=0):
    output.mkdir(parents=True,exist_ok=False)
    events,state,groups=load_segment(pcap)
    if any('event_phy0' in e.meta for e in events):raise ValueError('Experimental NMD4 is outside this NMD2/3 receiver profile')
    if calibration_seconds:events,pairs,features=select_features(events,calibration_seconds)
    else:
        iq=decode_selected(np.asarray([e.words for e in events])[:,:,CARRIERS])
        pairs=np.stack([iq[:,[a,b],ch] for ch,(a,b) in enumerate(PAIRS)],axis=1)
        features=dict(carriers=CARRIERS,pairs=PAIRS,selection='diagnostic fixed profile; not validated HR-sensitive features')
    times=np.asarray([(e.time_us-events[0].time_us)*1000 for e in events],dtype=np.uint64)
    export_raw(output/'receiver.csv',times,pairs,[e.index+1 for e in events],events[0].segment+1)
    command=[str(executable.resolve()),'--input',str((output/'receiver.csv').resolve()),'--output',str((output/'vitals.jsonl').resolve()),'--backend',backend]
    proc=subprocess.run(command,capture_output=True,text=True,timeout=120)
    save(output/'native-process.json',dict(command=command,exit=proc.returncode,stdout=proc.stdout,stderr=proc.stderr))
    if proc.returncode:raise RuntimeError('Native receiver failed; inspect preserved process result')
    rows=[json.loads(s) for s in (output/'vitals.jsonl').read_text().splitlines()]
    candidates=[r for r in rows if r['heart_bpm'] is not None]
    wrapped=np.angle(pairs[:,:,0]*pairs[:,:,1].conj())
    steps=np.abs(np.angle(np.exp(1j*np.diff(wrapped,axis=0))))
    faults=(steps>.25).any(axis=1)|(np.diff(times)>10_000_000)
    boundaries=np.r_[0,np.flatnonzero(faults)+1,len(events)]
    longest=max(float(times[b-1]-times[a])/1e9 for a,b in zip(boundaries[:-1],boundaries[1:]))
    result=dict(schema=1,source=str(pcap.resolve()),backend=backend,board_accessed=False,
        selected_segment=events[0].segment,selected_events=len(events),source_seconds=float(times[-1])/1e9,
        all_segments=[dict(segment=k,events=len(g),seconds=(g[-1].time_us-g[0].time_us)/1e6) for k,g in groups.items()],
        receiver_counts=state['counts'],interval_ms=describe(np.diff(times)/1e6),
        raw_phase_jumps_per_channel=(steps>.25).sum(axis=0).tolist(),
        source_gaps_over_10ms=int((np.diff(times)>10_000_000).sum()),
        longest_all_channel_source_run_s=longest,
        emitted_states=len(rows),analyzed_windows=sum(r['status'] in ('no_heart_estimate','candidate_unverified','valid') for r in rows),candidate_windows=len(candidates),
        candidate_heart_bpm=[r['heart_bpm'] for r in candidates],
        reason_counts=dict(Counter(reason for r in rows for reason in r['reasons'])),
        final_state=rows[-1],candidates_are_verified_measurements=False,
        synchronized_reference=False,features=features)
    save(output/'summary.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pcap',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--executable',type=Path,required=True)
    p.add_argument('--backend',choices=['cpu','fixed-reference'],default='cpu')
    p.add_argument('--calibrate-seconds',type=float,default=0);a=p.parse_args()
    if not 0<=a.calibrate_seconds<=30:raise ValueError('Calibration budget 0..30 seconds')
    print(json.dumps(run(a.pcap,a.output,a.executable,a.backend,a.calibrate_seconds),indent=2))

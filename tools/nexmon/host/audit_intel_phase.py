<<<<<<< HEAD
"""Read-only Intel raw/aligned phase audit; no model, radio or remote writes.

Remote execution streams this source and the existing Intel decoder over stdin.
Selection reuses the earlier fixed nine-group correspondence manifest, not flags.
=======
"""Read-only phase audit of Intel logs and their aligned MAT windows.

The remote mode streams this code and the existing Intel decoder into Python
memory over SSH. It creates no remote files and never runs a model or radio.
Only the existing fixed training-split correspondence sample is inspected.
>>>>>>> feat/model-refactor
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import shlex
import subprocess
<<<<<<< HEAD

import numpy as np
if 'read_intel' not in globals():
    from audit_intel_reference import read_intel

PAIRS=((0,1),(0,2),(1,2))
PHASE_LIMIT=.25
DISPERSION_LIMIT=.25
GAP_US=32768


def describe(x):
    x=np.asarray(x,dtype=float)
    return None if not x.size else dict(count=int(x.size),min=float(x.min()),
        median=float(np.median(x)),p99=float(np.quantile(x,.99)),max=float(x.max()))


def phase_metrics(csi,dt_us):
    if csi.ndim!=3 or csi.shape[1:]!=(3,30) or not np.isfinite(csi).all():
        raise ValueError('Require finite complex [frame,3,30] Intel CSI')
    dt=np.asarray(dt_us);clock_ok=(dt>0)&(dt<GAP_US)
    masks,rows=[],[]
    for a,b in PAIRS:
        positive=np.all(abs(csi[:,[a,b]])>0,axis=(1,2))
        eligible=positive[:-1]&positive[1:]&clock_ok
        phase=np.angle(csi[:,a]*csi[:,b].conj())
        delta=np.angle(np.exp(1j*np.diff(phase,axis=0)))
        circular=np.mean(np.exp(1j*delta),axis=1)
        center,coherence=np.angle(circular),abs(circular)
        dispersion=np.median(abs(np.angle(np.exp(1j*(delta-center[:,None])))),axis=1)
        affected=np.sum(abs(delta)>PHASE_LIMIT,axis=1)
        broad=eligible&(affected>=math.ceil(csi.shape[2]/2))&(dispersion<DISPERSION_LIMIT)
        returning=broad[:-1]&broad[1:]&(abs(np.angle(np.exp(1j*(center[:-1]+center[1:]))))<=.1)
        masks.append(broad)
        rows.append(dict(pair=[a,b],eligible_adjacent_steps=int(eligible.sum()),
            zero_value_ineligible_steps=int((~(positive[:-1]&positive[1:])).sum()),
            broadband_steps=int(broad.sum()),fraction_of_eligible=float(broad.sum()/eligible.sum()) if eligible.any() else None,
            step_abs_rad=describe(abs(center[broad])),across_tone_coherence=describe(coherence[broad]),
            near_pi_steps=int((broad&(abs(abs(center)-np.pi)<.15)).sum()),
            returning_adjacent_step_pairs=int(returning.sum()),
            first_flagged_row=int(np.flatnonzero(broad)[0]+1) if broad.any() else None))
    return rows,np.asarray(masks).T
=======
import sys

import numpy as np

if 'read_intel' not in globals():
    from audit_intel_reference import read_intel

PAIRS = ((0, 1), (0, 2), (1, 2))
PHASE_LIMIT = .25
DISPERSION_LIMIT = .25
GAP_US = 32768


def describe(x):
    x = np.asarray(x, dtype=float)
    if not x.size:
        return None
    return dict(count=int(x.size), min=float(x.min()), median=float(np.median(x)),
                p99=float(np.quantile(x, .99)), max=float(x.max()))


def phase_metrics(csi, dt_us):
    if csi.ndim != 3 or csi.shape[1:] != (3, 30) or not np.isfinite(csi).all():
        raise ValueError('Require finite complex [frame,3,30] Intel CSI')
    dt = np.asarray(dt_us)
    clock_ok = (dt > 0) & (dt < GAP_US)
    masks, rows = [], []
    for a, b in PAIRS:
        magnitude = abs(csi[:, [a, b]])
        positive = np.all(magnitude > 0, axis=(1, 2))
        eligible = positive[:-1] & positive[1:] & clock_ok
        phase = np.angle(csi[:, a] * csi[:, b].conj())
        delta = np.angle(np.exp(1j * np.diff(phase, axis=0)))
        circular = np.mean(np.exp(1j * delta), axis=1)
        center, coherence = np.angle(circular), abs(circular)
        dispersion = np.median(abs(np.angle(np.exp(1j*(delta-center[:, None])))), axis=1)
        affected = np.sum(abs(delta) > PHASE_LIMIT, axis=1)
        broad = eligible & (affected >= math.ceil(csi.shape[2]/2)) & (dispersion < DISPERSION_LIMIT)
        returning = broad[:-1] & broad[1:] & (abs(np.angle(np.exp(1j*(center[:-1]+center[1:])))) <= .1)
        near_pi = broad & (abs(abs(center)-np.pi) < .15)
        masks.append(broad)
        rows.append(dict(pair=[a,b], eligible_adjacent_steps=int(eligible.sum()),
            zero_value_ineligible_steps=int((~(positive[:-1]&positive[1:])).sum()),
            broadband_steps=int(broad.sum()), fraction_of_eligible=float(broad.sum()/eligible.sum()) if eligible.any() else None,
            step_abs_rad=describe(abs(center[broad])), across_tone_coherence=describe(coherence[broad]),
            near_pi_steps=int(near_pi.sum()), returning_adjacent_step_pairs=int(returning.sum()),
            first_flagged_row=int(np.flatnonzero(broad)[0]+1) if broad.any() else None))
    return rows, np.asarray(masks).T
>>>>>>> feat/model-refactor


def load_mat(path):
    import h5py
<<<<<<< HEAD
    with h5py.File(path,'r') as h:value=h['csi_out'][()]
    if value.shape!=(20,30,3,3) or not {'real','imag'}<=set(value.dtype.names or ()):
=======
    with h5py.File(path, 'r') as handle:
        value = handle['csi_out'][()]
    if value.shape != (20,30,3,3) or not {'real','imag'} <= set(value.dtype.names or ()):
>>>>>>> feat/model-refactor
        raise ValueError('Unexpected aligned MAT layout')
    return (value['real']+1j*value['imag']).transpose(3,2,1,0).astype('complex128')


<<<<<<< HEAD
def analyze(raw_root,repo,manifest):
    raw_reports,aligned_reports,witnesses=[],[],[]
    samples=sorted({m['sample'] for m in manifest['matches']})
    for session in manifest['sessions']:
        chosen=[n for n in samples if n.startswith(session+'_')]
        mats={n:load_mat(repo/'data/wifipose/train_data/csi'/(n+'.mat')) for n in chosen}
        for node in range(3):
            path=raw_root/('r'+str(node+1))/'data'/(session+'.dat')
            csi,meta=read_intel(path)
            ts=np.asarray([m['timestamp_low'] for m in meta],dtype='int64');dt=np.diff(ts)&0xffffffff
            rows,flags=phase_metrics(csi,dt)
            agc=np.asarray([m['agc'] for m in meta]);agc_change=np.diff(agc)!=0
            perm_change=np.any(np.diff(np.asarray([m['perm'] for m in meta]),axis=0)!=0,axis=1)
            rate_change=np.diff(np.asarray([m['rate'] for m in meta]))!=0
            bfee_step=np.diff(np.asarray([m['bfee_count'] for m in meta],dtype='int64'))&65535
            for k,row in enumerate(rows):
                mask=flags[:,k]
                row.update(agc_changes_at_flag=int(agc_change[mask].sum()),
                    rx_permutation_changes_at_flag=int(perm_change[mask].sum()),
                    rate_changes_at_flag=int(rate_change[mask].sum()),
                    bfee_count_gap_at_flag=int((bfee_step[mask]!=1).sum()))
            time_file=raw_root/('r'+str(node+1))/'time'/(session+'.txt')
            with time_file.open('r') as f:time_count=sum(bool(line.strip()) for line in f)
            raw_reports.append(dict(session=session,receiver=node+1,path=str(path),bytes=path.stat().st_size,
                frames=len(csi),positive_continuous_span_s=float(dt[(dt>0)&(dt<GAP_US)].sum()/1e6),
                clock_break_steps=int(((dt<=0)|(dt>=GAP_US)).sum()),interval_us=describe(dt[(dt>0)&(dt<GAP_US)]),
                timestamp_text_lines=time_count,timestamp_text_count_matches_frames=time_count==len(csi),
                agc_counts=dict(Counter(map(int,agc))),agc_change_steps=int(agc_change.sum()),
                permutation_change_steps=int(perm_change.sum()),rate_counts=dict(Counter(m['rate'] for m in meta)),
                any_pair_broadband_steps=int(flags.any(axis=1).sum()),pairs=rows))
            selected=[m for m in manifest['matches'] if m['node']==node and m['sample'] in chosen]
            for match in selected:
                name=match['sample'];ids=np.asarray(match['raw_packet_indices'],dtype=int)
                if len(ids)!=20 or np.any(np.diff(ids)<=0) or ids.min()<0 or ids.max()>=len(csi):
                    raise ValueError('Invalid prior correspondence indices')
                aligned=mats[name][node].transpose(2,0,1);exact=bool(np.array_equal(csi[ids],aligned))
                aligned_dt=np.asarray([(int(ts[b])-int(ts[a]))&0xffffffff for a,b in zip(ids,ids[1:])])
                mat_rows,mat_flags=phase_metrics(aligned,aligned_dt)
                retained=np.zeros_like(mat_flags);consecutive=np.diff(ids)==1
                retained[consecutive]=mat_flags[consecutive]&flags[ids[1:][consecutive]-1]
=======
def analyze(raw_root, repo, manifest):
    raw_reports, aligned_reports, witnesses = [], [], []
    samples = sorted({m['sample'] for m in manifest['matches']})
    for session in manifest['sessions']:
        chosen = [name for name in samples if name.startswith(session+'_')]
        mats = {name:load_mat(repo/'data/wifipose/train_data/csi'/(name+'.mat')) for name in chosen}
        for node in range(3):
            path = raw_root/('r'+str(node+1))/'data'/(session+'.dat')
            csi, meta = read_intel(path)
            ts = np.asarray([m['timestamp_low'] for m in meta], dtype='int64')
            dt = np.diff(ts) & 0xffffffff
            rows, flags = phase_metrics(csi, dt)
            agc = np.asarray([m['agc'] for m in meta])
            agc_change = np.diff(agc) != 0
            perm_change = np.any(np.diff(np.asarray([m['perm'] for m in meta]),axis=0) != 0,axis=1)
            rate_change = np.diff(np.asarray([m['rate'] for m in meta])) != 0
            bfee_step = np.diff(np.asarray([m['bfee_count'] for m in meta],dtype='int64')) & 65535
            for k, row in enumerate(rows):
                mask = flags[:, k]
                row.update(agc_changes_at_flag=int(agc_change[mask].sum()),
                    rx_permutation_changes_at_flag=int(perm_change[mask].sum()),
                    rate_changes_at_flag=int(rate_change[mask].sum()),
                    bfee_count_gap_at_flag=int((bfee_step[mask] != 1).sum()))
            time_file = raw_root/('r'+str(node+1))/'time'/(session+'.txt')
            time_count = sum(1 for line in time_file.open('r') if line.strip())
            raw_reports.append(dict(session=session, receiver=node+1, path=str(path), bytes=path.stat().st_size,
                frames=len(csi), positive_continuous_span_s=float(dt[(dt>0)&(dt<GAP_US)].sum()/1e6),
                clock_break_steps=int(((dt<=0)|(dt>=GAP_US)).sum()), interval_us=describe(dt[(dt>0)&(dt<GAP_US)]),
                timestamp_text_lines=time_count, timestamp_text_count_matches_frames=time_count==len(csi),
                agc_counts=dict(Counter(map(int,agc))), agc_change_steps=int(agc_change.sum()),
                permutation_change_steps=int(perm_change.sum()), rate_counts=dict(Counter(m['rate'] for m in meta)),
                any_pair_broadband_steps=int(flags.any(axis=1).sum()),pairs=rows))
            selected = [m for m in manifest['matches'] if m['node']==node and m['sample'] in chosen]
            for match in selected:
                name = match['sample']
                ids = np.asarray(match['raw_packet_indices'],dtype=int)
                if len(ids)!=20 or np.any(np.diff(ids)<=0) or ids.min()<0 or ids.max()>=len(csi):
                    raise ValueError('Invalid prior correspondence indices')
                aligned = mats[name][node].transpose(2,0,1)
                exact = bool(np.array_equal(csi[ids],aligned))
                # Underlying timestamps, not a newly invented aligned clock.
                aligned_dt = np.asarray([(int(ts[b])-int(ts[a]))&0xffffffff for a,b in zip(ids,ids[1:])])
                mat_rows, mat_flags = phase_metrics(aligned, aligned_dt)
                retained = np.zeros_like(mat_flags)
                consecutive = np.diff(ids)==1
                retained[consecutive] = mat_flags[consecutive] & flags[ids[1:][consecutive]-1]
>>>>>>> feat/model-refactor
                aligned_reports.append(dict(sample=name,receiver=node+1,all_complex_values_exact=exact,
                    raw_packet_indices=ids.tolist(),selected_source_interval_us=describe(aligned_dt),
                    consecutive_raw_steps=int(consecutive.sum()),any_pair_broadband_steps=int(mat_flags.any(axis=1).sum()),
                    original_adjacent_broadband_steps_retained=int(retained.any(axis=1).sum()),pairs=mat_rows))
<<<<<<< HEAD
                for k,(a,b) in enumerate(PAIRS):
                    found=np.flatnonzero(retained[:,k])
                    if not len(found):continue
                    t=int(found[0]);before,after=map(int,ids[t:t+2])
                    phase=np.angle(aligned[:,a]*aligned[:,b].conj())
                    change=np.angle(np.exp(1j*(phase[t+1]-phase[t])))
                    gain=[float(np.median(abs(csi[after,c]))/np.median(abs(csi[before,c])))
                        if np.median(abs(csi[before,c]))>0 else None for c in range(3)]
                    witnesses.append(dict(sample=name,receiver=node+1,pair=[a,b],aligned_rows=[t,t+1],
                        raw_rows=[before,after],raw_mat_values_exact=exact,
                        common_phase_step_rad=float(np.angle(np.mean(np.exp(1j*change)))),
                        affected_of_30=int((abs(change)>PHASE_LIMIT).sum()),dt_us=int(aligned_dt[t]),
                        agc=[meta[before]['agc'],meta[after]['agc']],rx_permutation=[meta[before]['perm'],meta[after]['perm']],
                        median_magnitude_ratios_by_chain=gain))
            print(json.dumps(dict(progress=True,session=session,receiver=node+1,frames=len(csi),
                broadband_by_pair=[x['broadband_steps'] for x in rows],aligned_node_windows=len(selected))),flush=True)
    return dict(scope='Representative original Intel 5300 and timestamp-aligned complex MAT phase audit',
=======
                for k, (a,b) in enumerate(PAIRS):
                    found=np.flatnonzero(retained[:,k])
                    if not len(found):continue
                    t=int(found[0]); before,after=map(int,ids[t:t+2])
                    phase=np.angle(aligned[:,a]*aligned[:,b].conj())
                    change=np.angle(np.exp(1j*(phase[t+1]-phase[t])))
                    gain=[float(np.median(abs(csi[after,c]))/np.median(abs(csi[before,c])))
                          if np.median(abs(csi[before,c]))>0 else None for c in range(3)]
                    witnesses.append(dict(sample=name,receiver=node+1,pair=[a,b],aligned_rows=[t,t+1],
                        raw_rows=[before,after],raw_mat_values_exact=exact,
                        common_phase_step_rad=float(np.angle(np.mean(np.exp(1j*change)))),
                        affected_of_30=int((abs(change)>PHASE_LIMIT).sum()),
                        dt_us=int(aligned_dt[t]),agc=[meta[before]['agc'],meta[after]['agc']],
                        rx_permutation=[meta[before]['perm'],meta[after]['perm']],
                        median_magnitude_ratios_by_chain=gain))
            print(json.dumps(dict(progress=True,session=session,receiver=node+1,frames=len(csi),
                broadband_by_pair=[x['broadband_steps'] for x in rows],aligned_node_windows=len(selected))),flush=True)
    result=dict(scope='Representative original Intel 5300 and timestamp-aligned complex MAT phase audit',
>>>>>>> feat/model-refactor
        read_only=True,remote_files_created_or_modified=False,hardware_accessed=False,
        model_preprocessing_math_protocol_changed=False,raw_root=str(raw_root),repo=str(repo),
        selection='Reuse the fixed nine training-group sessions and first/middle/last windows from the prior raw correspondence audit; not selected using phase results.',
        sessions=manifest['sessions'],raw_files=len(raw_reports),raw_frames=sum(x['frames'] for x in raw_reports),
        aligned_mat_files=len(samples),aligned_node_windows=len(aligned_reports),
        all_selected_raw_mat_values_exact=all(x['all_complex_values_exact'] for x in aligned_reports),
        flagged_raw_files=sum(x['any_pair_broadband_steps']>0 for x in raw_reports),
        flagged_aligned_node_windows=sum(x['any_pair_broadband_steps']>0 for x in aligned_reports),
        node_windows_retaining_original_adjacent_flags=sum(x['original_adjacent_broadband_steps_retained']>0 for x in aligned_reports),
<<<<<<< HEAD
        policy=dict(phase_threshold_rad=PHASE_LIMIT,min_affected_fraction=.5,dispersion_rad_limit=DISPERSION_LIMIT,
            intel_carriers=30,nexmon_carriers=56,require_all_pair_tones_nonzero=True,max_continuous_gap_us=GAP_US,
=======
        policy=dict(phase_threshold_rad=PHASE_LIMIT,min_affected_fraction=.5,
            dispersion_rad_limit=DISPERSION_LIMIT,intel_carriers=30,nexmon_carriers=56,
            require_all_pair_tones_nonzero=True,max_continuous_gap_us=GAP_US,
>>>>>>> feat/model-refactor
            circular_difference=True,physical_rx_permutation_applied=True,no_interpolation=True,
            diagnostic_flags_not_proof_of_hardware_error_or_paper_accuracy_gate=True),
        raw=raw_reports,aligned=aligned_reports,witnesses=witnesses,
        limitations=['Training subset only; not a dataset-wide prevalence estimate.',
            'Human actions and deployment environments differ from the RT-AC86U tests.',
            'Intel per-record AGC is one field; it does not identify every RX-chain analog state.',
            'A shared diagnostic phase pattern does not establish the same hardware cause.',
            'No model inference or physiological validation; flags are not a universal correctness threshold.'])
<<<<<<< HEAD


def remote(args):
    output=args.output;output.mkdir(parents=True,exist_ok=False)
    manifest=json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    selection=dict(sessions=manifest['sessions'],matches=[{k:m[k] for k in ('sample','node','raw_packet_indices')} for m in manifest['matches']])
    decoder=Path(__file__).with_name('audit_intel_reference.py').read_text(encoding='utf-8')
    decoder=decoder[decoder.index('def read_intel('):decoder.index('\ndef fingerprint(')]
    program='from pathlib import Path\nimport numpy as np\n'+decoder+'\nimport json\nSELECTION=json.loads('+repr(json.dumps(selection))+')\n'+Path(__file__).read_text(encoding='utf-8')
    command='/home/ubuntu/miniconda3/envs/PersonInWIFI/bin/python -B - --raw-root '+shlex.quote(str(args.raw_root).replace('\\','/'))+' --repo '+shlex.quote(str(args.repo).replace('\\','/'))
    with (output/'ssh.stderr').open('w',encoding='utf-8') as err,(output/'progress.log').open('w',encoding='utf-8') as log:
=======
    return result


def remote(args):
    output=args.output
    output.mkdir(parents=True,exist_ok=False)
    manifest=json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    manifest=dict(sessions=manifest['sessions'],matches=[{k:m[k] for k in ('sample','node','raw_packet_indices')}
        for m in manifest['matches']])
    decoder=Path(__file__).with_name('audit_intel_reference.py').read_text(encoding='utf-8')
    decoder=decoder[decoder.index('def read_intel('):decoder.index('\ndef fingerprint(')]
    program='from pathlib import Path\nimport numpy as np\n'+decoder+'\nimport json\nSELECTION=json.loads('+repr(json.dumps(manifest))+')\n'+Path(__file__).read_text(encoding='utf-8')
    command='/home/ubuntu/miniconda3/envs/PersonInWIFI/bin/python -B - --raw-root '+shlex.quote(str(args.raw_root).replace('\\','/'))+' --repo '+shlex.quote(str(args.repo).replace('\\','/'))
    with (output/'ssh.stderr').open('w',encoding='utf-8') as err, (output/'progress.log').open('w',encoding='utf-8') as log:
>>>>>>> feat/model-refactor
        proc=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
            '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3',args.ssh,command],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,encoding='utf-8')
        print(json.dumps(dict(remote_process_ssh_pid=proc.pid,remote_command=command)),flush=True)
<<<<<<< HEAD
        proc.stdin.write(program);proc.stdin.close();result=None
        for line in proc.stdout:
            if line.startswith('RESULT_JSON='):
                result=json.loads(line[len('RESULT_JSON='):]);(output/'analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            else:log.write(line);log.flush();print(line,end='',flush=True)
        code=proc.wait()
    (output/'execution.json').write_text(json.dumps(dict(ssh_exit_code=code,remote_command=command,result_received=result is not None),indent=2))
=======
        proc.stdin.write(program);proc.stdin.close()
        result=None
        for line in proc.stdout:
            if line.startswith('RESULT_JSON='):
                result=json.loads(line[len('RESULT_JSON='):])
                (output/'analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            else:
                log.write(line);log.flush();print(line,end='',flush=True)
        code=proc.wait()
    (output/'execution.json').write_text(json.dumps(dict(ssh_exit_code=code,remote_command=command,
        result_received=result is not None),indent=2))
>>>>>>> feat/model-refactor
    if code:raise SystemExit(code)
    if result is None:raise ValueError('No completed remote result; inspect logs before any rerun')
    print(json.dumps({k:result[k] for k in ('raw_files','raw_frames','aligned_mat_files','aligned_node_windows',
        'all_selected_raw_mat_values_exact','flagged_raw_files','flagged_aligned_node_windows',
        'node_windows_retaining_original_adjacent_flags')},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw-root',type=Path,required=True);p.add_argument('--repo',type=Path,required=True)
<<<<<<< HEAD
    p.add_argument('--manifest',type=Path);p.add_argument('--output',type=Path);p.add_argument('--ssh',choices=['gpu-server'])
    a=p.parse_args()
    if a.ssh:remote(a)
    else:print('RESULT_JSON='+json.dumps(analyze(a.raw_root,a.repo,SELECTION)),flush=True)
=======
    p.add_argument('--manifest',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--ssh',choices=['gpu-server'])
    a=p.parse_args()
    if a.ssh:remote(a)
    else:
        result=analyze(a.raw_root,a.repo,SELECTION)
        print('RESULT_JSON='+json.dumps(result),flush=True)
>>>>>>> feat/model-refactor

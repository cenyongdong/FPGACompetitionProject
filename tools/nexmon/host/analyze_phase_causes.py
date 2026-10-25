"""Offline causal clues for archived NMD3 CSI; never corrects or acquires CSI."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

from native_carriers import decode_selected
from validate_dedup import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'vitals'))
from audit_nexmon_vitals import load_segment, CARRIERS, PAIRS

SIGNED = np.r_[np.arange(-28, 0), np.arange(1, 29)]
PAIRS3 = [(0, 1), (0, 2), (1, 2)]


def wrap(a):
    return np.angle(np.exp(1j * a))


def packed_phase(words):
    """Direct signed-mantissa atan2: positive exponent cannot change phase."""
    r = ((words >> 18) & 2047).astype(float)
    q = ((words >> 6) & 2047).astype(float)
    r *= np.where(words & (1 << 29), -1, 1)
    q *= np.where(words & (1 << 17), -1, 1)
    return np.arctan2(q, r)


def analyze(path):
    events, state, groups = load_segment(path)
    words = np.asarray([e.words for e in events]).copy()
    words[:, :, 28:31] = np.asarray([e.original_words for e in events])
    selected = words[:, :, SIGNED % 64]
    iq = decode_selected(selected)
    if not np.isfinite(iq).all() or np.any(abs(iq) == 0):
        raise ValueError('Invalid source IQ; do not repair or silently omit it')
    raw_angle = packed_phase(selected)
    angle = np.angle(iq)
    error = abs(wrap(angle-raw_angle))
    phase = np.stack([np.angle(iq[:, a] * iq[:, b].conj()) for a, b in PAIRS3], axis=1)
    delta = wrap(np.diff(phase, axis=0))
    circular = np.mean(np.exp(1j*delta), axis=2)
    center, coherence = np.angle(circular), abs(circular)
    dispersion = np.median(abs(wrap(delta-center[:, :, None])), axis=2)
    bad = (abs(delta) > .25).sum(axis=2) >= 28
    bad &= dispersion < .25
    times = np.asarray([e.time_us for e in events]) / 1e6
    dt_us = np.diff(times) * 1e6
    seq = np.asarray([e.meta['seq'] >> 4 for e in events])
    seq_step = np.diff(seq) & 4095
    amplitudes = abs(iq)
    core_power = 10*np.log10(np.mean(amplitudes**2, axis=2))
    core_delta = np.diff(core_power, axis=0)
    row = dict(pcap=str(path), selected_events=len(events), continuous_segments=len(groups),
        packet_pairing_state=state['counts'], direct_mantissa_phase_max_error_rad=float(error.max()),
        all_iq_finite_nonzero=True, pairs=[], fixed_features=[])
    for k, (a, b) in enumerate(PAIRS3):
        mask = bad[:, k]
        med_amp_step = np.median(np.diff(20*np.log10(amplitudes[:, a]/amplitudes[:, b]), axis=0), axis=1)
        # Exclude positive28 even though its pre-overwrite original is available.
        clean = SIGNED != 28
        raw_bad = (abs(delta[:, k, clean]) > .25).sum(axis=1) >= 28
        raw_disp = np.median(abs(wrap(delta[:, k, clean]-np.angle(np.mean(np.exp(1j*delta[:, k, clean]),axis=1))[:,None])),axis=1)
        raw_bad &= raw_disp < .25
        returning = mask[:-1] & mask[1:] & (abs(wrap(center[:-1,k]+center[1:,k])) <= .1)
        indices = np.flatnonzero(mask)
        row['pairs'].append(dict(pair=[a,b], broadband_steps=int(mask.sum()),
            typical_abs_step_rad=stats(abs(center[mask,k])),
            across_tone_coherence_at_jump=stats(coherence[mask,k]),
            across_tone_phase_dispersion_rad=stats(dispersion[mask,k]),
            opposite_adjacent_step_pairs=int(returning.sum()),
            sequence_gap_at_jump=int((seq_step[mask] != 1).sum()),
            rx_interval_us_at_jump=stats(dt_us[mask]),
            abs_relative_amplitude_step_db_at_jump=stats(abs(med_amp_step[mask])),
            abs_relative_amplitude_step_db_elsewhere=stats(abs(med_amp_step[~mask])),
            abs_core_power_step_db_at_jump=[stats(abs(core_delta[mask,c])) for c in range(3)],
            excluding_overwritten_bin28_broadband_steps=int(raw_bad.sum()),
            jump_time_seconds=times[indices+1].tolist(),
            signed_phase_steps_rad=center[indices,k].tolist(),
            relative_amplitude_steps_db=med_amp_step[indices].tolist(),
            signed_phase_amplitude_correlation=float(np.corrcoef(center[indices,k],med_amp_step[indices])[0,1])
                if len(indices)>1 and np.std(center[indices,k])>0 and np.std(med_amp_step[indices])>0 else None,
            same_sign_phase_amplitude_fraction=float(np.mean(np.sign(center[indices,k]) == np.sign(med_amp_step[indices])))
                if len(indices) else None))
    for carrier, (a,b) in zip(CARRIERS,PAIRS):
        pos=int(np.flatnonzero(SIGNED == carrier)[0])
        change=abs(wrap(np.diff(np.angle(iq[:,a,pos]*iq[:,b,pos].conj()))))
        fault=change>.25
        strength=amplitudes[:,[a,b],pos]/np.median(amplitudes[:,[a,b],:],axis=2)
        endpoint_strength=np.minimum(strength[:-1],strength[1:])
        row['fixed_features'].append(dict(bin=carrier,pair=[a,b],phase_faults=int(fault.sum()),
            median_magnitude_relative_to_own_core_broadband=np.median(strength,axis=0).tolist(),
            endpoint_relative_strength_at_fault=[stats(endpoint_strength[fault,c]) for c in range(2)],
            endpoint_relative_strength_elsewhere=[stats(endpoint_strength[~fault,c]) for c in range(2)]))
    row['common_jump_intersection_01_02']=int((bad[:,0]&bad[:,1]).sum())
    row['core0_candidate_jump_union']=int((bad[:,0]|bad[:,1]).sum())
    return row, dict(times=times,phase=phase,center=center,bad=bad,core_power=core_power,delta=delta)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    rows=[]
    for i in (1,2,3):
        row,_=analyze(a.directory/f'run300-{i}.pcap');rows.append(row)
    result=dict(scope='offline_initial_phase_cause_analysis',hardware_accessed=False,
        phase_correction_applied=False,model_math_protocol_changed=False,runs=rows,
        metadata_limit='RSSI/phystatus in current extractor are cached from ordinary receive callbacks, not proven per-event AGC or current gain state. NMD3 lacks contemporaneous gain/calibration/antenna-selection telemetry.')
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps([dict(events=r['selected_events'],mantissa_phase_error=r['direct_mantissa_phase_max_error_rad'],
        intersection=r['common_jump_intersection_01_02'],pairs=[{k:v for k,v in x.items() if k not in ('jump_time_seconds','signed_phase_steps_rad','relative_amplitude_steps_db')} for x in r['pairs']],
        features=r['fixed_features']) for r in rows],indent=2))

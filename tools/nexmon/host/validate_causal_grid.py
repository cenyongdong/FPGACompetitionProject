"""Evaluate causal startup phase and streaming selection on retained observations."""
import argparse
import json
from pathlib import Path
import time

import numpy as np

from stream_time_grid import TimeGridStream, HZ, SCALE
from validate_dedup import stats, write_csv


def run(times, indices, segments, warmup_us=1_000_000, start_position=0):
    adapter = TimeGridStream(warmup_us=warmup_us)
    windows, tails, durations = [], [], []
    current = None
    for pos in range(start_position, len(times)):
        s = int(segments[pos])
        if s != current:
            if current is not None:
                tails.append(adapter.finish())
            adapter.reset(s)
            current = s
        tick = time.perf_counter_ns()
        windows.extend(adapter.feed(times[pos], indices[pos]))
        durations.append((time.perf_counter_ns()-tick)/1000)
    tails.append(adapter.finish())
    valid = [w for w in windows if w.valid]
    ids = [o.index for w in valid for o in w.observations]
    if len(ids) != len(set(ids)):
        raise ValueError('One observation reused across accepted windows')
    return adapter, windows, dict(total_windows=len(windows), valid_windows=len(valid),
        valid_fraction=len(valid)/len(windows) if windows else None,
        also_previous_interval_gate=sum(w.interval_gate for w in windows),
        distinct_selected_events=len(ids), startup=list(adapter.startup_records), tails=tails,
        max_buffered_observations=adapter.max_buffered_observations,
        processing_us=stats(durations),
        hardware_watermark_delay_after_last_observation_us=stats([
            w.close_time_us-w.observations[-1].time_us for w in valid]))


def analyze(source, output):
    output.mkdir(parents=True, exist_ok=False)
    with np.load(source/'retained-node-events.npz') as z:
        t, i, s = (z[k].astype('i8') for k in ('segment_time_us','original_event_indices','clock_segments'))
    adapter, windows, main = run(t,i,s)
    longest = max(np.unique(s), key=lambda seg:np.ptp(t[s==seg]))
    positions = np.flatnonzero(s==longest)
    # Predeclared start cuts; each separately calibrates its first second only.
    starts = (0,1,5,20,75,150,300,600)
    sensitivity=[]
    for cut in starts:
        p=positions[cut:]
        _,_,r=run(t[p],i[p],s[p])
        sensitivity.append(dict(start_offset_events=cut, first_original_index=int(i[p[0]]), **r))
    # Test an independently shifted clock origin, without tuning to later data.
    origin_tests=[]
    p=positions
    for offset in (0,833,1667,2500):
        _,_,r=run(t[p]+offset,i[p],s[p])
        origin_tests.append(dict(clock_origin_offset_us=offset,total_windows=r['total_windows'],
            valid_windows=r['valid_windows'],valid_fraction=r['valid_fraction']))
    rows=[]
    for w in windows:
        rows.append(dict(segment=w.segment,start_slot=w.start_slot,valid=w.valid,reason=w.reason,
            interval_gate=w.interval_gate,close_time_us=w.close_time_us,
            first_original_index=w.observations[0].index if w.observations[0] else None,
            last_original_index=w.observations[-1].index if w.observations[-1] else None))
    write_csv(output/'windows20.csv',rows)
    valid=[w for w in windows if w.valid]
    np.savez_compressed(output/'accepted-window-indices.npz',
        original_event_indices=np.asarray([[o.index for o in w.observations] for w in valid],dtype='i8').reshape(-1,20),
        actual_time_us=np.asarray([[o.time_us for o in w.observations] for w in valid],dtype='i8').reshape(-1,20),
        target_scaled=np.asarray([w.target_scaled for w in valid],dtype='i8').reshape(-1,20),
        segments=np.asarray([w.segment for w in valid],dtype='i8'))
    result=dict(offline_only=True,model_ready=False,target_hz=HZ,period_us=SCALE/HZ,
        policy=dict(warmup_us=1_000_000,minimum_startup_observations=120,
            minimum_circular_concentration=.75,tolerance_fraction=.25,
            phase_estimation='Circular mean seed plus circular median of first-second residues only',
            phase_after_startup='Fixed; no drift fitting or per-window fitting',
            period_after_startup='Fixed exact 300Hz; not estimated from capture',
            missing_policy='Discard 20-slot block; no interpolation/reuse',
            end_policy='Discard open cell and partial block; never advance RF clock from EOF'),
        main=main,longest_segment=int(longest),start_sensitivity=sensitivity,clock_origin_sensitivity=origin_tests,
        limitations=['Same historical capture is development data, not independent validation.',
            'Only reliable low16 clock segments; global clock and UDP slot association remain unknown.',
            'Processing timings exclude network/CSI decoding and OS scheduling.',
            'Single node/native64 time candidates, not model inputs or accuracy results.'])
    (output/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.source,a.output)
    print(json.dumps(dict(main=r['main'],start_sensitivity=[dict(start=x['start_offset_events'],
        valid=x['valid_windows'],total=x['total_windows'],fraction=x['valid_fraction']) for x in r['start_sensitivity']]),indent=2))

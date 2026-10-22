"""Compare fixed-scale single-node captures and explain rejected time windows.

Diagnostic only: legacy NMD1 comparisons use 29 intact common carriers and
never synthesize the lost positive28 value. No refitting, interpolation,
preprocessing, inference or device access.
"""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path

import numpy as np

from diagnose_metadata import packets
from map_node_windows import HT20_NG2
from native_carriers import decode_selected,select_packed
from single_node_adapter import SingleNodeAdapter,packet_rms
from stream_node import NodeStream
from validate_dedup import stats


def replay_events(pcap,profile,retry_startup=False):
    stream=NodeStream(profile['transmitter_mac'],profile['chanspec'],retry_startup=retry_startup)
    events=[];windows=[]
    stream.on_event=events.append
    for stamp,port,payload in packets(pcap):windows.extend(stream.feed(stamp,port,payload))
    final=stream.finish()
    return events,windows,final


def analyze(pcap,profile,adapted=None,retry_startup=False):
    events,windows,final=replay_events(pcap,profile,retry_startup=retry_startup)
    kept=[e for e in events if e.decision=='keep']
    if not kept:raise ValueError('No valid first receptions')
    words=np.asarray([e.words for e in kept])
    common=[x for x in HT20_NG2 if x!=28]
    common_csi=decode_selected(words[:,:,[x%64 for x in common]])
    common_rms=np.sqrt(np.mean(np.abs(common_csi)**2,axis=(1,2)))
    buckets=defaultdict(list)
    origin=kept[0].meta['time']
    for e,rms in zip(kept,common_rms):buckets[int(e.meta['time']-origin)].append(float(rms))
    amplitudes=dict(common29_signed_carriers=common,common29_all_first_valid_rms=stats(common_rms),
        common29_after_fixed_gain_rms=stats(common_rms*profile['gain']),
        per_host_second_median_common29={k:float(np.median(v)) for k,v in buckets.items()},
        host_seconds_are_diagnostic_bins_not_rf_timestamps=True)
    full=all(e.original_words is not None for e in kept)
    if full:
        original=np.asarray([e.original_words for e in kept])
        full_csi=decode_selected(select_packed(words,HT20_NG2,original))
        rms=np.sqrt(np.mean(np.abs(full_csi)**2,axis=(1,2)))
        amplitudes['full30_all_first_valid_rms']=stats(rms)
        amplitudes['full30_after_fixed_gain_rms']=stats(rms*profile['gain'])
    if adapted:
        with np.load(adapted) as z:
            values=z['csi_empirical'];ids=z['original_event_indices']
        accepted=[w for w in windows if w.valid]
        expected=np.asarray([[o.index for o in w.observations] for w in accepted],dtype='i8').reshape(-1,20)
        if not np.array_equal(ids,expected):raise ValueError('Adapted output event identity mismatch')
        # Exercise the stream mapping on actual recorded inputs, not synthetic data.
        adapter=SingleNodeAdapter(profile)
        mapped=np.asarray([adapter.map_window(w,profile['transmitter_mac'],profile['chanspec']) for w in accepted],dtype='complex128').reshape(-1,3,30,20)
        if mapped.tobytes()!=values.tobytes():raise ValueError('Adapted live output differs from recorded source mapping')
        rms=packet_rms(values).reshape(-1)
        amplitudes['accepted_windows_fixed_gain_rms']=stats(rms)
        reference=profile.get('reference_holdout_packet_rms_median')
        amplitudes['accepted_median_ratio_to_training_holdout']=float(np.median(rms)/reference) if len(rms) and reference else None
        amplitudes['live_values_match_original_record_replay_bitwise']=True
        amplitudes['accepted_windows_replayed']=len(values)
    grouped=defaultdict(list)
    for e in events:grouped[e.segment].append(e)
    by_id={e.index:e for e in events}
    rejected=[];missing_types=Counter();streak=longest=0;accepted_times=[]
    for w in windows:
        if w.valid:
            streak=0;accepted_times.append(by_id[w.observations[0].index].meta['time']);continue
        streak+=1;longest=max(longest,streak)
        missing=[];errors=[]
        for slot,(o,target) in enumerate(zip(w.observations,w.target_scaled)):
            if o is not None:
                errors.append((o.time_us*300-target)/300);continue
            inside=[e for e in grouped[w.segment] if target-500000<=e.time_us*300<target+500000]
            kinds=Counter(e.decision for e in inside)
            if not inside:kind='no_complete_reception_in_cell'
            elif set(kinds)=={'drop_retransmission'}:kind='only_later_retransmissions_in_cell'
            else:kind='no_retained_valid_reception_in_cell'
            missing_types[kind]+=1
            missing.append(dict(slot=slot,category=kind,raw_event_decisions=dict(kinds)))
        rejected.append(dict(segment=w.segment,start_slot=w.start_slot,reason=w.reason,missing=missing,
            selected_point_error_us=errors,largest_absolute_error_us=max(map(abs,errors)) if errors else None))
    valid=sum(w.valid for w in windows)
    same_gaps=[b.time_us-a.time_us for a,b in zip(kept,kept[1:]) if a.segment==b.segment]
    # Explain phase spread without fitting it away or changing frame selection.
    phase_rows=[]
    for lock in (x for x in final['startup'] if x.get('locked')):
        groups=defaultdict(list)
        for e in kept:
            if e.segment==lock['segment'] and e.time_us>lock['calibration_end_us']:
                groups[(e.time_us-lock['calibration_end_us'])//1000000].append(e)
        for second,items in sorted(groups.items()):
            residual=np.asarray([((e.time_us*300-lock['phase_scaled']+500000)%1000000-500000)/300 for e in items])
            phase_rows.append(dict(segment=lock['segment'],second_after_lock=int(second),events=len(items),
                residual_us=stats(residual),fraction_outside_original_tolerance=float(np.mean(np.abs(residual)>1000000/300*.25))))
    result=dict(source=str(pcap),receiver_nodes=1,model_ready=False,retry_startup=retry_startup,**final,
        full30_preoverwrite_available=full,amplitude=amplitudes,
        windows=len(windows),valid_windows=valid,valid_fraction=valid/len(windows) if windows else None,
        rejected_reasons=dict(Counter(w.reason for w in windows if not w.valid)),
        missing_cell_categories=dict(missing_types),longest_consecutive_rejected_enumerated_windows=longest,
        same_segment_retained_interval_us=stats(same_gaps),
        retained_intervals_above_1_5_period=sum(x>5000 for x in same_gaps),
        retained_intervals_below_half_period=sum(x<1000000/600 for x in same_gaps),
        per_second_phase_residual=phase_rows,
        host_gap_between_valid_window_starts_s=stats(np.diff(accepted_times)),
        rejected_windows=rejected,
        limitations=['Window denominator includes only enumerated complete windows in reliable local clock segments.',
            'No global RF clock, exact sender-slot association or attribution of missing reception to RF loss versus extractor suppression.',
            'Amplitude comparison keeps the original gain; no new gain fitted from this evaluation data.'])
    if retry_startup:
        _,old_windows,old_state=replay_events(pcap,profile,retry_startup=False)
        old=[w for w in old_windows if w.valid]
        def identity(w):return (w.segment,w.start_slot,tuple(o.index if o else -1 for o in w.observations))
        preserved={identity(w) for w in old}.issubset({identity(w) for w in windows if w.valid})
        if not preserved:raise ValueError('Startup recovery changed an already accepted window')
        result['counterfactual_without_retry']=dict(offline_replay=True,valid_windows=len(old),windows=len(old_windows),
            startup=old_state['startup'],old_accepted_windows_preserved=preserved)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('captures',type=Path,nargs='+')
    p.add_argument('--retry-startup',action='store_true')
    a=p.parse_args();profile=json.loads(a.profile.read_text())
    results=[]
    for capture in a.captures:
        adapted=capture.parent/'adapted-node-windows.npz'
        r=analyze(capture,profile,adapted if adapted.exists() else None,retry_startup=a.retry_startup)
        results.append(r)
        print(json.dumps(dict(source=str(capture),valid=r['valid_windows'],total=r['windows'],
            common29_rms=r['amplitude']['common29_all_first_valid_rms']['p50'],
            rejected=r['rejected_reasons'],missing=r['missing_cell_categories'])),flush=True)
    baseline=next(r for r in results if 'live-controlled2' in r['source'])
    baseline_rms=baseline['amplitude']['common29_all_first_valid_rms']['p50']
    for r in results:
        ratio=r['amplitude']['common29_all_first_valid_rms']['p50']/baseline_rms
        r['amplitude']['common29_median_ratio_to_original_calibration_recording']=ratio
        r['amplitude']['common29_median_change_db']=float(20*np.log10(ratio))
    output=dict(offline_analysis=True,profile=str(a.profile),gain_refitted=False,results=results)
    a.output.write_text(json.dumps(output,indent=2),encoding='utf-8')

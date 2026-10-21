"""Replay original ordered PCAP through the bounded single-node adapter."""
import argparse
import json
from pathlib import Path
import time

import numpy as np

from diagnose_metadata import packets
from stream_node import NodeStream
from validate_causal_grid import run
from validate_dedup import stats, write_csv
from single_node_adapter import SingleNodeAdapter


def replay(pcap, retained, output, source_mac, channel, paced=False, amplitude_profile=None):
    output.mkdir(parents=True,exist_ok=False)
    adapter=NodeStream(source_mac,channel)
    value_adapter=SingleNodeAdapter(amplitude_profile) if amplitude_profile else None
    adapted=[]
    windows,events,durations=[],[],[]
    # Evidence sink is outside the bounded adapter, with capture-sized budget.
    adapter.on_event=lambda e:events.append(e)
    tick0=pcap0=None
    for timestamp,port,payload in packets(pcap):
        if tick0 is None:
            tick0=time.monotonic();pcap0=timestamp
        if paced:
            target=tick0+timestamp-pcap0
            while (remaining:=target-time.monotonic())>0:
                time.sleep(min(remaining,.010))
                adapter.expire(min(timestamp,pcap0+time.monotonic()-tick0))
        tick=time.perf_counter_ns()
        ready=adapter.feed(timestamp,port,payload)
        if value_adapter is not None:
            adapted.extend(value_adapter.map_window(w,source_mac,channel) for w in ready if w.valid)
        windows.extend(ready)
        durations.append((time.perf_counter_ns()-tick)/1000)
        if len(events)>10000:
            raise ValueError('Replay evidence budget exceeded')
    final=adapter.finish()
    kept=[e for e in events if e.decision=='keep']
    with np.load(retained/'retained-node-events.npz') as z:
        indices=z['original_event_indices']
        actual=np.asarray([e.index for e in kept])
        same_indices=np.array_equal(actual,indices)
        same_words=np.array_equal(np.asarray([e.words for e in kept]),z['packed_words'])
        same_clock=(np.array_equal([e.segment for e in kept],z['clock_segments']) and
                    np.array_equal([e.time_us for e in kept],z['segment_time_us']))
        _,reference,_=run(z['segment_time_us'],indices,z['clock_segments'])
    def identity(w):
        return (w.segment,w.start_slot,w.valid,w.interval_gate,w.target_scaled,
                tuple(o.index if o else -1 for o in w.observations))
    same_windows=[identity(w) for w in windows]==[identity(w) for w in reference]
    valid=[w for w in windows if w.valid]
    ids=np.asarray([[o.index for o in w.observations] for w in valid],dtype='i8').reshape(-1,20)
    np.savez_compressed(output/'accepted-window-indices.npz',original_event_indices=ids,
        actual_time_us=np.asarray([[o.time_us for o in w.observations] for w in valid],dtype='i8').reshape(-1,20),
        target_scaled=np.asarray([w.target_scaled for w in valid],dtype='i8').reshape(-1,20))
    write_csv(output/'windows20.csv',[dict(segment=w.segment,start_slot=w.start_slot,valid=w.valid,
        reason=w.reason,interval_gate=w.interval_gate,close_time_us=w.close_time_us) for w in windows])
    result=dict(mode='paced_original_packet_replay' if paced else 'fast_original_packet_replay',
        live_radio_test=False,model_ready=False,model_or_board_protocol_changed=False,
        elapsed_s=time.monotonic()-tick0,**final,windows=len(windows),valid_windows=len(valid),
        valid_fraction=len(valid)/len(windows) if windows else None,
        also_previous_interval_gate=sum(w.interval_gate for w in windows),processing_us=stats(durations),
        verification=dict(retained_indices_match=same_indices,retained_raw_words_match=same_words,
            retained_clock_segments_match=same_clock,event_level_reference_windows_match=same_windows,
            no_selected_frame_reuse=len(ids.reshape(-1))==len(np.unique(ids))),
        limitations=['Ordered original PCAP replay; no live router-to-PC transport was tested.',
            'No full-width RF clock, cross-node sync or absolute RF calibration.',
            'Processing time is host compute only, not full end-to-end live latency.'])
    if value_adapter is not None:
        np.savez_compressed(output/'adapted-node-windows.npz',
            csi_empirical=np.asarray(adapted,dtype='complex128').reshape(-1,3,30,20),
            original_event_indices=ids,signed_subcarriers=value_adapter.profile['signed_carriers'])
        result['empirical_adapter']=dict(windows=len(adapted),gain=value_adapter.gain,
            physical_power_calibrated=False,model_ready=False,profile=str(amplitude_profile))
    (output/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    if not all(result['verification'].values()):
        raise ValueError('Stream/reference mismatch; raw results preserved')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pcap',type=Path);p.add_argument('--retained',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--source-mac',required=True)
    p.add_argument('--channel',type=lambda s:int(s,0),required=True);p.add_argument('--paced',action='store_true')
    p.add_argument('--amplitude-profile',type=Path)
    a=p.parse_args();print(json.dumps(replay(a.pcap,a.retained,a.output,a.source_mac,a.channel,a.paced,a.amplitude_profile),indent=2))

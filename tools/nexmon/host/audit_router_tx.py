"""Audit a finite router-TX capture with existing timing and phase diagnostics.

No radio access, threshold changes, interpolation, model or board output.
The transmitter status counts enqueue calls; CSI remains the reception evidence.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

import numpy as np

from diagnose_metadata import diagnose, packets
from native_carriers import decode_selected
from router_tx_job import decode_stats
from stream_node import NodeStream
from validate_dedup import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'vitals'))
from align_nexmon_phase import differential_phase, phase_diagnosis, MAX_PHASE_STEP
from audit_nexmon_vitals import CARRIERS, PAIRS


def audit(pcap, tx_result, native_result, source_mac, channel):
    tx_text = json.loads(tx_result.read_text(encoding='utf-8-sig'))['stdout']
    tx = decode_stats(tx_text)
    native_text = json.loads(native_result.read_text(encoding='utf-8-sig'))['stdout']
    native = next(json.loads(line) for line in native_text.splitlines()
                  if line.strip().startswith('{') and 'kernel_drops' in line)
    metadata, _ = diagnose(pcap)
    stream = NodeStream(source_mac, channel)
    events, windows = [], []
    stream.on_event = events.append
    for stamp, port, payload in packets(pcap):
        windows.extend(stream.feed(stamp, port, payload))
    state = stream.finish()
    kept = [e for e in events if e.decision == 'keep']
    groups = defaultdict(list)
    for event in kept:
        groups[event.segment].append(event)
    intervals = [b.time_us-a.time_us for group in groups.values()
                 for a, b in zip(group, group[1:])]
    valid = sum(w.valid for w in windows)
    phase = None
    phase_error = None
    if groups:
        selected = max(groups.values(), key=lambda g: g[-1].time_us-g[0].time_us)
        try:
            phase = phase_diagnosis(selected)
            iq = decode_selected(np.asarray([e.words for e in selected])[:, :, CARRIERS])
            pairs = np.stack([iq[:, [a, b], ch] for ch, (a, b) in enumerate(PAIRS)], axis=1)
            wrapped = differential_phase(pairs)
            steps = abs(np.angle(np.exp(1j * np.diff(wrapped, axis=0))))
            phase['fixed_feature_faults_over_0_25_rad'] = (steps > MAX_PHASE_STEP).sum(axis=0).tolist()
            phase['fixed_feature_max_step_rad'] = steps.max(axis=0).tolist()
            phase['segment_events'] = len(selected)
            phase['segment_span_s'] = (selected[-1].time_us-selected[0].time_us)/1e6
        except ValueError as error:
            phase_error = str(error)
    return dict(source_pcap=str(pcap), hardware_capture_source=True,
        audit_is_offline=True, tx_enqueue_status=tx, native_capture=native,
        metadata=metadata, first_valid_retained_events=len(kept),
        rx_intervals_us=stats(intervals), stream_state=state,
        windows20=dict(enumerated_after_startup=len(windows), valid=valid,
            valid_fraction=valid/len(windows) if windows else None,
            scope='Only complete windows after fixed startup lock in reliable segments; not whole-capture coverage.',
            reasons=dict((reason, sum(w.reason == reason for w in windows))
                         for reason in sorted({w.reason for w in windows}))),
        source_phase_diagnosis=phase, source_phase_error=phase_error,
        no_interpolation=True, model_or_math_or_board_protocol_changed=False,
        model_ready=False, model_inference_performed=False,
        limitations=['One receiver node; full model requires the existing multi-node contract.',
            'No synchronized heart-rate reference or human pose labels.',
            'Frame bandwidth is the explicit TX request; NMD3 has no per-frame PHY bandwidth proof.',
            'Short-run phase quality cannot establish long-term stability or a hardware root cause.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcap', type=Path, required=True)
    parser.add_argument('--tx-result', type=Path, required=True)
    parser.add_argument('--native-result', type=Path, required=True)
    parser.add_argument('--source-mac', required=True)
    parser.add_argument('--channel', type=lambda v: int(v, 0), required=True)
    parser.add_argument('--output', type=Path, required=True)
    a = parser.parse_args()
    result = audit(a.pcap, a.tx_result, a.native_result, a.source_mac, a.channel)
    with a.output.open('x', encoding='utf-8') as out:
        json.dump(result, out, indent=2, allow_nan=False)
    print(json.dumps(dict(events=result['metadata']['complete_events'],
        retry=result['metadata']['field_counts']['retry'],
        duplicates=result['metadata']['repeated_identity_events'],
        timing=result['rx_intervals_us'], windows20=result['windows20'],
        phase_error=result['source_phase_error'],
        phase_faults=[p['broadband_phase_fault_events'] for p in result['source_phase_diagnosis']['pairs']]
            if result['source_phase_diagnosis'] else None), indent=2))

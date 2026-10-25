"""Audit real router PCAPs with the unchanged first-valid/300Hz/20-slot adapter."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from csi_verify import verify
from diagnose_metadata import diagnose, packets
from stream_node import NodeStream
from validate_dedup import stats


def audit(path, source_mac, channel=0xd0a1):
    adapter = NodeStream(source_mac, channel)
    retained, windows = [], []

    def observe(event):
        if event.decision == 'keep':
            retained.append((event.index, event.segment, event.time_us))

    adapter.on_event = observe
    for stamp, port, payload in packets(path):
        windows.extend(adapter.feed(stamp, port, payload))
    state = adapter.finish()
    valid = [window for window in windows if window.valid]
    selected = [obs.index for window in valid for obs in window.observations]
    if len(selected) != len(set(selected)):
        raise ValueError('One event reused across accepted windows')
    intervals = [b[2]-a[2] for a, b in zip(retained, retained[1:]) if a[1] == b[1]]
    metadata, _ = diagnose(path)
    values = verify(path, 64, [0, 1, 2], 0, 106, source_mac)
    result = dict(source_pcap=str(path), hardware_capture_source=True, audit_is_offline=True,
        model_ready=False, model_structure_preprocessing_board_protocol_changed=False,
        metadata=metadata, acquisition=values, first_valid_retained_events=len(retained),
        rx_intervals_us=stats(intervals), stream_state=state,
        windows20=dict(enumerated_after_startup=len(windows), valid=len(valid),
            valid_fraction=len(valid)/len(windows) if windows else None,
            reasons=dict(Counter(window.reason for window in windows)),
            also_previous_interval_gate=sum(window.interval_gate for window in windows),
            scope='Complete enumerated windows after fixed startup inside reliable clock segments; not whole-recording coverage.'),
        policy=dict(target_hz=300, warmup_us=1000000, tolerance_fraction=.25,
            phase='Existing startup estimate then fixed; no drift fitting',
            missing='Discard window; no interpolation, fill or event reuse'),
        limitations=['One receiver node, not full model input or accuracy validation.',
            'PCAP boundaries may cut a pair/core group; original stream guards remain active.',
            'TX enqueue counts do not certify per-frame air transmission time.'])
    rows = [dict(segment=w.segment, start_slot=w.start_slot, valid=w.valid,
                 reason=w.reason, interval_gate=w.interval_gate,
                 selected_event_indices=';'.join(str(o.index) if o else '' for o in w.observations))
            for w in windows]
    return result, rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcap', type=Path)
    parser.add_argument('--source-mac', required=True)
    parser.add_argument('--channel', type=lambda x: int(x, 0), default=0xd0a1)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result, rows = audit(args.pcap, args.source_mac, args.channel)
    with args.output.open('x', encoding='utf8') as f:
        json.dump(result, f, indent=2)
    if rows:
        with args.output.with_suffix('.csv').open('x', encoding='utf8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(json.dumps({key: result[key] for key in ('first_valid_retained_events','rx_intervals_us','windows20')}))

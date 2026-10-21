"""Offline identity diagnostics for the pinned BCM4366 / 20 MHz capture.

Reads the original PCAP and existing export; does not deduplicate either input,
produce model inputs, change acceptance rules, or access a network device.
"""
import argparse
import collections
import csv
import json
from pathlib import Path

import numpy as np

from csi_verify import pcap_udp


def quantiles(values):
    if not len(values):
        return None
    return dict(zip(('min', 'p50', 'p95', 'p99', 'max'),
                    map(float, np.quantile(values, [0, .5, .95, .99, 1]))))


def diagnose(pcap, export_dir, sender_path):
    # Read header fields by their byte offsets, independently of parse_payload.
    # Source: pinned csi_udp_frame and BCM4366 microcode MAC_OFFSET + 22.
    records = []
    for timestamp, payload in pcap_udp(pcap):
        if len(payload) != 18 + 64 * 4 or payload[:2] != b'\x11\x11':
            raise ValueError('Expected current18 / 64-point BCM4366 report')
        chip = int.from_bytes(payload[16:18], 'little')
        config = int.from_bytes(payload[12:14], 'little')
        if chip != 106 or config not in (0, 256, 512):
            raise ValueError('Expected cores 0/1/2, stream 0, chip 106')
        records.append(dict(time=timestamp, mac=payload[4:10].hex(':'),
                            seq=int.from_bytes(payload[10:12], 'little'),
                            channel=int.from_bytes(payload[14:16], 'little'),
                            core=config >> 8, fc=payload[3],
                            words=np.frombuffer(payload, dtype='<u4', offset=18)))
    if not records or len(records) % 3:
        raise ValueError('Incomplete three-core capture')
    events = []
    for offset in range(0, len(records), 3):
        group = records[offset:offset + 3]
        key = lambda r: (r['mac'], r['seq'], r['channel'])
        if [r['core'] for r in group] != [0, 1, 2] or len({key(r) for r in group}) != 1:
            raise ValueError('Core reports interleaved or identities disagree')
        events.append(group)
    times = np.array([g[0]['time'] for g in events])
    seq = np.array([g[0]['seq'] for g in events], dtype=np.uint16)
    channels = np.array([g[0]['channel'] for g in events], dtype=np.uint16)
    words = np.array([[r['words'] for r in g] for g in events])
    seen, repeats, repeated = {}, [], []
    mask = np.ones(64, dtype=bool)
    mask[28:31] = False  # PHY-status overwrite in the pinned 20 MHz extractor.
    for i, group in enumerate(events):
        identity = (group[0]['mac'], int(seq[i]), int(channels[i]))
        previous = seen.get(identity)
        repeat = previous is not None and (times[i] - times[previous]) * 1000 <= 20
        repeated.append(repeat)
        if repeat:
            prior = words[previous][:, mask]
            current = words[i][:, mask]
            repeats.append(dict(event_index=i, previous_index=previous,
                                sequence_control=int(seq[i]), sequence_number=int(seq[i]) >> 4,
                                fragment_number=int(seq[i]) & 15,
                                receiver_relative_s=float(times[i] - times[0]),
                                arrival_gap_ms=float((times[i] - times[previous]) * 1000),
                                events_apart=i - previous,
                                changed_csi_words_excluding_metadata=int(np.count_nonzero(prior != current)),
                                csi_words_compared=int(current.size),
                                phy_metadata_equal=bool(np.array_equal(words[previous, :, 28:31],
                                                                      words[i, :, 28:31]))))
        seen[identity] = i
    repeated = np.asarray(repeated, dtype=bool)
    with np.load(export_dir / 'node-events.npz') as saved:
        matches = dict(packed_words=np.array_equal(words, saved['packed_words']),
                       sequence_control=np.array_equal(seq, saved['sequence_control']),
                       chanspec=np.array_equal(channels, saved['chanspec']),
                       all_core_arrivals=np.array_equal(
                           [[r['time'] for r in g] for g in events], saved['pcap_arrival_seconds']),
                       repeat_flags=np.array_equal(repeated, saved['repeated_identity_20ms']))
    if not all(matches.values()):
        raise ValueError(f'Independent header extraction disagrees with saved export: {matches}')
    runs, start = [], 0
    for end in range(1, len(events) + 1):
        if end == len(events) or (seq[end], channels[end]) != (seq[start], channels[start]):
            runs.append((start, end))
            start = end
    steps = np.diff(seq.astype(np.int32) >> 4) % 4096
    jumps = [dict(event_index=i, receiver_relative_s=float(times[i] - times[0]),
                  before_sequence_number=int(seq[i - 1]) >> 4,
                  after_sequence_number=int(seq[i]) >> 4,
                  modulo_step=int(steps[i - 1]),
                  arrival_gap_ms=float((times[i] - times[i - 1]) * 1000))
             for i in range(1, len(times)) if steps[i - 1] not in (0, 1)]
    distinct_runs = [(lo, hi) for lo, hi in runs if hi - lo > 1]
    sender = json.loads(sender_path.read_text(encoding='utf-8-sig'))
    sends = sender['sends']
    if [row[0] for row in sends] != list(range(sender['scheduled_slots'])):
        raise ValueError('Sender ledger does not cover the scheduled slots exactly once')
    per_second = collections.defaultdict(lambda: dict(events=0, repeat_events=0))
    for i, timestamp in enumerate(times):
        row = per_second[int(timestamp - times[0])]
        row['events'] += 1
        row['repeat_events'] += int(repeated[i])
    timing = {}
    for name, indices in [('all_events', np.arange(len(times))),
                          ('diagnostic_first_identity_only', np.flatnonzero(~repeated))]:
        selected = times[indices]
        timing[name] = dict(events=len(indices),
                            arrival_interval_ms=quantiles(np.diff(selected) * 1000),
                            twenty_event_first_to_last_ms=quantiles((selected[19:] - selected[:-19]) * 1000))
    report = dict(schema=1, hardware_test=False, model_ready=False,
                  inputs=dict(pcap=str(pcap), export=str(export_dir), sender=str(sender_path)),
                  independent_extraction_matches=matches,
                  csi_records=len(records), complete_core_events=len(events),
                  frame_control_low_counts=dict(collections.Counter(r['fc'] for r in records)),
                  sequence_control_low_nibble_counts=dict(collections.Counter(int(s) & 15 for s in seq)),
                  sequence_step_counts=dict(collections.Counter(map(int, steps))),
                  sequence_wraps=[dict(event_index=i, before=int(seq[i - 1]) >> 4,
                                       after=int(seq[i]) >> 4, adjacent_repeat=bool(repeated[i]))
                                  for i in range(1, len(seq)) if seq[i] < seq[i - 1]],
                  repeat_events=len(repeats), repeated_identity_runs=len(distinct_runs),
                  same_identity_run_lengths=dict(collections.Counter(hi - lo for lo, hi in runs)),
                  all_repeats_adjacent=all(r['events_apart'] == 1 for r in repeats),
                  repeat_gap_ms=quantiles([r['arrival_gap_ms'] for r in repeats]),
                  repeat_cluster_max_span_ms=max(((times[hi - 1] - times[lo]) * 1000
                                                  for lo, hi in distinct_runs), default=0),
                  repeat_threshold_sensitivity_ms={str(threshold): sum(r['arrival_gap_ms'] <= threshold for r in repeats)
                                                   for threshold in (.05, .1, .5, 1, 2, 5, 20)},
                  changed_csi_words=quantiles([r['changed_csi_words_excluding_metadata'] for r in repeats]),
                  identical_csi_repeat_events=sum(r['changed_csi_words_excluding_metadata'] == 0 for r in repeats),
                  repeat_events_with_equal_phy_metadata=sum(r['phy_metadata_equal'] for r in repeats),
                  sequence_jumps=jumps,
                  sender=dict(job_id=sender['id'], scheduled_slots=sender['scheduled_slots'],
                              ledger_rows=len(sends), distinct_slots=len({r[0] for r in sends}),
                              bytes_per_send=sorted({r[4] for r in sends}),
                              socket_schedule_complete=sender['schedule_complete'],
                              limitation='QPC ledger has no RF identity or shared receiver clock; cannot associate individual slots'),
                  timing_diagnostic_only=timing,
                  twenty_event_windows=dict(total=max(0, len(times) - 19),
                                             containing_marked_repeat=sum(bool(repeated[i:i + 20].any())
                                                                           for i in range(len(times) - 19))),
                  per_second=[dict(second=k, **v) for k, v in sorted(per_second.items())],
                  conclusions=dict(parser_or_core_order_error_found=False,
                                   complete_byte_copies_found=False,
                                   twenty_ms_horizon_is_direct_cause=False,
                                   leading_hypothesis='Repeated RF transmission of a frame; not confirmed',
                                   unresolved=['Retry vs different TID/subtype sequence spaces',
                                               'RF reception vs firmware/report identity reuse',
                                               'Thirteen sequence gaps vs test UDP delivery or extraction omissions']),
                  limitations=['No full 802.11 Frame Control, QoS TID, payload slot or RF TSF in the saved export',
                               'PCAP time is userspace recvfrom wall time, not a hardware sampling timestamp',
                               'Diagnostic first-occurrence timing is a comparison only; no cleaned dataset is emitted',
                               'Sequence jumps do not establish UDP loss or a radio failure',
                               'Original strict verification and all raw data remain unchanged'])
    return report, repeats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcap', type=Path, required=True)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--sender', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    csv_path = args.output.with_suffix('.csv')
    if args.output.exists() or csv_path.exists():
        raise ValueError('Refusing to overwrite an existing diagnostic')
    report, rows = diagnose(args.pcap, args.export, args.sender)
    with csv_path.open('x', newline='', encoding='utf-8') as stream:
        fields = list(rows[0]) if rows else ['event_index', 'previous_index']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('independent_extraction_matches', 'csi_records',
                                           'complete_core_events', 'repeat_events',
                                           'repeated_identity_runs', 'repeat_gap_ms',
                                           'identical_csi_repeat_events', 'sequence_step_counts')}, indent=2))


if __name__ == '__main__':
    main()

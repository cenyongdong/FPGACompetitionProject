"""Offline first-valid reception selection and 20-event timing diagnostics.

Retains an independent single-node export, never a PIWCSI1/model input. Original
CSI bytes, existing acceptance results, model and board protocol are untouched.
"""
import argparse
import collections
import csv
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np

from csi_verify import parse_payload, unpack_acphy
from diagnose_metadata import decode, packets

PERIOD_US = 1_000_000 / 300
TIMES = 20
# These fixed tolerances characterize candidate adapter windows. They are not
# trained-model accuracy limits or amendments to the existing acquisition gate.
TOLERANCE_FRACTIONS = (0.10, 0.25, 0.50)
CLOCK_HALF_WRAP_US = 32768
RETRY_HORIZON_US = 20000
PHY_WORDS = (28, 29, 30)


@dataclass
class Event:
    index: int
    meta: dict
    words: np.ndarray
    valid: bool = True
    reason: str = ''
    segment: int = 0
    time_us: int = 0
    decision: str = ''
    first_valid: int | None = None
    original_words: np.ndarray | None = None


def finalize(index, group, forced_reason=''):
    """A later retry can replace an incomplete/all-zero first observation."""
    m = dict(group[0][0])
    reasons = [forced_reason] if forced_reason else []
    if m['fc'] & 0x8c == 0x88 and m['tid'] is None:
        reasons.append('qos_tid_unavailable')
    core_ids = [g[0]['config'] >> 8 for g in group]
    if sorted(core_ids) != [0, 1, 2]:
        reasons.append('missing_or_duplicate_core')
    words = np.zeros((3, 64), dtype='<u4')
    for d, c in group:
        core = d['config'] >> 8
        words[core] = c['words']
        values = np.asarray(unpack_acphy([w for i, w in enumerate(c['words']) if i not in PHY_WORDS]))
        if not np.isfinite(values).all():
            raise ValueError('Non-finite CSI: stop affected export')
        if not np.any(values != 0):
            reasons.append('all_zero_core_excluding_phy')
    event = Event(index, m, words, not reasons, ';'.join(sorted(set(reasons))))
    if any('original_words' in d for d, _ in group):
        if not all(d.get('original_offset') == 28 and len(d.get('original_words', ())) == 3 for d, _ in group):
            raise ValueError('Inconsistent pre-overwrite word sidecar')
        saved = np.zeros((3,3), dtype='<u4')
        for d, _ in group:
            saved[d['config'] >> 8] = d['original_words']
        event.original_words = saved
    return event


def read_events(path):
    group, current, pending = [], None, None
    events, pair_errors = [], []
    counts = collections.Counter()
    identity = ('mac', 'seq', 'config', 'channel')
    shared = ('mac', 'seq', 'channel', 'fc', 'qos', 'rx_tsf16', 'event16')
    source_identities = set()
    for timestamp, port, payload in packets(path):
        if port == 5500:
            counts['csi_packets'] += 1
            if pending is not None:
                pair_errors.append('csi_without_diagnostic')
            c = parse_payload(payload, 64)
            if c['chip'] != 106 or c['stream'] != 0 or c['core'] not in (0, 1, 2):
                raise ValueError('Unexpected radio/core/stream identity')
            pending = dict(mac=c['mac'], seq=c['sequence_control'], config=c['core_config_raw'],
                           channel=c['chanspec'], words=c['words'], time=timestamp)
        elif port == 5501:
            counts['diagnostic_packets'] += 1
            d = decode(payload)
            if pending is None or any(d[k] != pending[k] for k in identity):
                pair_errors.append('diagnostic_csi_identity_mismatch')
                pending = None
                continue
            d['time'] = pending['time']  # first CSI arrival, consistent within group
            source_identities.add((d['mac'], d['channel']))
            key = tuple(d[k] for k in shared)
            if group and key != current:
                events.append(finalize(len(events), group))
                group = []
            current = key
            group.append((d, pending))
            pending = None
            if len(group) == 3:
                events.append(finalize(len(events), group))
                group, current = [], None
    if group:
        events.append(finalize(len(events), group))
    if pending is not None:
        pair_errors.append('trailing_csi_without_diagnostic')
    if len(source_identities) != 1:
        raise ValueError('Require one fixed transmitter/channel per offline capture')
    if pair_errors:
        # No guessing an association when the side channel itself was lost.
        raise ValueError('CSI/diagnostic pairing failed: ' + ','.join(pair_errors))
    if not events:
        raise ValueError('No reception events')
    return events, dict(counts)


def clock_segments(events):
    """Only unfold adjacent low16 increments within a half-wrap horizon.

    Host arrival time is a conservative discontinuity guard, not a substitute
    RF timestamp. No full-width clock or time across ambiguous gaps is inferred.
    """
    boundaries = []
    segment, local = 0, 0
    for i, e in enumerate(events):
        if i:
            previous = events[i-1]
            host_us = (e.meta['time'] - previous.meta['time']) * 1e6
            delta = (e.meta['rx_tsf16'] - previous.meta['rx_tsf16']) & 65535
            step = (e.meta['event16'] - previous.meta['event16']) & 65535
            reason = []
            if not 0 < host_us < CLOCK_HALF_WRAP_US:
                reason.append('arrival_gap_outside_half_wrap')
            if not 0 < delta < CLOCK_HALF_WRAP_US:
                reason.append('rx_tsf_delta_outside_half_wrap')
            if step != 1:
                reason.append('microcode_event_discontinuity')
            if reason:
                segment += 1
                local = 0
                boundaries.append(dict(event_index=e.index, previous_index=previous.index,
                    host_gap_us=host_us, hardware_delta_mod65536=delta,
                    event_step=step, reason=';'.join(reason)))
            else:
                local += delta
        e.segment, e.time_us = segment, local
    return boundaries


def select_first_valid(events):
    first, last_seen = {}, {}
    for e in events:
        if not e.valid:
            e.decision = 'invalid'
            continue
        m = e.meta
        key = (m['mac'], m['channel'], m['tid'], m['seq'])  # includes fragment bits
        old = last_seen.get(key)
        recent = old is not None and 0 <= (m['time'] - old.meta['time']) * 1e6 <= RETRY_HORIZON_US
        if recent and m['retry']:
            original = first[key]
            e.decision, e.first_valid = 'drop_retransmission', original.index
        elif recent:
            # Non-Retry reuse cannot be silently labelled a retransmission.
            e.decision, e.first_valid = 'ambiguous_identity_reuse', first[key].index
        else:
            e.decision, e.first_valid = 'keep', e.index
            first[key] = e
        last_seen[key] = e
    return [e for e in events if e.decision == 'keep']


def stats(values):
    a = np.asarray(values, dtype=float)
    if not a.size:
        return None
    return dict(count=int(a.size), **dict(zip(('min','p01','p50','p95','p99','max'),
        map(float, np.quantile(a, [0,.01,.5,.95,.99,1])))))


def intervals(events):
    rows = []
    for a, b in zip(events, events[1:]):
        same = a.segment == b.segment
        rows.append(dict(previous_index=a.index, event_index=b.index, same_clock_segment=same,
            hardware_interval_us=b.time_us-a.time_us if same else None,
            host_interval_us=(b.meta['time']-a.meta['time'])*1e6,
            event_step=(b.meta['event16']-a.meta['event16']) & 65535))
    hardware = [r['hardware_interval_us'] for r in rows if r['same_clock_segment']]
    return rows, dict(adjacent_pairs=len(rows), clock_boundary_pairs=sum(not r['same_clock_segment'] for r in rows),
        hardware_interval_us=stats(hardware),
        hardware_absolute_period_error_us=stats(np.abs(np.asarray(hardware)-PERIOD_US)),
        host_interval_us=stats([r['host_interval_us'] for r in rows]),
        note='Long/ambiguous gaps remain counted as clock boundaries; not omitted and claimed uniform.')


def windows(events):
    rows = []
    for i in range(max(0, len(events)-TIMES+1)):
        group = events[i:i+TIMES]
        valid = all(e.valid and e.decision != 'ambiguous_identity_reuse' for e in group)
        same_clock = len({e.segment for e in group}) == 1
        row = dict(start_index=group[0].index, end_index=group[-1].index,
                   valid_events=valid, same_clock_segment=same_clock,
                   span_us=None, min_interval_us=None, max_interval_us=None,
                   max_grid_error_us=None, max_interval_error_us=None,
                   contains_retry=any(e.meta['retry'] for e in group))
        if valid and same_clock:
            t = np.asarray([e.time_us for e in group], dtype=float)
            delta = np.diff(t)
            row.update(span_us=float(t[-1]-t[0]), min_interval_us=float(delta.min()),
                max_interval_us=float(delta.max()),
                max_grid_error_us=float(np.max(np.abs(t-t[0]-np.arange(TIMES)*PERIOD_US))),
                max_interval_error_us=float(np.max(np.abs(delta-PERIOD_US))))
        for fraction in TOLERANCE_FRACTIONS:
            row[f'candidate_{int(fraction*100)}pct'] = bool(valid and same_clock and
                row['max_grid_error_us'] <= PERIOD_US*fraction and
                row['max_interval_error_us'] <= PERIOD_US*fraction)
        # Integer microsecond timestamp quantization allows <=1us around the
        # rational ideal. This characterizes exact uniformity, not model accuracy.
        row['integer_clock_uniform'] = bool(valid and same_clock and
                row['max_grid_error_us'] <= 1 and row['max_interval_error_us'] <= 1)
        rows.append(row)
    summaries = {}
    for key in ['integer_clock_uniform'] + [f'candidate_{int(f*100)}pct' for f in TOLERANCE_FRACTIONS]:
        run = longest = 0
        longest_start = None
        start = None
        for i, r in enumerate(rows):
            if r[key]:
                if run == 0:
                    start = i
                run += 1
                if run > longest:
                    longest, longest_start = run, start
            else:
                run = 0
        count = sum(r[key] for r in rows)
        summaries[key] = dict(windows=count, fraction_of_all_windows=count/len(rows) if rows else None,
            longest_consecutive_window_starts=longest,
            longest_run_start_event=rows[longest_start]['start_index'] if longest else None,
            longest_run_end_event=rows[longest_start+longest-1]['end_index'] if longest else None)
    usable = [r for r in rows if r['span_us'] is not None]
    return rows, dict(total_sliding_windows=len(rows),
        invalid_or_ambiguous_clock_windows=sum(r['span_us'] is None for r in rows),
        span_us=stats([r['span_us'] for r in usable]),
        span_absolute_ideal_error_us=stats([abs(r['span_us']-19*PERIOD_US) for r in usable]),
        max_grid_error_us=stats([r['max_grid_error_us'] for r in usable]),
        criteria=summaries)


def write_csv(path, rows):
    if not rows:
        return
    with path.open('x', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def validate(pcap, output, source_sha256=None):
    output.mkdir(parents=True, exist_ok=False)
    events, packet_counts = read_events(pcap)
    boundaries = clock_segments(events)
    kept = select_first_valid(events)
    before_intervals, before_timing = intervals(events)
    after_intervals, after_timing = intervals(kept)
    before_windows, before_window_summary = windows(events)
    after_windows, after_window_summary = windows(kept)
    decisions = dict(collections.Counter(e.decision for e in events))
    retry_firsts = [e.index for e in kept if e.meta['retry']]
    drop = [e for e in events if e.decision == 'drop_retransmission']
    by_index = {e.index:e for e in events}
    # Verify selected data are exactly the first complete valid observations,
    # with no cross-TID/fragment deletion and no copying/interpolation.
    for e in drop:
        a = by_index[e.first_valid]
        if not (a.valid and a.index < e.index and a.decision == 'keep' and e.meta['retry'] and
                all(a.meta[k] == e.meta[k] for k in ('mac','channel','tid','seq'))):
            raise ValueError('First-valid retention invariant violated')
    ledger = []
    for e in events:
        ledger.append(dict(index=e.index, **e.meta, valid=e.valid, invalid_reason=e.reason,
            segment=e.segment, segment_time_us=e.time_us, decision=e.decision,
            first_valid_index=e.first_valid))
    write_csv(output/'events.csv', ledger)
    write_csv(output/'clock-boundaries.csv', boundaries)
    write_csv(output/'retained-intervals.csv', after_intervals)
    write_csv(output/'retained-windows20.csv', after_windows)
    np.savez_compressed(output/'retained-node-events.npz',
        packed_words=np.asarray([e.words for e in kept], dtype='<u4'),
        original_event_indices=np.asarray([e.index for e in kept], dtype='<u4'),
        rx_tsf16=np.asarray([e.meta['rx_tsf16'] for e in kept], dtype='<u2'),
        clock_segments=np.asarray([e.segment for e in kept], dtype='<u4'),
        segment_time_us=np.asarray([e.time_us for e in kept], dtype='<u8'),
        sequence_control=np.asarray([e.meta['seq'] for e in kept], dtype='<u2'),
        qos_tid=np.asarray([e.meta['tid'] if e.meta['tid'] is not None else 255 for e in kept], dtype='u1'),
        retry=np.asarray([e.meta['retry'] for e in kept], dtype=bool))
    result = dict(schema=1, offline_only=True, source_pcap=str(pcap.resolve()),
        source_sha256_from_capture_manifest=source_sha256,
        model_ready=False, model_or_preprocessing_or_board_protocol_changed=False,
        strict_original_acquisition_result_changed=False, packet_counts=packet_counts,
        selection=dict(events_read=len(events), decisions=decisions, retained=len(kept),
            retained_first_seen_retry_indices=retry_firsts,
            removal_rule='Valid Retry=1 with same source/channel/TID/full Sequence Control as a recent valid observation; keep first complete valid group. 20ms horizon extends with observed retries.',
            invalid_events=[dict(index=e.index,reason=e.reason) for e in events if not e.valid]),
        timing_policy=dict(target_hz=300, target_period_us=PERIOD_US, samples_per_window=20,
            ideal_first_to_last_us=19*PERIOD_US, retry_horizon_us=RETRY_HORIZON_US,
            clock_half_wrap_guard_us=CLOCK_HALF_WRAP_US,
            timestamp_basis='Hardware RxTSFTime low16, modulo increments only within conservative continuous segments; arrival time is a gap guard.',
            interpretation='10/25/50 percent are fixed candidate adapter filters, NOT paper-derived or validated model tolerance. No interpolation or grid reselection is used.'),
        clock_boundaries=len(boundaries), before=dict(timing=before_timing,windows20=before_window_summary),
        after=dict(timing=after_timing,windows20=after_window_summary),
        model_contract=dict(required_raw_shape=[3,3,30,20],available_receiver_nodes=1,
            available_chains_per_node=3,available_native_fft_points=64,
            carrier_mapping_done=False,multi_node_sync_done=False,model_inference_performed=False,
            time_candidates_are_not_full_model_inputs=True),
        limitations=['Background and idle periods are included. Sender QPC and receiver clock lack a shared anchor; no per-UDP-slot RF mapping or hand-picked active interval.',
            'Packet metadata do not include FCS outcome. Validity here means paired complete three-core data, finite and nonzero CSI excluding PHY-overwritten words, with consistent identity.',
            'The low16 clock cannot prove absence of hidden whole-wrap offsets or provide cross-node synchronization; ambiguous gaps split segments.',
            'No temporal tolerance has been validated against pose accuracy. Even good single-node timing windows do not meet the full 3-node/30-carrier contract.'])
    (output/'summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('pcap',type=Path); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source-sha256',help='Reuse the existing capture identity; do not recompute or overwrite it')
    args = p.parse_args()
    r = validate(args.pcap,args.output,args.source_sha256)
    print(json.dumps(dict(selection=r['selection'],clock_boundaries=r['clock_boundaries'],
                         before=r['before'],after=r['after'],model_ready=r['model_ready']),indent=2))

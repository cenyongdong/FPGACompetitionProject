"""Offline common-packet audit of three NMD3 captures from ONE bounded TX job.

This wraps the existing NodeStream and its fixed 300Hz grid. It never creates
samples, fits clock drift, changes CSI, or emits model/board input. Batch and
receiver identities must come from the acquisition manifest: NMD3 does not
carry an application batch/slot ID or a shared hardware clock.
"""
import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path

from diagnose_metadata import packets
from router_tx_job import decode_stats
from stream_node import NodeStream
from stream_time_grid import HZ, SCALE, HALF


@dataclass
class Receiver:
    name: str
    batch: str
    events: list
    windows: list
    state: dict
    path: str = ''


def read_receiver(path, name, batch, source_mac, channel):
    stream = NodeStream(source_mac, channel)
    events, windows = [], []
    stream.on_event = events.append
    for stamp, port, payload in packets(Path(path)):
        windows.extend(stream.feed(stamp, port, payload))
    return Receiver(name, batch, events, windows, stream.finish(), str(path))


def identity(event):
    m = event.meta
    # Full Sequence Control retains the fragment bits; TID identifies a
    # sequence space, and is not the physical hardware queue number.
    return (m['mac'], m['channel'], m['tid'], m['seq'], m['fc'] & ~0x800)


def sequence_audit(events):
    kept = [e for e in events if e.decision == 'keep']
    collisions = [list(k) for k, n in Counter(map(identity, kept)).items() if n > 1]
    seq = [e.meta['seq'] >> 4 for e in kept]
    deltas = [(b-a) & 4095 for a, b in zip(seq, seq[1:])]
    return dict(retained=len(kept), retained_identity_collisions=collisions,
                ambiguous_forward_steps=sum(d == 0 or d >= 2048 for d in deltas),
                observed_mod4096_wraps=sum(b < a and 0 < d < 2048
                    for a, b, d in zip(seq, seq[1:], deltas)),
                skipped_sequence_numbers=sum(d-1 for d in deltas if 0 < d < 2048),
                nonzero_fragment_events=sum(bool(e.meta['seq'] & 15) for e in kept),
                ambiguous_identity_events=sum(e.decision == 'ambiguous_identity_reuse' for e in events),
                dropped_retransmissions=sum(e.decision == 'drop_retransmission' for e in events))


def summarize_receiver(receiver):
    valid = sum(w.valid for w in receiver.windows)
    return dict(receiver_id=receiver.name, batch_id=receiver.batch, pcap=receiver.path,
        sequence=sequence_audit(receiver.events), stream=receiver.state,
        local_grid=dict(complete_windows=len(receiver.windows), valid_windows=valid,
            valid_fraction=valid/len(receiver.windows) if receiver.windows else None,
            also_previous_interval_gate=sum(w.interval_gate for w in receiver.windows),
            reasons=dict(Counter(w.reason for w in receiver.windows if not w.valid))))


def common_runs(ordered_keys):
    runs, current = [], []
    for key in ordered_keys:
        if current and (((key[3] >> 4)-(current[-1][3] >> 4)) & 4095) != 1:
            runs.append(current)
            current = []
        current.append(key)
    if current:
        runs.append(current)
    return dict(longest_run_events=max(map(len, runs), default=0),
        nonoverlapping_20_event_candidates=sum(len(r)//20 for r in runs),
        sliding_20_event_candidates=sum(max(0, len(r)-19) for r in runs),
        proves_300hz_grid=False)


def compare(receivers, expected_slots=3000, tx_status=None):
    """Compare real events; a unique common identity fixes integer slot offset.

    An event is never assigned a time using its sequence number. Each local
    grid is already fixed by the original startup prefix. Later slot
    disagreements are reported and reject affected windows, never refitted.
    """
    if len(receivers) != 3 or len({r.name for r in receivers}) != 3:
        raise ValueError('Require three distinct receiver identities')
    if len({r.batch for r in receivers}) != 1 or not receivers[0].batch:
        raise ValueError('Different or absent TX batch: sequence numbers cannot associate recordings')
    if not 0 < expected_slots < 4096:
        raise ValueError('Require a single bounded TX job shorter than one sequence cycle')
    result = dict(schema=1, offline_only=True, batch_id=receivers[0].batch,
        expected_tx_slots=expected_slots, receivers=[summarize_receiver(r) for r in receivers],
        model_structure_or_preprocessing_or_board_protocol_changed=False,
        model_ready=False, hardware_synchronization_proven=False,
        no_interpolation=True, no_drift_fit=True, tx_status=tx_status,
        limitations=[
            'Batch and distinct receiver identities are acquisition-manifest evidence, not fields carried by NMD3.',
            'Sequence Control is conditional common-frame identity within this bounded, isolated TX job; it is not an application slot ID.',
            'RX TSF/event16 counters belong to each receiver. Neither their numeric equality nor PCAP wall clocks proves cross-radio clock synchronization.',
            'The joint denominator excludes startup, ambiguous clock segments and unfinished capture tails; it is not whole-run delivery coverage.',
            'Same-packet alignment does not prove shared RF clock, coherent phase, pose accuracy, or complete calibrated model input.'])
    maps = [{identity(e): e for e in r.events if e.decision == 'keep'} for r in receivers]
    union = set().union(*(set(m) for m in maps))
    common = set.intersection(*(set(m) for m in maps))
    ordered = [identity(e) for e in receivers[0].events
               if e.decision == 'keep' and identity(e) in common]
    result['common_packets'] = dict(union_identities=len(union), common_identities=len(common),
        missing_from_union_by_receiver=[len(union-set(m)) for m in maps],
        consecutive_events=common_runs(ordered))
    issues = []
    for r, summary in zip(receivers, result['receivers']):
        s = summary['sequence']
        kept = [e for e in r.events if e.decision == 'keep']
        if s['retained_identity_collisions'] or s['ambiguous_forward_steps'] or s['ambiguous_identity_events']:
            issues.append(r.name+': sequence reuse/wrap/order ambiguity')
        if s['nonzero_fragment_events']:
            issues.append(r.name+': unexpected fragmentation in bounded broadcast profile')
        if s['retained'] > expected_slots:
            issues.append(r.name+': more retained events than declared TX slots')
        if any((e.meta['fc'] & ~0x800) != 0x0008 or e.meta['tid'] is not None
               for e in kept):
            issues.append(r.name+': unexpected frame/sequence-space profile')
        if any('raw_rx_frame_size' not in e.meta or 'hook_tsf_l' not in e.meta for e in kept):
            issues.append(r.name+': NMD3 frame-size/clock diagnostics unavailable')
        if len({e.meta.get('raw_rx_frame_size') for e in kept}) > 1:
            issues.append(r.name+': frame length changes within the fixed TX profile')
        if r.state.get('clock_segment_resets', 0):
            issues.append(r.name+': cross-segment grid association is not implemented')
    if len({k[:3]+k[4:] for k in union}) > 1:
        issues.append('Source/channel/TID/frame type changes across captures')
    if any(len({m[k].meta.get('raw_rx_frame_size') for m in maps}) != 1 for k in common):
        issues.append('Matching sequence identities have conflicting raw frame lengths')
    if tx_status is not None:
        if (tx_status.get('rate_hz') != HZ or tx_status.get('error') != 0 or
            tx_status.get('running') != 0 or tx_status.get('remaining_slots') != 0 or
            tx_status.get('submitted_frames', -1)+tx_status.get('skipped_slots', -1) != expected_slots):
            issues.append('TX receipt does not certify the declared completed bounded job')
    fits = []
    for r in receivers:
        locked = [s for s in r.state['startup'] if s.get('locked')]
        if len(locked) != 1:
            issues.append(r.name+': require one uniquely locked local clock segment')
        fits.append(locked[0] if len(locked) == 1 else None)
    if not ordered:
        issues.append('No common first-valid events')
    if issues:
        result['joint_grid'] = dict(status='unproven', reasons=issues, valid_windows=None)
        return result

    def local_slot(event, fit):
        return (event.time_us*HZ-fit['phase_scaled']+HALF)//SCALE

    # A common unique event after every local startup fixes the integer
    # origin. It does not estimate a clock rate or optimize later windows.
    anchors = [k for k in ordered if all(m[k].time_us > f['calibration_end_us']
                                         for m, f in zip(maps, fits))]
    if not anchors:
        result['joint_grid'] = dict(status='unproven', reasons=['No common post-startup anchor'], valid_windows=None)
        return result
    anchor = anchors[0]
    anchor_slots = [local_slot(m[anchor], f) for m, f in zip(maps, fits)]
    shifts = [anchor_slots[0]-slot for slot in anchor_slots]
    mismatch = [sum(local_slot(m[k], f)+shift != local_slot(maps[0][k], fits[0])
                    for k in ordered) for m, f, shift in zip(maps, fits, shifts)]

    cells = []
    for r, fit, shift in zip(receivers, fits, shifts):
        node = {}
        for w in r.windows:
            for target, observation in zip(w.target_scaled, w.observations):
                slot = (target-fit['phase_scaled'])//SCALE+shift
                if slot in node:
                    raise ValueError('Local grid reused a finalized cell')
                node[slot] = (observation, target)
        cells.append(node)
    if any(not c for c in cells):
        result['joint_grid'] = dict(status='unproven', reasons=['No finalized cells at every receiver'], valid_windows=None)
        return result
    first = max(min(c) for c in cells)
    # Preserve receiver 0's original nonoverlapping 20-slot partition. No
    # phase or block-boundary search is allowed to improve acceptance.
    first += (min(cells[0])-first) % 20
    last = min(max(c) for c in cells)
    rows = []
    for start in range(first, last-18, 20):
        reasons, node_intervals = [], []
        selected = []
        for slot in range(start, start+20):
            triplet = [c.get(slot, (None, None)) for c in cells]
            observations = [x[0] for x in triplet]
            selected.append(observations)
            if any(o is None for o in observations):
                reasons.append('missing_cell')
            elif any(abs(o.time_us*HZ-target) > .25*SCALE
                     for o, target in triplet):
                reasons.append('point_error')
            elif len({identity(receivers[n].events[o.index])
                      for n, o in enumerate(observations)}) != 1:
                reasons.append('different_selected_event')
        for node_index in range(3):
            obs = [triplet[node_index] for triplet in selected]
            node_intervals.append(all(o is not None for o in obs) and all(
                abs((b.time_us-a.time_us)*HZ-SCALE) <= .25*SCALE
                for a, b in zip(obs, obs[1:])))
        rows.append(dict(start_reference_slot=start, valid=not reasons,
            reasons=sorted(set(reasons)), also_previous_interval_gate=all(node_intervals)))
    valid = sum(row['valid'] for row in rows)
    result['joint_grid'] = dict(status='common_packet_anchor_proven',
        anchor_sequence_control=anchor[3], anchor_local_slots=anchor_slots,
        fixed_integer_slot_shifts=shifts, common_event_slot_disagreements=mismatch,
        complete_windows=len(rows), valid_windows=valid,
        valid_fraction=valid/len(rows) if rows else None,
        also_previous_interval_gate=sum(r['valid'] and r['also_previous_interval_gate'] for r in rows),
        reasons=dict(Counter(reason for row in rows for reason in row['reasons'])), windows=rows,
        hardware_clock_or_phase_coherence_proven=False,
        acceptance_scope='Same real TX event in every selected cell, all three unchanged local point gates; no shared hardware clock claim.')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pcaps', nargs=3, type=Path, required=True)
    p.add_argument('--receiver-ids', nargs=3, required=True)
    p.add_argument('--batch-ids', nargs=3, required=True)
    p.add_argument('--source-mac', required=True)
    p.add_argument('--channel', type=lambda v: int(v, 0), required=True)
    p.add_argument('--expected-slots', type=int, default=3000)
    p.add_argument('--tx-result', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if len({path.resolve() for path in a.pcaps}) != 3:
        p.error('Three independent capture paths are required')
    tx = decode_stats(json.loads(a.tx_result.read_text(encoding='utf-8-sig'))['stdout']) if a.tx_result else None
    result = compare([read_receiver(path, name, batch, a.source_mac, a.channel)
        for path, name, batch in zip(a.pcaps, a.receiver_ids, a.batch_ids)], a.expected_slots, tx)
    with a.output.open('x', encoding='utf-8') as out:
        json.dump(result, out, indent=2, ensure_ascii=False, allow_nan=False)
    print(json.dumps({k: result[k] for k in ('common_packets', 'joint_grid')}, ensure_ascii=False))

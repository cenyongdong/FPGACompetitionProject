"""Associate diagnostic UDP slots by unique observed length-code runs.

Uses no timestamps or SeqCtl to choose a slot. An eight-size sequence must be
unique in the sent ledger, conflict free, and ordered. Missing/ambiguous
associations stay absent. This is a coded experiment, not general decryption
or an association method for the ordinary fixed-size sender.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np

from analyze_node_stability import replay_events
from audit_sampling_clocks import distribution, ledger_audit, slope
from diagnose_metadata import decode, packets


def match_codes(sent_sizes, received_sizes, overhead, width=8,
                sent_contiguous=None, received_contiguous=None):
    expected = defaultdict(list)
    for i in range(len(sent_sizes)-width+1):
        if sent_contiguous is not None and not all(sent_contiguous[i:i+width-1]):
            continue
        expected[tuple(sent_sizes[i:i+width])].append(i)
    choices = defaultdict(set)
    anchors = 0
    for j in range(len(received_sizes)-width+1):
        if received_contiguous is not None and not all(received_contiguous[j:j+width-1]):
            continue
        key = tuple(s-overhead for s in received_sizes[j:j+width])
        candidates = expected.get(key, ())
        if len(candidates) != 1:
            continue
        anchors += 1
        i = candidates[0]
        for k in range(width):
            choices[j+k].add(i+k)
    conflicts = sum(len(v) != 1 for v in choices.values())
    pairs = [(j, next(iter(v))) for j, v in choices.items() if len(v) == 1]
    multiplicity = defaultdict(list)
    for j, i in pairs:
        multiplicity[i].append(j)
    pairs = sorted((j, i) for j, i in pairs if len(multiplicity[i]) == 1)
    if any(b[1] <= a[1] for a, b in zip(pairs, pairs[1:])):
        raise ValueError('Length associations disagree with send order; do not guess')
    return pairs, dict(unique_run_anchors=anchors, conflicting_received_indices=conflicts,
        multiply_received_send_slots=sum(len(v)>1 for v in multiplicity.values()),
        ambiguous_sent_runs=sum(len(v)>1 for v in expected.values()), width=width)


def continuity(sends, kept):
    # A loss can accidentally leave the same length at the start of a later
    # unique run. Never anchor across a missing/reordered MPDU or send slot.
    # SeqCtl is a continuity guard, not the application slot identifier.
    tx = [b[0]-a[0] == 1 for a,b in zip(sends,sends[1:])]
    rx = [(b.meta['seq']-a.meta['seq'])%65536 == 16 and
          a.meta['tid'] == b.meta['tid'] and not (a.meta['seq'] & 15 or b.meta['seq'] & 15)
          for a,b in zip(kept,kept[1:])]
    return dict(sent_contiguous=tx,received_contiguous=rx)


def read(directory, profile):
    events, _, final = replay_events(directory/'capture.pcap', profile, retry_startup=True)
    kept = [e for e in events if e.decision == 'keep']
    sender = json.loads((directory/'sender.json').read_text(encoding='utf-8-sig'))
    if sender.get('mode') != 'coded_length_diagnostic':
        raise ValueError('Only independently length-coded jobs can be associated')
    if any('raw_rx_frame_size' not in e.meta for e in kept):
        raise ValueError('NMD3 raw RX size required')
    return events, kept, sender, final


def hook_clock_audit(directory):
    records = [decode(p) for _, port, p in packets(directory/'capture.pcap') if port == 5501]
    if not records or any('hook_tsf_l' not in d for d in records):
        raise ValueError('NMD3 hook clock required')
    delay = [d['hook_minus_rx_low16'] for d in records]
    return dict(records=len(records), hook_minus_rx_mod65536_us=distribution(delay),
        records_at_or_above_half_wrap=sum(t>=32768 for t in delay),
        interpretation='Firmware processing context, not NIC-to-host or absolute propagation latency')


def anchored_rx32(kept):
    # Anchor a candidate RF low32 using nearby firmware TSF low32. This does
    # not replace the production low16 continuity guard. Modulo ambiguity is
    # reported and excluded, never resolved with host wall time.
    result = []
    previous = None
    elapsed = 0
    for e in kept:
        m = e.meta
        if m['hook_minus_rx_low16'] >= 32768:
            raise ValueError('Firmware/RX low16 anchor outside conservative half wrap')
        value = (m['hook_tsf_l']-m['hook_minus_rx_low16']) & 0xffffffff
        if previous is not None:
            delta = (value-previous) & 0xffffffff
            if not 0 < delta < 2**31:
                raise ValueError('Anchored RX low32 is not monotonic')
            elapsed += delta
        result.append(elapsed)
        previous = value
    return np.asarray(result, dtype='i8')


def analyze(directory, profile, overhead):
    events, kept, sender, final = read(directory, profile)
    sends = sender['sends']
    pairs, info = match_codes([r[4] for r in sends], [e.meta['raw_rx_frame_size'] for e in kept], overhead,
                             **continuity(sends,kept))
    if len(pairs) < 20:
        raise ValueError('Insufficient length-only associations')
    rf = anchored_rx32(kept)
    observed = np.asarray([rf[j] for j, _ in pairs], dtype='f8')
    before = np.asarray([sends[i][2] for _, i in pairs], dtype='f8')/1000
    slots = np.asarray([sends[i][0] for _, i in pairs], dtype='i8')
    qpc = before-before[0]
    rx = observed-observed[0]
    bins = defaultdict(list)
    for t, diff in zip(qpc, rx-qpc):
        bins[int(t//250_000)].append((t, diff))
    centres, qs = [], []
    for rows in bins.values():
        if len(rows) < 10:
            continue
        arr = np.asarray(rows)
        centres.append(float(np.median(arr[:,0])))
        qs.append(np.percentile(arr[:,1], [10,50,90]))
    rates = [slope(centres, [r[k] for r in qs]) for k in range(3)]
    rate = rates[1] or 0
    relative_delay = rx-qpc*(1+rate)
    relative_delay -= np.median(relative_delay)
    adjacent = np.diff(slots) == 1
    interval_excess = (np.diff(rx)-np.diff(qpc)*(1+rate))[adjacent]
    retries = np.asarray([bool(kept[j].meta['retry']) for j,_ in pairs])
    both_nonretry = adjacent & ~retries[:-1] & ~retries[1:]
    nonretry_excess = (np.diff(rx)-np.diff(qpc)*(1+rate))[both_nonretry]
    matches = [dict(event_index=kept[j].index, sender_row=i, slot=int(sends[i][0]),
        raw_rx_size=int(kept[j].meta['raw_rx_frame_size']), udp_size=int(sends[i][4]),
        sequence_control=int(kept[j].meta['seq']), tid=kept[j].meta['tid'],
        retry=bool(kept[j].meta['retry']),
        rx_elapsed_us=int(rf[j]), before_send_ns=int(sends[i][2])) for j,i in pairs]
    return dict(directory=str(directory), associations=info, length_overhead_frozen_from_pilot=overhead,
        matched_events=len(pairs), first_valid_events=len(kept), sends=len(sends),
        matched_send_fraction=len(pairs)/len(sends),
        sender=ledger_audit(sender), hook_clock=hook_clock_audit(directory),
        rf_us_per_qpc_us_ppm_by_delay_quantile=[None if r is None else r*1e6 for r in rates],
        quantiles=[.1,.5,.9],
        detrended_send_to_rx_delay_variation_us=distribution(relative_delay),
        delay_p95_minus_p05_us=float(np.percentile(relative_delay,95)-np.percentile(relative_delay,5)),
        adjacent_slot_pairs=int(adjacent.sum()),
        adjacent_rf_interval_us=distribution(np.diff(rx)[adjacent]),
        adjacent_send_interval_us=distribution(np.diff(qpc)[adjacent]),
        adjacent_rf_minus_clock_scaled_send_interval_us=distribution(interval_excess),
        interval_excess_absolute_above_833us=int((abs(interval_excess)>1e6/1200).sum()),
        both_nonretry_adjacent_pairs=int(both_nonretry.sum()),
        both_nonretry_interval_excess_us=distribution(nonretry_excess),
        both_nonretry_excess_absolute_above_833us=int((abs(nonretry_excess)>1e6/1200).sum()),
        phase_lock_successes=sum(s['locked'] for s in final['startup']),
        matches=matches,
        limitations=['Matches rely on unique eight-length runs and independent sequence-continuity guards, not decoded payloads.',
            'Unmatched sends are not proven RF losses: extractor suppression and incomplete diagnostic coverage remain possible.',
            'Clock ratio includes the trend of variable wireless delay; quantile sensitivity is reported, no physical correction adopted.',
            'Processing-anchored RX low32 is diagnostic only; production still uses the original conservative low16 segments.',
            'Different payload sizes and the PowerShell sender change airtime and CPU timing; this is not normal-sender stability acceptance.'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', required=True, type=Path)
    p.add_argument('--pilot', required=True, type=Path)
    p.add_argument('--capture', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a=p.parse_args();profile=json.loads(a.profile.read_text())
    _,kept,sender,_=read(a.pilot,profile)
    candidates=[]
    for overhead in range(257):
        try:pairs,info=match_codes([r[4] for r in sender['sends']], [e.meta['raw_rx_frame_size'] for e in kept],overhead,
                                 **continuity(sender['sends'],kept))
        except ValueError:continue
        candidates.append((len(pairs),overhead))
    candidates.sort(reverse=True)
    if not candidates or candidates[0][0]<80 or candidates[0][0]==candidates[1][0]:
        raise ValueError('Pilot failed to identify a unique constant length overhead')
    overhead=candidates[0][1]
    pilot=analyze(a.pilot,profile,overhead)
    evaluation=analyze(a.capture,profile,overhead)
    result=dict(hardware_record_replay=True,pilot=pilot,evaluation=evaluation,
        pilot_overhead_top_candidates=candidates[:5],
        model_preprocess_math_board_protocol_changed=False,stable_300hz_acceptance=False)
    a.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    for r in (pilot,evaluation):
        print(json.dumps({k:v for k,v in r.items() if k not in ('matches','limitations','sender')}))


if __name__=='__main__':main()

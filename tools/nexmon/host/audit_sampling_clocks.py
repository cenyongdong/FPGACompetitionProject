"""Offline clock and scheduling audit, never an input-selection correction.

RF RX TSF, router CLOCK_REALTIME and sender QPC are separate clocks. Frame
sequence numbers do not bind encrypted MPDUs to application UDP slots. A
fixed-scale counterfactual is learned only from designated earlier captures
and evaluated on separate captures; it is not an oscillator calibration.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

import numpy as np

from analyze_node_stability import replay_events
from stream_time_grid import TimeGridStream


def distribution(values):
    x = np.asarray(values, dtype='f8')
    if not len(x):
        return dict(n=0)
    return dict(n=len(x), **{k: float(v) for k, v in zip(
        ('min', 'p01', 'p50', 'p95', 'p99', 'max'),
        np.percentile(x, [0, 1, 50, 95, 99, 100]))})


def slope(x, y):
    """Median of pair slopes >=1 s apart; do not let a short burst set rate."""
    pairs = [(b-d)/(a-c) for i, (a, b) in enumerate(zip(x, y))
             for c, d in zip(x[:i], y[:i]) if a-c >= 1_000_000]
    return float(np.median(pairs)) if pairs else None


def receiver_scale(events, bin_us=250_000):
    """Estimate relative RX ticks/Linux time, with variable delivery delay.

    Bin paired differences (not a difference of independently ranked clocks).
    Lower/upper quantiles expose sensitivity to processing delays. Host wall
    time may also be disciplined; this cannot establish absolute SI scale.
    """
    groups = defaultdict(list)
    for e in events:
        groups[e.segment].append(e)
    out = []
    for segment, g in sorted(groups.items()):
        if len(g) < 2:
            continue
        rf = np.asarray([e.time_us-g[0].time_us for e in g], dtype='f8')
        host = np.asarray([(e.meta['time']-g[0].meta['time'])*1e6 for e in g])
        bins = defaultdict(list)
        for t, error in zip(rf, host-rf):
            bins[int(t//bin_us)].append((t, error))
        centres, qs = [], []
        for _, rows in sorted(bins.items()):
            if len(rows) < 10:
                continue
            a = np.asarray(rows)
            centres.append(float(np.median(a[:, 0])))
            qs.append(np.percentile(a[:, 1], [10, 50, 90]))
        slopes = [slope(centres, [row[i] for row in qs]) for i in range(3)]
        median = slopes[1]
        detrended = host-rf-(median*rf if median is not None else 0)
        # Subtract an arbitrary median: this is delay variation, not latency.
        detrended -= np.median(detrended)
        out.append(dict(segment=segment, events=len(g), span_rx_us=int(rf[-1]),
            linux_us_per_rx_tick_ppm_by_delay_quantile=[None if s is None else s*1e6 for s in slopes],
            quantiles=[.1, .5, .9], bins=len(centres),
            detrended_delivery_delay_variation_us=distribution(detrended),
            absolute_clock_calibration=False))
    return out


def phase_trends(events, startup):
    out = []
    for lock in (s for s in startup if s.get('locked')):
        bins = defaultdict(list)
        for e in events:
            if e.decision == 'keep' and e.segment == lock['segment'] and e.time_us > lock['calibration_end_us']:
                bins[(e.time_us-lock['calibration_end_us'])//1_000_000].append(e)
        centres, medians, rows = [], [], []
        for second, items in sorted(bins.items()):
            if len(items) < 120:
                continue
            times = np.asarray([e.time_us for e in items], dtype='i8')
            residual = ((times*300-lock['phase_scaled']+500_000)%1_000_000-500_000)/300
            # A local circular centre handles values straddling the phase cut.
            z = np.mean(np.exp(2j*np.pi*residual/(1e6/300)))
            seed = np.angle(z)*(1e6/300)/(2*np.pi)
            centred = (residual-seed+1e6/600)%(1e6/300)-1e6/600
            centre = float(seed+np.median(centred))
            centres.append(float(np.median(times)))
            medians.append(centre)
            rows.append(dict(second=int(second), events=len(items), median_residual_us=centre,
                concentration=float(abs(z)), outside_tolerance_fraction=float(np.mean(abs(residual)>1e6/1200))))
        if len(medians) > 1:
            medians = (np.unwrap(np.asarray(medians)*2*np.pi/(1e6/300))*(1e6/300)/(2*np.pi)).tolist()
        rate = slope(centres, medians)
        out.append(dict(segment=lock['segment'], post_lock_bins=rows,
            residual_slope_us_per_s=None if rate is None else rate*1e6,
            interpretation='Observed periodic phase trend; includes clock ratio and scheduling, not physical calibration'))
    return out


def ledger_audit(sender):
    rows = np.asarray(sender['sends'], dtype='i8')
    if rows.ndim != 2 or rows.shape[1] != 5 or len(rows) < 2:
        raise ValueError('Sender ledger shape')
    slots, target, before, after, size = rows.T
    if (np.any(np.diff(slots) <= 0) or np.any(np.diff(target) <= 0) or
            np.any(np.diff(before) <= 0) or np.any(after < before)):
        raise ValueError('Invalid sender ledger ordering')
    nominal = (slots-slots[0])*1e9/sender['requested_hz']
    return dict(sends=len(rows), skipped=sender['skipped_late_slots'],
        relative_deadline_quantization_ns=distribution((target-target[0])-nominal),
        call_lateness_us=distribution((before-target)/1000),
        call_duration_us=distribution((after-before)/1000),
        call_interval_us=distribution(np.diff(before)/1000),
        bytes_histogram={str(int(k)): int(v) for k, v in zip(*np.unique(size, return_counts=True))},
        trusted_udp_slot_to_rf_associations=0,
        reason='A send ledger alone cannot associate an RF event; SeqCtl/TID alone is insufficient')


def replay_fixed_scale(events, rx_ticks_per_nominal_us_ppm=0):
    """Independent offline experiment. Scale timestamp coordinates, never CSI.

    Same first-valid events, 1 s startup, 300 Hz, .25 tolerance and 20 slots.
    No event interpolation, no new observations, no changes to the live path.
    """
    if not np.isfinite(rx_ticks_per_nominal_us_ppm) or abs(rx_ticks_per_nominal_us_ppm) > 1000:
        raise ValueError('Diagnostic scale outside bounded clock experiment')
    ratio = 1+rx_ticks_per_nominal_us_ppm/1e6
    grid = TimeGridStream(retry_startup=True)
    windows, segment = [], None
    for e in events:
        if e.decision != 'keep':
            continue
        if e.segment != segment:
            grid.finish()
            grid.reset(e.segment)
            segment = e.segment
        windows.extend(grid.feed(round(e.time_us/ratio), e.index))
    grid.finish()
    return dict(valid_windows=sum(w.valid for w in windows), windows=len(windows),
        valid_fraction=sum(w.valid for w in windows)/len(windows) if windows else None,
        interval_gate_windows=sum(w.valid and w.interval_gate for w in windows),
        rejected=dict(Counter(w.reason for w in windows if not w.valid)),
        startup=list(grid.startup_records), real_observations_only=True)


def audit_capture(directory, profile):
    events, windows, final = replay_events(directory/'capture.pcap', profile, retry_startup=True)
    kept = [e for e in events if e.decision == 'keep']
    intervals = [b.time_us-a.time_us for a, b in zip(kept, kept[1:]) if a.segment == b.segment]
    sequence = Counter()
    for a, b in zip(kept, kept[1:]):
        if a.segment == b.segment and a.meta['tid'] == b.meta['tid']:
            sequence[(b.meta['seq']-a.meta['seq'])%65536] += 1
    base = replay_fixed_scale(events)
    if (base['windows'], base['valid_windows']) != (len(windows), sum(w.valid for w in windows)):
        raise ValueError('Independent unscaled grid replay disagrees with existing path')
    result = dict(directory=str(directory), baseline=base,
        sender=ledger_audit(json.loads((directory/'sender.json').read_text(encoding='utf-8-sig'))),
        receiver_linux_clock_comparison=receiver_scale(events),
        phase=phase_trends(events, final['startup']),
        first_valid_rf_interval_us=distribution(intervals),
        rf_intervals_shorter_than_half_period=sum(x < 1e6/600 for x in intervals),
        rf_intervals_longer_than_1_5_period=sum(x > 5000 for x in intervals),
        retained_sequence_control_steps=dict(sequence),
        complete_events=len(events), first_valid_events=len(kept))
    return events, result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', required=True, type=Path)
    p.add_argument('--fit', required=True, type=Path, nargs='+')
    p.add_argument('--evaluate', required=True, type=Path, nargs='+')
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    if set(d.resolve() for d in a.fit) & set(d.resolve() for d in a.evaluate):
        raise ValueError('Scale fit/evaluation captures overlap')
    profile = json.loads(a.profile.read_text())
    fit = [audit_capture(d, profile)[1] for d in a.fit]
    rates = [s['residual_slope_us_per_s'] for r in fit for s in r['phase']
             if s['residual_slope_us_per_s'] is not None and len(s['post_lock_bins']) >= 4]
    if not rates:
        raise ValueError('Insufficient earlier captures for diagnostic scale hypothesis')
    ppm = float(np.median(rates))
    evaluation = []
    for d in a.evaluate:
        events, r = audit_capture(d, profile)
        r['earlier_fit_fixed_scale_counterfactual'] = replay_fixed_scale(events, ppm)
        evaluation.append(r)
    result = dict(offline_only=True, fit_captures=fit, evaluation_captures=evaluation,
        frozen_hypothesis_rx_ticks_per_nominal_us_ppm=ppm, hypothesis_fitted_only_on_earlier_captures=True,
        absolute_clock_scale_validated=False, trusted_tx_rf_associations=0,
        live_sampler_changed=False, model_preprocess_math_board_protocol_changed=False,
        adoption='Diagnostic comparison only; clock skew is not proven independently of wireless scheduling',
        limitations=['Linux capture timestamps include variable driver/kernel/capture delays and possible wall-clock discipline.',
            'RX TSF low16 is unwrapped only within the existing conservative clock segments.',
            'Phase slope estimates use nominal traffic periodicity, not a shared clock or identified UDP payloads.',
            'No attribution of missing CSI to sender driver, RF loss, aggregation or Nexmon suppression is established.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(frozen_ppm=ppm, evaluation=[dict(directory=r['directory'],
        original=r['baseline'], scaled=r['earlier_fit_fixed_scale_counterfactual']) for r in evaluation])))


if __name__ == '__main__':
    main()

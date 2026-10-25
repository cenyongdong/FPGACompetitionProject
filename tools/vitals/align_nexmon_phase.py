"""Offline Nexmon differential-phase timing adapter; never emits strict CSI or HR.

Use first-valid three-core events in ONE continuous RX-clock segment. Time-aware
interpolation precedes anti-alias filtering and 50Hz reduction. Source phase jumps
and gaps invalidate the ENTIRE filter support, even if filtering hides the jump.
No source mutation, extrapolation, segment joining, invented RF IDs or clock claims.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy import signal

from audit_nexmon_vitals import CARRIERS, PAIRS, describe, load_segment, save
from native_carriers import decode_selected

RATE = 50
WORK_RATE = 600
FIR_TAPS = 481
FIR_CUTOFF_HZ = 15
MAX_GAP_NS = 10_000_000  # Conservative offline eligibility bound, not RF certification.
MAX_PHASE_STEP = .25    # Existing reference quality limit; never relaxed after filtering.
HISTORY_SAMPLES = 2000  # Unchanged 10s warmup + 30s analysis at 50Hz.


def differential_phase(pairs):
    pairs = np.asarray(pairs)
    if pairs.ndim != 3 or pairs.shape[1:] != (4, 2) or not np.isfinite(pairs).all():
        raise ValueError('Require finite same-frame antenna pairs [N,4,2]')
    scale = np.maximum(abs(pairs.real), abs(pairs.imag))
    if (scale < 1e-12).any():
        raise ValueError('Undefined phase at zero/insufficient antenna amplitude')
    normalized = pairs / scale
    return np.angle(normalized[:, :, 0] * normalized[:, :, 1].conj())


def longest_run(mask):
    edges = np.flatnonzero(np.diff(np.r_[False, mask, False].astype(np.int8)))
    return int(np.max(edges[1::2] - edges[::2], initial=0))


def window_quality(grid_ns, phase, valid):
    """Count overlapping one-second-stride histories; never shorten or pad 40s."""
    candidates = qualified = 0
    for first in range(0, len(grid_ns) - HISTORY_SAMPLES + 1, RATE):
        candidates += 1
        sl = slice(first, first + HISTORY_SAMPLES)
        if not valid[sl].all():
            continue
        values = phase[sl]
        if (np.abs(np.diff(values, axis=0)) > MAX_PHASE_STEP).any():
            continue
        rms = np.sqrt(np.mean(signal.detrend(values, axis=0) ** 2, axis=0))
        qualified += int((rms <= 1).all())
    return dict(required_samples=HISTORY_SAMPLES, required_history_seconds=40,
                candidate_windows=candidates, locally_qualified_windows=qualified,
                longest_all_channel_valid_samples=longest_run(valid.all(axis=1)),
                rf_clock_certified=False, strict_cpp_input_emitted=False,
                reason='insufficient_40s_history' if not candidates else
                       ('source_phase_or_gap_or_output_quality' if not qualified else
                        'local_signal_checks_only_not_RF_or_physiological_validation'))


def align_phase(times_ns, wrapped_phase):
    stamps = np.asarray(times_ns)
    wrapped = np.asarray(wrapped_phase, dtype=float)
    if (stamps.ndim != 1 or stamps.dtype.kind not in 'iu' or len(stamps) < 3 or
            len(stamps) > 50000 or stamps.min() < 0 or
            stamps.max() > np.iinfo(np.int64).max):
        raise ValueError('Require 3..50000 nonnegative int64-range source timestamps')
    stamps = stamps.astype(np.int64)
    if (np.diff(stamps) <= 0).any():
        raise ValueError('Non-monotone source clock; do not sort or repair')
    if wrapped.shape != (len(stamps), 4) or not np.isfinite(wrapped).all():
        raise ValueError('Require finite [N,4] phase')
    stamps = stamps - stamps[0]
    if stamps[-1] > 180_000_000_000:
        raise ValueError('Offline adapter is bounded to one segment <=180s')
    unwrapped = np.unwrap(wrapped, axis=0)
    steps = abs(np.angle(np.exp(1j * np.diff(wrapped, axis=0))))
    jump = steps > MAX_PHASE_STEP
    gaps = np.diff(stamps) > MAX_GAP_NS
    # A 2pi representation wrap is removed; a smaller true discontinuity is NOT.
    dense_indices = np.arange(int(stamps[-1] * WORK_RATE // 1_000_000_000) + 1)
    dense_t = dense_indices / WORK_RATE
    taps = signal.firwin(FIR_TAPS, FIR_CUTOFF_HZ, fs=WORK_RATE, window=('kaiser', 8.6))
    half = FIR_TAPS // 2
    if len(dense_t) < FIR_TAPS:
        raise ValueError('Insufficient measured FIR context; no extrapolation allowed')
    dense = np.column_stack([np.interp(dense_t, stamps / 1e9, unwrapped[:, ch])
                             for ch in range(4)])
    filtered = signal.convolve(dense, taps[:, None], mode='valid', method='auto')
    centers = np.arange(half, len(dense_t) - half)
    retained = centers % (WORK_RATE // RATE) == 0
    centers = centers[retained]
    grid_ns = (centers // (WORK_RATE // RATE)) * (1_000_000_000 // RATE)
    values = filtered[retained]
    # Include exact source brackets used at BOTH filter edges. Tiny jump intervals
    # between work-grid points must remain visible in the source-quality mask.
    left_ns = grid_ns - half * 1_000_000_000 // WORK_RATE
    right_ns = grid_ns + half * 1_000_000_000 // WORK_RATE
    first = np.searchsorted(stamps, left_ns, side='right') - 1
    last = np.searchsorted(stamps, right_ns, side='left')
    gap_prefix = np.r_[0, np.cumsum(gaps)]
    jump_prefix = np.vstack((np.zeros(4, dtype=int), np.cumsum(jump, axis=0)))
    gap_bad = gap_prefix[last] > gap_prefix[first]
    phase_bad = jump_prefix[last] > jump_prefix[first]
    valid = ~phase_bad & ~gap_bad[:, None]
    # Values in an invalid footprint are absent, not smoothed replacement data.
    values[~valid] = np.nan
    quality = dict(target_rate_hz=RATE, target_interval_ms=1000 / RATE,
        target_samples=len(grid_ns), work_rate_hz=WORK_RATE,
        fir_taps=FIR_TAPS, fir_cutoff_hz=FIR_CUTOFF_HZ,
        measured_context_seconds_per_side=half / WORK_RATE,
        filter='linear-time interpolation then symmetric Kaiser beta=8.6 FIR then decimation',
        source_gap_limit_ms=MAX_GAP_NS / 1e6,
        source_max_gap_ms=float(np.diff(stamps).max() / 1e6),
        source_gap_faults=int(gaps.sum()), source_phase_step_limit_rad=MAX_PHASE_STEP,
        source_phase_jumps=jump.sum(axis=0).tolist(),
        phase_invalid_output_samples=phase_bad.sum(axis=0).tolist(),
        gap_invalid_output_samples=int(gap_bad.sum()),
        locally_valid_samples_per_channel=valid.sum(axis=0).tolist(),
        longest_valid_samples_per_channel=[longest_run(valid[:, ch]) for ch in range(4)],
        all_channel_valid_samples=int(valid.all(axis=1).sum()),
        quality_scope='conservative offline signal support; not an accepted production RF profile',
        derived_grid_is_acquisition_clock=False,
        windows=window_quality(grid_ns, values, valid))
    return dict(source_ns=stamps, source_wrapped_phase=wrapped,
                source_unwrapped_phase=unwrapped, source_jump=jump, source_gap=gaps,
                grid_ns=grid_ns, phase=values, valid=valid,
                source_support_first=first, source_support_last=last), quality


def timing_comparison(stamps):
    """Contrast every-sixth with actual nearest-to-20ms sample selection (no FIR)."""
    stamps = np.asarray(stamps) - stamps[0]
    every_sixth = stamps[::6]
    grid = np.arange(0, stamps[-1] + 1, 20_000_000, dtype=np.int64)
    right = np.searchsorted(stamps, grid).clip(0, len(stamps) - 1)
    left = (right - 1).clip(0, len(stamps) - 1)
    chosen = np.where(abs(stamps[left] - grid) <= abs(stamps[right] - grid), left, right)
    offsets = stamps[chosen] - grid
    # Keep original timestamps: don't call the ideal grid a measured acquisition.
    actual = stamps[chosen]
    return dict(
        every_sixth=dict(samples=len(every_sixth),
            interval_ms=describe(np.diff(every_sixth) / 1e6),
            interval_errors_over_2ms=int((abs(np.diff(every_sixth) - 20_000_000) > 2_000_000).sum()),
            final_elapsed_error_ms=float((every_sixth[-1] - (len(every_sixth) - 1) * 20_000_000) / 1e6)),
        nearest_grid=dict(samples=len(grid), anchor='first source event; no phase fitting',
            offset_ms=describe(abs(offsets) / 1e6),
            interval_errors_over_2ms=int((abs(np.diff(actual) - 20_000_000) > 2_000_000).sum()),
            grid_points_without_sample_within_1ms=int((abs(offsets) > 1_000_000).sum()),
            duplicated_source_samples=int((np.diff(chosen) == 0).sum()),
            anti_alias_filter_applied=False))


def phase_diagnosis(events):
    """Broadband discontinuity evidence, never a hardware cause or correction claim."""
    words = np.asarray([e.words for e in events]).copy()
    if any(e.original_words is None for e in events):
        raise ValueError('Need NMD2/3 originals to inspect all 56 occupied tones')
    words[:, :, 28:31] = np.asarray([e.original_words for e in events])
    bins = np.r_[np.arange(-28, 0), np.arange(1, 29)] % 64
    iq = decode_selected(words[:, :, bins])
    if not np.isfinite(iq).all() or (abs(iq) < 1e-12).any():
        raise ValueError('Invalid occupied-tone IQ; preserve source and stop')
    angle = np.angle(iq)
    diff = np.angle(np.exp(1j * (angle[:, [0, 0, 1]] - angle[:, [1, 2, 2]])))
    delta = np.angle(np.exp(1j * np.diff(diff, axis=0)))
    rows = []
    for k, pair in enumerate(((0, 1), (0, 2), (1, 2))):
        bad = abs(delta[:, k]) > MAX_PHASE_STEP
        # Circular aggregate avoids a spurious arithmetic median at the +-pi cut.
        center = np.angle(np.mean(np.exp(1j * delta[:, k]), axis=1))
        dispersion = np.median(abs(np.angle(np.exp(1j * (delta[:, k] - center[:, None])))), axis=1)
        broadband = (bad.sum(axis=1) >= 28) & (dispersion < .25)
        jumps = np.flatnonzero(broadband)
        out_back = 0
        for i in jumps:
            if i + 1 < len(center) and broadband[i + 1] and abs(
                    np.angle(np.exp(1j * (center[i] + center[i + 1])))) <= .1:
                out_back += 1
        largest = np.argsort(abs(center))[-5:]
        rows.append(dict(rx_pair=pair,
            simultaneous_tone_faults_max=int(bad.sum(axis=1).max()),
            broadband_phase_fault_events=int(broadband.sum()),
            adjacent_returning_fault_pairs=out_back,
            typical_broadband_step_abs_rad=describe(abs(center[broadband])),
            largest_events=[dict(retained_row=int(i + 1), rx_time_us=events[i + 1].time_us,
                median_circular_deviation_rad=float(dispersion[i]),
                common_step_rad=float(center[i]), affected_tones=int(bad[i].sum()),
                retry=bool(events[i + 1].meta['retry']), tid=events[i + 1].meta['tid'],
                raw_rx_frame_size=events[i + 1].meta.get('raw_rx_frame_size')) for i in largest]))
    return dict(occupied_tones=56, pairs=rows,
        cause_confirmed=False, phase_offset_correction_applied=False,
        interpretation='Broadband and sometimes returning jumps are consistent with a changing link/radio state; neither motion nor a specific radio cause is proven. Same-packet RX differencing and temporal unwrap do not remove them. Do not subtract a fitted common offset: it may also remove real motion.',
        handling='Split usable epochs through per-channel source-fault masks; any affected FIR footprint is invalid.')


def run(pcap, output):
    events, state, groups = load_segment(pcap)
    if any('event_phy0' in e.meta for e in events):
        raise ValueError('Experimental NMD4 captures are outside this NMD2/3 adapter profile')
    iq = decode_selected(np.asarray([e.words for e in events])[:, :, CARRIERS])
    pairs = np.stack([iq[:, [a, b], ch] for ch, (a, b) in enumerate(PAIRS)], axis=1)
    stamps = np.asarray([e.time_us - events[0].time_us for e in events], dtype=np.int64) * 1000
    arrays, quality = align_phase(stamps, differential_phase(pairs))
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'phase-arrays.npz').open('xb') as f:
        np.savez_compressed(f, **arrays)
    result = dict(schema=1, scope='offline_nexmon_50hz_phase_alignment',
        source=str(pcap.resolve()), hardware_accessed=False,
        source_segment=events[0].segment,
        segments=[dict(segment=key, events=len(g), span_seconds=(g[-1].time_us - g[0].time_us) / 1e6)
                  for key, g in groups.items()],
        source_events=len(events), source_relative_rx_span_seconds=float(stamps[-1] / 1e9),
        source_clock='NMD relative RX microseconds within continuity-checked segment; not PCAP arrival',
        source_counts=state['counts'], fixed_fft_indices=CARRIERS, fixed_rx_pairs=PAIRS,
        timing_comparison=timing_comparison(stamps), alignment=quality,
        phase_diagnosis=phase_diagnosis(events),
        heart=None, breath=None, real_heart_estimation_executed=False,
        strict_cpp_or_pose_or_board_changed=False, production_eligible=False,
        remaining=['Need one continuous >=40s eligible history plus measured FIR context.',
                   'Need stable source differential phase; masks contain faults but do not repair radio state.',
                   'The four fixed diagnostic features are not validated HR-sensitive channels.',
                   'Derived phase arrays are not the strict same-packet complex-IQ input interface.',
                   'No synchronized HR reference; no real detection/accuracy claim.'])
    save(output / 'alignment.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcap', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = run(args.pcap, args.output)
    print(json.dumps(dict(samples=report['source_events'], alignment=report['alignment']), indent=2))

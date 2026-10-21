"""Offline recorded-time experiment, separate from the strict C++ CSI input contract.

This exports phase arrays, never fabricated antenna pairs, RF sequences or verified
clocks. Interpolation cannot certify acquisition timing, recover loss or calibrate RX.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import scipy
from scipy import signal

from audit_octonet_stage_a import elapsed_ns, load


RATES = (10, 20, 25, 50)
WORK_RATE = 200
CONTEXT_SECONDS = 2
HISTORY_SECONDS = 40
MAX_GAP_SECONDS = 0.2  # Exploratory limit, not a certified RF sampling requirement.
MAX_PHASE_STEP = 0.25  # Preserve the existing reference's motion/phase gate.


def save_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def phase_from_pairs(pairs):
    """Same-packet RX difference BEFORE interpolation, with overflow-safe scaling."""
    pairs = np.asarray(pairs)
    if pairs.ndim != 3 or pairs.shape[1:] != (4, 2) or len(pairs) > 50000:
        raise ValueError("Expected at most 50000 [time, 4 features, 2 RX] records")
    if not np.isfinite(pairs).all():
        raise ValueError("Non-finite source IQ; stop this experiment")
    scale = np.maximum(np.abs(pairs.real), np.abs(pairs.imag))
    if (scale < 1e-12).any():
        raise ValueError("Insufficient source amplitude; do not invent phase")
    normalized = pairs / scale
    return np.unwrap(np.angle(normalized[:, :, 0] * normalized[:, :, 1].conj()), axis=0)


def adapt_phase(times_ns, phase, rate, start_seconds):
    """Conditional time interpolation + anti-alias filtering, retaining source gates.

    The 200Hz work grid adds no observations. Kaiser FIR polyphase conversion then
    limits aliasing at each target rate. Two seconds of measured context per side
    keep its finite support outside the retained 40s history; no source extrapolation.
    This is not a general bandlimited reconstruction of arbitrary irregular RF data.
    """
    stamps = np.asarray(times_ns)
    phase = np.asarray(phase, dtype=np.float64)
    if (stamps.ndim != 1 or not np.issubdtype(stamps.dtype, np.integer) or
            len(stamps) < 2 or len(stamps) > 50000 or stamps.min() < 0 or
            stamps.max() > np.iinfo(np.int64).max):
        raise ValueError("Expected bounded nonnegative integer relative timestamps")
    stamps = stamps.astype(np.int64)
    if (np.diff(stamps) <= 0).any():
        raise ValueError("Source timestamps must increase strictly; no sorting/deduplication")
    if phase.shape != (len(stamps), 4) or not np.isfinite(phase).all():
        raise ValueError("Expected finite source phase [time, 4]")
    if rate not in RATES or not np.isfinite(start_seconds):
        raise ValueError("Unsupported experiment profile")
    # Relative integer timestamps are differenced before floating-point conversion.
    seconds = (stamps - stamps[0]) / 1e9
    left = start_seconds - CONTEXT_SECONDS
    right = start_seconds + HISTORY_SECONDS + CONTEXT_SECONDS
    if left < seconds[0] or right > seconds[-1]:
        raise ValueError("Insufficient measured context; source extrapolation is forbidden")
    first = max(0, int(np.searchsorted(seconds, left, side="right")) - 1)
    last = int(np.searchsorted(seconds, right, side="left"))
    source_t = seconds[first:last + 1]
    source_phase = phase[first:last + 1]
    intervals = np.diff(source_t)
    steps = np.abs(np.diff(source_phase, axis=0))
    reasons = []
    if intervals.max() > MAX_GAP_SECONDS + 1e-12:
        reasons.append("source_gap_exceeds_experiment_limit")
    if (steps > MAX_PHASE_STEP).any():
        reasons.append("source_motion_or_phase_jump")
    dense_t = left + np.arange((HISTORY_SECONDS + 2 * CONTEXT_SECONDS) * WORK_RATE + 1) / WORK_RATE
    dense_phase = np.column_stack([np.interp(dense_t, source_t, source_phase[:, ch]) for ch in range(4)])
    divisor = np.gcd(rate, WORK_RATE)
    converted = signal.resample_poly(dense_phase, rate // divisor, WORK_RATE // divisor,
                                     axis=0, window=("kaiser", 8.6), padtype="line")
    begin = CONTEXT_SECONDS * rate
    retained = converted[begin:begin + HISTORY_SECONDS * rate]
    grid_ns = np.rint((start_seconds + np.arange(len(retained)) / rate) * 1e9).astype(np.int64)
    quality = dict(
        target_rate_hz=rate, target_samples=len(retained), target_start_seconds=start_seconds,
        target_last_seconds=float(grid_ns[-1] / 1e9), history_seconds=HISTORY_SECONDS,
        measured_context_seconds_per_side=CONTEXT_SECONDS, source_first_row=first,
        source_last_row=last, source_samples=last - first + 1,
        source_timestamp_average_hz=float((len(source_t) - 1) / (source_t[-1] - source_t[0])),
        source_max_gap_ms=float(intervals.max() * 1000), experiment_max_gap_ms=MAX_GAP_SECONDS * 1000,
        source_max_phase_step_rad=steps.max(axis=0).tolist(),
        source_phase_steps_over_reference_limit=(steps > MAX_PHASE_STEP).sum(axis=0).tolist(),
        source_phase_step_p95_rad=np.percentile(steps, 95, axis=0).tolist(),
        source_phase_step_limit_rad=MAX_PHASE_STEP,
        numerically_qualified=not reasons, reasons=reasons,
        source_clock_verified=False, source_packet_sequence_available=False,
        production_eligible=False,
    )
    return grid_ns, retained, quality


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output_dir.resolve()
    manifest_path = root / "metadata/stage-a-download.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest.get("complete") or len(manifest["records"]) != 2:
        raise ValueError("Require the previously verified approved pair")
    paths = {}
    for item in manifest["records"]:
        path = Path(item["local_path"])
        if not item["verified"] or path.stat().st_size != item["expected_bytes"]:
            raise ValueError("Original source identity/size no longer matches the download")
        paths[path.name.split("_")[1]] = path
    wt, wifi, _ = load(paths["wifi"])
    ht, hr, _ = load(paths["heartrate"])
    if wifi.shape[1:] != (2, 114) or not np.iscomplexobj(wifi):
        raise ValueError("Unsupported OctoNet CSI layout")
    if hr.shape != (len(ht),) or np.iscomplexobj(hr) or not (hr > 0).all():
        raise ValueError("Unsupported reference heart-rate layout")
    times = np.array([elapsed_ns(stamp - wt[0]) for stamp in wt], dtype=np.int64)
    usable = np.where((np.maximum(np.abs(wifi.real), np.abs(wifi.imag)) >= 1e-12).all(axis=(0, 1)))[0]
    if len(usable) < 4:
        raise ValueError("Fewer than four amplitude-eligible indices")
    # Fixed ranks, selected only by nonzero amplitude; never inspect HR or optimize a spectrum.
    indices = usable[np.rint(np.array([.10, .35, .60, .85]) * (len(usable) - 1)).astype(int)]
    pairs = np.stack((wifi[:, 0, indices], wifi[:, 1, indices]), axis=-1)
    phase = phase_from_pairs(pairs)
    output.mkdir(parents=True, exist_ok=False)
    arrays = dict(original_relative_ns=times, original_differential_phase=phase, fft_array_indices=indices)
    windows = []
    start = float(CONTEXT_SECONDS)
    while start + HISTORY_SECONDS + CONTEXT_SECONDS <= times[-1] / 1e9:
        for rate in RATES:
            grid, values, quality = adapt_phase(times, phase, rate, start)
            key = f"start{start:g}_fs{rate}"
            arrays[key + "_grid_ns"] = grid
            arrays[key + "_phase"] = values
            # Preserve reference values in each full 30s estimation interval, no label shifts.
            ref = [dict(timestamp=t.isoformat(timespec="microseconds"), bpm=int(v))
                   for t, v in zip(ht, hr) if start + 10 <= (t - wt[0]).total_seconds() < start + 40]
            windows.append(dict(id=key, quality=quality, reference_interval_values=ref,
                                heart=None, heart_estimation_executed=False,
                                reason="Source phase gate failed" if quality["reasons"] else
                                "Recorded time/sequence provenance is insufficient for the strict reference"))
        start += 5  # Overlapping diagnostics, not independent subject/window accuracy samples.
    if not windows:
        raise ValueError("No complete history plus measured filter context")
    with (output / "phase-arrays.npz").open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    report = dict(
        schema=1, scope="offline_recorded_time_adaptation_experiment", hardware_test=False,
        source_manifest=str(manifest_path), revision=manifest["revision"],
        original_audit=str(root / "derived/stage-a-audit.json"),
        selection="10/35/60/85 percent ranks of amplitude-eligible FFT array indices; no HR-based selection",
        fft_array_indices=indices.tolist(), physical_subcarrier_mapping_verified=False,
        original_samples=len(times), observed_timestamp_rate_hz=float((len(times) - 1) * 1e9 / times[-1]),
        source_phase_max_step_rad=np.abs(np.diff(phase, axis=0)).max(axis=0).tolist(),
        source_phase_steps_over_025_rad=(np.abs(np.diff(phase, axis=0)) > MAX_PHASE_STEP).sum(axis=0).tolist(),
        work_rate_hz=WORK_RATE, target_rates_hz=list(RATES), anti_alias="SciPy resample_poly Kaiser beta=8.6 after linear time interpolation",
        python_adapter_requires_host_numpy_scipy=True, core_cpp_or_arm64_source_changed=False,
        resampling_performed=True, reference_clock_relabelled_as_verified=False,
        rf_sequences_invented=False, source_iq_overwritten=False, phase_jumps_corrected=False,
        arrays=str(output / "phase-arrays.npz"), windows=windows,
        real_heart_estimation_executed=False, real_heart_rate_accuracy_verified=False,
        original_strict_contract_passed=False, stage_a_adaptation_passed=False,
        stage_b_started=False, production_eligible=False,
        blockers=["unverified_RF_clock", "RF_packet_sequence_absent"] +
                 (["original_differential_phase_jumps"] if any(
                     "source_motion_or_phase_jump" in w["quality"]["reasons"] for w in windows) else []) +
                 (["source_gaps"] if any("source_gap_exceeds_experiment_limit" in w["quality"]["reasons"] for w in windows) else []),
        versions=dict(numpy=np.__version__, scipy=scipy.__version__),
        limits=["Host/NTP timestamps are not verified RF acquisition times",
                "Interpolation cannot restore packet loss, RX calibration or missing cardiac evidence",
                "Exploratory 200ms gap bound is not a production sampling specification",
                "No reliable HR accuracy/MAE can be reported without accepted real estimates",
                "No label-driven phase correction, band/quality tuning or clock alignment was performed"],
    )
    save_json(output / "adaptation.json", report)
    print(json.dumps({k: report[k] for k in ("fft_array_indices", "observed_timestamp_rate_hz", "source_phase_steps_over_025_rad", "stage_a_adaptation_passed", "stage_b_started")}, indent=2))


if __name__ == "__main__":
    main()

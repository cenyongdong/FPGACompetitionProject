"""Validate recorded-time adaptation with analytic signals, never RF/subject accuracy.

Calls a separately built C++ executable. Only wholly synthetic phase arrays are encoded
as synthetic CSI for its uniform-input interface; real OctoNet IQ is never fabricated.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from adapt_octonet_timing import adapt_phase, phase_from_pairs, RATES, save_json
from audit_octonet_stage_a import elapsed_ns, load
from signal_fixtures import write_csv
from validate_offline import invoke


def analytic(seconds, heart_hz=1.2, breath_hz=.25, heart_amplitude=.03):
    return np.column_stack([
        .3 * np.sin(2 * np.pi * breath_hz * seconds + ch * .1) +
        heart_amplitude * np.sin(2 * np.pi * heart_hz * seconds + ch * .2)
        for ch in range(4)])


def synthetic_pairs(phase, seed=241):
    rng = np.random.default_rng(seed)
    # Independent common packet phase must cancel before any time interpolation.
    common = rng.uniform(-np.pi, np.pi, phase.shape)
    return np.stack((np.exp(1j * (phase + common)), .8 * np.exp(1j * common)), axis=-1)


def synthetic_fixture(grid, phase, rate):
    # This function is used ONLY on analytic/noise test signals, not dataset phase.
    return dict(pairs=np.stack((np.exp(1j * phase), np.ones_like(phase)), axis=-1),
                times=grid.astype(np.uint64), sequences=np.arange(1, len(grid) + 1, dtype=np.uint64),
                valid=np.ones(len(grid), dtype=np.uint8), origin="synthetic", clock="synthetic_uniform", rate=rate,
                clock_evidence="analytic test signal on known irregular times, interpolated to an analytic uniform grid; not RF data")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--rate-followup", action="store_true",
                        help="Only new high-HR/rate combinations prompted by the first 10Hz rejection")
    args = parser.parse_args()
    manifest = json.loads((args.root / "metadata/stage-a-download.json").read_text(encoding="utf-8"))
    source = next(Path(item["local_path"]) for item in manifest["records"] if "_wifi_" in item["remote_path"])
    wt, _, _ = load(source)
    observed = np.array([elapsed_ns(t - wt[0]) for t in wt], dtype=np.int64)
    regular = lambda rate: np.rint(np.arange(int(53.1 * rate) + 1) / rate * 1e9).astype(np.int64)
    rng = np.random.default_rng(20261020)
    jittered = np.rint(np.r_[0., np.cumsum(rng.uniform(.07, .13, 600))] * 1e9).astype(np.int64)
    clocks = dict(observed_octonet=observed, uniform_9_615hz=regular(9.615),
                  uniform_50hz=regular(50), irregular_approx_10hz=jittered)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    executable = args.executable.resolve()
    log = output / "commands.jsonl"
    tests = []
    source_arrays = {}

    def check_signal(name, stamps, rate, hz=1.2, breath=.25, amplitude=.03, expected=True, noise_seed=None):
        seconds = stamps / 1e9
        if noise_seed is None:
            original_phase = analytic(seconds, hz, breath, amplitude)
        else:
            original_phase = np.random.default_rng(noise_seed).normal(0, .03, (len(stamps), 4))
        pairs = synthetic_pairs(original_phase)
        recovered = phase_from_pairs(pairs)
        cancel_error = float(np.max(np.abs(np.angle(np.exp(1j * (recovered - original_phase))))))
        grid, phase, quality = adapt_phase(stamps, recovered, rate, 2)
        source_arrays[name + "_source_ns"] = stamps
        source_arrays[name + "_source_phase"] = recovered
        source_arrays[name + "_grid_ns"] = grid
        source_arrays[name + "_adapted_phase"] = phase
        csv_path, result_path = output / f"{name}.csv", output / f"{name}.json"
        trace_path = output / f"{name}-trace.json"
        fixture = synthetic_fixture(grid, phase, rate)
        write_csv(csv_path, fixture)
        response = invoke([executable, "--input", csv_path, "--output", result_path, "--trace", trace_path], log)
        if response["returncode"]:
            raise RuntimeError(f"C++ execution failed, preserve {log}")
        # Actual C++ outputs and full traces have been saved BEFORE comparing.
        actual = json.loads(result_path.read_text(encoding="utf-8"))
        estimate = actual["heart"]
        bpm_error = abs(estimate["bpm"] - hz * 60) if estimate and expected else None
        passed = (quality["numerically_qualified"] and cancel_error < 2e-12 and
                  ((estimate is not None and bpm_error <= 1.0) if expected else estimate is None))
        phase_rmse = None
        if noise_seed is None:
            phase_rmse = float(np.sqrt(np.mean((phase - analytic(grid / 1e9, hz, breath, amplitude)) ** 2)))
            passed = passed and phase_rmse < .015
        tests.append(dict(name=name, passed=bool(passed), target_rate_hz=rate,
                          expected_bpm=hz * 60 if expected else None,
                          actual_bpm=estimate["bpm"] if estimate else None,
                          absolute_bpm_error=bpm_error, known_phase_rmse_rad=phase_rmse,
                          common_packet_phase_cancellation_max_error_rad=cancel_error,
                          actual_result=str(result_path), actual_trace=str(trace_path), quality=quality))

    def finish(checks):
        with (output / "synthetic-arrays.npz").open("xb") as stream:
            np.savez_compressed(stream, **source_arrays)
        report = dict(schema=1, scope="synthetic_timing_adaptation_only", passed=all(t["passed"] for t in tests + checks),
                      suite="rate_followup" if args.rate_followup else "timing",
                      hardware_test=False, real_heart_rate_accuracy_verified=False, core_cpp_modified_by_this_script=False,
                      executable=str(executable), signal_tests=tests, safety_and_alias_checks=checks,
                      signal_test_count=len(tests), signal_tests_passed=sum(t["passed"] for t in tests),
                      check_count=len(checks),
                      maximum_absolute_bpm_error=max(t["absolute_bpm_error"] or 0 for t in tests),
                      error_statistic_excludes_rejected_estimates=True,
                      overlapping_or_resampled_tests_are_not_independent_real_data=True,
                      raw_arrays=str(output / "synthetic-arrays.npz"),
                      limits=["RF clock, loss and RX calibration remain unverified",
                              "Known-signal recovery under recorded timestamps is not subject HR accuracy",
                              "Stop-band attenuation is finite; no universal no-alias guarantee"])
        save_json(output / "validation.json", report)
        print(json.dumps({k: report[k] for k in ("passed", "signal_test_count", "signal_tests_passed", "check_count", "maximum_absolute_bpm_error")}, indent=2))
        return 0 if report["passed"] else 1

    if args.rate_followup:
        # New cases only: retain first-run failures instead of rerunning/tuning them away.
        for clock in ("observed_octonet", "uniform_9_615hz"):
            for hz in (110 / 60, 2.):
                for rate in RATES:
                    if clock == "observed_octonet" and rate in (10, 50):
                        continue
                    check_signal(f"{clock}_fs{rate}_{hz * 60:g}bpm", clocks[clock], rate, hz, .27)
        raise SystemExit(finish([]))
    else:
        # 16 combinations exercise observed ~65Hz timestamps and the actual ~10Hz input scale.
        for clock, stamps in clocks.items():
            for rate in RATES:
                check_signal(f"{clock}_fs{rate}_72bpm", stamps, rate)
        # Band edges and near-upper-band rate, no HR-label-based tuning.
        for hz, breath in ((.8, .29), (2., .27), (110 / 60, .27)):
            for rate in (10, 50):
                check_signal(f"observed_fs{rate}_{hz * 60:g}bpm", observed, rate, hz, breath)
        for rate in (10, 50):
            check_signal(f"observed_breath_only_fs{rate}", observed, rate, amplitude=0, expected=False)
            check_signal(f"observed_noise_fs{rate}", observed, rate, expected=False, noise_seed=882)

    checks = []
    stamps = clocks["uniform_50hz"]
    phase = analytic(stamps / 1e9)
    for name, input_stamps, input_phase, expected_reason in (
            ("long_gap", stamps[(stamps < 20e9) | (stamps > 20.4e9)],
             phase[(stamps < 20e9) | (stamps > 20.4e9)], "source_gap_exceeds_experiment_limit"),
            ("source_phase_jump", stamps, phase + (stamps[:, None] >= 20e9) * np.array([1., 0, 0, 0]),
             "source_motion_or_phase_jump")):
        _, _, q = adapt_phase(input_stamps, input_phase, 10, 2)
        checks.append(dict(name=name, passed=not q["numerically_qualified"] and expected_reason in q["reasons"], quality=q))

    duplicate = stamps.copy()
    duplicate[30] = duplicate[29]
    bad_phase = phase.copy()
    bad_phase[30, 1] = np.nan
    for name, action in (
            ("duplicate_time", lambda: adapt_phase(duplicate, phase, 10, 2)),
            ("nonfinite_phase", lambda: adapt_phase(stamps, bad_phase, 10, 2)),
            ("no_left_extrapolation", lambda: adapt_phase(stamps, phase, 10, 0)),
            ("no_right_extrapolation", lambda: adapt_phase(stamps, phase, 10, 13)),
            ("unsupported_target_rate", lambda: adapt_phase(stamps, phase, 100, 2)),
            ("zero_iq", lambda: phase_from_pairs(np.zeros((10, 4, 2), dtype=np.complex128))),
            ("nonfinite_iq", lambda: phase_from_pairs(np.full((10, 4, 2), np.nan, dtype=np.complex128)))):
        try:
            action()
            checks.append(dict(name=name, passed=False))
        except ValueError as error:
            checks.append(dict(name=name, passed=True, reason=str(error)))

    # A 19Hz tone aliases to 1Hz at 20Hz without anti-alias filtering.
    # Measure attenuation, rather than pretending interpolation alone is a low-pass filter.
    high_stamps = regular(200)
    high_phase = .03 * np.sin(2 * np.pi * 19 * high_stamps / 1e9)[:, None] * np.ones((1, 4))
    grid, limited, quality = adapt_phase(high_stamps, high_phase, 20, 2)
    naive = np.interp(grid / 1e9, high_stamps / 1e9, high_phase[:, 0])
    attenuation_db = float(20 * np.log10(np.linalg.norm(limited[:, 0]) / np.linalg.norm(naive)))
    checks.append(dict(name="anti_alias_19hz_to_20hz", passed=attenuation_db <= -50,
                       rms_attenuation_db=attenuation_db, required_db=-50,
                       scope="FIR rejection for this tone; not proof of arbitrary irregular-RF reconstruction"))
    source_arrays.update(alias_source_ns=high_stamps, alias_source_phase=high_phase,
                         alias_target_ns=grid, alias_naive_phase=naive, alias_filtered_phase=limited)
    # These remain SYNTHETIC tests with real clock metadata deliberately unverified.
    fixture = synthetic_fixture(grid, limited, 20)
    fixture.update(clock="unknown_arrival", clock_evidence="deliberately unverified clock in a synthetic negative test")
    path = output / "unknown-clock.csv"
    write_csv(path, fixture)
    response = invoke([executable, "--input", path, "--output", output / "unknown-clock.json"], log)
    unknown = json.loads((output / "unknown-clock.json").read_text(encoding="utf-8"))
    checks.append(dict(name="uniform_grid_does_not_verify_clock", passed=response["returncode"] == 0 and
                       unknown["heart"] is None and "unverified_sample_clock" in unknown["reasons"]))
    raise SystemExit(finish(checks))


if __name__ == "__main__":
    main()

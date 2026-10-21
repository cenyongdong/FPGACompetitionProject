"""Analytic HR/rate sweep and negative controls for the cardiac ACF peak fix.

No RF accuracy claims, hardware access, downloads, label fitting or threshold tuning.
The measured timestamp pattern is reused only as times for generated signals.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from adapt_octonet_timing import adapt_phase, phase_from_pairs, RATES, save_json
from audit_octonet_stage_a import elapsed_ns, load
from signal_fixtures import write_csv
from validate_offline import independent_reference, invoke
from validate_timing_adapter import synthetic_fixture, synthetic_pairs


def make_phase(seconds, kind, bpm):
    rng = np.random.default_rng(7331 + int(bpm))
    cardiac = np.sin(2 * np.pi * (bpm / 60) * seconds[:, None] + np.arange(4)[None, :] * .2)
    breath = .3 * np.sin(2 * np.pi * .25 * seconds[:, None] + np.arange(4)[None, :] * .1)
    if kind == "heart_only":
        return .03 * cardiac + rng.normal(0, .0002, cardiac.shape)
    if kind == "breath_harmonic":
        return breath + .03 * cardiac
    if kind == "breath_only":
        return breath
    if kind == "noise":
        return rng.normal(0, .03, cardiac.shape)
    if kind == "out_of_band":
        return .03 * cardiac
    if kind == "disagreeing_channels":
        hz = np.array([1., 1., 1.7, 1.7])
        return .03 * np.sin(2 * np.pi * seconds[:, None] * hz[None, :] + np.arange(4)[None, :] * .2)
    raise ValueError("Unsupported analytic scenario")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.root / "metadata/stage-a-download.json").read_text(encoding="utf-8"))
    source = next(Path(r["local_path"]) for r in manifest["records"] if "_wifi_" in r["remote_path"])
    times, _, _ = load(source)
    clocks = dict(
        observed_octonet=np.array([elapsed_ns(t - times[0]) for t in times], dtype=np.int64),
        uniform_9_615hz=np.rint(np.arange(int(53.1 * 9.615) + 1) / 9.615 * 1e9).astype(np.int64),
    )
    directory, executable = args.output_dir.resolve(), args.executable.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    tests = []
    log = directory / "commands.jsonl"
    scenarios = [("heart_only", bpm, bpm) for bpm in range(48, 121, 2)]
    scenarios += [("breath_harmonic", bpm, None) for bpm in (60, 75, 90, 105, 120)]
    scenarios += [("breath_only", 0, None), ("noise", 1, None), ("noise", 2, None), ("noise", 3, None),
                  ("out_of_band", 39, None), ("out_of_band", 144, None), ("disagreeing_channels", 0, None)]
    for clock_name, stamps in clocks.items():
        seconds = stamps / 1e9
        for kind, bpm, expected in scenarios:
            source_phase = phase_from_pairs(synthetic_pairs(make_phase(seconds, kind, bpm)))
            for rate in RATES:
                name = f"{clock_name}_{kind}_{bpm}_fs{rate}"
                grid, phase, quality = adapt_phase(stamps, source_phase, rate, 2)
                fixture = synthetic_fixture(grid, phase, rate)
                csv_path, result_path = directory / f"{name}.csv", directory / f"{name}.json"
                write_csv(csv_path, fixture)
                command = [executable, "--input", csv_path, "--output", result_path]
                math_case = clock_name == "observed_octonet" and kind == "heart_only" and bpm == 72
                trace_path = directory / f"{name}-trace.json"
                if math_case:
                    command += ["--trace", trace_path]
                returned = invoke(command, log)
                if returned["returncode"]:
                    raise RuntimeError(f"C++ execution failed; preserve {log}")
                # Complete actual outputs are saved first, then compared.
                actual = json.loads(result_path.read_text(encoding="utf-8"))
                heart = actual["heart"]
                error = abs(heart["bpm"] - expected) if expected is not None and heart else None
                accepted = (heart is not None and error <= 1) if expected is not None else heart is None
                review = independent_reference(fixture, trace_path) if math_case else None
                passed = quality["numerically_qualified"] and accepted and (not review or review["passed"])
                tests.append(dict(name=name, passed=bool(passed), kind=kind, input_time_pattern=clock_name,
                                  target_rate_hz=rate, expected_bpm=expected, actual_heart=heart,
                                  absolute_bpm_error=error, status=actual["status"], reasons=actual["reasons"],
                                  actual_result=str(result_path), independent_math=review))
    positive = [t for t in tests if t["expected_bpm"] is not None]
    negative = [t for t in tests if t["expected_bpm"] is None]
    report = dict(schema=1, scope="synthetic_HR_rate_sweep_and_negative_controls", hardware_test=False,
                  passed=all(t["passed"] for t in tests), executable=str(executable),
                  positive_tests=len(positive), positive_passed=sum(t["passed"] for t in positive),
                  negative_tests=len(negative), negative_passed=sum(t["passed"] for t in negative),
                  maximum_absolute_bpm_error_detected_only=max(t["absolute_bpm_error"] or 0 for t in positive),
                  heart_scan_bpm=dict(minimum=48, maximum=120, step=2), target_rates_hz=list(RATES),
                  math_review_count=sum(t["independent_math"] is not None for t in tests), tests=tests,
                  real_HR_accuracy_verified=False,
                  limits=["Generated signals do not establish human cardiac CSI accuracy",
                          "Heart-only scan separates ACF selection from intentional breathing-harmonic rejection",
                          "48:2:120 is a discrete scan, not a guarantee at all intermediate rates"])
    save_json(directory / "validation.json", report)
    print(json.dumps({k: report[k] for k in ("passed", "positive_tests", "positive_passed", "negative_tests", "negative_passed", "maximum_absolute_bpm_error_detected_only")}, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()

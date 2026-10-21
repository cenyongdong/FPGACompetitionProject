"""Offline C++ reference validation against analytic inputs and independent SciPy.

Requires existing NumPy/SciPy; installs nothing and never opens a device/socket.
"""
import argparse
import csv
import json
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
import scipy
from scipy import signal

from signal_fixtures import cases, write_csv


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def invoke(argv, log):
    start = time.perf_counter()
    completed = subprocess.run([str(a) for a in argv], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=60)
    item = dict(argv=[str(a) for a in argv], returncode=completed.returncode,
                wall_seconds=time.perf_counter() - start,
                stdout=completed.stdout, stderr=completed.stderr)
    with log.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(item, ensure_ascii=False) + "\n")
    return item


def independent_reference(fixture, trace_path):
    """SciPy designs SOS, detrends and filters; NumPy dots compute energy-normalized ACF."""
    actual = load_json(trace_path)
    fs = fixture["rate"]
    heart_sos = np.vstack((signal.butter(4, 0.8, "highpass", fs=fs, output="sos"),
                           signal.butter(2, 2.0, "lowpass", fs=fs, output="sos")))
    breath_sos = np.vstack((signal.butter(2, 0.1, "highpass", fs=fs, output="sos"),
                            signal.butter(2, 0.5, "lowpass", fs=fs, output="sos")))
    # SciPy可将串联系数增益放在不同SOS节；比较整个传递函数及实际波形，
    # 不把等价的系数分解方式当成算法失败。
    frequencies, expected_response = signal.sosfreqz(heart_sos, worN=4096, fs=fs)
    _, returned_response = signal.sosfreqz(actual["heart_sos"], worN=frequencies, fs=fs)
    errors = {"heart_frequency_response": float(np.max(np.abs(expected_response - returned_response)))}
    _, expected_response = signal.sosfreqz(breath_sos, worN=frequencies, fs=fs)
    _, returned_response = signal.sosfreqz(actual["breath_sos"], worN=frequencies, fs=fs)
    errors["breath_frequency_response"] = float(np.max(np.abs(expected_response - returned_response)))
    pairs = fixture["pairs"]
    phases = np.unwrap(np.angle(pairs[:, :, 0] * np.conj(pairs[:, :, 1])), axis=0)
    detrended = signal.detrend(phases, axis=0, type="linear")
    warmup = int(round(fixture.get("warmup_seconds", 10) * fs))
    heart = signal.sosfilt(heart_sos, detrended, axis=0)[warmup:]
    breath = signal.sosfilt(breath_sos, detrended, axis=0)[warmup:]
    for ch, returned in enumerate(actual["channels"]):
        expected = dict(phase=phases[:, ch], detrended=detrended[:, ch],
                        heart=heart[:, ch], breath=breath[:, ch])
        for key, values in (("heart_acf", heart[:, ch]), ("breath_acf", breath[:, ch])):
            acf = []
            for lag in range(len(returned[key])):
                left = values[lag:]
                right = values[:len(values) - lag]
                denominator = np.linalg.norm(left) * np.linalg.norm(right)
                acf.append(float(np.dot(left, right) / denominator) if denominator > 1e-24 else 0.0)
            expected[key] = np.array(acf)
        for key, values in expected.items():
            error = float(np.max(np.abs(values - returned[key])))
            errors[key] = max(error, errors.get(key, 0.0))
    # IIR滤波采用不同极点对排序和浮点实现，按数值误差检查，不把文案作为门。
    passed = all(error <= 2e-9 for error in errors.values())
    return dict(passed=passed, maximum_absolute_errors=errors, tolerance=2e-9,
                numpy=np.__version__, scipy=scipy.__version__)


def parser_checks(executable, directory, source, log):
    original = source.read_text(encoding="utf-8")
    tests = []
    mutations = {
        "bad_header": original.replace("time_ns,sequence,valid", "time_ns,seq,valid", 1),
        "bad_width": original + "1,2,3\n",
        "bad_tail": original + "malformed\n",
        "false_synthetic_origin": original.replace("origin=synthetic", "origin=real_capture", 1),
        "unsubstantiated_clock": original.replace("clock=synthetic_uniform", "clock=verified_sampling", 1)
            .replace("# clock_evidence=analytic uniform samples generated offline\n", ""),
        "duplicate_configuration": "# sample_rate_hz=20\n" + original,
    }
    for name, text in mutations.items():
        path = directory / f"parser-{name}.csv"
        path.write_text(text, encoding="utf-8")
        response = invoke([executable, "--input", path, "--output", directory / f"parser-{name}.json"], log)
        tests.append(dict(name=name, passed=response["returncode"] != 0))
    output = directory / "heart_72.json"
    before = output.read_bytes()
    response = invoke([executable, "--input", source, "--output", output], log)
    tests.append(dict(name="preserve_existing_output", passed=response["returncode"] != 0 and before == output.read_bytes()))
    compatible = directory / "parser-utf8-bom-crlf.csv"
    compatible.write_bytes(b"\xef\xbb\xbf" + original.replace("\n", "\r\n").encode("utf-8"))
    out = directory / "parser-utf8-bom-crlf.json"
    response = invoke([executable, "--input", compatible, "--output", out], log)
    returned = load_json(out) if out.exists() else {}
    tests.append(dict(name="utf8_bom_crlf", passed=response["returncode"] == 0 and
                      returned.get("heart") is not None and abs(returned["heart"]["bpm"] - 72) < 1))
    return tests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--benchmark-repeats", type=int, default=100)
    args = parser.parse_args()
    executable = args.executable.resolve()
    directory = args.output_dir.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    log = directory / "commands.jsonl"
    results = []
    fixture_map = {}
    for name, fixture, expected in cases():
        fixture_map[name] = fixture
        csv_path = directory / f"{name}.csv"
        output = directory / f"{name}.json"
        trace = directory / f"{name}-trace.json"
        write_csv(csv_path, fixture)
        argv = [executable, "--input", csv_path, "--output", output]
        if name in ("heart_72", "phase_wrap"):
            argv += ["--trace", trace]
        if name == "heart_72":
            argv += ["--repeat", args.benchmark_repeats]
        response = invoke(argv, log)
        returned = load_json(output) if output.exists() else None
        estimate = None if returned is None else returned["heart"]
        if expected is None:
            passed = response["returncode"] == 0 and returned is not None and estimate is None
        else:
            passed = (response["returncode"] == 0 and estimate is not None and
                      abs(estimate["bpm"] - expected) <= 1.0)
        item = dict(name=name, passed=passed, expected_bpm=expected,
                    actual_heart=estimate, status=returned["status"] if returned else "execution_failed",
                    reasons=returned["reasons"] if returned else [response["stderr"]])
        if expected is not None and estimate:
            item["absolute_error_bpm"] = abs(estimate["bpm"] - expected)
        results.append(item)
    independent = []
    for name in ("heart_72", "phase_wrap"):
        path = directory / f"{name}-trace.json"
        if path.exists():
            checked = independent_reference(fixture_map[name], path)
            independent.append(dict(name=name, **checked))
    malformed = parser_checks(executable, directory, directory / "heart_72.csv", log)
    final = dict(schema=1, scope="host_offline_algorithm_only", hardware_test=False,
                 environment=dict(platform=platform.platform(), python=platform.python_version(),
                                  numpy=np.__version__, scipy=scipy.__version__),
                 cases=results, independent_reference=independent, parser_checks=malformed,
                 benchmark=load_json(directory / "heart_72.json").get("benchmark"),
                 passed=all(item["passed"] for item in results + independent + malformed))
    save_json(directory / "validation.json", final)
    print(json.dumps(dict(passed=final["passed"], cases_passed=sum(i["passed"] for i in results),
                          cases=len(results), independent=independent,
                          parser_checks=malformed, benchmark={k: v for k, v in (final["benchmark"] or {}).items()
                                                             if k != "per_iteration"}), indent=2))
    raise SystemExit(0 if final["passed"] else 1)


if __name__ == "__main__":
    main()

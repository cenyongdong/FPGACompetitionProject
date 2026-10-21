"""Deterministic analytic CSI fixtures; never presented as RF/subject measurements."""
import csv
import math
from pathlib import Path

import numpy as np


def synthesize(heart_hz=1.2, breath_hz=0.25, heart_amplitude=0.03,
               breath_amplitude=0.3, noise=0.0005, seed=431, count=2000,
               phase_offset=0.0, harmonics=(), per_channel_hz=None):
    rate = 50.0
    t = np.arange(count, dtype=np.float64) / rate
    rng = np.random.default_rng(seed)
    pairs = np.empty((count, 4, 2), dtype=np.complex128)
    for ch in range(4):
        frequency = heart_hz if per_channel_hz is None else per_channel_hz[ch]
        phase = phase_offset + breath_amplitude * np.sin(2 * np.pi * breath_hz * t + ch * 0.1)
        phase += heart_amplitude * np.sin(2 * np.pi * frequency * t + ch * 0.2)
        phase += noise * rng.normal(size=count)
        for multiple, amplitude in harmonics:
            phase += amplitude * np.sin(2 * np.pi * breath_hz * multiple * t + ch * 0.1)
        common = 3.0 * np.sin(2 * np.pi * 0.7 * t) + 0.05 * t
        pairs[:, ch, 0] = np.exp(1j * (phase + common))
        pairs[:, ch, 1] = 0.8 * np.exp(1j * common)
    return dict(pairs=pairs, times=np.arange(count, dtype=np.uint64) * 20_000_000,
                sequences=np.arange(1, count + 1, dtype=np.uint64), valid=np.ones(count, dtype=np.uint8),
                origin="synthetic", clock="synthetic_uniform", rate=rate,
                clock_evidence="analytic uniform samples generated offline")


def write_csv(path, fixture):
    path = Path(path)
    with path.open("x", encoding="utf-8", newline="") as stream:
        for key, value in [("origin", fixture["origin"]), ("clock", fixture["clock"]),
                           ("sample_rate_hz", fixture["rate"]),
                           ("clock_evidence", fixture.get("clock_evidence", ""))]:
            stream.write(f"# {key}={value}\n")
        writer = csv.writer(stream)
        writer.writerow(["time_ns", "sequence", "valid"] +
                        [f"{part}{ch}" for ch in range(4) for part in ("ia", "qa", "ib", "qb")])
        for i, values in enumerate(fixture["pairs"]):
            row = [int(fixture["times"][i]), int(fixture["sequences"][i]), int(fixture["valid"][i])]
            row += [format(v, ".17g") for pair in values
                    for z in pair for v in (z.real, z.imag)]
            writer.writerow(row)


def cases():
    output = []
    for name, hz, breath in [("heart_48", 0.8, 0.29), ("heart_60", 1.0, 0.31),
                            ("heart_72", 1.2, 0.25), ("heart_90", 1.5, 0.23),
                            ("heart_110", 110 / 60, 0.27), ("heart_120", 2.0, 0.27)]:
        output.append((name, synthesize(heart_hz=hz, breath_hz=breath), hz * 60))
    output += [("weak_heart", synthesize(heart_amplitude=0.005, noise=0.0002), 72),
               ("phase_wrap", synthesize(phase_offset=3.1), 72),
               ("breathing_only", synthesize(heart_amplitude=0, noise=0), None),
               ("breathing_harmonic", synthesize(heart_amplitude=0, noise=0,
                                                 harmonics=((4, 0.04),)), None),
               ("constant", synthesize(heart_amplitude=0, breath_amplitude=0, noise=0), None),
               ("out_of_band_low", synthesize(heart_hz=0.65, breath_hz=0.23), None),
               ("out_of_band_high", synthesize(heart_hz=2.4), None),
               ("disagreeing_channels", synthesize(per_channel_hz=(1.0, 1.0, 1.7, 1.7)), None)]
    for seed in range(10):
        output.append((f"noise_{seed}", synthesize(heart_amplitude=0, breath_amplitude=0,
                                                   noise=0.03, seed=seed), None))
    for name in ("arrival_clock", "short", "missing", "duplicate_sequence", "duplicate_time",
                 "reverse_time", "jitter", "invalid_sample", "zero_pair", "nan", "infinity", "motion"):
        f = synthesize()
        if name == "arrival_clock":
            f["clock"], f["origin"] = "unknown_arrival", "real_capture"
        elif name == "short":
            for key in ("pairs", "times", "sequences", "valid"):
                f[key] = f[key][:100]
        elif name == "missing":
            f["sequences"][1000:] += 1
        elif name == "duplicate_sequence":
            f["sequences"][1000] = f["sequences"][999]
        elif name == "duplicate_time":
            f["times"][1000] = f["times"][999]
        elif name == "reverse_time":
            f["times"][1000] = f["times"][998]
        elif name == "jitter":
            f["times"][1000] += 5_000_000
        elif name == "invalid_sample":
            f["valid"][1000] = 0
        elif name == "zero_pair":
            f["pairs"][1000, 0, 0] = 0
        elif name == "nan":
            f["pairs"][1000, 0, 0] = complex(math.nan, 1)
        elif name == "infinity":
            f["pairs"][1000, 0, 0] = complex(math.inf, 1)
        elif name == "motion":
            f["pairs"][1000:, :, 0] *= np.exp(1j)
        output.append((name, f, None))
    return output

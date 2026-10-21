"""Read-only structural/time audit of the approved OctoNet pair; never resamples or estimates HR."""
import argparse
import csv
import datetime as dt
import io
import json
import pickle
from pathlib import Path

import numpy as np


class DataOnly(pickle.Unpickler):
    def find_class(self, module, name):
        allowed = {
            ("datetime", "datetime"): dt.datetime,
            ("numpy", "ndarray"): np.ndarray,
            ("numpy", "dtype"): np.dtype,
            ("numpy._core.multiarray", "_reconstruct"): np._core.multiarray._reconstruct,
            ("numpy.core.multiarray", "_reconstruct"): np._core.multiarray._reconstruct,
        }
        if (module, name) not in allowed:
            raise pickle.UnpicklingError(f"Unsupported data type: {module}.{name}")
        return allowed[module, name]

    def persistent_load(self, pid):
        raise pickle.UnpicklingError("External persistent objects are unsupported")


def load(path):
    raw = path.read_bytes()
    if len(raw) > 100 * 1024**2:
        raise ValueError("Input exceeds the stage-A file budget")
    stream = io.BytesIO(raw)
    objects = []
    while stream.tell() < len(raw):
        # Each original pickle.dump record has its own memo, as in the public loader.
        item = DataOnly(stream).load()
        if not isinstance(item, dict) or set(item) != {"timestamp", "data"}:
            raise ValueError("Unrecognized original record schema; do not infer fields")
        objects.append(item)
    times, arrays = [], []
    for item in objects:
        if isinstance(item["timestamp"], list):
            if len(item["timestamp"]) != len(item["data"]):
                raise ValueError("Timestamp/data count mismatch")
            times.extend(item["timestamp"])
            arrays.extend(item["data"])
        else:
            times.append(item["timestamp"])
            arrays.append(item["data"])
    if len(times) < 2 or any(type(t) is not dt.datetime for t in times):
        raise ValueError("Insufficient or unsupported timestamp representation")
    values = np.asarray(arrays)
    if values.dtype.hasobject or not np.issubdtype(values.dtype, np.number):
        raise ValueError("Only numeric arrays are supported")
    if not np.isfinite(values).all():
        raise ValueError("Non-finite source data; stop the affected audit")
    return times, values, len(objects)


def elapsed_ns(value):
    return ((value.days * 86400 + value.seconds) * 1_000_000 + value.microseconds) * 1000


def interval_stats(times):
    intervals = np.asarray([elapsed_ns(b - a) for a, b in zip(times, times[1:])], dtype=np.int64)
    milliseconds = intervals / 1e6
    return intervals, {
        "count": len(intervals), "nonpositive": int((intervals <= 0).sum()),
        "min_ms": float(milliseconds.min()), "p05_ms": float(np.percentile(milliseconds, 5)),
        "p50_ms": float(np.median(milliseconds)), "p95_ms": float(np.percentile(milliseconds, 95)),
        "p99_ms": float(np.percentile(milliseconds, 99)), "max_ms": float(milliseconds.max()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = root / "metadata/stage-a-download.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest["complete"] or len(manifest["records"]) != 2 or not all(r["verified"] for r in manifest["records"]):
        raise ValueError("The approved pair must have completed content verification")
    paths = {}
    for record in manifest["records"]:
        path = Path(record["local_path"])
        if path.stat().st_size != record["expected_bytes"]:
            raise ValueError("Source size changed since verified download")
        paths[path.name.split("_")[1]] = path
    wt, wifi, wifi_records = load(paths["wifi"])
    ht, hr, hr_records = load(paths["heartrate"])
    if wifi.ndim != 3 or wifi.shape[1:] != (2, 114) or not np.iscomplexobj(wifi):
        raise ValueError("Expected original [time, 2 RX, 114 tones] complex data")
    if hr.shape != (len(ht),) or np.iscomplexobj(hr) or not (hr > 0).all():
        raise ValueError("Expected positive scalar reference BPM values")
    wd, wi = interval_stats(wt)
    _, hi = interval_stats(ht)
    good = np.abs(wd - 20_000_000) <= 2_000_000
    longest = run = 0
    for item in good:
        run = run + 1 if item else 0
        longest = max(longest, run)
    common_start, common_end = max(wt[0], ht[0]), min(wt[-1], ht[-1])
    overlap = max(0.0, (common_end - common_start).total_seconds())
    zero = wifi == 0
    usable = (~zero.any(axis=(0, 1))).nonzero()[0].tolist()
    derived = root / "derived"
    derived.mkdir(exist_ok=True)
    targets = [derived / name for name in ("stage-a-audit.json", "wifi-timing.csv", "reference-heart-rate.csv")]
    if any(p.exists() for p in targets):
        raise ValueError("Preserve the previous audit; choose a new audit directory")
    with targets[1].open("x", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["local_row_index_not_rf_sequence", "original_naive_timestamp", "relative_ns", "interval_ns", "within_50hz_2ms"])
        for i, stamp in enumerate(wt):
            writer.writerow([i, stamp.isoformat(timespec="microseconds"), elapsed_ns(stamp - wt[0]),
                             "" if not i else int(wd[i - 1]), "" if not i else bool(good[i - 1])])
    with targets[2].open("x", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["original_naive_timestamp", "reference_bpm"])
        writer.writerows((t.isoformat(timespec="microseconds"), int(v)) for t, v in zip(ht, hr))
    reasons = []
    if not good.all():
        reasons.append("non_uniform_sampling_for_50hz_profile")
    # These two fields are absent in the actual released records. A local row number
    # or a newly uniform grid cannot establish their physical acquisition provenance.
    reasons.extend(["rf_sampling_clock_not_verified", "source_packet_sequence_not_available"])
    if overlap < 40:
        reasons.append("insufficient_overlapping_history")
    report = dict(
        schema=1, source_manifest=str(manifest_path), repository=manifest["repository"], revision=manifest["revision"],
        scope="original_data_structure_and_time_audit_only", hardware_test=False,
        dataset_files_downloaded=2, downloaded_bytes=manifest["received_bytes"],
        wifi=dict(pickle_records=wifi_records, original_record_keys=["timestamp", "data"],
                  shape=list(wifi.shape), dtype=str(wifi.dtype), finite=True,
                  first_timestamp=wt[0].isoformat(timespec="microseconds"), last_timestamp=wt[-1].isoformat(timespec="microseconds"),
                  span_seconds=(wt[-1] - wt[0]).total_seconds(),
                  observed_timestamp_rate_hz=(len(wt) - 1) / (wt[-1] - wt[0]).total_seconds(),
                  intervals=wi, stored_timestamp_resolution_ns=1000,
                  timestamp_timezone="naive; no timezone identifier stored",
                  clock_basis="paper describes NTP alignment; per-packet RF sampling timing is not established",
                  source_packet_sequence_available=False,
                  always_zero_fft_indices_by_rx=[np.where(zero[:, a].all(axis=0))[0].tolist() for a in range(2)],
                  never_zero_in_either_rx_fft_indices=usable),
        reference_heart_rate=dict(pickle_records=hr_records, samples=len(ht), dtype=str(hr.dtype),
                                  first_timestamp=ht[0].isoformat(timespec="microseconds"), last_timestamp=ht[-1].isoformat(timespec="microseconds"),
                                  span_seconds=(ht[-1] - ht[0]).total_seconds(), intervals=hi,
                                  min_bpm=int(hr.min()), max_bpm=int(hr.max()), mean_bpm=float(hr.mean()),
                                  outside_current_48_to_120_bpm_samples=int(((hr < 48) | (hr > 120)).sum()),
                                  raw_ecg_or_rr_intervals_present=False),
        pairing=dict(filename_identity_matches=True, scene="1", user="1", activity="sit", trial="1", capture="20240519162409",
                     overlap_start=common_start.isoformat(timespec="microseconds"), overlap_end=common_end.isoformat(timespec="microseconds"),
                     overlap_seconds=overlap, residual_cross_modality_clock_offset_verified=False,
                     comment="Timestamp overlap is not independent proof of physiological synchronization"),
        current_reference_contract=dict(sample_rate_hz=50, max_interval_deviation_ms=2,
                                        warmup_seconds=10, estimation_seconds=30, required_samples=2000, max_samples=2048,
                                        total_intervals=len(wd), violating_intervals=int((~good).sum()),
                                        longest_compatible_sample_run=longest + 1,
                                        first_2000_sample_span_seconds=(wt[1999] - wt[0]).total_seconds(),
                                        directly_compatible=not reasons, reasons=reasons),
        structure_and_timestamp_overlap_passed=bool(wi["nonpositive"] == 0 and hi["nonpositive"] == 0 and overlap >= 40),
        stage_a_passed=not reasons, stage_b_started=False,
        resampling_performed=False, source_samples_dropped_or_interpolated=False,
        reference_clock_relabelled_as_verified=False, algorithm_modified=False,
        heart_estimation_executed=False, real_heart_rate_accuracy_verified=False,
        next_action="Report the timing/sequence contract gap to the user before resampling or changing the algorithm/interface",
    )
    with targets[0].open("x", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

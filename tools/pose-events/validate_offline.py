"""Run only standalone host executables; no device, model, SDK, SSH or network work."""
from __future__ import annotations
import argparse
import csv
import ctypes
import json
import os
import platform
from pathlib import Path
import subprocess
import time


def run(command, destination):
    before = time.perf_counter()
    process = subprocess.Popen([str(x) for x in command], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    info = {"command": [str(x) for x in command], "exit_code": process.returncode,
            "wall_seconds": time.perf_counter() - before,
            "peak_working_set_bytes": None, "process_cpu_seconds": None}
    if os.name == "nt":
        from ctypes import wintypes as w
        class Memory(ctypes.Structure):
            _fields_ = [("cb", w.DWORD), ("faults", w.DWORD)] + [
                (name, ctypes.c_size_t) for name in ("peak_working_set", "working_set",
                "peak_paged", "paged", "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile")]
        memory = Memory()
        memory.cb = ctypes.sizeof(memory)
        api = ctypes.WinDLL("psapi")
        api.GetProcessMemoryInfo.argtypes = [w.HANDLE, ctypes.c_void_p, w.DWORD]
        if api.GetProcessMemoryInfo(w.HANDLE(int(process._handle)), ctypes.byref(memory), memory.cb):
            info["peak_working_set_bytes"] = memory.peak_working_set
        kernel = ctypes.WinDLL("kernel32")
        kernel.GetProcessTimes.argtypes = [w.HANDLE] + [ctypes.POINTER(w.FILETIME)] * 4
        times = [w.FILETIME() for _ in range(4)]
        if kernel.GetProcessTimes(w.HANDLE(int(process._handle)), *[ctypes.byref(x) for x in times]):
            info["process_cpu_seconds"] = sum((x.dwHighDateTime << 32) | x.dwLowDateTime for x in times[2:]) / 1e7
    (destination.with_suffix(".stdout.txt")).write_bytes(stdout)
    (destination.with_suffix(".stderr.txt")).write_bytes(stderr)
    destination.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    if process.returncode:
        raise RuntimeError(f"Native exit {process.returncode}: {stderr.decode(errors='replace')}")
    return info


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--tests", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--dataset-contract", type=Path,
                        help="Optional read-only dataset audit; known facts never invent semantic trust")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    for field in ("exe", "tests", "input", "audit", "output"):
        setattr(args, field, getattr(args, field).resolve())
    test_info = run([args.tests, args.output / "synthetic-summary.json",
                     args.output / "synthetic-feedback.csv"], args.output / "tests-execution.json")
    archive_info = run([args.exe, args.input, args.output / "archive-trace.csv",
                        args.output / "archive-summary.json"], args.output / "archive-execution.json")
    archive = json.loads((args.output / "archive-summary.json").read_text(encoding="utf-8"))
    synthetic = json.loads((args.output / "synthetic-summary.json").read_text(encoding="utf-8"))
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    dataset = None
    if args.dataset_contract:
        dataset = json.loads(args.dataset_contract.read_text(encoding="utf-8"))
        if archive.get("dataset_profile") != dataset["schema"]:
            raise AssertionError("Offline executable/dataset profile mismatch")
        for key in ("joint_count", "training_coordinate_unit", "training_preserves_npy_joint_order",
                    "nominal_camera_fps_in_paper"):
            if archive["dataset_facts"][key] != dataset["confirmed"][key]:
                raise AssertionError(f"Known dataset fact mismatch: {key}")
        if archive["dataset_facts"]["capture_timeline_verified"]:
            raise AssertionError("Nominal FPS promoted to a capture timeline")
        if any(dataset["activation"][key] for key in
               ("mapping_verified", "up_verified", "capture_clock_verified", "subject_verified")):
            raise AssertionError("This audit still has unresolved semantic prerequisites")
        if dataset["existing_results_source_check"]["frames"] != archive["frames"]:
            raise AssertionError("Dataset source coverage differs from consumed results")
    frames = 0
    tail = []
    with (args.output / "archive-trace.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["kind"] == "F":
                frames += 1
                if (row["stance"], row["trunk"], row["arms"], row["help"]) != ("unknown",) * 4:
                    raise AssertionError("Unverified archive produced a semantic action")
                if row["availability"] != "unverified" or row["pl_pending"] != "0":
                    raise AssertionError("Unverified archive produced normal monitoring or a request")
                if int(row["reasons"]) & 15 != 15:
                    raise AssertionError("Unknown mapping/up/time/subject causes missing")
            if row["kind"] == "T":
                tail.append(row["availability"])
    if frames != audit["frames"] or archive["help_events"] != 0:
        raise AssertionError("Archive count/request mismatch")
    if tail != ["result_stale", "input_stale", "service_lost"]:
        raise AssertionError(f"Virtual fault transitions differ: {tail}")
    with (args.output / "synthetic-feedback.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if rows[1]["availability"] != "service_lost" or rows[1]["request_pending"] != "1":
        raise AssertionError("PS freeze failed to retain the simulated request")
    if rows[-1]["request_pending"] != "0":
        raise AssertionError("Explicit acknowledgment failed")
    result = {
        "date": "2026-10-24", "status": "offline_prototype_validated_real_semantics_unknown",
        "hardware_test": False, "new_inferences": 0, "model_sdk_protocol_changed": False,
        "host": {"system": platform.platform(), "machine": platform.machine(),
                 "processor": os.environ.get("PROCESSOR_IDENTIFIER", platform.processor()),
                 "measurement": "Release C++17 -O2 -DNDEBUG -ffp-contract=off; host only, not ARM/PS measured"},
        "contract_audit": audit, "archive": archive, "synthetic": synthetic,
        "independent_trace_checks": {"unverified_frames": frames, "tail_states": tail,
                                     "freeze_latch_and_ack": True},
        "executions": {"tests": test_info, "archive": archive_info},
        "limits": ["No verified anatomical index map or physical up calibration for real outputs",
                   "Host send/receive times do not establish original human action duration",
                   "Synthetic logic tests/benchmark are not human recognition accuracy or PL timing",
                   "No action labels: F1, human request recall and false alarms/hour remain unavailable",
                   "sizeof excludes string storage; process peak includes runtime/CLI/timing buffers"]}
    if dataset is not None:
        result["status"] = "dataset_audited_real_semantics_remain_unknown"
        result["dataset_contract"] = {"path": str(args.dataset_contract.resolve()),
                                      "schema": dataset["schema"],
                                      "processed_labels_inspected": sum(x["frames"] for x in dataset["processed_labels"].values()),
                                      "facts_match_offline_executable": True,
                                      "existing_result_sources_checked": dataset["existing_results_source_check"]["frames"]}
    (args.output / "validation-summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "archive_frames": frames,
                      "synthetic_cases": synthetic["passed_cases"],
                      "synthetic_us": synthetic["host_core_and_feedback_us"],
                      "archive_core_us": archive["core_and_feedback_us"],
                      "archive_decode_and_core_us": archive["frame_decode_and_core_us"],
                      "process_peaks": [test_info["peak_working_set_bytes"], archive_info["peak_working_set_bytes"]]}, indent=2))


if __name__ == "__main__":
    main()

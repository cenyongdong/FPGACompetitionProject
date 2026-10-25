"""Read existing labels/metadata only. No inference, SDK, devices or network calls.

Paper facts below were checked against the local CVPR PDF (pp. 3, 5, 6).
Candidate names deliberately do not establish array indices or wrist identities.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path
import re
import time
import zipfile

import numpy as np


CANDIDATE_NAMES = ["neck", "head", "left_shoulder", "right_shoulder",
                   "left_elbow", "left_hip", "right_elbow", "right_hip",
                   "left_hand", "left_knee", "right_hand", "right_knee",
                   "left_ankle", "right_ankle"]
TOPOLOGY = [[0, 1], [0, 2], [0, 3], [2, 4], [2, 5], [3, 6], [3, 7],
            [4, 8], [5, 7], [5, 9], [6, 10], [7, 11], [9, 12], [11, 13]]


def identity(name):
    match = re.fullmatch(r"(S\d+_\d+)_(\d+)", name)
    if not match:
        raise ValueError(f"Unknown sample name: {name}")
    return match[1], int(match[2])


def stats(values):
    return dict(zip(("min", "p01", "median", "p99", "max"),
                    np.percentile(values, [0, 1, 50, 99, 100]).tolist()))


def time_tables(root):
    result = []
    for path in sorted((root / "rgbd").glob("*/time_list.txt")):
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        rows = [line.split("_", 1) for line in lines if line.strip()]
        indices = [int(row[0]) for row in rows]
        stamps = [datetime.fromisoformat(row[1]) for row in rows]
        deltas = [(b - a).total_seconds() * 1000 for a, b in zip(stamps, stamps[1:])]
        result.append({"path": str(path.resolve()), "clip": path.parent.name,
                       "rows": len(rows), "first_index": indices[0], "last_index": indices[-1],
                       "index_gaps": sum(b != a + 1 for a, b in zip(indices, indices[1:])),
                       "elapsed_seconds": (stamps[-1] - stamps[0]).total_seconds(),
                       "delta_ms": stats(deltas), "nonpositive_deltas": sum(x <= 0 for x in deltas),
                       "capture_clock_verified": False,
                       "processed_sample_alignment_verified": False})
    csi = []
    for path in sorted((root / "CSI").glob("*/time/*.txt")):
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        stamps = [datetime.strptime(line.strip(), "%H:%M:%S.%f") for line in lines if line.strip()]
        deltas = [(b - a).total_seconds() * 1000 for a, b in zip(stamps, stamps[1:])]
        csi.append({"path": str(path.resolve()), "rows": len(stamps),
                    "elapsed_seconds": (stamps[-1] - stamps[0]).total_seconds(),
                    "delta_ms": stats(deltas), "nonpositive_deltas": sum(x <= 0 for x in deltas),
                    "matched_to_processed_csi_window": False})
    return {"rgbd_tables": result, "csi_tables": csi,
            "interpretation": "Original tables exist; their clock generation and raw-index to processed suffix mapping remain unknown. No nominal-fps interpolation is authorized."}


def archive_inventory(path):
    entries = []
    for block in path.read_text(encoding="utf-8-sig").split("\n\n"):
        entry = dict(line.split(" = ", 1) for line in block.splitlines() if " = " in line)
        if int(entry.get("Size", "0")) > 0:
            entries.append(entry)
    return {"file_count": len(entries),
            "extensions": dict(Counter(Path(e["Path"]).suffix for e in entries)),
            "annotation_export_or_alignment_script_found": False,
            "calibration_scope": "The one calibration.json is S11_06 camera intrinsics/extrinsics; it is not a processed-label transform or gravity/room calibration."}


def audit_labels(repo, archive):
    summary, manifests = {}, {}
    up_differences, torso_cosines, lengths = [], [], []
    started = time.perf_counter()
    with zipfile.ZipFile(archive) as source_zip:
        members = source_zip.infolist()
        zip_ext = Counter(Path(x.filename).suffix for x in members if not x.is_dir())
        for split in ("train", "test"):
            base = repo / "data/wifipose" / f"{split}_data"
            list_path = base / f"{split}_data_list.txt"
            names = [x.split()[0] for x in list_path.read_text().splitlines() if x.strip()]
            manifests[split] = set(names)
            if len(names) != len(set(names)):
                raise ValueError("Duplicate dataset sample names")
            original_list = source_zip.read(f"{split}_data/{split}_data_list.txt").decode("utf-8-sig")
            original_names = [x.split()[0] for x in original_list.splitlines() if x.strip()]
            if names != original_names:
                raise ValueError("Local/original zip sample order differs")
            clips, people = defaultdict(list), Counter()
            checked_bytes, shapes = 0, Counter()
            for i, name in enumerate(names):
                clip, index = identity(name)
                clips[clip].append(index)
                label_path = base / "keypoint" / f"{name}.npy"
                points = np.load(label_path, allow_pickle=False)
                if points.ndim != 3 or points.shape[1:] != (14, 3) or not np.isfinite(points).all():
                    raise ValueError(f"Invalid label array: {label_path}")
                people[int(points.shape[0])] += 1
                shapes[str(points.shape)] += 1
                # Numerical corroboration only; not an anatomical or gravity calibration.
                up_differences.extend((points[:, [12, 13], 2].mean(1) - points[:, 1, 2]).tolist())
                torso = points[:, [2, 3], :].mean(1) - points[:, [5, 7], :].mean(1)
                norm = np.linalg.norm(torso, axis=1)
                torso_cosines.extend((-torso[norm > 1e-9, 2] / norm[norm > 1e-9]).tolist())
                lengths.extend(np.linalg.norm(points[:, 4] - points[:, 8], axis=1).tolist())
                # Sparse byte comparisons establish the inspected local labels' archive provenance.
                if i in {0, len(names) // 4, len(names) // 2, 3 * len(names) // 4, len(names) - 1}:
                    if source_zip.read(f"{split}_data/keypoint/{name}.npy") != label_path.read_bytes():
                        raise ValueError("Local/original label bytes differ")
                    checked_bytes += 1
                if (i + 1) % 20000 == 0:
                    print(f"Audited {split} labels: {i + 1}", flush=True)
            summary[split] = {"frames": len(names), "people_counts": dict(people), "shapes": dict(shapes),
                              "clip_count": len(clips), "sample_list_exactly_matches_original_zip": True,
                              "sparse_label_byte_matches": checked_bytes,
                              "within_clip_list_order_decreases": sum(
                                  b < a for v in clips.values() for a, b in zip(v, v[1:])),
                              "within_clip_missing_integer_indices": sum(
                                  b - a - 1 for v in clips.values() for a, b in zip(sorted(v), sorted(v)[1:])),
                              "source_index_range": [min(min(v) for v in clips.values()), max(max(v) for v in clips.values())]}
        zip_info = {"file_count": sum(not x.is_dir() for x in members), "extensions": dict(zip_ext),
                    "annotation_arrays_contain_names_ids_action_labels_or_timestamps": False,
                    "dedicated_metadata_files": [x.filename for x in members
                                                 if not x.is_dir() and Path(x.filename).suffix not in (".mat", ".npy")],
                    "all_csi_mat_fields_inspected": False}
    return summary, manifests, zip_info, {
        "classification": "corroboration_only_not_verified_mapping_or_up",
        "candidate_ankles_minus_head_C2_m": stats(up_differences),
        "candidate_torso_alignment_with_minus_C2": stats(torso_cosines),
        "candidate_elbow_to_hand_length_m": stats(lengths),
        "audit_wall_seconds": time.perf_counter() - started}


def revalidate_archive(csv_path, manifests):
    import csv
    counts, missing = Counter(), []
    with csv_path.open(encoding="utf-8", newline="") as stream:
        rows = csv.DictReader(line for line in stream if not line.startswith("#"))
        for row in rows:
            if row["kind"] != "F":
                continue
            split, clip = row["segment"].split(":", 1)
            name = f"{clip}_{row['capture_sequence']}"
            counts[split] += 1
            if name not in manifests[split]:
                missing.append(name)
            if row["capture_ns"] != "0" or row["clock"] != "unknown" or row["subject_verified"] != "0":
                raise ValueError("Existing offline input invented timing or subject trust")
    if missing:
        raise ValueError(f"Archive sources missing from original lists: {missing[:3]}")
    return {"frames": sum(counts.values()), "splits": dict(counts), "all_sources_present_in_original_lists": True,
            "unknown_capture_times_and_subject_flags_preserved": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--processed-archive", required=True, type=Path)
    parser.add_argument("--raw-list", required=True, type=Path)
    parser.add_argument("--raw-metadata", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    before = args.processed_archive.stat()
    labels, manifests, zipped, geometry = audit_labels(args.repo, args.processed_archive)
    after = args.processed_archive.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Source archive changed during audit")
    # Inspect MAT metadata using an existing environment; never execute training imports.
    import h5py
    mats = []
    for split in ("train", "test"):
        for name in sorted(manifests[split])[::max(1, len(manifests[split]) // 3)][:3]:
            path = args.repo / "data/wifipose" / f"{split}_data/csi/{name}.mat"
            with h5py.File(path, "r") as handle:
                mats.append({"path": str(path), "keys": list(handle.keys()),
                             "csi_out_shape": list(handle["csi_out"].shape),
                             "csi_out_dtype": str(handle["csi_out"].dtype),
                             "timestamp_field_present": any("time" in k.lower() for k in handle.keys())})
    result = {
        "schema": "person_in_wifi_3d_2024_audit_v1", "date": "2026-10-24",
        "hardware_test": False, "new_inferences": 0, "model_sdk_protocol_changed": False,
        "sources": {"repo": str(args.repo.resolve()), "processed_archive": str(args.processed_archive.resolve()),
                    "processed_archive_size_bytes": before.st_size, "processed_archive_unchanged_size_mtime": True,
                    "raw_inventory": str(args.raw_list.resolve()),
                    "paper": str(args.repo / "paper/Person-in-WiFi_3D_End-to-End_Multi-Person_3D_Pose_Estimation_with_Wi-Fi.pdf"),
                    "paper_url": "https://aiotgroup.github.io/Person-in-WiFi-3D/paper/2024CVPR_Person_in_WiFi_3D.pdf"},
        "confirmed": {"joint_count": 14, "label_axes": 3, "training_coordinate_unit": "m",
                      "training_preserves_npy_joint_order": True, "nominal_camera_fps_in_paper": 15,
                      "label_source": "Kinect Body Tracking SDK, followed by frame-by-frame cleaning (paper section 5.1)",
                      "label_order_evidence": ["opera/datasets/wifi_pose.py:get_item_single_frame np.load then FloatTensor",
                                               "opera/datasets/pipelines/formatting.py extra_keys to_tensor without reindex",
                                               "opera/models/dense_heads/petr_head.py:739-753 assigns GT then reshape without reindex"],
                      "unit_evidence": "wifi_pose.py calc_mpjpe multiplies raw coordinate differences by 1000 for millimetres; existing raw-coordinate visualization explicitly uses metres"},
        "unknown": {"anatomical_index_mapping_verified": False, "physical_up_calibration_verified": False,
                    "source_capture_times_verified": False, "single_subject_identity_verified": False,
                    "hand_endpoint_is_wrist_verified": False, "raw_to_processed_frame_index_mapping_verified": False,
                    "action_or_help_intent_labels_available": False},
        "candidate_mapping": {"status": "paper_row_order_plus_topology_corroborated_not_export_verified",
                              "index_names": dict(enumerate(CANDIDATE_NAMES)), "topology": TOPOLOGY,
                              "evidence": "CVPR paper Table 2 row order agrees with limb_loss.py graph; Table 2 has no array indices and the Kinect subset/export script is absent",
                              "hand_caveat": "Table 2 says hand, not wrist; no K4ABT joint-ID selection list found"},
        "candidate_coordinates": {"observed_up": [0, 0, -1], "status": "corroborated_not_calibrated",
                                  "axis_names": ["unknown", "unknown", "unknown"],
                                  "evidence": "Stored label geometry and existing display; no camera-to-label transform or gravity calibration found. Do not substitute Azure Kinect native axes."},
        "processed_labels": labels, "processed_archive_inventory": zipped,
        "raw_archive_inventory": archive_inventory(args.raw_list), "mat_samples": mats,
        "raw_time_audit": time_tables(args.raw_metadata), "geometry_diagnostics": geometry,
        "existing_results_source_check": revalidate_archive(args.input, manifests),
        "activation": {"mapping_verified": False, "up_verified": False, "capture_clock_verified": False,
                       "subject_verified": False, "expected_real_actions": "unknown", "expected_help_events": 0},
        "limits": ["Paper table order, sample geometry and nominal FPS are not an explicit export/alignment contract",
                   "Only six CSI MAT metadata samples and five RGB-D tables inspected; all processed labels inspected",
                   "Raw MKV tracks not extracted or inspected",
                   "No independent action/intent labels; no recognition accuracy, recall or false alarms/hour claim"]}
    result["split_index_audit"] = {
        "shared_train_test_sample_names": len(manifests["train"] & manifests["test"]),
        "released_test_suffix_range": labels["test"]["source_index_range"],
        "paper_first550_last50_rule_cannot_be_applied_to_released_suffixes": True,
        "list_order_is_not_a_capture_timeline": True}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"labels": labels, "existing_results": result["existing_results_source_check"],
                      "activation": result["activation"], "audit_seconds": geometry["audit_wall_seconds"]}, indent=2))


if __name__ == "__main__":
    main()

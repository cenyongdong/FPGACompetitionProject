"""Compare index hypotheses against owned, previously validated outputs.

Only distances and raw-axis diagnostics are computed. No semantic gate, model,
SDK, frame protocol, pose coordinates or temporal identity is changed.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

import numpy as np


IMAGE_NAMES = ["left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
               "left_wrist", "right_wrist", "left_hip", "right_hip", "left_knee",
               "right_knee", "left_ankle", "right_ankle", "head_top", "neck"]


def distribution(values):
    values = np.asarray(values, dtype=np.float64).reshape(-1)
    if not values.size or not np.isfinite(values).all():
        raise ValueError("Missing/non-finite geometry")
    result = dict(zip(("min", "p05", "median", "p95", "max"),
                      np.percentile(values, [0, 5, 50, 95, 100]).tolist()))
    result["mean"] = float(values.mean())
    result["stddev"] = float(values.std())
    return result


def metrics(poses, names):
    lookup = {name: i for i, name in enumerate(names)}
    # Endpoints are kept as named by each source, never silently changed to wrist.
    distal_l = lookup.get("left_wrist", lookup.get("left_hand"))
    distal_r = lookup.get("right_wrist", lookup.get("right_hand"))
    head = lookup.get("head_top", lookup.get("head"))
    index_pairs = {
        "head_neck": [head, lookup["neck"]],
        "shoulder_width": [lookup["left_shoulder"], lookup["right_shoulder"]],
        "hip_width": [lookup["left_hip"], lookup["right_hip"]],
        "upper_arm_l": [lookup["left_shoulder"], lookup["left_elbow"]],
        "upper_arm_r": [lookup["right_shoulder"], lookup["right_elbow"]],
        "forearm_or_elbow_to_hand_l": [lookup["left_elbow"], distal_l],
        "forearm_or_elbow_to_hand_r": [lookup["right_elbow"], distal_r],
        "thigh_l": [lookup["left_hip"], lookup["left_knee"]],
        "thigh_r": [lookup["right_hip"], lookup["right_knee"]],
        "shank_l": [lookup["left_knee"], lookup["left_ankle"]],
        "shank_r": [lookup["right_knee"], lookup["right_ankle"]],
    }
    distances = {name: {"indices": indices,
                        "distance_mm": distribution(np.linalg.norm(poses[:, indices[0]] -
                                                                     poses[:, indices[1]], axis=1) * 1000)}
                 for name, indices in index_pairs.items()}
    return {"index_names": names, "pose_count": len(poses), "distances": distances,
            "raw_head_minus_neck_C2_mm": distribution(
                (poses[:, head, 2] - poses[:, lookup["neck"], 2]) * 1000)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--gt-samples-per-split", type=int, default=32)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if not 1 <= args.gt_samples_per_split <= 256:
        raise ValueError("Ground-truth spot check must be bounded to 1..256 per split")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    candidate = [contract["candidate_mapping"]["index_names"][str(i)] for i in range(14)]
    original = args.input.stat()
    frames, poses, scores = [], [], []
    with args.input.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(line for line in stream if not line.startswith("#")):
            if row["kind"] != "F":
                continue
            split, clip = row["segment"].split(":", 1)
            coordinates = np.asarray([float(row[f"j{j}c{c}"]) for j in range(14) for c in range(3)])
            if not np.isfinite(coordinates).all() or not np.isfinite(float(row["score"])):
                raise ValueError("Invalid existing output")
            frames.append({"split": split, "sample": f"{clip}_{row['capture_sequence']}",
                           "result_sequence": int(row["sequence"])})
            poses.append(coordinates.reshape(14, 3))
            scores.append(float(row["score"]))
    if not poses:
        raise ValueError("No owned pose outputs")
    if len({(f["split"], f["sample"]) for f in frames}) != len(frames):
        raise ValueError("Use one result per source; repeated inferences must not inflate the count")
    observed = np.stack(poses)
    truth, paired_predictions, selected_sources = [], [], []
    for split in ("train", "test"):
        indices = [i for i, f in enumerate(frames) if f["split"] == split]
        for offset in np.linspace(0, len(indices) - 1, min(args.gt_samples_per_split, len(indices)), dtype=int):
            i = indices[offset]
            path = args.dataset / f"{split}_data/keypoint/{frames[i]['sample']}.npy"
            labels = np.load(path, allow_pickle=False)
            if labels.ndim != 3 or labels.shape[1:] != (14, 3) or not len(labels) or not np.isfinite(labels).all():
                raise ValueError(f"Invalid corresponding label: {path}")
            truth.extend(labels)
            # Index-wise nearest pose only verifies frame-level numerical correspondence.
            # This uses GT for offline analysis and is not tracking or a deployable selector.
            errors = np.linalg.norm(labels - observed[i], axis=2).mean(1) * 1000
            nearest = int(np.argmin(errors))
            paired_predictions.append(observed[i])
            selected_sources.append({**frames[i], "gt_people": len(labels),
                                     "nearest_gt_row": nearest,
                                     "minimum_indexwise_mpjpe_mm": float(errors[nearest])})
    truth = np.stack(truth)
    paired_predictions = np.stack(paired_predictions)
    after = args.input.stat()
    if (original.st_size, original.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Source output CSV changed during read-only comparison")
    names = {"screenshot_crowdpose": IMAGE_NAMES, "paper_topology_candidate": candidate}
    result = {
        "schema": "pose_joint_hypothesis_comparison_v1", "date": "2026-10-24",
        "hardware_test": False, "new_inferences": 0, "model_sdk_protocol_changed": False,
        "source": {"owned_outputs": str(args.input.resolve()),
                   "archive_origin": "demo_v1/runs/delivery-long-r1/actual.full, decoded/identity/selected-full agreement checked in the initial import",
                   "model_context": "Existing shared FP16 board outputs; numerical validation is not anatomical/action ground truth",
                   "dataset": str(args.dataset.resolve()), "contract": str(args.contract.resolve()),
                   "csv_unchanged_size_mtime": True},
        "output_frames": len(frames), "splits": dict(Counter(f["split"] for f in frames)),
        "scores": distribution(scores),
        "observed_output_geometry": {k: metrics(observed, v) for k, v in names.items()},
        "matched_subset_output_geometry": {k: metrics(paired_predictions, v) for k, v in names.items()},
        "corresponding_gt_geometry": {k: metrics(truth, v) for k, v in names.items()},
        "gt_spot_check": {"frames": len(selected_sources), "people": len(truth),
                          "selection": f"Up to {args.gt_samples_per_split} evenly spaced existing sources per split, not consecutive frames",
                          "sources": selected_sources},
        "conclusion": {"screenshot_map_directly_applicable_to_stored_outputs": False,
                       "paper_topology_candidate_numerically_supported": True,
                       "explicit_anatomical_export_verified": False,
                       "hand_equals_wrist_verified": False,
                       "physical_up_verified": False, "capture_timeline_verified": False,
                       "semantic_activation_changed": False},
        "limits": ["Distances are numerical diagnostics under two name hypotheses, not action accuracy",
                   "Matching GT by index does not independently establish joint names, body identity or left/right semantics",
                   f"All selected outputs checked geometrically; only {len(selected_sources)} corresponding label files inspected",
                   "No axis flip, coordinate reorder, model invocation or temporal stitching"]}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    compact = {"output_frames": len(frames), "gt_frames": len(selected_sources), "gt_people": len(truth)}
    for section in ("observed_output_geometry", "corresponding_gt_geometry"):
        compact[section] = {hyp: {name: x["distances"][name]["distance_mm"]
                                  for name in ("shoulder_width", "head_neck", "shank_l", "shank_r")}
                            for hyp, x in result[section].items()}
    print(json.dumps(compact, indent=2))


if __name__ == "__main__":
    main()

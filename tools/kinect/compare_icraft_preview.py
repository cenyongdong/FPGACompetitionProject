"""Compare saved Icraft generated-graph Host outputs with this model's FP32 outputs.

This command reads existing conversion/reference artifacts only; it never invokes
Icraft, PyTorch, a GPU, or a device. Numerical differences are reported without an
accuracy acceptance threshold. Existing reports and native outputs are preserved.
"""

import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np


NAME = "piw24_pose180"
INPUT_SHAPE = (1, 180, 60)
SCORE_SHAPE = (1, 180)
POSE_SHAPE = (1, 180, 14, 3)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_f32(path, shape):
    """Read a complete, finite, headerless little-endian FP32 tensor."""
    expected = int(np.prod(shape)) * 4
    actual = path.stat().st_size
    if actual != expected:
        raise ValueError(f"{path}: expected {expected} bytes, found {actual}")
    values = np.fromfile(path, dtype="<f4").reshape(shape)
    if not np.isfinite(values).all():
        raise ValueError(f"{path}: non-finite values; original file retained")
    return values


def generated_graph(model_dir):
    graph = read_json(model_dir / f"{NAME}_ZG.json")
    ops = graph["ops"]
    counts = Counter(op["_type_key"] for op in ops)
    inputs = [op for op in ops if op["_type_key"] == "icraft::xir::Input"]
    outputs = [op for op in ops if op["_type_key"] == "icraft::xir::Output"]
    if len(inputs) != 1 or len(outputs) != 1:
        raise ValueError("Generated graph must have one Input and one Output operator")
    input_ports = inputs[0]["outputs"]
    output_ports = outputs[0]["inputs"]
    if len(input_ports) != 1 or len(output_ports) != 2:
        raise ValueError("Generated graph must expose one input and two outputs")
    ports = input_ports + output_ports
    shapes = [tuple(port["dtype"]["shape"]) for port in ports]
    if shapes[0] != INPUT_SHAPE or set(shapes[1:]) != {SCORE_SHAPE, POSE_SHAPE}:
        raise ValueError(f"Unexpected generated graph port shapes: {shapes}")
    if any(port["dtype"]["element_dtype"] != "@fp(32)" for port in ports):
        raise ValueError("Generated graph public ports must remain FP32")
    host = [dict(id=op["op_id"], type=op["_type_key"]) for op in ops
            if op["compile_target"] == "@hostt"
            and op["_type_key"] not in ("icraft::xir::Input", "icraft::xir::Output")]
    if host:
        raise ValueError(f"Generated graph retains Host computation: {host}")
    raw_bytes = (model_dir / f"{NAME}_ZG.raw").stat().st_size
    if raw_bytes != graph["params_bytes"]:
        raise ValueError("Generated graph parameter file size differs from JSON")
    output_ids = {tuple(port["dtype"]["shape"]): int(port["v_id"])
                  for port in output_ports}
    if any(value < 0 for value in output_ids.values()) or len(set(output_ids.values())) != 2:
        raise ValueError("Invalid or duplicate generated output value IDs")
    summary = dict(
        stage="generate", operators=dict(counts), host_compute=host,
        topk=sum(n for kind, n in counts.items() if "topk" in kind.lower()),
        candidate_gather_elements=sum(n for kind, n in counts.items()
                                      if "gatherelements" in kind.lower()),
        scatter_nd=sum(n for kind, n in counts.items() if "scatternd" in kind.lower()),
        port_shapes=[list(shape) for shape in shapes], raw_bytes=raw_bytes,
        static_layer_count_sum=sum(op.get("layer_count", 0) for op in ops),
    )
    return summary, output_ids


def compare_model(model_dir):
    """Return the report without writing, permitting read-only regression checks."""
    model_dir = Path(model_dir).resolve()
    conversion = read_json(model_dir / "conversion.json")
    stages = conversion["stages"]
    expected_stages = {"parse", "optimize", "quantize", "adapt", "generate"}
    if {stage["stage"] for stage in stages} != expected_stages:
        raise ValueError("Conversion record does not contain all five stages")
    for stage in stages:
        if stage["native_exit"] != 0:
            raise ValueError(f"Native {stage['stage']} exit was {stage['native_exit']}")
    summary, output_ids = generated_graph(model_dir)
    cases = read_json(model_dir / "fixtures/cases.json")
    if not isinstance(cases, list) or not cases:
        raise ValueError("fixtures/cases.json must contain a nonempty case list")
    samples = []
    seen = set()
    for case in cases:
        name = case["name"]
        if (not isinstance(name, str) or not name or name in (".", "..")
                or any(c in name for c in ("/", "\\", ":")) or name in seen):
            raise ValueError(f"Invalid or duplicate case name: {name!r}")
        seen.add(name)
        folder = model_dir / "reference-generated" / name
        native_exit = read_json(folder / "exit.json")["native_exit"]
        if native_exit != 0:
            raise ValueError(f"{name}: native Host exit was {native_exit}")
        # A .ftmp SFB output contains raw FP32 values, without a NumPy header.
        output_dir = folder / "native" / NAME / "ftmpSFB"
        scores = read_f32(output_dir / f"{output_ids[SCORE_SHAPE]}.ftmp", SCORE_SHAPE)[0]
        poses = read_f32(output_dir / f"{output_ids[POSE_SHAPE]}.ftmp", POSE_SHAPE)[0]
        fp32_scores = read_f32(model_dir / "fixtures" / f"{name}.fp32.scores.f32", SCORE_SHAPE)[0]
        fp32_poses = read_f32(model_dir / "fixtures" / f"{name}.fp32.poses.f32", POSE_SHAPE)[0]
        joint_delta = np.linalg.norm(poses.astype(np.float64) - fp32_poses, axis=-1) * 1000
        fp32_top1 = int(fp32_scores.argmax())
        generated_top1 = int(scores.argmax())
        # Compare the actual selected poses if quantization changes Top1 identity.
        top1_delta = np.linalg.norm(
            poses[generated_top1].astype(np.float64) - fp32_poses[fp32_top1], axis=-1
        ) * 1000
        samples.append(dict(
            name=name, source_sample=case.get("source_sample"), split=case.get("split"),
            native_exit=native_exit, finite=True,
            score_max_abs=float(np.abs(scores.astype(np.float64) - fp32_scores).max()),
            all_candidate_joint_max_mm=float(joint_delta.max()),
            all_candidate_joint_mean_mm=float(joint_delta.mean()),
            fp32_top1_index=fp32_top1, generated_top1_index=generated_top1,
            top1_index_unchanged=fp32_top1 == generated_top1,
            fp32_top1_score=float(fp32_scores[fp32_top1]),
            generated_top1_score=float(scores[generated_top1]),
            top1_joint_max_delta_mm=float(top1_delta.max()),
            top1_joint_mean_delta_mm=float(top1_delta.mean()),
        ))
    if len(cases) == 3 and all(case.get("split") == "train" for case in cases):
        reference = "current frozen checkpoint PyTorch FP32; same three TRAIN inputs"
    else:
        reference = f"current frozen checkpoint PyTorch FP32; same {len(cases)} fixture inputs"
    return dict(
        native_execution_passed=True, reference=reference,
        accuracy_acceptance="not evaluated against an accuracy gate; numerical deltas recorded",
        board_tested=False, conversion_seconds=conversion["seconds"],
        generated_graph=summary, samples=samples,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.model_dir.resolve() / "host-comparison.json"
    if output.exists():
        raise FileExistsError(f"Existing report preserved: {output}")
    report = compare_model(args.model_dir)
    # Exclusive creation avoids replacing earlier numerical evidence on a rerun.
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(report=str(output), native_execution_passed=True,
                          samples=len(report["samples"])), ensure_ascii=False))


if __name__ == "__main__":
    main()

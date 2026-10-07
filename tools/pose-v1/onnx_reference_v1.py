"""Pinned CPU-only ONNX reference; reads existing verified CSI token package."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

MODEL_SHA = "7b04090e374e31e016d5703bbcf1d0a561d0b98f268fde984b0bf0461598bd21"
CASES = ("S11_01_308", "S11_01_309", "S11_01_310")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save(path, data):
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode())


def run(package, output):
    import numpy as np
    import onnxruntime as ort
    if sys.version_info[:3] != (3, 10, 21) or np.__version__ != "2.2.5" or ort.__version__ != "1.23.2":
        raise ValueError("Pinned Python/NumPy/ORT versions differ")
    prefix = Path(sys.prefix).resolve()
    if not all(Path(m.__file__).resolve().is_relative_to(prefix) for m in (np, ort)):
        raise ValueError("Modules leaked from another environment")
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    if tuple(c["case"] for c in manifest["cases"]) != CASES:
        raise ValueError("Three-case manifest changed")
    for item in manifest["files"]:
        if digest(package / item["relative_path"]) != item["sha256"]:
            raise ValueError("Source package identity differs: " + item["relative_path"])
    model = package / "models/person_in_wifi_2024_best_epoch442_full.onnx"
    if digest(model) != MODEL_SHA:
        raise ValueError("ONNX model identity differs")
    if output.exists():
        raise FileExistsError("Preserve previous reference output")
    output.mkdir(parents=True)
    try:
        options = ort.SessionOptions()
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        begin = time.perf_counter()
        session = ort.InferenceSession(str(model), sess_options=options, providers=["CPUExecutionProvider"])
        init_ms = (time.perf_counter() - begin) * 1000
        if session.get_providers() != ["CPUExecutionProvider"]:
            raise ValueError("Unexpected execution provider")
        inputs, outputs = session.get_inputs(), session.get_outputs()
        if len(inputs) != 1 or inputs[0].shape != [1, 180, 60] or inputs[0].type != "tensor(float)":
            raise ValueError("ONNX input signature differs")
        score = [o for o in outputs if o.shape == [1, 100] and o.type == "tensor(float)"]
        pose = [o for o in outputs if o.shape == [1, 100, 14, 3] and o.type == "tensor(float)"]
        if len(outputs) != 2 or len(score) != 1 or len(pose) != 1:
            raise ValueError("Ambiguous ONNX output mapping")
        records, tokens, baseline = [], [], None
        for item in manifest["cases"]:
            name = item["case"]
            raw = (package / "reference" / (name + ".input.f32")).read_bytes()
            x = np.frombuffer(raw, dtype="<f4").reshape(1, 180, 60).copy()
            if not np.isfinite(x).all():
                raise ValueError("Non-finite reference input")
            begin = time.perf_counter()
            scores, poses = session.run([score[0].name, pose[0].name], {inputs[0].name: x})
            ms = (time.perf_counter() - begin) * 1000
            if scores.shape != (1, 100) or poses.shape != (1, 100, 14, 3) or not all(np.isfinite(v).all() for v in (scores, poses)):
                raise ValueError("Invalid ONNX output")
            if any(v.dtype != np.float32 for v in (scores, poses)):
                raise ValueError("Output dtype differs")
            (output / (name + ".input.f32")).write_bytes(raw)
            score_bytes, pose_bytes = scores.astype("<f4").tobytes(), poses.astype("<f4").tobytes()
            (output / (name + ".scores.f32")).write_bytes(score_bytes)
            (output / (name + ".poses.f32")).write_bytes(pose_bytes)
            records.append(dict(item, mode="onnx_cpu_reference", forward_ms=ms,
                                top_index=int(np.argmax(scores)), top_score=float(scores.max()),
                                numerical_acceptance="reference_ready_not_board_acceptance"))
            tokens.append(x)
            if baseline is None:
                baseline = (score_bytes, pose_bytes)
        repeated = session.run([score[0].name, pose[0].name], {inputs[0].name: tokens[0]})
        if tuple(v.astype("<f4").tobytes() for v in repeated) != baseline:
            raise ValueError("Repeated first reference is not bitwise reproducible")
        (output / "results.jsonl").write_bytes("".join(json.dumps(r, allow_nan=False) + "\n" for r in records).encode())
        save(output / "environment.json", {"python": platform.python_version(), "numpy": np.__version__,
             "onnxruntime": ort.__version__, "prefix": str(prefix), "providers": session.get_providers(),
             "execution_mode": "ORT_SEQUENTIAL", "intra_op_threads": 1, "inter_op_threads": 1,
             "graph_optimization": "ORT_ENABLE_ALL", "model_sha256": MODEL_SHA,
             "source_manifest_sha256": digest(package / "manifest.json"), "runner_sha256": digest(Path(__file__)),
             "session_init_ms": init_ms, "purpose": "deployment numerical reference; no ground-truth MPJPE"})
        pairs = [(digest(output / (n + ".scores.f32")), digest(output / (n + ".poses.f32"))) for n in CASES]
        save(output / "summary.json", {"status": "onnx_reference_ready", "cases": 3,
             "repeated_first_bitwise_equal": True, "distinct_input_response": len(set(pairs)) > 1,
             "board_numerical_accepted": False, "mixed_verified": False})
        paths = sorted(p for p in output.rglob("*") if p.is_file())
        (output / "files.sha256").write_bytes("".join(f"{digest(p)}  {p.relative_to(output).as_posix()}\n" for p in paths).encode())
        print(f"ONNX CPU reference ready, 3 cases and repeated-first bitwise equal: {output}")
    except Exception as error:
        save(output / "failure.json", {"error": str(error), "status": "failed_stop_no_retry"})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.package.resolve(), args.output.resolve())

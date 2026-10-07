"""User-run synthetic CPU gate: fixed NumPy reference, hashing, returned evidence.

No inference, SDK loading, SSH, Docker invocation or dependency installation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
GRAPH_SHA = "75ffdc37b93dcb4913678991d6e7cf5cd0ab09c59653224d07c7434345acb8a0"
HOST_SHA = "d0fbf6c81e5b57b4a908f11aad27571b8f2e68a3ede7ba33c9a4f783ba266130"
BUILD_FILES = {
    "software/pose_v1/include/host_cpu_adapter.hpp": "host_cpu_adapter.hpp",
    "software/pose_v1/src/host_cpu_adapter.cpp": "host_cpu_adapter.cpp",
    "software/pose_v1/src/host_cpu_adapter_check.cpp": "host_cpu_adapter_check.cpp",
    "tools/pose-v1/cpu-adapter-CMakeLists.txt": "CMakeLists.txt",
    "tools/pose-v1/aarch64-icraft.cmake": "toolchain.cmake",
}
HEADERS = (
    "icraft-backends/hostbackend/backend.h",
    "icraft-backends/hostbackend/common/tensor_kernel.h",
    "icraft-backends/hostbackend/port/common/tensor_ops.h",
    "icraft-xrt/core/backend.h",
    "icraft-xrt/core/tensor.h",
    "icraft-xir/core/data_type_attr.h",
)
SDK_PINS = {
    "icraft-backends/hostbackend/backend.h": "8cf82840f340ff4173d6d855f8a39b72225dc5d7681fc3d7b7ed9b3cac2da378",
    "icraft-backends/hostbackend/common/tensor_kernel.h": "509d54a778dcbc25094be73dfc5250b0b84ba3681a3d0b9f49905779338e015d",
    "icraft-backends/hostbackend/port/common/tensor_ops.h": "f339262a95a63ebe9e1834e56278e737312319a52413a1d749e1a63bf4e48e92",
    "icraft-xrt/core/backend.h": "f6a8ee61524cff91b2a4bfa5409cf46633d101ffe0528ac0c7599c21dd8b2607",
    "icraft-xrt/core/tensor.h": "4b2c4d0ad24db042f151a56afce2fba881ad8f2fe1c87c9d32d620caf89b365a",
    "icraft-xir/core/data_type_attr.h": "a0461bf7f078443fb609d472e802aed9f86407a536c8aa2058bc60a7dab50cec",
}
PRESERVED = {
    "software/pose_v1/src/inference_check.cpp": "75e51aff69c61ed431e0201aa21b10463b43add17c0ad125739f8dd252accf6d",
    "software/pose_v1/CMakeLists.txt": "0b2732d3fe62caa797628feb95f713a57d2f26812b379fb42f42d9ac114c76a3",
}

def need(yes, message):
    if not yes:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save_json(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

def write_checksums(root, name="files.sha256"):
    paths = sorted(p for p in root.rglob("*") if p.is_file() and p != root / name)
    (root / name).write_bytes("".join(f"{sha(p)}  {p.relative_to(root).as_posix()}\n" for p in paths).encode("ascii"))

def verify_checksums(root, name="files.sha256"):
    lines = (root / name).read_text(encoding="ascii").splitlines()
    need(bool(lines), "Empty checksum manifest")
    seen = set()
    for line in lines:
        need(len(line) > 66 and line[64:66] == "  ", "Invalid checksum line")
        digest, rel = line[:64], line[66:]
        rel = rel.removeprefix("./")
        target = (root / rel).resolve()
        need(target.is_relative_to(root.resolve()) and rel not in seen, "Unsafe or duplicate checksum path")
        seen.add(rel)
        need(target.is_file() and sha(target) == digest, "Hash mismatch: " + rel)
    return len(lines)

def model_specs(graph):
    j = json.loads(graph.read_text(encoding="utf-8"))
    need(j["icraft_version"] == "v3.39.0" and j["icraft_xir_version"] == "3.39.0.0", "Model version changed")
    ops = {op["op_id"]: op for op in j["ops"] if op["op_id"] in (188,192,437,442,582,649)}
    need(len(ops) == 6, "Missing CPU nodes")
    for op in ops.values():
        need(op["compile_target"] == "@hostt", "CPU target changed")
        for value in op["inputs"] + op["outputs"]:
            d = value["dtype"]
            need(d["element_dtype"] == "@fp(32)", "Only original FP32 metadata accepted")
            for distribution in d["merged_distrs"]:
                m = re.fullmatch(r"@merged_distr\(\[([0-9, ]+)\]\^ZERO:\{v:\[0, ([0-9]+)\)\}\)", distribution)
                need(m is not None, "Unexpected distribution encoding")
                axes = [int(x) for x in m[1].split(",")]
                size = 1
                for axis in axes:
                    size *= d["shape"][axis]
                need(size == int(m[2]), "Distribution is not fully valid")
    return ops

def prepare(args):
    import numpy as np
    need(np.__version__ == "2.2.5", "Use approved pose-v1-conda NumPy 2.2.5; do not install/change it")
    need(sha(args.graph) == GRAPH_SHA, "Frozen ZG graph hash changed")
    need(not args.output.exists(), "Preserve existing package; output already exists")
    pins = {rel:hashlib.sha256((args.sdk / "include" / rel).read_bytes().replace(b"\r\n",b"\n")).hexdigest() for rel in HEADERS}
    need(pins == SDK_PINS, "SDK headers differ from audited original ARM package")
    need(all(sha(ROOT / rel) == value for rel,value in PRESERVED.items()), "Original inference sources changed")
    ops = model_specs(args.graph)
    args.output.mkdir(parents=True)
    shutil.copyfile(args.graph, args.output / "piw24_ZG.json")
    fixture_root = args.output / "fixtures"
    fixture_root.mkdir()
    records = []
    manifest_cases = []

    def arrays(op):
        result = []
        for value in op["inputs"]:
            dims = value["dtype"]["shape"]
            n = int(np.prod(dims))
            a = ((np.arange(n, dtype=np.int64) % 29) - 14).astype(np.float32).reshape(dims)
            a.flat[0] = np.float32(-0.0)
            result.append(a)
        kind = op["_type_key"].split("::")[-1]
        if kind == "TopK":
            result[1][0] = np.float32(100)
        elif kind in ("Gather", "GatherElements"):
            extent = op["inputs"][0]["dtype"]["shape"][op["axis"]]
            result[1] = (np.arange(result[1].size, dtype=np.int64) * 7 % extent).astype(np.float32).reshape(result[1].shape)
        elif kind == "ScatterND":
            coords = np.indices(result[0].shape, dtype=np.int64).transpose(1,2,3,0).copy()
            coords[...,0] = 99 - coords[...,0]
            coords[...,2] = 2 - coords[...,2]
            result[1] = coords.astype(np.float32)
            result[2] = (np.arange(result[2].size, dtype=np.int64) + 1000).astype(np.float32).reshape(result[2].shape)
            result[2].flat[0] = np.float32(-0.0)
        return result

    def reference(op, values):
        kind = op["_type_key"].split("::")[-1]
        if kind == "TopK":
            # Stable sorting enforces ascending original indices for ties.
            index = np.argsort(-values[0], axis=op["axis"], kind="stable")
            selection = [slice(None)] * values[0].ndim
            selection[op["axis"]] = slice(0,100)
            index = index[tuple(selection)]
            return [np.take_along_axis(values[0],index,axis=op["axis"]), index.astype(np.float32)]
        if kind == "GatherElements":
            return [np.take_along_axis(values[0], values[1].astype(np.int64), axis=op["axis"])]
        if kind == "Gather":
            return [np.take(values[0], values[1].astype(np.int64), axis=op["axis"])]
        out = values[0].copy()
        index = values[1].astype(np.int64)
        out[tuple(index[...,axis] for axis in range(3))] = values[2]
        return [out]

    def add(opid, suffix, expected="PASS", mutation="none", buffers=False, change=None):
        op = ops[opid]
        name = f"op{opid}_{suffix}"
        directory = fixture_root / name
        directory.mkdir()
        values = arrays(op)
        if change:
            change(values)
        for i, value in enumerate(values):
            (directory / f"input{i}.f32").write_bytes(value.astype("<f4").tobytes())
        outputs = reference(op,values) if expected == "PASS" else []
        for i, value in enumerate(outputs):
            need(list(value.shape) == op["outputs"][i]["dtype"]["shape"], "Reference shape mismatch")
            (directory / f"expected{i}.f32").write_bytes(value.astype("<f4").tobytes())
        records.append(f"{name}\t{opid}\t{expected}\t{mutation}\t{int(buffers)}\n")
        manifest_cases.append({"case_id":name,"op_id":opid,"expected":expected,"mutation":mutation,
                               "buffers":buffers,"outputs":len(outputs)})

    for opid in ops:
        add(opid,"allocated")
        add(opid,"buffers",buffers=True)
    for opid in (192,582,649):
        def negative(a, current=opid):
            if current == 192:
                a[1] -= np.float32(180)
            else:
                a[1] -= np.array([100,14,3],dtype=np.float32)
        add(opid,"negative_indices",change=negative)
        add(opid,"negative_indices_buffers",buffers=True,change=negative)
    # Each missing operator type has both declared-shape and data-error gates.
    for opid in (188,192,437,582,649):
        if opid in (188,192,437):
            add(opid,"invalid_axis","axis","axis")
        for mutation, expected in (("dtype","dtype"),("shape","shape"),("layout","layout"),
                                   ("mask_gap","distribution"),("mask_length","distribution"),
                                   ("mask_axis","distribution"),("byte_mismatch","storage"),
                                   ("missing_runtime","arity"),("extra_runtime","arity")):
            add(opid,mutation,expected,mutation)
        add(opid,"wrong_output","output","wrong_output",buffers=True)
        for bad in ("nan","inf"):
            add(opid,bad,"finite",change=lambda a, b=bad: a[0].flat.__setitem__(0, np.nan if b=="nan" else np.inf))
    for opid in (188,437):
        add(opid,"unsorted","spec","sorted")
        add(opid,"output_count","output","output_count",buffers=True)
        for suffix, value in (("k_zero",0),("k_too_large",1000),("k_fraction",99.5),("k_wrong_output",50)):
            add(opid,suffix,"k",change=lambda a,v=value: a[1].__setitem__(0,np.float32(v)))
    for opid in (192,582,649):
        for suffix, value in (("index_fraction",0.5),("index_overflow",1000),("index_underflow",-1000)):
            add(opid,suffix,"kernel",change=lambda a,v=value: a[1].flat.__setitem__(0,np.float32(v)))
        add(opid,"index_nan","finite",change=lambda a: a[1].flat.__setitem__(0,np.nan))
    for opid in (582,649):
        add(opid,"reduction","reduction","reduction")
    (fixture_root / "cases.tsv").write_bytes(("case_id\top_id\texpected\tmutation\tbuffers\n" + "".join(records)).encode("ascii"))
    build_files = {rel:{"destination":dest,"sha256":sha(ROOT / rel)} for rel,dest in BUILD_FILES.items()}
    sources = {rel:sha(ROOT / rel) for rel in (*BUILD_FILES,
        "tools/pose-v1/cpu_adapter_gate.py","tools/pose-v1/Build-CpuAdapter.ps1","tools/pose-v1/run-cpu-adapter.sh")}
    save_json(args.output / "manifest.json", {
        "stage":"fixtures_prepared_not_executed","numpy_version":np.__version__,"graph_sha256":GRAPH_SHA,
        "host_library_sha256":HOST_SHA,"sdk_headers_normalized_sha256":pins,"build_files":build_files,
        "sources":sources,"cases":manifest_cases,"model_ops":list(ops.values()),
        "device_access_allowed":False,"mixed_verified":False,
        "preserved_files": PRESERVED})
    shutil.copyfile(ROOT / "tools/pose-v1/run-cpu-adapter.sh", args.output / "run-cpu-adapter.sh")
    write_checksums(args.output)
    print(f"Prepared {len(records)} CPU-only cases; no tests executed: {args.output}")

def review(args):
    import numpy as np
    need(np.__version__ == "2.2.5", "Use approved NumPy environment")
    bundle = args.package.resolve()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    need(manifest["graph_sha256"] == GRAPH_SHA and manifest["sdk_headers_normalized_sha256"] == SDK_PINS,
         "Package SDK/model baseline changed")
    package_count = verify_checksums(bundle)
    returned_count = verify_checksums(args.results)
    need((args.results / "exit.txt").read_text(encoding="ascii").strip() == "0", "Board checker failed or timed out; no numerical acceptance")
    need((args.results / "run.stderr.log").stat().st_size == 0, "Non-empty stderr requires discussion")
    build = json.loads((args.build / "build-result.json").read_text(encoding="utf-8-sig"))
    need(build["binary_sha256"] == sha(args.results / "pose_cpu_adapter_check"), "Returned binary differs from build")
    need(build["package_manifest_sha256"] == sha(bundle / "manifest.json"), "Build and fixtures differ")
    for rel, identity in manifest["build_files"].items():
        need(build["source_sha256"][rel] == identity["sha256"], "Compiled source identity differs")
    identities = {Path(line[66:]).name:line[:64] for line in
        (args.results / "input-identities.sha256").read_text(encoding="ascii").splitlines()}
    need(identities.get("piw24_ZG.json") == GRAPH_SHA and
         identities.get("libicraft_hostbackend.so") == HOST_SHA and
         identities.get("pose_cpu_adapter_check") == build["binary_sha256"], "Board identity record incomplete")
    for audit_path in (args.results / "sdk-audit.json", args.build / "sdk-audit.json"):
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        need(audit["headers_normalized_sha256"] == SDK_PINS and audit["host_sha256"] == HOST_SHA and
             all(audit["versions"].get(p) == "3.39.0" for p in ("icraft:arm64","customop:arm64")),
             "ARM SDK identity differs")
    summary = json.loads((args.results / "results/summary.json").read_text(encoding="utf-8"))
    need(summary["case_count"] == len(manifest["cases"]) and not summary["device_opened"] and
         not summary["full_model_executed"] and not summary["mixed_verified"], "Wrong run scope/count")
    records = [json.loads(line) for line in (args.results / "results/cases.jsonl").read_text(encoding="utf-8").splitlines()]
    need(len(records) == len(manifest["cases"]), "Incomplete or duplicate case results")
    numeric = []
    for expected, actual in zip(manifest["cases"],records):
        need(actual["case_id"] == expected["case_id"] and actual["op_id"] == expected["op_id"] and
             actual["expected"] == expected["expected"] and actual["passed"], "Case/order mismatch")
        need(actual["rejection"] == ("" if expected["expected"] == "PASS" else expected["expected"]), "Unexpected rejection")
        for i in range(expected["outputs"]):
            target = args.results / "results" / expected["case_id"] / f"output{i}.f32"
            reference = bundle / "fixtures" / expected["case_id"] / f"expected{i}.f32"
            need(target.read_bytes() == reference.read_bytes(), "Bitwise mismatch: " + str(target))
            value = np.frombuffer(target.read_bytes(),dtype="<f4")
            need(np.isfinite(value).all(), "Non-finite result")
            numeric.append({"case_id":expected["case_id"],"output":i,"count":value.size,"bitwise_equal":True,"max_abs_error":0.0})
    registry = [json.loads(line) for line in (args.results / "results/registry.jsonl").read_text(encoding="utf-8").splitlines()]
    need(len(registry) == 12, "Registry evidence incomplete")
    for row, (phase,opid) in zip(registry,[(p,i) for p in ("before","after") for i in (188,192,437,442,582,649)]):
        present = phase == "after" or opid == 442
        need(row["phase"] == phase and row["op_id"] == opid and
             all(row[k] == present for k in ("supported","init","forward")), "Registry baseline differs")
    need(not args.output.exists(), "Preserve previous review")
    save_json(args.output,{"status":"cpu_candidate_gate_passed","cases":len(records),"numeric":numeric,
                          "package_files_checked":package_count,"returned_files_checked":returned_count,
                          "mixed_verified":False,"device_accessed":False})
    print("CPU candidate evidence verified; complete mixed inference remains blocked/pending.")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command",required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--graph",type=Path,required=True)
    p.add_argument("--sdk",type=Path,default=Path("C:/Icraft/CLI v3.39.0"))
    p.add_argument("--output",type=Path,required=True)
    p = sub.add_parser("review")
    p.add_argument("--package",type=Path,required=True)
    p.add_argument("--build",type=Path,required=True)
    p.add_argument("--results",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    (prepare if args.command == "prepare" else review)(args)

if __name__ == "__main__":
    main()

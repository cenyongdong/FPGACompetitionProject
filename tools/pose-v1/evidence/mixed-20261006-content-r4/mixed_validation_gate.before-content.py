"""Package and inspect mixed-validation files. Never opens a board/device or installs software."""
import argparse
from collections import Counter
import hashlib
import json
import re
import runpy
from pathlib import Path
import shutil
import struct

ROOT = Path(__file__).resolve().parents[2]
CASES = ("S11_01_308", "S11_01_309", "S11_01_310")
HOST_IDS = (188, 192, 437, 442, 582, 649)
BUILD_FILES = {
    "software/pose_v1/include/mixed_bridge.hpp": "mixed_bridge.hpp",
    "software/pose_v1/include/mixed_fusion_baseline.hpp": "mixed_fusion_baseline.hpp",
    "software/pose_v1/src/mixed_bridge.cpp": "mixed_bridge.cpp",
    "software/pose_v1/src/mixed_check.cpp": "mixed_check.cpp",
    "software/pose_v1/src/mixed_host_check.cpp": "mixed_host_check.cpp",
    "software/pose_v1/include/host_cpu_adapter.hpp": "host_cpu_adapter.hpp",
    "software/pose_v1/src/host_cpu_adapter.cpp": "host_cpu_adapter.cpp",
    "software/pose_v1/include/preprocess.hpp": "preprocess.hpp",
    "software/pose_v1/src/preprocess.cpp": "preprocess.cpp",
    "tools/pose-v1/mixed-validation-CMakeLists.txt": "CMakeLists.txt",
    "tools/pose-v1/aarch64-icraft.cmake": "toolchain.cmake",
}


def need(yes, message):
    if not yes:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    need(not path.exists(), "Preserve earlier evidence: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode())


def checksum(root):
    paths = sorted(p for p in root.rglob("*") if p.is_file() and p != root / "files.sha256")
    (root / "files.sha256").write_bytes("".join(f"{sha(p)}  {p.relative_to(root).as_posix()}\n" for p in paths).encode())


def verify(root):
    found = set()
    for line in (root / "files.sha256").read_text(encoding="ascii").splitlines():
        need(line[64:66] == "  ", "Invalid checksum format")
        rel = line[66:].removeprefix("./")
        p = (root / rel).resolve()
        need(p.is_relative_to(root.resolve()) and rel not in found, "Unsafe checksum path")
        need(p.is_file() and sha(p) == line[:64], "Hash mismatch: " + rel)
        found.add(rel)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p != root / "files.sha256"}
    need(found == actual, "Unlisted or missing files")
    return len(found)


def prepare(a):
    source = load(a.source / "manifest.json")
    need(tuple(x["case"] for x in source["cases"]) == CASES, "Fixed cases changed")
    for item in source["files"]:
        need(sha(a.source / item["relative_path"]) == item["sha256"], "Original package changed")
    verify(a.cpu)
    old = load(a.cpu / "manifest.json")
    for rel, identity in old["preserved_files"].items():
        need(sha(ROOT / rel) == identity, "Original inference sources changed")
    for rel in ("software/pose_v1/include/host_cpu_adapter.hpp", "software/pose_v1/src/host_cpu_adapter.cpp",
                "software/pose_v1/src/host_cpu_adapter_check.cpp"):
        need(sha(ROOT / rel) == old["sources"][rel], "Frozen CPU implementation changed")
    pins = load(ROOT / "tools/pose-v1/mixed-sdk-pins.json")
    for rel, h in pins["headers"].items():
        raw = (Path("C:/Icraft/CLI v3.39.0/include") / rel).read_bytes()
        need(hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == h, "Local SDK header changed")
    need(not a.output.exists(), "Preserve previous package")
    a.output.mkdir(parents=True)
    for folder in ("inputs", "reference", "graph"):
        (a.output / folder).mkdir()
    for name in CASES:
        for folder, suffix in (("inputs", ".csi"), ("reference", ".input.f32")):
            shutil.copyfile(a.source / folder / (name + suffix), a.output / folder / (name + suffix))
    for name in ("piw24_ZG.json", "piw24_ZG.raw"):
        shutil.copyfile(a.source / "models" / name, a.output / "graph" / name)
    need(sha(a.output / "graph/piw24_ZG.json") == old["graph_sha256"], "Graph changed")
    shutil.copytree(a.cpu / "fixtures", a.output / "fixtures")
    shutil.copyfile(ROOT / "tools/pose-v1/run-mixed-validation.sh", a.output / "run-mixed-validation.sh")
    baseline_path = ROOT / "tools/pose-v1/mixed-fusion-baseline.json"
    baseline = load(baseline_path)
    need(baseline["graph_sha256"] == old["graph_sha256"] and
         baseline["raw_sha256"] == sha(a.output / "graph/piw24_ZG.raw") and
         baseline["host_library_sha256"] == pins["host_library_sha256"] and
         baseline["zg_library_sha256"] == pins["zg_library_sha256"], "Fusion baseline identity differs")
    shutil.copyfile(baseline_path, a.output / "mixed-fusion-baseline.json")
    save(a.output / "cpu-fixture-manifest.json", old)
    save(a.output / "manifest.json", {
        "schema_version": 1, "model": "2024 epoch442", "cases": source["cases"],
        "source_package_manifest_sha256": sha(a.source / "manifest.json"),
        "graph_sha256": old["graph_sha256"], "raw_sha256": sha(a.output / "graph/piw24_ZG.raw"),
        "sdk_headers_normalized_sha256": pins["headers"], "host_library_sha256": pins["host_library_sha256"],
        "zg_library_sha256": pins["zg_library_sha256"],
        "build_files": {r: {"destination": dest, "sha256": sha(ROOT / r)} for r, dest in BUILD_FILES.items()},
        "sources": {r: sha(ROOT / r) for r in (*BUILD_FILES, "tools/pose-v1/Build-MixedValidation.ps1",
                    "tools/pose-v1/mixed_validation_gate.py", "tools/pose-v1/run-mixed-validation.sh",
                    "tools/pose-v1/mixed_binding_snapshot_audit.py", "tools/pose-v1/mixed-fusion-baseline.json",
                    "tools/pose-v1/test_mixed_fusion_binding.py")},
        "preserved_files": old["preserved_files"], "stage": "prepared_not_executed",
        "reference_policy": "ONNX_direct_to_board; Icraft_CPU_Matmul_not_blocking",
        "numerical_acceptance": "pending_measured_tolerance_discussion"})
    checksum(a.output)
    print("Mixed validation package prepared; no compiler/device operations executed:", a.output)


def build_review(a):
    verify(a.package)
    m, b = load(a.package / "manifest.json"), load(a.build / "build-result.json")
    need(b["stage"] == "compiled_not_executed" and b["container"] == "FPAI" and not b["device_accessed"], "Wrong build scope")
    for rel, identity in m["sources"].items():
        need(sha(ROOT / rel) == identity, "Prepared source changed: " + rel)
    need(b["package_manifest_sha256"] == sha(a.package / "manifest.json"), "Build/package mismatch")
    need(b["build_script_sha256"] == sha(ROOT / "tools/pose-v1/Build-MixedValidation.ps1"), "Build script differs")
    for rel, item in m["build_files"].items():
        need(sha(ROOT / rel) == sha(a.build / "source" / item["destination"]) == b["source_sha256"][rel] == item["sha256"], "Source differs")
    audit = load(a.build / "sdk-audit.json")
    sdk(audit, m)
    for rel, identity in m["sdk_headers_normalized_sha256"].items():
        raw = (a.build / "sdk-snapshot" / rel).read_bytes()
        need(hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == identity, "Exported ARM header differs")
    for filename, identity in (("libicraft_hostbackend.so", m["host_library_sha256"]),
                               ("libicraft_zg330backend.so", m["zg_library_sha256"])):
        need(sha(a.build / "sdk-snapshot" / filename) == identity, "Exported ARM backend differs")
    binary = a.build / "pose_mixed_check.arm64"
    need(sha(binary) == b["binary_sha256"], "Binary differs")
    raw = binary.read_bytes()
    need(raw[:6] == b"\x7fELF\x02\x01" and struct.unpack_from("<H", raw, 18)[0] == 183, "Not AArch64 ELF64")
    lograw = (a.build / "build.log").read_bytes()
    log = lograw.decode("utf-16" if lograw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig")
    need("Built target pose_mixed_check" in log, "Build did not complete")
    need("9.4.0" in log and "cmake version 3.24.2" in log, "Compiler/CMake version changed")
    need("[libicraft_hostbackend.so]" in log and "[libicraft_zg330backend.so]" in log, "Direct backend dependencies differ")
    save(a.output, {"status": "mixed_build_reviewed", "binary_sha256": sha(binary),
         "package_manifest_sha256": sha(a.package / "manifest.json"), "sources_verified": len(m["build_files"]),
         "device_accessed": False, "runtime_verified": False})


def sdk(audit, m):
    need(audit["headers_normalized_sha256"] == m["sdk_headers_normalized_sha256"], "SDK headers differ")
    need(audit["host_sha256"] == m["host_library_sha256"] and audit["zg_sha256"] == m["zg_library_sha256"], "Backend library identity differs")
    need(all(audit["versions"][p] == "3.39.0" for p in ("icraft:arm64", "customop:arm64")), "SDK version differs")


def lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def registry(path):
    rows = lines(path)
    need(len(rows) == 12, "Incomplete registration evidence")
    for row, (phase, opid) in zip(rows, [(p, i) for p in ("before", "after") for i in HOST_IDS]):
        present = phase == "after" or opid == 442
        need(row["phase"] == phase and row["op_id"] == opid and
             all(row[k] == present for k in ("init", "forward", "supported")), "Registration differs")


def fusion_binding_review(output, baseline):
    """Independent original-to-effective proof, using only returned public snapshots."""
    audit = runpy.run_path(str(ROOT / "tools/pose-v1/mixed_binding_snapshot_audit.py"))
    snapshots = {phase: {part: lines(output / f"{phase}.{part}.jsonl") for part in audit["PARTS"]}
                 for phase in ("after-create", "after-apply")}
    mapping, groups = audit["audit"](snapshots)
    expected = {}
    for group in baseline["groups"]:
        need(len(set(group["members"])) == len(group["members"]), "Duplicate pinned group member")
        for op_id in group["members"]:
            need(op_id not in expected, "Duplicate pinned original coverage")
            expected[op_id] = group["effective_op_id"]
    need(mapping == expected and len(mapping) == baseline["original_hardop_count"] == 1173,
         "Fusion membership differs from reviewed baseline")
    pinned = [{"effective_op_id": g["effective_op_id"], "original_hardop_count": len(g["members"]),
               "sync_index": g["sync_index"], "layer_count": g["layer_count"]} for g in baseline["groups"]]
    need(groups == pinned, "Effective group sync baseline changed")
    original = [v for v in snapshots["after-create"]["views"] if v["owner"] == "original_graph"]
    bound = lines(output / "bindings.jsonl")
    need(len(bound) == len(original) == baseline["original_op_count"] == 1181, "Final original trace incomplete")
    need(baseline["host_direct_ids"] == sorted(audit["HOST_IDS"]), "Pinned Host identity differs")
    for row, op in zip(bound, original):
        hard = op["is_hardop"]
        need(type(row.get("is_hardop")) is bool, "HardOp trace flag must be boolean")
        target = mapping[op["op_id"]] if hard else op["op_id"]
        need(row == {"op_id": op["op_id"], "operator": op["operator"], "is_hardop": hard,
                     "effective_op_id": target, "binding_kind": "zg_merge_from" if hard else "host_direct",
                     "backend": audit["ZG"] if hard else audit["HOST"]}, "Original-to-effective trace differs")
    hard_rows = [row for row in bound if row["is_hardop"]]
    need(len(hard_rows) == 1173 and all(row["operator"] == "icraft::xir::HardOpNode" for row in hard_rows),
         "HardOpNode runtime identity differs")
    need(load(output / "binding-summary.json") == {"original_ops": 1181, "original_hardops": 1173,
         "direct_host_ops": 8, "effective_zg_groups": 7, "coverage_complete": True}, "Binding summary differs")
    return groups


def stage_review(a):
    import numpy as np
    verify(a.package)
    count = verify(a.results)
    m, b = load(a.package / "manifest.json"), load(a.build / "build-result.json")
    need(b["package_manifest_sha256"] == sha(a.package / "manifest.json"), "Build/package differs")
    need((a.results / "exit.txt").read_text().strip() == "0", "Stage failed/timed out; preserve logs")
    need((a.results / "run.stderr.log").stat().st_size == 0, "SDK/compiler stderr needs discussion")
    need(sha(a.results / "pose_mixed_check") == b["binary_sha256"], "Returned program differs")
    sdk(load(a.results / "sdk-audit.json"), m)
    identity = load(a.results / "run-identity.json")
    need(identity["package_manifest_sha256"] == sha(a.package / "manifest.json") and
         identity["binary_sha256"] == b["binary_sha256"] and identity["stage"] == a.stage, "Stage/package differs")
    previous = {"host-check": "build", "offline-check": "host-check", "memory-check": "offline-check",
                "apply-check": "memory-check", "mixed-one": "apply-check", "mixed-three": "mixed-one"}[a.stage]
    approved = load(a.results / "previous-acceptance.json")
    need(approved["package_manifest_sha256"] == b["package_manifest_sha256"] and
         approved["binary_sha256"] == b["binary_sha256"], "Prior approval identity differs")
    need(approved["status"] == ("mixed_build_reviewed" if previous == "build" else "stage_engineering_review_passed") and
         (previous == "build" or approved["stage"] == previous), "Prior stage differs")
    before = Counter((a.results / "dmesg.before.log").read_text(errors="replace").splitlines())
    after = Counter((a.results / "dmesg.after.log").read_text(errors="replace").splitlines())
    new = list((after - before).elements())
    need(not any(re.search(r"out of memory|oom-kill|killed process|bus error|external abort|kernel panic|segfault|SError|DMA.*(?:error|fault)",
                          s, re.I) for s in new), "New kernel error; review and discuss before proceeding")
    ldd = (a.results / "ldd.txt").read_text()
    need("not found" not in ldd, "Unresolved board library")
    output = a.results / "results"
    config = load(output / "run-config.json")
    mode = "mixed" if a.stage.startswith("mixed-") else a.stage
    need(config["mode"] == mode, "Wrong program mode")
    hardware = a.stage not in ("host-check", "offline-check")
    need(config["device_init_allowed"] == hardware, "Wrong hardware scope")
    need(not (output / "failure.json").exists(), "Failure record present")
    if hardware:
        versions = load(output / "device-version.json")["versions"]
        need(versions["device"] == "25122301" and versions["icore"] == "FMSHZGV3TECH-AID - 24160628", "Runtime FPGA changed")
    if a.stage == "host-check":
        fixture = load(a.package / "cpu-fixture-manifest.json")
        record = lines(output / "host/cases.jsonl")
        need(len(record) == len(fixture["cases"]) == 107, "Host regression incomplete")
        registry(output / "host/registry.jsonl")
        for expect, got in zip(fixture["cases"], record):
            need(all(got[k] == expect[k] for k in ("case_id", "op_id", "expected")) and got["passed"], "Host case differs")
            need(got["rejection"] == ("" if expect["expected"] == "PASS" else expect["expected"]), "Host rejection differs")
            for i in range(expect["outputs"]):
                need((output / "host" / expect["case_id"] / f"output{i}.f32").read_bytes() ==
                     (a.package / "fixtures" / expect["case_id"] / f"expected{i}.f32").read_bytes(), "Host bridge numeric mismatch")
        need(load(output / "host/summary.json")["status"] == "mixed_host_bridge_tests_passed", "Wrong host summary")
    elif a.stage == "memory-check":
        meta = load(output / "memory-region.json")
        need(all(meta[k]["pointer"] in ("ADDR", "BOTH") and meta[k]["bytes"] == 16384 for k in ("left", "right")), "Device memory metadata differs")
        for n in range(3):
            x = np.arange(4096, dtype=np.float32) - np.float32(2048) + np.float32(n / 8)
            y = np.float32(2047) - np.arange(4096, dtype=np.float32) - np.float32(n / 16)
            x[0], y[0] = np.float32(-0.), np.float32(0.)
            for side, ref in (("left", x), ("right", y)):
                need((output / f"memory-pass{n}.{side}.f32").read_bytes() == ref.astype("<f4").tobytes(), "SDK memory roundtrip differs")
    else:
        registry(output / "registry.jsonl")
        for item in m["cases"]:
            name = item["case"]
            need((output / (name + ".input.f32")).read_bytes() == (a.package / "reference" / (name + ".input.f32")).read_bytes(), "PS preprocessing differs")
        params = lines(output / "host-parameters.jsonl")
        need(len(params) == 4 and all(p["loaded_from_real_RAW"] for p in params), "Real CPU parameters incomplete")
        need({p["op_id"] for p in params} == {188, 437, 582, 649}, "Wrong real parameter operators")
        for p in params:
            expected_size = 4 if p["op_id"] in (188, 437) else 50400
            v = np.frombuffer((output / f"op{p['op_id']}.param{p['input']}.f32").read_bytes(), dtype="<f4")
            need(p["input"] == 1 and p["bytes"] == expected_size == v.nbytes and np.isfinite(v).all(), "Real parameter bytes differ")
            if expected_size == 4:
                need(v[0] == 100, "Real RAW K differs")
            else:
                limits = np.array([100, 14, 3], dtype="f4")
                triples = v.reshape(-1, 3)
                need(np.array_equal(triples, np.trunc(triples)) and (triples >= -limits).all() and (triples < limits).all(), "Real RAW indices differ")
        if a.stage != "offline-check":
            for rel in ("tools/pose-v1/mixed_binding_snapshot_audit.py", "tools/pose-v1/mixed-fusion-baseline.json"):
                need(sha(ROOT / rel) == m["sources"][rel], "Fusion reviewer source identity differs")
            baseline = load(a.package / "mixed-fusion-baseline.json")
            need(baseline["graph_sha256"] == m["graph_sha256"] and baseline["raw_sha256"] == m["raw_sha256"] and
                 baseline["host_library_sha256"] == m["host_library_sha256"] and
                 baseline["zg_library_sha256"] == m["zg_library_sha256"], "Fusion baseline identities differ")
            fusion_binding_review(output, baseline)
        if a.stage.startswith("mixed-"):
            expected = CASES[:1] if a.stage == "mixed-one" else CASES
            rows = lines(output / "results.jsonl")
            need(tuple(p["case"] for p in rows) == expected, "Wrong forward cases")
            need(config["cases"] == ("one" if a.stage == "mixed-one" else "three"), "Wrong mixed case selector")
            execution = lines(output / "operator-execution.jsonl")
            moves = lines(output / "bridge.jsonl")
            for item in rows:
                name, frame = item["case"], item["frame_id"]
                need(frame == 6 + CASES.index(name) and item["source_time_ns"] == 0 and item["observed_zg_callbacks"] > 0, "Frame/backend differs")
                observed = {r["op_id"] for r in execution if r["frame_id"] == frame and r["invocation"] == item["invocation"] and "HostBackend" in r["backend"]}
                need(set(HOST_IDS).issubset(observed), "Missing actual CPU execution")
                copied = {r["op_id"] for r in moves if r["frame_id"] == frame and r["action"] == "input_to_host"}
                need({188, 192, 437, 582, 649}.issubset(copied), "Missing bridge execution")
                for suffix, size in (("scores", 100), ("poses", 4200)):
                    v = np.frombuffer((output / (name + "." + suffix + ".f32")).read_bytes(), dtype="<f4")
                    need(v.size == size and np.isfinite(v).all(), "Invalid model output")
            if a.stage == "mixed-three":
                need(a.previous_one is not None, "Compare with previously reviewed first-case output")
                verify(a.previous_one)
                need(sha(a.previous_one / "pose_mixed_check") == b["binary_sha256"], "Previous-one binary differs")
                previous = a.previous_one / "results"
                for suffix in ("input", "scores", "poses"):
                    need((previous / (CASES[0] + "." + suffix + ".f32")).read_bytes() ==
                         (output / (CASES[0] + "." + suffix + ".f32")).read_bytes(), "Repeated first mixed result differs")
                signatures = {(sha(output / (n + ".scores.f32")), sha(output / (n + ".poses.f32"))) for n in CASES}
                need(len(signatures) > 1, "No distinct-input response")
                repeat = load(output / "repeat-first.json")
                need(repeat["case"] == CASES[0] and repeat["frame_id"] == 6 and repeat["repeated_first_within_session"] and
                     repeat["observed_zg_callbacks"] > 0 and repeat["invocation"] == 3, "Same-Session first-case repeat incomplete")
                repeated_host = {r["op_id"] for r in execution if r["invocation"] == 3 and r["frame_id"] == 6 and "HostBackend" in r["backend"]}
                need(set(HOST_IDS).issubset(repeated_host), "Repeat lacks six actual Host callbacks")
                for suffix in ("scores", "poses"):
                    need((output / (CASES[0] + ".repeat." + suffix + ".f32")).read_bytes() ==
                         (output / (CASES[0] + "." + suffix + ".f32")).read_bytes(), "Same-Session repeated first result differs")
                need(load(output / "summary.json")["forward_calls"] == 4, "Three cases plus first-case repeat required")
    stage_names = {p["stage"] for p in lines(output / "stages.jsonl")}
    if a.stage in ("apply-check", "mixed-one", "mixed-three"):
        need({"original_bindings_validated_before_apply", "original_to_effective_bindings_validated"} <= stage_names,
             "Missing formal fusion validation stages")
    if a.stage == "apply-check":
        need("forward_started" not in stage_names and (output / "bridge.jsonl").stat().st_size == 0 and
             not (output / "results.jsonl").exists() and not (output / "operator-execution.jsonl").exists(),
             "Apply-only scope includes unexpected forward artifacts")
    expected_end = {"host-check": "host_bridge_regression_completed", "offline-check": "offline_validation_completed",
                    "memory-check": "sdk_memory_roundtrip_completed_not_NPU_coherence_proof",
                    "apply-check": "apply_and_bindings_completed_no_forward", "mixed-one": "mixed_completed_not_numerically_accepted",
                    "mixed-three": "mixed_completed_not_numerically_accepted"}[a.stage]
    need(expected_end in stage_names and "failed_stop_no_retry" not in stage_names, "Stage incomplete")
    save(a.output, {"status": "stage_engineering_review_passed", "stage": a.stage,
         "binary_sha256": b["binary_sha256"], "package_manifest_sha256": sha(a.package / "manifest.json"),
         "returned_files_verified": count, "numerical_accepted": False, "performance_accepted": False})
    print("Stage reviewed, numerical/performance acceptance remains separate:", a.stage)


def compare(a):
    import numpy as np
    verify(a.reference)
    verify(a.board)
    ref = a.reference
    board = a.board / "results"
    accepted = load(a.acceptance)
    need(accepted["status"] == "stage_engineering_review_passed" and accepted["stage"] == "mixed-three" and
         accepted["binary_sha256"] == sha(a.board / "pose_mixed_check") and
         accepted["package_manifest_sha256"] == load(a.board / "run-identity.json")["package_manifest_sha256"], "Review three-case engineering evidence first")
    environment = load(ref / "environment.json")
    need(environment["model_sha256"] == "7b04090e374e31e016d5703bbcf1d0a561d0b98f268fde984b0bf0461598bd21" and
         environment["providers"] == ["CPUExecutionProvider"] and
         load(ref / "summary.json")["repeated_first_bitwise_equal"], "ONNX reference identity differs")
    reference_rows, board_rows = lines(ref / "results.jsonl"), lines(board / "results.jsonl")
    need(tuple(r["case"] for r in reference_rows) == CASES and tuple(r["case"] for r in board_rows) == CASES, "Three-case comparison required")
    def stats(delta):
        v = np.abs(delta.astype(np.float64))
        return {"max_abs": float(v.max()), "mean_abs": float(v.mean()), "rms": float(np.sqrt(np.mean(v*v))),
                "p95_abs": float(np.percentile(v, 95))}
    report = {"numerical_acceptance": "pending_measured_tolerance_discussion", "coordinate_units": "model_raw_not_physical_calibration",
              "comparison": "same output slot, not assumed candidate/person identity", "cases": [],
              "model_sha256": environment["model_sha256"], "board_binary_sha256": accepted["binary_sha256"],
              "engineering_acceptance_sha256": sha(a.acceptance)}
    for r, b in zip(reference_rows, board_rows):
        name = r["case"]
        need((r["frame_id"], r["source_time_ns"]) == (b["frame_id"], b["source_time_ns"]), "Frame differs")
        need((ref / (name + ".input.f32")).read_bytes() == (board / (name + ".input.f32")).read_bytes(), "Reference/PS input differs")
        arrays = {}
        for suffix, shape in (("scores", (100,)), ("poses", (100, 14, 3))):
            left = np.frombuffer((ref / (name + "." + suffix + ".f32")).read_bytes(), dtype="<f4").reshape(shape)
            right = np.frombuffer((board / (name + "." + suffix + ".f32")).read_bytes(), dtype="<f4").reshape(shape)
            need(np.isfinite(left).all() and np.isfinite(right).all(), "Non-finite output")
            arrays[suffix] = (left, right)
        i = int(np.argmax(arrays["scores"][0])); j = int(np.argmax(arrays["scores"][1]))
        need(i == r["top_index"] and j == b["top_index"], "Top index metadata differs")
        entry = {"case": name, "frame_id": r["frame_id"], "reference_top_index": i, "board_top_index": j, "top_slot_changed": i != j}
        for suffix, (left, right) in arrays.items():
            entry[suffix] = dict(stats(right.astype("f8")-left.astype("f8")), bitwise_equal=left.tobytes() == right.tobytes())
        left, right = arrays["poses"]
        entry["same_slot_joint_l2"] = stats(np.linalg.norm(right.astype("f8")-left.astype("f8"), axis=2))
        entry["selected_best_coordinates"] = stats(right[j].astype("f8")-left[i].astype("f8"))
        entry["selected_best_joint_l2"] = stats(np.linalg.norm(right[j].astype("f8")-left[i].astype("f8"), axis=1))
        report["cases"].append(entry)
    save(a.output, report)
    print("ONNX/board difference statistics saved; no tolerance/MPJPE acceptance claimed.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("prepare")
    for k in ("source", "cpu", "output"):
        s.add_argument("--" + k, type=Path, required=True)
    s = sub.add_parser("review-build")
    for k in ("package", "build", "output"):
        s.add_argument("--" + k, type=Path, required=True)
    s = sub.add_parser("review-stage")
    s.add_argument("--stage", choices=("host-check", "offline-check", "memory-check", "apply-check", "mixed-one", "mixed-three"), required=True)
    for k in ("package", "build", "results", "output"):
        s.add_argument("--" + k, type=Path, required=True)
    s.add_argument("--previous-one", type=Path)
    s = sub.add_parser("compare")
    for k in ("reference", "board", "acceptance", "output"):
        s.add_argument("--" + k, type=Path, required=True)
    a = p.parse_args()
    {"prepare": prepare, "review-build": build_review, "review-stage": stage_review, "compare": compare}[a.command](a)

"""Verify the approved runtime's PE imports, DLL locations and help commands.

No model, CUDA kernel, device download, or inference is executed. Requires
Windows and Python 3.8+ with only its standard library.
"""

import base64
import ctypes
import hashlib
import json
import os
import struct
import subprocess
import sys
import winreg
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
ROOT = PROJECT / ".local" / "icraft-runtime" / "cuda-11.8.0"
MANIFEST = json.loads((ROOT / "runtime-manifest.json").read_text(encoding="utf-8"))
ICRAFT_BIN = Path(MANIFEST["icraft_bin"])
DLLS = {dll["name"].lower(): dll for comp in MANIFEST["components"] for dll in comp["dlls"]}
BINS = [Path(p) for comp in MANIFEST["components"] for p in comp["bin_dirs"]]
LOGS = ROOT / "logs"


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class PE:
    def __init__(self, path):
        self.path = Path(path)
        self.file = self.path.open("rb")
        pe = self.u32(0x3C)
        if self.read(pe, 4) != b"PE\0\0":
            raise RuntimeError("Not PE: " + str(path))
        self.machine, nsections = struct.unpack("<HH", self.read(pe + 4, 4))
        optional_size = struct.unpack("<H", self.read(pe + 20, 2))[0]
        optional = pe + 24
        magic = struct.unpack("<H", self.read(optional, 2))[0]
        self.width = 8 if magic == 0x20B else 4
        self.image_base = struct.unpack("<Q" if self.width == 8 else "<I", self.read(optional + (24 if self.width == 8 else 28), self.width))[0]
        self.directories = optional + (112 if self.width == 8 else 96)
        self.sections = []
        for index in range(nsections):
            section = self.read(optional + optional_size + index * 40, 40)
            vsize, va, rsize, raw = struct.unpack_from("<IIII", section, 8)
            self.sections.append((va, max(vsize, rsize), raw))

    def close(self):
        self.file.close()

    def read(self, offset, length):
        self.file.seek(offset)
        return self.file.read(length)

    def u32(self, offset):
        return struct.unpack("<I", self.read(offset, 4))[0]

    def offset(self, rva):
        for va, size, raw in self.sections:
            if va <= rva < va + size:
                return raw + rva - va
        return rva

    def string(self, rva):
        return self.read(self.offset(rva), 2048).split(b"\0", 1)[0].decode("ascii")

    def thunks(self, rva):
        result = []
        high = 1 << (self.width * 8 - 1)
        offset = self.offset(rva)
        for index in range(50000):
            value = struct.unpack("<Q" if self.width == 8 else "<I", self.read(offset + index * self.width, self.width))[0]
            if not value:
                return result
            result.append("#" + str(value & 0xFFFF) if value & high else self.string(value + 2))
        raise RuntimeError("Unterminated import table")

    def imports(self):
        result = {}
        rva, _ = struct.unpack("<II", self.read(self.directories + 8, 8))
        if rva:
            offset = self.offset(rva)
            for index in range(1000):
                record = struct.unpack("<IIIII", self.read(offset + index * 20, 20))
                if not any(record):
                    break
                result[self.string(record[3]).lower()] = self.thunks(record[0] or record[4])
        # Include delay imports so a new delayed dependency is not overlooked.
        rva, _ = struct.unpack("<II", self.read(self.directories + 13 * 8, 8))
        if rva:
            offset = self.offset(rva)
            for index in range(1000):
                record = struct.unpack("<IIIIIIII", self.read(offset + index * 32, 32))
                if not any(record):
                    break
                name_rva, thunk_rva = record[1], record[4]
                if not record[0] & 1:
                    name_rva -= self.image_base
                    thunk_rva -= self.image_base
                result[self.string(name_rva).lower()] = self.thunks(thunk_rva)
        return result

    def exports(self):
        rva, _ = struct.unpack("<II", self.read(self.directories, 8))
        if not rva:
            return set()
        data = struct.unpack("<IIHHIIIIIII", self.read(self.offset(rva), 40))
        ordinal_base, nfunctions, nnames, functions_rva, names_rva = data[5:10]
        result = set()
        for index in range(nfunctions):
            if self.u32(self.offset(functions_rva) + index * 4):
                result.add("#" + str(ordinal_base + index))
        for index in range(nnames):
            result.add(self.string(self.u32(self.offset(names_rva) + index * 4)))
        return result


def pe_info(path, kind):
    pe = PE(path)
    try:
        if pe.machine != 0x8664:
            raise RuntimeError("Non-x64 library: " + str(path))
        return pe.imports() if kind == "imports" else pe.exports()
    finally:
        pe.close()


def load_probe():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LoadLibraryW.argtypes = [ctypes.c_wchar_p]
    kernel.LoadLibraryW.restype = ctypes.c_void_p
    kernel.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    kernel.GetModuleHandleW.restype = ctypes.c_void_p
    kernel.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
    kernel.GetModuleFileNameW.restype = ctypes.c_uint32
    result = {"loads": [], "actual_loaded_dlls": []}
    for name in ["cusolver64_11.dll", "torch_cuda_ic.dll", "nvfuser_codegen_ic.dll"]:
        ctypes.set_last_error(0)
        handle = kernel.LoadLibraryW(str(ICRAFT_BIN / name))
        error = ctypes.get_last_error()
        result["loads"].append({"name": name, "loaded": bool(handle), "error": error if not handle else 0})
        if not handle:
            print(json.dumps(result, ensure_ascii=False))
            return 2
    for name, record in DLLS.items():
        handle = kernel.GetModuleHandleW(name)
        buffer = ctypes.create_unicode_buffer(32768)
        if not handle or not kernel.GetModuleFileNameW(handle, buffer, len(buffer)):
            raise RuntimeError("Cannot locate loaded module: " + name)
        actual = Path(buffer.value).resolve()
        expected = Path(record["path"]).resolve()
        result["actual_loaded_dlls"].append({"name": name, "actual_path": str(actual), "matches_manifest": actual == expected})
        if actual != expected:
            raise RuntimeError("Unexpected library source: " + str(actual))
    print(json.dumps(result, ensure_ascii=False))
    return 0


def permanent_path_hashes():
    result = {}
    for label, hive, key in [
        ("user", winreg.HKEY_CURRENT_USER, r"Environment"),
        ("machine", winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
    ]:
        with winreg.OpenKey(hive, key) as handle:
            try:
                value = winreg.QueryValueEx(handle, "Path")[0]
            except FileNotFoundError:
                value = ""
        result[label] = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return result


def run_command(label, argv, env):
    completed = subprocess.run(argv, cwd=str(PROJECT), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    stdout = LOGS / ("verify-" + label + ".stdout.log")
    stderr = LOGS / ("verify-" + label + ".stderr.log")
    stdout.write_bytes(completed.stdout)
    stderr.write_bytes(completed.stderr)
    return {
        "label": label, "exit_code": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stdout_bytes": len(completed.stdout), "stderr_bytes": len(completed.stderr),
        "nvfuser_warning": b"Loading nvfuser library failed" in completed.stderr,
        "stdout_log": str(stdout), "stderr_log": str(stderr),
    }, completed.stdout


def main():
    LOGS.mkdir(exist_ok=True)
    original_files = [ICRAFT_BIN / name for name in ["icraft.exe", "icraft-run.exe", "nvfuser_codegen_ic.dll", "torch_cuda_ic.dll", "cusolver64_11.dll", "cusparse64_11.dll", "cudnn64_8.dll"]]
    installation_before = {str(p): sha256_file(p) for p in original_files}
    registry_before = permanent_path_hashes()
    system = Path(os.environ["SystemRoot"])
    system_dirs = [system / "System32", system, system / "System32" / "Wbem"]
    search = [ICRAFT_BIN] + BINS + system_dirs
    clean_env = os.environ.copy()
    clean_env["PATH"] = ";".join(str(p) for p in search)
    clean_env["PYTHONIOENCODING"] = "utf-8"
    baseline_env = clean_env.copy()
    baseline_env["PATH"] = ";".join(str(p) for p in [ICRAFT_BIN] + system_dirs)

    exports = {name: pe_info(record["path"], "exports") for name, record in DLLS.items()}
    queue = [ICRAFT_BIN / "nvfuser_codegen_ic.dll"]
    visited, symbol_checks, unresolved = set(), [], []
    while queue:
        path = queue.pop(0)
        if str(path).lower() in visited:
            continue
        visited.add(str(path).lower())
        imports = pe_info(path, "imports")
        for name, symbols in imports.items():
            if name in exports:
                missing = sorted(set(symbols) - exports[name])
                symbol_checks.append({"importer": str(path), "dependency": name, "checked_symbols": len(symbols), "missing_symbols": missing})
                if missing:
                    raise RuntimeError("Missing imported symbols: " + name + ": " + repr(missing))
            candidates = [directory / name for directory in search if (directory / name).is_file()]
            if not candidates:
                if not name.startswith(("api-ms-", "ext-ms-")):
                    unresolved.append({"importer": str(path), "dependency": name})
                continue
            candidate = candidates[0]
            if candidate.parent == ICRAFT_BIN or candidate.parent in BINS:
                queue.append(candidate)
    if unresolved:
        raise RuntimeError("New unresolved dependencies; discuss before proceeding: " + json.dumps(unresolved))
    print("Static checks: {} libraries, {} import-symbol groups; no unresolved dependency or missing symbol".format(len(visited), len(symbol_checks)), flush=True)

    records = []
    probe, probe_stdout = run_command("dll-probe", [sys.executable, str(Path(__file__).resolve()), "--probe"], clean_env)
    records.append(probe)
    if probe["exit_code"] != 0 or probe["stderr_bytes"]:
        raise RuntimeError("DLL probe failed; inspect verification logs before changing dependencies.")
    probe_data = json.loads(probe_stdout.decode("utf-8"))
    print("DLL loading: three Icraft libraries loaded; all three NVIDIA DLL paths match the manifest", flush=True)

    baseline, baseline_stdout = run_command("baseline-help", [str(ICRAFT_BIN / "icraft.exe"), "run", "--help"], baseline_env)
    records.append(baseline)
    if baseline["exit_code"] != 0 or not baseline["nvfuser_warning"]:
        raise RuntimeError("The original environment no longer matches the warning baseline; inspect before accepting.")
    for label, args in [("isolated-version", ["--version"]), ("isolated-help", ["run", "--help"])]:
        result, stdout = run_command(label, [str(ICRAFT_BIN / "icraft.exe")] + args, clean_env)
        records.append(result)
        if result["exit_code"] or result["stderr_bytes"]:
            raise RuntimeError("Independent CLI verification failed: " + label)
        if label.endswith("help") and stdout != baseline_stdout:
            raise RuntimeError("Help output changed")
        if label.endswith("version") and b"3.39.0" not in stdout:
            raise RuntimeError("Incorrect Icraft version")

    powershell = system / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    parent_check = LOGS / "verify-parent-path.json"
    for label, args in [("launcher-version", "@('--version')"), ("launcher-help", "@('run','--help')")]:
        code = "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $beforePath=$env:PATH; & '" + str(PROJECT / "tools" / "Invoke-Icraft.ps1") + "' -WorkingDirectory '" + str(PROJECT) + "' -IcraftArgs " + args + "; $toolCode=$LASTEXITCODE; [IO.File]::WriteAllText('" + str(parent_check) + "', ('{\"unchanged\":' + (($beforePath -ceq $env:PATH).ToString().ToLowerInvariant()) + '}')); exit $toolCode"
        encoded = base64.b64encode(code.encode("utf-16-le")).decode("ascii")
        result, stdout = run_command(label, [str(powershell), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded], clean_env)
        records.append(result)
        if result["exit_code"] or result["stderr_bytes"]:
            raise RuntimeError("PowerShell launcher failed: " + label)
        if label.endswith("help") and stdout != baseline_stdout:
            raise RuntimeError("Launcher help differs from the direct CLI")
        if label.endswith("version") and b"3.39.0" not in stdout:
            raise RuntimeError("Launcher used an incorrect version")
        if not json.loads(parent_check.read_text(encoding="utf-8"))["unchanged"]:
            raise RuntimeError("Launcher changed its parent PATH")

    installation_after = {str(p): sha256_file(p) for p in original_files}
    registry_after = permanent_path_hashes()
    if installation_before != installation_after or registry_before != registry_after:
        raise RuntimeError("Original Icraft files or permanent PATH changed")
    report = {
        "status": "passed_help_and_loading_only", "date": "2026-10-01",
        "icraft_version": "3.39.0", "no_conda_in_test_path": True,
        "clean_test_path": clean_env["PATH"], "static_checked_libraries": len(visited),
        "import_symbol_checks": symbol_checks, "load_probe": probe_data,
        "commands": records, "original_installation_hashes": installation_before,
        "original_installation_unchanged": True, "permanent_path_unchanged": True,
        "permanent_path_hashes": registry_before, "launcher_parent_path_unchanged": True,
        "limitations": ["No model compilation, quantization, CPU/GPU inference or ZG330 board execution was tested"],
    }
    report_path = ROOT / "verification-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MANIFEST["status"] = "verified_help_and_loading_only"
    MANIFEST["verification_report"] = str(report_path)
    (ROOT / "runtime-manifest.json").write_text(json.dumps(MANIFEST, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: clean isolated CLI and Windows PowerShell launcher; original installation and permanent PATH unchanged", flush=True)
    print("Verification report: " + str(report_path), flush=True)


if __name__ == "__main__":
    if "--probe" in sys.argv:
        sys.exit(load_probe())
    main()

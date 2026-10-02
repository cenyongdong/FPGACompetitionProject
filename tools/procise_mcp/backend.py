"""Restricted adapter for the approved Lite LED prototype, not a general shell."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "FPGA/lite_led_chaser"
RUNS = PROJECT / "runs"
RUNTIME = ROOT / ".local/procise-mcp"
PROCISE = Path("C:/FudanMicro/Procise")
POWERSHELL = Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
BASELINE_SIM = RUNS / "sim_20261001_115631_342b3c"
SCRIPTS = ["scripts/Build.ps1", "scripts/build.tcl", "scripts/ReviewBuild.py"]
INPUTS = ["rtl/lite_led_chaser.v", "constraints/lite_led_chaser.fdc", *SCRIPTS]
PINS = {"clk_100m": ["AC14", "LVCMOS33"], "led[0]": ["J1", "LVCMOS15"],
        "led[1]": ["M6", "LVCMOS15"], "led[2]": ["H7", "LVCMOS15"],
        "led[3]": ["J8", "LVCMOS15"]}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scoped_directory(value: str, prefix: str) -> Path:
    # resolve also rejects junction/symlink escapes from the approved runs root.
    path = Path(value).resolve(strict=True)
    root = RUNS.resolve(strict=True)
    require(path.is_dir() and path.parent == root and path.name.startswith(prefix),
            "Only direct, existing approved LED run directories are allowed")
    return path


def scoped_file(path: Path, directory: Path) -> Path:
    resolved = path.resolve(strict=True)
    require(resolved.is_relative_to(directory.resolve(strict=True)) and resolved.is_file(),
            "Artifact escapes the approved run directory")
    return resolved


def read_text(path: Path) -> str:
    # PowerShell launcher output is often UTF-16; Procise native logs are byte text.
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    return data.decode("utf-8-sig", errors="replace")


def fingerprints() -> dict:
    return {name: sha(PROJECT / name) for name in INPUTS}


def check_scripts() -> None:
    expected = json.loads((Path(__file__).parent / "approved-scripts.json").read_text())
    for name in SCRIPTS:
        require(sha(PROJECT / name) == expected[name],
                f"Approved execution script changed; review and approval required: {name}")


def native_environment() -> dict:
    env = os.environ.copy()
    env.update(APP_DIR=str(PROCISE), TCL_LIBRARY=str(PROCISE / "tcl8.4"),
               ICTIME_HOME=str(PROCISE), FMSH_DB=str(PROCISE / "db"))
    env["PATH"] = str(PROCISE / "dll") + os.pathsep + env.get("PATH", "")
    return env


def get_environment() -> dict:
    require((PROCISE / "bin/procise.exe").is_file(), "Procise executable missing")
    check_scripts()
    directory = RUNTIME / "probes" / uuid.uuid4().hex
    directory.mkdir(parents=True)
    (directory / "probe.tcl").write_text('puts "MCP_ENV_PROBE_OK"\nexit\n', encoding="ascii")
    with (directory / "stdout.log").open("wb") as out, (directory / "stderr.log").open("wb") as err:
        process = subprocess.Popen([str(PROCISE / "bin/procise.exe"), "probe.tcl"],
            cwd=directory, env=native_environment(), stdin=subprocess.DEVNULL,
            stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            code = process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise RuntimeError(f"Environment probe timed out; see {directory}") from None
    log = read_text(directory / "stdout.log")
    require(code == 0 and "MCP_ENV_PROBE_OK" in log, "Native environment probe failed")
    require((directory / "stderr.log").stat().st_size == 0, "Native probe stderr is non-empty")
    # Return the actual banner rather than deriving version from an installer name.
    banner = log.split("MCP_ENV_PROBE_OK", 1)[0].strip()
    return {"native_probe": "passed", "banner": banner, "procise_root": str(PROCISE),
            "python": sys.executable, "python_version": sys.version.split()[0],
            "mcp_sdk": importlib.metadata.version("mcp"), "logs": str(directory),
            "project": str(PROJECT), "scope": "LED prototype only; no JTAG or arbitrary Tcl",
            "codex_connection": "not assessed by this environment probe"}


def validate_timing(route: dict) -> dict:
    summary = route["Design Summary"]["item_data"]
    clocks = route["Clock Summary"]["item_data"]
    require(isinstance(summary["Timing constraints met"], bool), "Invalid native timing flag")
    require(len(clocks) == 1 and clocks[0]["Period(ns)"] == 10.0, "Unexpected clock")
    for kind, slack, total in [("Setup", "Worst Negative Slack (WNS)", "Total Negative Slack (TNS)"),
                              ("Hold", "Worst Hold Slack (WHS)", "Total Hold Slack (THS)")]:
        entry = summary[kind]
        for name in ["Number of Failing Endpoints", "Total Number of Endpoints"]:
            require(type(entry[name]) is int and entry[name] >= 0, f"Invalid {kind}/{name}")
        require(entry["Total Number of Endpoints"] > 0, "Missing timed endpoints")
        for name in [slack, total]:
            require(isinstance(entry[name], str) and entry[name].endswith(" ns"), "Invalid slack")
            require(math.isfinite(float(entry[name][:-3])), "Non-finite slack")
    checks = {item["Timing Check"]: item["Count"] for item in route["Check Timing"]["item_data"]}
    require(checks and "no_output_delay" in checks, "Timing checks missing")
    require(all(type(value) is int and value >= 0 for value in checks.values()), "Invalid check count")
    outputs = route["Check Timing"]["no_output_delay"]["item_data"]
    expected_checks = json.loads((Path(__file__).parent / "expected-timing-checks.json").read_text())
    require(set(checks) == set(expected_checks), "Native timing check schema changed or incomplete")
    only_led_outputs = (checks == expected_checks and
        {item["Name"] for item in outputs} == {f"led[{i}]" for i in range(4)})
    internal_pass = summary["Timing constraints met"] and all(
        summary[kind]["Number of Failing Endpoints"] == 0 for kind in ["Setup", "Hold"])
    return {"native_timing": summary, "clock": clocks, "timing_checks": checks,
            "internal_timing_pass": internal_pass, "expected_led_output_exception": only_led_outputs,
            "limitation": "Four LED outputs lack external output delays; no full interface timing or board acceptance."}


def read_build_report(build_dir: str) -> dict:
    directory = scoped_directory(build_dir, "build_")
    rundir = directory / "rundir"
    route_path = scoped_file(rundir / "lite_led_chaser_route.json", directory)
    timing = validate_timing(json.loads(route_path.read_text()))
    fdc_path = scoped_file(rundir / "lite_led_chaser_placed.fdc", directory)
    fdc = read_text(fdc_path)
    pin_pass = all(f"set_property {prop} {value} [get_ports {{{port}}}]" in fdc
        for port, pair in PINS.items() for prop, value in zip(["PACKAGE_PIN", "IOSTANDARD"], pair))
    bgn_path = scoped_file(rundir / "lite_led_chaser.bgn", directory)
    bgn = read_text(bgn_path)
    startup = re.search(r"\| StartupClk\s*\| (\S+)\s*\|", bgn)
    unconstrained = re.search(r"\| UnconstrainedPins\s*\| (\S+)\s*\|", bgn)
    require(startup is not None and unconstrained is not None, "Bitgen fields missing")
    device_pass = "device JFMQL30TAI676H" in bgn
    bit = scoped_file(rundir / "lite_led_chaser.bit", directory)
    return {"build_directory": str(directory), **timing,
            "expected_device": "JFMQL30TAI676H", "device_matches": device_pass,
            "pin_constraints_match": pin_pass, "expected_pins": PINS,
            "startup_clock": startup[1].removesuffix("*"),
            "unconstrained_pins": unconstrained[1].removesuffix("*"),
            "bitgen_raw_values": {"StartupClk": startup[1], "UnconstrainedPins": unconstrained[1]},
            "bitstream": str(bit), "bitstream_sha256": sha(bit), "bitstream_size": bit.stat().st_size,
            "raw_report": str(route_path), "raw_report_sha256": sha(route_path),
            "review_scope": "Native report query only; register INIT and simulation consistency require review_led_build."}


class Job:
    def __init__(self, job_id: str, directory: Path, process: subprocess.Popen, inputs: dict):
        self.id, self.directory, self.process, self.inputs = job_id, directory, process, inputs
        self.created = time.time()
        self.build_dir: Path | None = None
        self.review: dict | None = None
        self.failure: str | None = None
        self.lock = threading.Lock()

    def snapshot(self) -> dict:
        with self.lock:
            output = read_text(self.directory / "launcher.stdout.log")
            match = re.search(r"(?m)^Build directory: (.+?)\s*$", output)
            if match:
                discovered = scoped_directory(match[1], "build_")
                require(discovered.stat().st_ctime >= self.created - 5, "Stale build directory")
                self.build_dir = discovered
            code = self.process.poll()
            state = "running" if code is None else "native_completed"
            if code is not None:
                try:
                    require(code == 0, f"Launcher exited with code {code}")
                    require(self.build_dir is not None and "BUILD_ARTIFACTS_GENERATED" in output,
                            "Missing new build directory or completion marker")
                    require(fingerprints() == self.inputs, "Project inputs changed during the job")
                    for source, staged in [("rtl/lite_led_chaser.v", "lite_led_chaser.v"),
                            ("constraints/lite_led_chaser.fdc", "lite_led_chaser.fdc"),
                            ("scripts/build.tcl", "build.tcl")]:
                        require(sha(scoped_file(self.build_dir / staged, self.build_dir)) == self.inputs[source],
                                f"Staged input mismatch: {source}")
                    log = read_text(scoped_file(self.build_dir / "procise.stdout.log", self.build_dir))
                    require("BUILD_TCL_COMPLETED" in log and not re.search(r"(?im)^\s*(ERROR|BUILD_TCL_FAIL)\b", log),
                            "Native build incomplete or failed")
                    require(scoped_file(self.build_dir / "procise.stderr.log", self.build_dir).stat().st_size == 0,
                            "Native stderr is non-empty")
                    report = read_build_report(str(self.build_dir))
                    require(all(report[field] for field in ["internal_timing_pass", "expected_led_output_exception",
                            "device_matches", "pin_constraints_match"]), "Native report failed prototype gates")
                    require(report["startup_clock"] == "JtagClk" and report["unconstrained_pins"] == "Disallow",
                            "Unexpected bitgen configuration")
                    if self.review:
                        require(report["bitstream_sha256"] == self.review["bitstream_sha256"],
                                "Reviewed bitstream changed after review")
                except Exception as exc:
                    self.failure = str(exc)
                if self.failure:
                    state = "failed"
                elif self.review:
                    state = "reviewed"
            result = {"job_id": self.id, "state": state, "exit_code": code,
                      "launcher_pid": self.process.pid, "build_directory": str(self.build_dir) if self.build_dir else None,
                      "logs_directory": str(self.directory), "failure": self.failure,
                      "input_sha256": self.inputs, "review": self.review,
                      "board_action": "none", "timeout_means_cancelled": False}
            save_json(self.directory / "status.json", result)
            return result


JOBS: dict[str, Job] = {}
JOB_LOCK = threading.Lock()


def get_job(job_id: str) -> Job:
    require(re.fullmatch(r"[0-9a-f]{32}", job_id) is not None, "Invalid job ID")
    require(job_id in JOBS, "Unknown job in this server instance; restart recovery is not supported")
    return JOBS[job_id]


def start_led_build() -> dict:
    with JOB_LOCK:
        require(not any(job.process.poll() is None for job in JOBS.values()), "A LED build is already active")
        check_scripts()
        inputs = fingerprints()
        job_id = uuid.uuid4().hex
        directory = RUNTIME / "jobs" / job_id
        directory.mkdir(parents=True)
        command = [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                   "-File", str(PROJECT / "scripts/Build.ps1")]
        with (directory / "launcher.stdout.log").open("wb") as out, (directory / "launcher.stderr.log").open("wb") as err:
            process = subprocess.Popen(command, cwd=PROJECT, stdin=subprocess.DEVNULL,
                stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
        job = Job(job_id, directory, process, inputs)
        JOBS[job_id] = job
        save_json(directory / "request.json", {"command": command, "job_id": job_id,
                  "created_unix": job.created, "inputs": inputs, "pid": process.pid})
        return {"job_id": job_id, "state": "running", "logs_directory": str(directory),
                "note": "Poll get_job_status. Native completion alone is not artifact review or board acceptance."}


def get_job_status(job_id: str) -> dict:
    return get_job(job_id).snapshot()


def tail_job_log(job_id: str, lines: int = 40) -> dict:
    require(1 <= lines <= 200, "lines must be between 1 and 200")
    job = get_job(job_id)
    status = job.snapshot()
    paths = [job.directory / "launcher.stdout.log", job.directory / "launcher.stderr.log"]
    if job.build_dir:
        paths += [scoped_file(job.build_dir / name, job.build_dir)
                  for name in ["procise.stdout.log", "procise.stderr.log"] if (job.build_dir / name).is_file()]
    # Bound bytes as well as line count; partial UTF-8 is decoded with replacement.
    result = {}
    for path in paths:
        with path.open("rb") as f:
            f.seek(max(0, path.stat().st_size - 64000))
            data = f.read(64000)
        result[str(path)] = "\n".join(data.decode("utf-8", errors="replace").splitlines()[-lines:])[-16000:]
    return {"job_id": job_id, "state": status["state"], "logs": result}


def list_artifacts(job_id: str) -> dict:
    job = get_job(job_id)
    status = job.snapshot()
    artifacts = []
    if job.build_dir:
        for name in ["lite_led_chaser.bit", "lite_led_chaser.bgn", "lite_led_chaser_route.json",
                     "lite_led_chaser_placed.fdc", "lite_led_chaser.edif"]:
            path = job.build_dir / "rundir" / name
            if path.is_file():
                path = scoped_file(path, job.build_dir)
                artifacts.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)})
        path = job.build_dir / "build-review.json"
        if path.is_file():
            path = scoped_file(path, job.build_dir)
            artifacts.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)})
    return {"job_id": job_id, "state": status["state"], "artifacts": artifacts,
            "provisional": status["state"] == "running"}


def review_led_build(job_id: str, sim_dir: str) -> dict:
    job = get_job(job_id)
    status = job.snapshot()
    require(status["state"] in ["native_completed", "reviewed"], "Only a completed, successful owned job can be reviewed")
    simulation = scoped_directory(sim_dir, "sim_")
    for name in ["lite_led_chaser.v", "tb_lite_led_chaser.sv", "simulate.stdout.log"]:
        scoped_file(simulation / name, simulation)
    check_scripts()
    with job.lock:
        if job.review:
            require(job.review["sim_directory"] == str(simulation), "Job already reviewed against another simulation")
            require(sha(job.build_dir / "rundir/lite_led_chaser.bit") == job.review["bitstream_sha256"],
                    "Reviewed bitstream changed")
            return job.review
        command = [sys.executable, str(PROJECT / "scripts/ReviewBuild.py"), "--build-dir",
                   str(job.build_dir), "--sim-dir", str(simulation)]
        with (job.directory / "review.stdout.log").open("wb") as out, (job.directory / "review.stderr.log").open("wb") as err:
            result = subprocess.run(command, cwd=PROJECT, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
        require(result.returncode == 0 and "BUILD_REVIEW_PASS" in read_text(job.directory / "review.stdout.log"),
                f"Artifact review failed; see {job.directory / 'review.stderr.log'}")
        review = json.loads(scoped_file(job.build_dir / "build-review.json", job.build_dir).read_text(encoding="utf-8"))
        require(review["status"] == "reviewed_for_jtag_download", "Unexpected review status")
        require(review["bitstream_sha256"] == sha(job.build_dir / "rundir/lite_led_chaser.bit"), "Review hash mismatch")
        job.review = {"artifact_review": "passed", "review_file": str(job.build_dir / "build-review.json"),
                      "sim_directory": str(simulation), "bitstream_sha256": review["bitstream_sha256"],
                      "register_init_checked": len(review["register_initial_values"]),
                      "board_result": "not tested for this MCP build", "programming_authorized_by_tool": False}
        return job.review

"""Review the native artifacts before downloading this specific Lite test."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_log(path):
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    return data.decode("utf-8-sig", errors="replace")


p = argparse.ArgumentParser()
p.add_argument("--build-dir", required=True, type=Path)
p.add_argument("--sim-dir", required=True, type=Path)
a = p.parse_args()
r = a.build_dir / "rundir"
project = Path(__file__).resolve().parents[1]
bit = r / "lite_led_chaser.bit"
require(bit.is_file() and bit.stat().st_size > 1000000, "Missing/invalid bitstream")
require((a.build_dir / "procise.stderr.log").stat().st_size == 0, "Non-empty native stderr")
log = read_log(a.build_dir / "procise.stdout.log")
require("BUILD_TCL_COMPLETED" in log, "Incomplete native build")
require(not re.search(r"(?im)^\s*(?:ERROR|BUILD_TCL_FAIL)\b", log), "Native error in build log")
simlog = read_log(a.sim_dir / "simulate.stdout.log")
require("PASS: initialization" in simlog and not re.search(r"FAIL|Fatal:|ERROR:", simlog),
        "Self-checking RTL simulation did not pass")
rtl = project / "rtl/lite_led_chaser.v"
require(sha(rtl) == sha(a.build_dir / rtl.name) == sha(a.sim_dir / rtl.name),
        "Simulation/build/current RTL differ")
require(sha(project / "constraints/lite_led_chaser.fdc") == sha(a.build_dir / "lite_led_chaser.fdc"),
        "Current/staged constraints differ")
require(sha(project / "sim/tb_lite_led_chaser.sv") == sha(a.sim_dir / "tb_lite_led_chaser.sv"),
        "Current/staged testbench differ")
require(sha(project / "scripts/build.tcl") == sha(a.build_dir / "build.tcl"),
        "Current/staged build script differ")
manifest_path = project / "source-manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
require(manifest["status"] == "specific_plaintext_source_closure_audited", "IP audit not completed")
require(sha(manifest_path) == sha(a.build_dir / manifest_path.name) == sha(a.sim_dir / manifest_path.name),
        "Source manifests differ")
source_hashes = {}
for entry in manifest["design_sources"]:
    require(sha(project / entry["path"]) == sha(a.build_dir / entry["stage_name"]) ==
            sha(a.sim_dir / entry["stage_name"]) == entry["sha256"],
            f"IP/source differs between current, simulation and build: {entry['path']}")
    source_hashes[entry["stage_name"]] = entry["sha256"]
require(sha(project / manifest["xci"]["path"]) == sha(a.build_dir / "led_state_concat.xci") ==
        sha(a.sim_dir / "led_state_concat.xci") == manifest["xci"]["sha256"], "XCI provenance changed")
require("PASS: xlconcat all 16 input combinations" in simlog, "IP unit self-check missing")
ip_trace = re.findall(r"IP_TRACE input=([0-9a-f]) next=([0-9a-f])", simlog)
require(ip_trace == list(zip("0123456789abcdef", "048c26ae159d37bf")),
        "Actual IP truth table trace incomplete or wrong")
for name in ["compile.stdout.log", "elaborate.stdout.log"]:
    require(not re.search(r"(?im)^\s*(?:ERROR|Fatal:)\b", read_log(a.sim_dir / name)),
            f"XSim compilation/elaboration errors: {name}")
fdc = (r / "lite_led_chaser_placed.fdc").read_text()
pins = {"clk_100m": ("AC14", "LVCMOS33"), "led[0]": ("J1", "LVCMOS15"),
        "led[1]": ("M6", "LVCMOS15"), "led[2]": ("H7", "LVCMOS15"),
        "led[3]": ("J8", "LVCMOS15")}
for port, (pin, standard) in pins.items():
    for prop, value in [("PACKAGE_PIN", pin), ("IOSTANDARD", standard)]:
        require(f"set_property {prop} {value} [get_ports {{{port}}}]" in fdc,
                f"Native placed constraints mismatch: {port}/{prop}")
route = json.loads((r / "lite_led_chaser_route.json").read_text())
clock = route["Clock Summary"]["item_data"]
require(len(clock) == 1 and clock[0]["Period(ns)"] == 10.0, "Unexpected clock")
summary = route["Design Summary"]["item_data"]
require(summary["Timing constraints met"] is True, "Internal timing not met")
for kind in ["Setup", "Hold"]:
    require(summary[kind]["Number of Failing Endpoints"] == 0, f"{kind} violation")
checks = {i["Timing Check"]: i["Count"] for i in route["Check Timing"]["item_data"]}
for name, count in checks.items():
    require(count == (4 if name == "no_output_delay" else 0), f"Unexpected timing check: {name}")
outputs = route["Check Timing"]["no_output_delay"]["item_data"]
require({o["Name"] for o in outputs} == {f"led[{i}]" for i in range(4)},
        "Unconstrained output is not an LED")
edif = (r / "lite_led_chaser.edif").read_text()
require(not re.search(r"\b(?:black_box|syn_black_box)\b", edif, re.I), "Black-box netlist attribute")
cells = set(re.findall(r"\(cell\s+(\w+)", edif))
cell_refs = set(re.findall(r"\(cellRef\s+(\w+)", edif))
require(cell_refs <= cells, f"Undefined EDIF cell references: {cell_refs - cells}")
require(not ({"led_state_concat", "xlconcat_v2_1_3_xlconcat"} & cell_refs),
        "IP remains as an unresolved cell rather than synthesized logic")
require(not re.search(r"(?im)^.*(?:unresolved|undefined|black[ _-]?box).*$", log),
        "Native log contains unresolved/black-box indication")
initials = {}
for group, count in [("tick_count", 25), ("led_state", 4)]:
    for i in range(count):
        pattern = (rf'\(instance \(rename {group}_reg_{i}_ "{group}_reg\[{i}\]"\)'
                   r'(?:(?!\(instance).)*?\(property INIT \(string "([01])"\)')
        match = re.search(pattern, edif, re.S)
        wanted = "1" if group == "led_state" and i == 0 else "0"
        require(match is not None and match[1] == wanted, f"INIT mismatch: {group}[{i}]")
        initials[f"{group}[{i}]"] = wanted
bgn = (r / "lite_led_chaser.bgn").read_text()
require("device JFMQL30TAI676H" in bgn, "Wrong native device")
require(re.search(r"\| StartupClk\s*\| JtagClk\s*\|", bgn, re.I), "StartupClk must be JtagClk")
require(re.search(r"\| UnconstrainedPins\s*\| Disallow", bgn), "Unconstrained pins permitted")
report = {
    "status": "reviewed_for_jtag_download",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "device": "JFMQL30TAI676H", "bitstream": str(bit.resolve()),
    "bitstream_sha256": sha(bit), "bitstream_size": bit.stat().st_size,
    "rtl_sha256": sha(rtl), "sim_directory": str(a.sim_dir.resolve()),
    "ip": manifest["ip"], "design_source_sha256": source_hashes,
    "source_manifest_sha256": sha(manifest_path), "ip_truth_table_trace": ip_trace,
    "edif_defined_cells": sorted(cells), "edif_referenced_cells": sorted(cell_refs),
    "clock": clock, "native_timing": summary,
    "timing_checks": checks, "pin_constraints": pins, "register_initial_values": initials,
    "startup_clock": "JtagClk",
    "limitation": "Simple unencrypted xlconcat source IP only; 4 LED outputs have no external synchronous timing contract; behavioral simulation only.",
    "board_visual_result": "pending_user_observation",
}
out = a.build_dir / "build-review.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("BUILD_REVIEW_PASS", out)
print("BITSTREAM_SHA256", report["bitstream_sha256"])

"""Bounded, two-valued audit of four r2 residuals; no EDA or device access.

The two storage LUTs need a zero SRL/storage invariant, and the two AR-CDC
RAM input differences need a two-register zero invariant.  No recursive cone
expansion, BDD, RAM-state model, or whole-design equivalence is attempted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import itertools
import json
from pathlib import Path
import platform
import re
import shutil
import sys
import time
import traceback


PAUSE_SHA = "c99af5e5f51987a66b615cbffbf1dea6834e247ffc08ec534630fc859f40115e"
MODEL_SHA = {
    "FDCE": "74d30d7c788e7db47f12b92d5b4b57b707974a0962708b309e4cc081d5f98b04",
    "FDRE": "e2965e4b5174bd8de84b82e89a7b4ea5df36d8715c4f585580c16b8e6d9aa80d",
    "SRLC32E": "6e34d740f76a972dab9df24950a9c2d990988b16dc1fabf7a4d62c434e0c8a8b",
}
NAME = r'(?:\(rename (\S+) "([^"]+)"\)|(\S+))'
BASE = "U0_ps_ai_peripheral/ZGolo/u_AI_Mate_top/"
CROSS = BASE + "u_axi_2to1/inst/axi_interconnect_inst/crossbar_samd/"
RAM = (BASE + "U0_ddr2hp_itcn/u0_ar_cdc_fifo_ddr/u0_cdc_fifo_ar_64/U0/"
       "inst_fifo_gen/gconvfifo.rf/grf.rf/gntv_or_sync_fifo.mem/gdm.dm_gen.dm/"
       "RAM_reg_0_15_30_35")
CLOCK = ("U0_ps_ai_peripheral/mig_ddr3_u0/u_mig_7series_0_mig/"
         "u_ddr3_infrastructure/u_bufg_clkdiv0/O")
RESET = BASE + "clkrst_wrapper_u0/u_sync_ddr_clk_rst/reset_2d_reg/Q"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def number(value: str) -> int:
    match = re.fullmatch(r"\d+'([hHbB])([0-9a-fA-F]+)", value)
    require(match is not None, "unsupported numeric property: " + value)
    return int(match[2], 16 if match[1].lower() == "h" else 2)


def lut(table: int, inputs: tuple[int, ...]) -> int:
    """I0 is the least significant index bit, as in the stored LUT INIT."""
    return (table >> sum(bit << i for i, bit in enumerate(inputs))) & 1


def ff_step(q: int, d: int, ce: int, reset: int) -> int:
    """Binary FDCE clear/FDRE reset transition at the relevant event."""
    return 0 if reset else d if ce else q


def srl_step(state: int, d: int, ce: int) -> int:
    return ((state << 1) | d) & 0xFFFFFFFF if ce else state


def selftest() -> dict:
    # Independent bit-selection tables catch a reversed I0/IN convention.
    for width in range(1, 7):
        for selected in range(width):
            table = sum(((index >> selected) & 1) << index
                        for index in range(1 << width))
            for bits in itertools.product((0, 1), repeat=width):
                require(lut(table, bits) == bits[selected], "LUT pin-order selftest")
    require(lut(0xB8, (1, 1, 0)) == 1, "mux true branch")
    require(lut(0xB8, (1, 0, 0)) == 0, "mux false branch")
    for address in range(32):
        for ce in (0, 1):
            require((srl_step(0, 0, ce) >> address) & 1 == 0, "SRL zero closure")
    require(srl_step(0, 1, 1) & 1 == 1, "SRL nonzero-input negative control")
    require(srl_step(1, 0, 0) & 1 == 1, "SRL nonzero-INIT negative control")
    require(ff_step(1, 1, 0, 1) == 0, "FDCE asynchronous clear priority")
    require(ff_step(1, 0, 0, 0) == 1, "FF disabled hold")
    require(ff_step(0, 1, 1, 0) == 1, "FF nonzero-data negative control")
    return {"LUT_I0_LSB_basis_all_widths_1_to_6": True,
            "mux_branch_polarity": True, "SRL_zero_and_negative_controls": True,
            "FF_clear_priority_hold_and_negative_controls": True}


class RawInstances:
    """Resolve only requested EDIF hierarchy paths and retain raw properties.

    Net connectivity is read from the separately hash-bound r2 graph.  This
    reader extracts instance properties directly from both original EDIFs;
    it does not execute the previous parser or any other script.
    """

    def __init__(self, path: Path):
        self.text = path.read_text(encoding="utf-8")
        matches = list(re.finditer(r"^   \(cell " + NAME + r" \(celltype ",
                                   self.text, re.MULTILINE))
        self.ranges = {}
        self.cache = {}
        for i, match in enumerate(matches):
            identity = match[1] or match[3]
            require(identity not in self.ranges, "duplicate EDIF cell identity")
            self.ranges[identity] = (match.start(),
                                    matches[i + 1].start() if i + 1 < len(matches)
                                    else len(self.text))

    def instances(self, ref: str) -> dict:
        if ref in self.cache:
            return self.cache[ref]
        start, end = self.ranges[ref]
        body = self.text[start:end]
        matches = list(re.finditer(r"\(instance " + NAME, body))
        first_net = re.search(r"\(net " + NAME, body)
        result = {}
        for i, match in enumerate(matches):
            label = match[2] or match[3]
            limit = matches[i + 1].start() if i + 1 < len(matches) else (
                first_net.start() if first_net else len(body))
            block = body[match.start():limit].rstrip()
            child_ref = re.search(r"\(cellref (\S+)", block)
            require(child_ref is not None, "EDIF instance has no cellref")
            properties = dict(re.findall(r'\(property (\S+) \(string "([^"]*)"\)\)',
                                         block))
            require(label not in result, "duplicate EDIF instance label")
            result[label] = {"ref": child_ref[1], "properties": properties,
                             "raw_instance": block, "containing_cell": ref}
        self.cache[ref] = result
        return result

    def select(self, targets: set[str]) -> dict:
        found = {}

        def visit(ref: str, prefix: str) -> None:
            for label, row in self.instances(ref).items():
                path = prefix + "/" + label if prefix else label
                if path in targets:
                    found[path] = row
                if any(target.startswith(path + "/") for target in targets):
                    visit(row["ref"], path)

        visit("ai7030_edif_top", "")
        require(set(found) == targets, "raw EDIF target missing: " + str(targets - found.keys()))
        return found


def slot_paths(slot: int) -> tuple[str, str, str]:
    suffix = "" if slot == 0 else "__0"
    fifo = (CROSS + "gen_samd.crossbar_samd/gen_crossbar.gen_slave_slots["
            + str(slot) + "].gen_si_write.wdata_router_w/wrouter_aw_fifo/")
    return (CROSS + "storage_data1[0]_i_1" + suffix,
            fifo + "storage_data1_reg[0]",
            fifo + "gen_srls[0].gen_rep[0].srl_nx1/gen_srls[0].srl_inst")


def verify_raw(node: dict, raw: dict) -> None:
    require(node["ref"] == raw["ref"], "raw/graph primitive identity differs")
    if node["init"] is not None:
        require(raw["properties"].get("INIT") == node["init"], "raw/graph INIT differs")


def verify_zero_state_parameters(node: dict, raw: dict, defaults: dict) -> dict:
    verify_raw(node, raw)
    require(number(node["init"]) == 0, "nonzero state initialization")
    properties = raw["properties"]
    observed = {key: properties.get(key) for key in defaults}
    for key, default in defaults.items():
        require(number(properties.get(key, default)) == 0, "nonzero inversion: " + key)
    unexpected = [key for key in properties if key.startswith("IS_") and key not in defaults]
    require(not unexpected, "unmodeled inversion properties: " + str(unexpected))
    return {"explicit": observed, "effective": defaults,
            "absent_properties_use_hash_bound_local_model_defaults": True}


def truth_rows(node: dict, fixed: dict[int, int]) -> dict:
    width = int(node["ref"][3:])
    require(1 <= width <= 6, "unexpected LUT width")
    table = number(node["init"])
    rows = [{"inputs_I0_first": list(bits), "O": lut(table, bits),
             "meets_zero_invariant": all(bits[i] == value for i, value in fixed.items())}
            for bits in itertools.product((0, 1), repeat=width)]
    accepted = [row for row in rows if row["meets_zero_invariant"]]
    require(accepted and all(row["O"] == 0 for row in accepted),
            "zero-invariant LUT closure failed")
    return {"fixed_pins": {"I" + str(k): v for k, v in fixed.items()},
            "all_rows": rows, "closure_rows": len(accepted), "closure_output": 0}


def run(root: Path, out: Path, started: float) -> dict:
    r2 = root / "tools/pose-v1/evidence/hdmi-live-20261017-r2"
    manifest_path = r2 / "pause-manifest.json"
    require(digest(manifest_path) == PAUSE_SHA, "r2 frozen manifest identity changed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = {record["path"].replace("\\", "/"): record for record in manifest["files"]}
    verified = [{"path": str(manifest_path), "sha256": PAUSE_SHA}]

    def frozen(relative: str) -> Path:
        path = r2 / relative
        expected = records[relative]
        actual = {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}
        require(actual["bytes"] == expected["bytes"] and actual["sha256"] == expected["sha256"],
                "r2 frozen dependency identity changed: " + relative)
        verified.append(actual)
        return path

    graphs = {design: json.loads(frozen("routed-graph-export/" + design + "-graph.json")
                                .read_text(encoding="utf-8"))
              for design in ("original", "candidate")}
    edifs = {design: frozen("routed-netlist-export/" + name + ".edf")
             for design, name in (("original", "original"), ("candidate", "monitor_v2"))}
    for ref, expected in MODEL_SHA.items():
        path = Path("D:/vivado18.3/Vivado/2018.3/data/verilog/src/unisims") / (ref + ".v")
        require(digest(path) == expected, "local primitive model identity changed: " + ref)
        verified.append({"path": str(path), "bytes": path.stat().st_size, "sha256": expected})
        shutil.copyfile(path, out / (ref + ".local-model.v"))
    (out / "dependencies-identity.json").write_text(json.dumps(verified, indent=2) + "\n")

    targets = {design: {RAM} for design in graphs}
    for design in graphs:
        for slot in (0, 1):
            lut_path, ff, srl = slot_paths(slot)
            targets[design].update((lut_path, ff))
            if design == "candidate":
                targets[design].add(srl)
    for bit, mux in ((31, 654), (30, 655)):
        targets["candidate"].update((
            BASE + f"ddr_ritcn_u0/avr_rs_u0/u_avr_brs/payload_tmp0_reg[{bit}]",
            BASE + f"ddr_ritcn_u0/avr_rs_u0/u_avr_frs/s_data_reg[{bit}]",
            "U0_ps_ai_peripheral/ZGolo/u0_ddr64_wrapper_i_" + str(mux)))

    dependencies = {}
    raw = {}
    for design in graphs:
        reader = RawInstances(edifs[design])
        raw[design] = reader.select(targets[design])
        dependencies[design] = {}
        for cell in sorted(targets[design]):
            node = graphs[design][cell]
            verify_raw(node, raw[design][cell])
            dependencies[design][cell] = {"graph": node, "raw_EDIF": raw[design][cell]}
        del reader
    (out / "dependency-original-values.json").write_text(json.dumps(dependencies, indent=2) + "\n")

    tests = selftest()
    storage = []
    for slot in (0, 1):
        lut_path, ff, srl = slot_paths(slot)
        require(graphs["original"][ff] == graphs["candidate"][ff], "storage FF graph differs")
        row = {"slot": slot, "storage_FF": ff, "LUT": lut_path, "designs": {}}
        for design in graphs:
            g = graphs[design]
            params = verify_zero_state_parameters(g[ff], raw[design][ff], {
                "IS_C_INVERTED": "1'b0", "IS_D_INVERTED": "1'b0", "IS_R_INVERTED": "1'b0"})
            require(g[ff]["ref"] == "FDRE", "storage primitive must be FDRE")
            require(g[ff]["inputs"] == {"R": ["CONST:0"], "CE": ["CONST:1"],
                                           "C": [CLOCK], "D": [lut_path + "/O"]},
                    "storage feedback, clock, enable, or reset differs")
            fixed = {4: 0} if design == "original" else {0: 0, 5: 0}
            require(g[lut_path]["inputs"]["I4" if design == "original" else "I5"] == [ff + "/Q"],
                    "storage LUT own-state dependency differs")
            detail = {"FF_parameters": params, "truth_table": truth_rows(g[lut_path], fixed)}
            if design == "candidate":
                require(g[lut_path]["inputs"]["I0"] == [srl + "/Q"], "SRL dependency differs")
                require(g[srl]["ref"] == "SRLC32E" and g[srl]["inputs"]["D"] == ["CONST:0"],
                        "SRL type or D differs")
                detail["SRL_parameters"] = verify_zero_state_parameters(
                    g[srl], raw[design][srl], {"IS_CLK_INVERTED": "1'b0"})
                require(g[srl]["inputs"]["CLK"] == [CLOCK], "SRL clock differs")
                detail["SRL_all_addresses_and_enables"] = [
                    {"A": address, "CE": ce, "D": 0, "next_32_bits": srl_step(0, 0, ce), "Q": 0}
                    for address in range(32) for ce in (0, 1)]
                # Confirm that this is a reachable-state argument, not a
                # combinational equivalence result with SRL Q left free.
                width = int(g[lut_path]["ref"][3:])
                counterexamples = [list(bits) for bits in itertools.product((0, 1), repeat=width)
                                   if bits[5] == 0 and lut(number(g[lut_path]["init"]), bits) == 1]
                require(counterexamples, "missing storage/SRL assumption negative control")
                detail["without_SRL_zero_invariant_counterexample_I0_first"] = counterexamples[0]
            else:
                require(srl not in g, "original SRL unexpectedly present")
                detail["SRL_instance_absent_in_original_graph"] = True
            row["designs"][design] = detail
        row["invariant"] = ("INIT establishes storage Q=0; original D is 0 for any other input. "
                            "Candidate SRL all-zero INIT and D=0 establish Q=0; with storage Q=0, "
                            "candidate D is 0 for any other input. Thus both storage Q and LUT O remain 0.")
        storage.append(row)

    ar_inputs = []
    for bit, mux, ram_pin in ((31, 654, "(member DIA 0)"), (30, 655, "(member DIA 1)")):
        g = graphs["candidate"]
        front = BASE + f"ddr_ritcn_u0/avr_rs_u0/u_avr_frs/s_data_reg[{bit}]"
        back = BASE + f"ddr_ritcn_u0/avr_rs_u0/u_avr_brs/payload_tmp0_reg[{bit}]"
        valid = BASE + "ddr_ritcn_u0/avr_rs_u0/u_avr_brs/valid_tmp0_reg/Q"
        mux_path = "U0_ps_ai_peripheral/ZGolo/u0_ddr64_wrapper_i_" + str(mux)
        require(graphs["original"][RAM]["inputs"][ram_pin] == ["CONST:0"], "original RAM input differs")
        require(g[RAM]["inputs"][ram_pin] == [mux_path + "/O"], "candidate RAM input differs")
        parameters = {}
        for cell, data in ((front, "CONST:0"), (back, front + "/Q")):
            require(cell not in graphs["original"], "original removed state unexpectedly present")
            require(g[cell]["ref"] == "FDCE", "AR state primitive must be FDCE")
            parameters[cell] = verify_zero_state_parameters(g[cell], raw["candidate"][cell], {
                "IS_C_INVERTED": "1'b0", "IS_D_INVERTED": "1'b0", "IS_CLR_INVERTED": "1'b0"})
            require(g[cell]["inputs"]["D"] == [data] and g[cell]["inputs"]["CLR"] == [RESET]
                    and g[cell]["inputs"]["C"] == [CLOCK], "AR FF data/reset/clock differs")
        require(g[mux_path]["ref"] == "LUT3" and number(g[mux_path]["init"]) == 0xB8,
                "AR mux identity differs")
        require(g[mux_path]["inputs"] == {"I0": [back + "/Q"], "I1": [valid], "I2": [front + "/Q"]},
                "AR mux connectivity differs")
        transitions = [{"front_Q": 0, "back_Q": 0, "front_CE": fce, "back_CE": bce,
                        "CLR": reset, "front_next": ff_step(0, 0, fce, reset),
                        "back_next": ff_step(0, 0, bce, reset)}
                       for fce, bce, reset in itertools.product((0, 1), repeat=3)]
        require(all(row["front_next"] == row["back_next"] == 0 for row in transitions),
                "AR state zero closure failed")
        ar_inputs.append({"RAM_pin": ram_pin, "original": "CONST:0", "candidate_mux": mux_path,
                          "FDCE_parameters": parameters, "state_transitions": transitions,
                          "mux_truth_table": truth_rows(g[mux_path], {0: 0, 2: 0}),
                          "invariant": "Front INIT0/D0 and back INIT0/D=front Q preserve both Q=0; "
                                       "asynchronous CLR asserts zero, disabled CE holds zero. "
                                       "Mux output is 0 for either valid value.",
                          "original_front_and_back_instances_absent": True})
    require(time.monotonic() - started < 90, "90-second static-analysis limit exceeded")
    result = {
        "passed": True, "selftest": tests, "storage_LUT_residuals": storage,
        "AR_CDC_RAM_input_residuals": ar_inputs,
        "scope": "Four named residuals only, under two-valued standard primitive INIT/transition "
                 "semantics verified against hash-bound local Vivado models and exact raw EDIF properties. "
                 "No RAM state/output semantics, full-design equivalence, routed timing, electrical reset "
                 "release, X/Z propagation, FMQL physical primitive equivalence, or D45 root-cause proof.",
        "uncovered": ["Other primitive parameters and unmatched cells throughout the design",
                      "PS7 attribute/response residuals", "CDC and physical implementation behavior"],
        "actions": {"EDA": False, "board_access": False, "functional_source_changes": False,
                    "BDD": False, "recursive_cone_expansion": False},
        "failure_stop": "Any frozen dependency/model hash, graph/raw identity, parameter, connectivity, "
                        "truth-table closure, or elapsed budget mismatch raises and saves failure.json; "
                        "no retry, broader cone, EDA, board load, or gate relaxation.",
        "seconds": round(time.monotonic() - started, 6),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    r3 = root / "tools/pose-v1/evidence/hdmi-live-20261017-r3"
    out = args.out.resolve() if args.out else r3 / "local-zero-invariants"
    require(out.is_relative_to(r3), "output must be a new r3 evidence directory")
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    shutil.copyfile(__file__, out / "actual-source.py")
    metadata = {"time": datetime.now(timezone(timedelta(hours=8))).isoformat(),
                "cwd": str(Path.cwd()), "project_root": str(root), "argv": sys.argv,
                "Python": sys.version, "platform": platform.platform(),
                "source_sha256": digest(Path(__file__))}
    try:
        result = run(root, out, started)
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        metadata["exit_code"] = 0
        print(json.dumps({"passed": True, "output": str(out), "seconds": result["seconds"],
                          "storage_LUT_residuals": 2, "AR_CDC_RAM_input_residuals": 2}))
        return 0
    except Exception as error:
        metadata["exit_code"] = 1
        (out / "failure.json").write_text(json.dumps({"error": str(error),
                                                       "traceback": traceback.format_exc()}, indent=2) + "\n")
        print(traceback.format_exc(), file=sys.stderr)
        return 1
    finally:
        metadata["elapsed_seconds"] = round(time.monotonic() - started, 6)
        (out / "execution.json").write_text(json.dumps(metadata, indent=2) + "\n")
        files = [{"path": file.name, "bytes": file.stat().st_size, "sha256": digest(file)}
                 for file in sorted(out.iterdir()) if file.is_file()]
        (out / "manifest.json").write_text(json.dumps({"files": files}, indent=2) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())

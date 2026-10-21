"""Summarize an existing routed resource audit; no Vivado or board operations.

LUTs and Slices are physical locations touched by a subtree. Different subtrees
can share them. Exclusive Slices contain no cells outside the selected subtree
or union; they are an observation of this placement, not a rebuilt saving.
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import re


BASE = "U0_ps_ai_peripheral/"
AI = BASE + "ZGolo/u_AI_Mate_top/"
FIELDS = ["LUTs", "FFs", "RAMB36", "RAMB18", "DSP", "Slice_touched",
          "Slice_exclusive", "BRAM36_equivalent", "GTX_channels", "GTX_common",
          "MMCM", "PLL", "BUFG"]
LOGICAL_PREFIXES = {
    AI + "buyi_icore_post_top_u0": "NPU post-processing namespace in supplied EDIF",
    AI + "image_make_top_u0": "PL image-input namespace in supplied EDIF",
    AI + "ddr_intf_u": "NPU PL-DDR data interface",
    AI + "ddr_witcn_u0": "PL-DDR write interconnect",
    AI + "ddr_ritcn_u0": "PL-DDR read interconnect",
    AI + "host_ctrl_u0": "NPU host control",
    AI + "u_ps_ai_io": "NPU PS register interfaces",
    AI + "u_pspl_split": "NPU PS/PL split interface",
}
GROUPS = {
    "legacy_video": ["rx_sdi_inst", BASE + "frame_to_ps_inst0",
                     BASE + "frame_trans_inst0", BASE + "u_vtc",
                     BASE + "a2sync_reset_cam0_clk"],
    "legacy_video_and_adder": ["rx_sdi_inst", "U_adder_top",
                               BASE + "frame_to_ps_inst0",
                               BASE + "frame_trans_inst0", BASE + "u_vtc",
                               BASE + "a2sync_reset_cam0_clk"],
    "diagnostics": [BASE + "ai_read_path_monitor", BASE + "ai_path_monitor",
                    BASE + "ai_read_diag_router", BASE + "ai_diag_router"],
    "HDMI": [BASE + "hdmi_display", BASE + "hdmi_router"],
}
GROUPS["all_candidates"] = GROUPS["legacy_video_and_adder"] + GROUPS["diagnostics"]


def new_stats():
    return dict(luts=set(), slices=set(), FFs=0, RAMB36=0, RAMB18=0, DSP=0,
                primitives=Counter())


def hierarchy(path):
    stack, result = [], []
    for line in path.read_text().splitlines():
        parts = line.split("|")
        if len(parts) != 12:
            continue
        try:
            values = [int(x.strip()) for x in parts[3:-1]]
        except ValueError:
            continue
        name = parts[1].strip()
        if name.startswith("("):
            continue  # Native parent-own subtotal, not another module.
        depth = (len(parts[1]) - len(parts[1].lstrip()) - 1) // 2
        while stack and stack[-1][0] >= depth:
            stack.pop()
        full = "" if depth == 0 else ((stack[-1][1] + "/" if stack[-1][1] else "") + name)
        stack.append((depth, full))
        result.append(dict(path=full, depth=depth, ref_name=parts[2].strip(),
                           native_LUTs=values[0], native_FFs=values[4],
                           native_RAMB36=values[5], native_RAMB18=values[6],
                           native_DSP=values[7]))
    if not result or result[0]["path"]:
        raise ValueError("Native hierarchy root missing")
    return result


def summarize(evidence):
    run = json.loads((evidence / "resource-audit-execution.json").read_text())
    if run["exit_code"] != 0:
        raise ValueError("Native resource inspection failed; inspect its raw log")
    native = hierarchy(evidence / "utilization-hierarchical.rpt")
    if "Design State : Routed" not in (evidence / "utilization-hierarchical.rpt").read_text():
        raise ValueError("Expected the actual routed checkpoint")
    with (evidence / "modules.tsv").open(newline="") as stream:
        modules = {r["name"]: r["ref_name"] for r in csv.DictReader(stream, delimiter="\t")}
    actual_modules = set(modules)
    modules[""] = "ai7030_edif_top"
    for prefix, description in LOGICAL_PREFIXES.items():
        modules.setdefault(prefix, description)
    stats = {name: new_stats() for name in modules}
    slice_common_ancestors = {}
    slice_candidates = defaultdict(set)
    classified_roots = {root for roots in GROUPS.values() for root in roots}
    count = 0
    with (evidence / "leaf-placement.tsv").open(newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            count += 1
            name, ref, loc, bel = (row[k] for k in ("name", "ref_name", "loc", "bel"))
            pieces = name.split("/")
            ancestors = [""] + ["/".join(pieces[:i]) for i in range(1, len(pieces))
                                if "/".join(pieces[:i]) in stats]
            is_slice = loc.startswith("SLICE_")
            lut = re.search(r"\.([ABCD])[56]LUT$", bel) if is_slice else None
            if is_slice:
                parents = set(ancestors)
                if loc not in slice_common_ancestors:
                    slice_common_ancestors[loc] = parents
                else:
                    slice_common_ancestors[loc].intersection_update(parents)
                owner = next((x for x in ancestors if x in classified_roots), "KEEP")
                slice_candidates[loc].add(owner)
            for parent in ancestors:
                item = stats[parent]
                item["primitives"][ref] += 1
                if is_slice:
                    item["slices"].add(loc)
                if lut:
                    item["luts"].add((loc, lut[1]))
                if ref.startswith(("FD", "LD")):
                    item["FFs"] += 1
                if ref == "RAMB36E1":
                    item["RAMB36"] += 1
                if ref == "RAMB18E1":
                    item["RAMB18"] += 1
                if ref == "DSP48E1":
                    item["DSP"] += 1
    exclusive = Counter(parent for parents in slice_common_ancestors.values() for parent in parents)

    def row(parent):
        item = stats[parent]
        return dict(path=parent or "(top)", ref_name=modules[parent],
                    scope="root" if not parent else ("module" if parent in actual_modules else "flattened_name_prefix"),
                    LUTs=len(item["luts"]), FFs=item["FFs"], RAMB36=item["RAMB36"],
                    RAMB18=item["RAMB18"], DSP=item["DSP"],
                    BRAM36_equivalent=item["RAMB36"] + item["RAMB18"] / 2,
                    Slice_touched=len(item["slices"]), Slice_exclusive=exclusive[parent],
                    GTX_channels=item["primitives"]["GTXE2_CHANNEL"],
                    GTX_common=item["primitives"]["GTXE2_COMMON"],
                    MMCM=item["primitives"]["MMCME2_ADV"],
                    PLL=item["primitives"]["PLLE2_ADV"],
                    BUFG=sum(item["primitives"][x] for x in ("BUFG", "BUFGCTRL")))

    result_rows = [row(p) for p in sorted(stats)]
    by_path = {x["path"]: x for x in result_rows}
    mismatches = []
    for item in native:
        key = item["path"] or "(top)"
        actual = by_path.get(key)
        if actual is None:
            mismatches.append(dict(path=key, reason="native hierarchy node absent"))
            continue
        for field in ("LUTs", "FFs", "RAMB36", "RAMB18", "DSP"):
            if actual[field] != item["native_" + field]:
                mismatches.append(dict(path=key, field=field,
                                       physical=actual[field], native=item["native_" + field]))
    if mismatches:
        raise ValueError("Physical/native resource totals disagree: " + repr(mismatches[:8]))
    root = by_path["(top)"]
    groups = {}
    for name, roots in GROUPS.items():
        objects = [stats[p] for p in roots]
        keys = set(roots)
        sliced = set.union(*(x["slices"] for x in objects))
        empty = sum(owners <= keys for owners in slice_candidates.values())
        groups[name] = dict(
            roots=roots,
            LUTs=len(set.union(*(x["luts"] for x in objects))),
            FFs=sum(x["FFs"] for x in objects),
            RAMB36=sum(x["RAMB36"] for x in objects),
            RAMB18=sum(x["RAMB18"] for x in objects),
            DSP=sum(x["DSP"] for x in objects),
            BRAM36_equivalent=sum(x["RAMB36"] + x["RAMB18"] / 2 for x in objects),
            GTX_channels=sum(x["primitives"]["GTXE2_CHANNEL"] for x in objects),
            GTX_common=sum(x["primitives"]["GTXE2_COMMON"] for x in objects),
            Slice_touched=len(sliced), Slice_exclusive=empty,
            occupied_slices_after_static_cell_deletion=root["Slice_touched"] - empty,
            static_remaining_slice_pct=round((root["Slice_touched"] - empty) / 19650 * 100, 2),
            rebuilt_savings="not measured; compatibility stubs, dependencies and new placement may change this",
        )
    native_root = (evidence / "utilization-routed.rpt").read_text()
    m = re.search(r"\| Slice\s+\|\s*(\d+)\s*\|\s*\d+\s*\|\s*(\d+)\s*\|", native_root)
    if not m or int(m[1]) != root["Slice_touched"] or int(m[2]) != 19650:
        raise ValueError("Physical Slice union differs from native utilization")
    with (evidence / "modules-resources.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "ref_name", "scope"] + FIELDS)
        writer.writeheader()
        writer.writerows(result_rows)
    keep = ["ZGolo", "mig_ddr3_u0", "ps_ai_wrapper_u0", "ai_read_path_monitor", "ai_path_monitor",
            "hdmi_display", "frame_to_ps_inst0", "frame_trans_inst0", "u_vtc"]
    selected = [by_path[BASE + x] for x in keep] + [by_path["rx_sdi_inst"], by_path["U_adder_top"]]
    subblocks = [by_path[x] for x in LOGICAL_PREFIXES]
    summary = dict(
        checkpoint="D:/FPGACompetitionProject/.local/hdmi-boot-witness-20261019-r23/reference/fpai_demo_vivado.runs/impl_hp2ready_r24/ai7030_edif_top_routed.dcp",
        target="xc7z030ffg676-2 via existing 030ai/JFM adaptation",
        native_exit_code=run["exit_code"], native_seconds=run["seconds"],
        design_state="Routed", primitive_or_blackbox_records=count,
        preserved_modules=len(actual_modules), native_hierarchy_rows_cross_checked=len(native),
        totals=root, capacity=dict(Slice=19650, LUTs=78600, FFs=157200, BRAM36_equivalent=265, DSP=400),
        modules=selected, AI_logical_subblocks=subblocks, candidate_groups=groups,
        semantics=dict(
            LUTs="Unique physical (Slice site, A/B/C/D LUT) slots touched; O5/O6 packing and macro expansion deduplicated",
            Slice_touched="Unique Slice locations touched; cross-module packing makes row sums non-additive",
            Slice_exclusive="Sites whose all placed cells belong to the subtree or selected union",
            BRAM36_equivalent="RAMB36 + RAMB18/2",
            groups="Subtree roots in each union are disjoint; candidate classes are an engineering assessment",
            rebuilt_savings="No design modified, rebuilt or board-tested in this audit",
        ),
    )
    (evidence / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(native_hierarchy_rows_cross_checked=len(native),
                          preserved_modules=len(actual_modules), totals=root,
                          candidate_groups=groups, AI_logical_subblocks=subblocks),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    summarize(parser.parse_args().evidence.resolve())

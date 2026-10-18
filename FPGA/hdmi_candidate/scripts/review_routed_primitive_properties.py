"""Read explicit r2 EDIF properties, retaining unknown attributes and raw text.

This bounded static audit uses no EDA, board, connectivity expansion, or BDD.
Only fully identical within-design property groups may share a replica-normalized
name.  Missing properties remain missing; no primitive defaults are inferred.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import sys
import time
import traceback


PAUSE_SHA = "c99af5e5f51987a66b615cbffbf1dea6834e247ffc08ec534630fc859f40115e"
NAME = r'(?:\(rename (\S+) "([^"]+)"\)|(\S+))'
PHYSICAL = {
    "LOC", "BEL", "RLOC", "RLOC_ORIGIN", "RLOC_RANGE", "HLUTNM", "SOFT_HLUTNM",
    "HU_SET", "U_SET", "ROUTE", "FIXED_ROUTE", "IS_LOC_FIXED", "IS_BEL_FIXED",
    "LUTNM", "LOCK_PINS", "IODELAY_GROUP", "CLOCK_REGION", "USER_SLR_ASSIGNMENT",
}
DIRECTIVE = {
    "DONT_TOUCH", "KEEP", "ASYNC_REG", "MARK_DEBUG", "SHREG_EXTRACT", "RAM_STYLE",
    "IOB", "MAX_FANOUT", "RTL_MAX_FANOUT", "SYN_MAXFAN", "SYN_KEEP",
    "EQUIVALENT_REGISTER_REMOVAL", "RTL_KEEP", "USE_CLOCK_ENABLE",
}
PROVENANCE = {
    "ORIG_REF_NAME", "ORIG_CELL_NAME", "OPT_MODIFIED", "PHYS_OPT_MODIFIED",
    "PHYS_OPT_SKIPPED", "BOX_TYPE", "SRL_NAME", "SRL_BUS_NAME", "X_CORE_INFO",
    "CHECK_LICENSE_TYPE", "CORE_GENERATION_INFO", "DOWNGRADEIPIDENTIFIEDWARNINGS",
    "X_INTERFACE_PARAMETER", "X_INTERFACE_INFO", "XILINX_LEGACY_PRIM",
}
FUNCTIONAL = {
    "RAM_MODE", "READ_WIDTH_A", "READ_WIDTH_B", "WRITE_WIDTH_A", "WRITE_WIDTH_B",
    "WRITE_MODE_A", "WRITE_MODE_B", "DOA_REG", "DOB_REG", "RAM_EXTENSION_A",
    "RAM_EXTENSION_B", "EN_ECC_READ", "EN_ECC_WRITE", "RDADDR_COLLISION_HWCONFIG",
    "EN_SYN", "FIFO_MODE", "FIRST_WORD_FALL_THROUGH", "DATA_WIDTH", "FIFO_SIZE",
    "ALMOST_EMPTY_OFFSET", "ALMOST_FULL_OFFSET", "OUTPUT_REG", "REGCE_PRIORITY",
}
LEAF = re.compile(r"^(?:FD[A-Z0-9_]+|SRL[A-Z0-9_]+|RAM[A-Z0-9_]+|FIFO[A-Z0-9_]+|"
                  r"LUT[1-6]|MUXF[78]|INV|BUF|CARRY4|PS7)$")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize(path: str) -> str:
    return re.sub(r"_replica(?:_\d+)?", "", re.sub(r"_repN(?:_\d+)?", "", path))


def selected(path: str) -> bool:
    return ("/ZGolo/" in path or path.endswith("/ZGolo")
            or "/processing_system7_0/" in path or path.endswith("/processing_system7_0"))


def balanced(text: str, start: int) -> int:
    """Return first byte offset after one balanced expression; quoted text is opaque."""
    require(text[start] == "(", "balanced reader must start at an expression")
    depth = 0
    quoted = False
    for pos in range(start, len(text)):
        char = text[pos]
        if char == '"':
            quoted = not quoted
        elif not quoted:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return pos + 1
    raise ValueError("unterminated EDIF expression")


def properties(block: str) -> dict:
    result = {}
    for match in re.finditer(r"\(property " + NAME + r"\s+", block):
        identity, label = match[1] or match[3], match[2] or match[3]
        end = balanced(block, match.start())
        raw_value = block[match.end():end - 1].strip()
        tokens = re.findall(r'"[^"]*"|[()]|[^\s()]+', raw_value)
        require(label not in result, "duplicate property label: " + label)
        result[label] = {"identity": identity, "value": " ".join(tokens),
                         "raw": block[match.start():end]}
    return result


def classify(key: str) -> str:
    upper = key.upper()
    if upper in PHYSICAL:
        return "physical_metadata"
    if upper in DIRECTIVE:
        return "implementation_directive"
    if upper in PROVENANCE:
        return "provenance_metadata"
    if upper.startswith("SIM_") or upper in {"MSGON", "XON"}:
        return "simulation_configuration"
    if (upper in FUNCTIONAL or upper.startswith(("INIT", "SRVAL", "RST", "C_", "G_", "P_"))
            or re.fullmatch(r"IS_.+_INVERTED", upper)):
        return "functional_configuration"
    return "unknown"


def canonical(props: dict) -> dict:
    return {key: value["value"] for key, value in props.items()}


class Edif:
    def __init__(self, path: Path, started: float):
        self.text = path.read_text(encoding="utf-8")
        self.started = started
        matches = list(re.finditer(r"^   \(cell " + NAME + r" \(celltype ",
                                   self.text, re.MULTILINE))
        self.ranges = {}
        self.cache = {}
        for i, match in enumerate(matches):
            identity = match[1] or match[3]
            require(identity not in self.ranges, "duplicate EDIF cell")
            self.ranges[identity] = (match.start(), matches[i + 1].start()
                                    if i + 1 < len(matches) else len(self.text))

    def check_budget(self) -> None:
        require(time.monotonic() - self.started <= 90, "90-second static-analysis ceiling")

    def body(self, ref: str) -> str:
        start, end = self.ranges[ref]
        return self.text[start:end]

    def instances(self, ref: str) -> dict:
        if ref in self.cache:
            return self.cache[ref]
        self.check_budget()
        body = self.body(ref)
        rows = {}
        for match in re.finditer(r"\(instance " + NAME, body):
            label = match[2] or match[3]
            block = body[match.start():balanced(body, match.start())]
            child = re.search(r"\(cellref (\S+) \(libraryref (\S+)\)\)", block)
            require(child is not None, "unresolved instance reference")
            require(label not in rows, "duplicate instance label")
            rows[label] = {"ref": child[1], "library": child[2],
                           "properties": properties(block), "raw_instance": block,
                           "containing_cell": ref}
        self.cache[ref] = rows
        return rows

    def extract(self, graph: dict, destination: Path) -> tuple[dict, dict, dict]:
        rows = {}
        definitions = {}
        counts = Counter()

        def walk(ref: str, path: str) -> None:
            children = self.instances(ref)
            is_leaf = not children
            in_scope = selected(path)
            hierarchy_fifo = bool(re.search("fifo|processing_system7", ref, re.IGNORECASE))
            include = in_scope and ((is_leaf and LEAF.fullmatch(ref)) or (not is_leaf and hierarchy_fifo))
            if include:
                require(path not in rows, "duplicate flattened path")
                row = dict(instance_stack[-1])
                row.update({"path": path, "normalized_path": normalize(path), "leaf": is_leaf,
                            "kind": "primitive" if is_leaf else "FIFO_or_PS_hierarchy"})
                if is_leaf:
                    known = graph[normalize(path)]
                    require(known["ref"] == ref, "raw/graph reference differs: " + path)
                    init = row["properties"].get("INIT")
                    if known["init"] is not None:
                        require(init is not None and init["value"] == '( string "' + known["init"] + '" )',
                                "raw/graph INIT differs: " + path)
                rows[path] = row
                counts[ref] += 1
                if is_leaf and ref not in definitions:
                    body = self.body(ref)
                    definitions[ref] = {"raw_cell_definition": body,
                                        "sha256_text_utf8": hashlib.sha256(body.encode()).hexdigest(),
                                        "properties_anywhere_in_definition": properties(body)}
            for label, child in children.items():
                instance_stack.append(child)
                walk(child["ref"], path + "/" + label if path else label)
                instance_stack.pop()

        instance_stack = []
        walk("ai7030_edif_top", "")
        with destination.open("w", encoding="utf-8", newline="\n") as stream:
            for path in sorted(rows):
                stream.write(json.dumps(rows[path], ensure_ascii=False) + "\n")
        return rows, definitions, dict(counts)


def grouped(rows: dict) -> tuple[dict, list, list]:
    groups = defaultdict(list)
    for row in rows.values():
        groups[row["normalized_path"]].append(row)
    safe = {}
    audits = []
    excluded = []
    for key, members in groups.items():
        signatures = {(member["ref"], json.dumps(canonical(member["properties"]), sort_keys=True))
                      for member in members}
        agree = len(signatures) == 1
        if agree:
            safe[key] = members[0]
        else:
            excluded.append(key)
        if len(members) > 1 or not agree:
            differences = []
            keys = set().union(*(member["properties"] for member in members))
            for prop in sorted(keys):
                values = [{"path": member["path"],
                           "value": canonical(member["properties"]).get(prop)} for member in members]
                if len({value["value"] for value in values}) > 1:
                    differences.append({"property": prop, "category": classify(prop), "values": values})
            audits.append({"normalized_path": key, "members": [row["path"] for row in members],
                           "all_properties_and_ref_identical": agree, "differences": differences})
    return safe, audits, excluded


def selftest() -> dict:
    fixture = '(property (rename p0 "INIT_A") (string "16\'h00(00)"))'
    require(properties(fixture)["INIT_A"]["value"] == '( string "16\'h00(00)" )',
            "quoted parentheses/renamed property parser test")
    require(properties('(property FLAG (boolean (true)))')["FLAG"]["value"] == '( boolean ( true ) )',
            "typed property parser test")
    require(normalize("a_repN_3/b_replica_2") == "a/b", "replica normalization test")
    require(classify("MYSTERY_MODE") == "unknown", "unknown must remain unknown")
    require(classify("LOC") == "physical_metadata" and classify("INIT_40") == "functional_configuration",
            "property category test")
    sample = {
        "a": {"path": "a", "normalized_path": "a", "ref": "FDRE", "properties": properties('(property INIT (string "0"))')},
        "a_repN_1": {"path": "a_repN_1", "normalized_path": "a", "ref": "FDRE", "properties": properties('(property INIT (string "1"))')},
    }
    safe, audits, excluded = grouped(sample)
    require(not safe and len(audits) == len(excluded) == 1, "inconsistent aliases must not collapse")
    return {"typed_and_renamed_property_parser": True, "quoted_parentheses": True,
            "unknown_preserved": True, "replica_mismatch_excluded": True}


def run(root: Path, out: Path, started: float) -> dict:
    r2 = root / "tools/pose-v1/evidence/hdmi-live-20261017-r2"
    manifest = r2 / "pause-manifest.json"
    require(digest(manifest) == PAUSE_SHA, "r2 pause manifest identity differs")
    records = {row["path"].replace("\\", "/"): row
               for row in json.loads(manifest.read_text(encoding="utf-8"))["files"]}
    identities = [{"path": str(manifest), "sha256": PAUSE_SHA}]

    def frozen(relative: str) -> Path:
        path = r2 / relative
        row = {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}
        require(row["bytes"] == records[relative]["bytes"]
                and row["sha256"] == records[relative]["sha256"], "r2 input identity differs: " + relative)
        identities.append(row)
        return path

    tests = selftest()
    outputs = {}
    summaries = {}
    definitions = {}
    alias_audits = {}
    excluded = {}
    unknown = defaultdict(list)
    categories = defaultdict(Counter)
    for design, edif_name in (("original", "original"), ("candidate", "monitor_v2")):
        graph = json.loads(frozen("routed-graph-export/" + design + "-graph.json").read_text(encoding="utf-8"))
        reader = Edif(frozen("routed-netlist-export/" + edif_name + ".edf"), started)
        rows, definitions[design], refs = reader.extract(graph, out / (design + "-raw-properties.jsonl"))
        safe, alias_audits[design], excluded[design] = grouped(rows)
        outputs[design] = safe
        summaries[design] = {"selected_raw_instances": len(rows), "normalized_groups_safe": len(safe),
                             "excluded_inconsistent_alias_groups": len(excluded[design]), "references": refs,
                             "primitive_definitions": len(definitions[design])}
        for row in rows.values():
            for key, value in row["properties"].items():
                category = classify(key)
                categories[design][category] += 1
                if category == "unknown":
                    unknown[key].append({"design": design, "path": row["path"], "ref": row["ref"],
                                         "value": value["value"]})
        del reader, graph, rows
    (out / "dependencies-identity.json").write_text(json.dumps(identities, indent=2) + "\n")
    (out / "primitive-definitions.json").write_text(json.dumps(definitions, indent=2) + "\n")
    (out / "replica-group-audit.json").write_text(json.dumps(alias_audits, indent=2) + "\n")
    (out / "unknown-properties.json").write_text(json.dumps(unknown, indent=2) + "\n")
    rules = {"physical_metadata_allowlist": sorted(PHYSICAL), "implementation_directive_allowlist": sorted(DIRECTIVE),
             "provenance_metadata_allowlist": sorted(PROVENANCE), "functional_configuration_allowlist": sorted(FUNCTIONAL),
             "functional_patterns": ["INIT*", "SRVAL*", "RST*", "IS_*_INVERTED", "C_*", "G_*", "P_*"],
             "simulation_patterns": ["SIM_*", "MSGON", "XON"],
             "fallback": "unknown; never silently classified as physical or ignored"}
    (out / "classification-rules.json").write_text(json.dumps(rules, indent=2) + "\n")

    a, b = outputs["original"], outputs["candidate"]
    common = a.keys() & b.keys()
    differences = []
    property_counts = Counter()
    for path in sorted(common):
        x, y = a[path], b[path]
        old, new = canonical(x["properties"]), canonical(y["properties"])
        changes = [{"property": key, "category": classify(key), "original": old.get(key), "candidate": new.get(key)}
                   for key in sorted(old.keys() | new.keys()) if old.get(key) != new.get(key)]
        property_counts.update(change["category"] for change in changes)
        if changes or x["ref"] != y["ref"]:
            differences.append({"normalized_path": path, "original_path": x["path"], "candidate_path": y["path"],
                                "original_ref": x["ref"], "candidate_ref": y["ref"], "changes": changes})
    type_differences = [{"ref": ref, "original": definitions["original"][ref]["sha256_text_utf8"],
                         "candidate": definitions["candidate"][ref]["sha256_text_utf8"]}
                        for ref in sorted(definitions["original"].keys() & definitions["candidate"].keys())
                        if definitions["original"][ref]["sha256_text_utf8"] != definitions["candidate"][ref]["sha256_text_utf8"]]
    (out / "differences.json").write_text(json.dumps({"common_instance_changes": differences,
                                                       "primitive_definition_changes": type_differences,
                                                       "missing_safe_groups": sorted(a.keys() - b.keys()),
                                                       "added_safe_groups": sorted(b.keys() - a.keys()),
                                                       "excluded_inconsistent_alias_groups": excluded}, indent=2) + "\n")
    require(time.monotonic() - started < 90, "90-second static-analysis ceiling")
    return {
        "completed": True, "seconds": round(time.monotonic() - started, 6), "selftest": tests,
        "designs": summaries, "common_safe_groups": len(common), "changed_common_groups": len(differences),
        "changed_property_occurrences_by_category": property_counts, "property_occurrences_by_category": categories,
        "primitive_definition_changes": len(type_differences), "unknown_property_names": sorted(unknown),
        "all_alias_groups_safe": not any(excluded.values()),
        "no_explicit_functional_property_change": property_counts["functional_configuration"] == 0,
        "scope": "Explicit instance properties of AI/PS selected FD*, SRL*, RAM*, FIFO*, PS7, LUT1-6, "
                 "MUXF7/8, INV, BUF, CARRY4 leaves and FIFO/processing_system7 hierarchy nodes. "
                 "All original property types/values/raw expressions retained; missing properties stay missing. "
                 "Primitive definitions saved and compared as exact text. Only entirely matching property/ref "
                 "replica groups may merge; excluded groups block a complete normalized comparison.",
        "limits": ["No implicit/default-parameter equivalence or interpretation of unknown attributes",
                   "No connectivity, reachable-state, timing, physical implementation, or D45 root-cause proof",
                   "No assumption that an Xilinx primitive definition alone certifies FMQL physical behavior",
                   "Missing/added groups and explicit property differences require separate interpretation"],
        "failure_stop": "Input hash, parsing, raw/graph identity, duplicate property, or 90-second budget "
                        "failure saves failure.json and stops; no retry, EDA, board access, or BDD expansion.",
        "actions": {"EDA": False, "board_access": False, "BDD": False, "functional_source_changes": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    r3 = root / "tools/pose-v1/evidence/hdmi-live-20261017-r3"
    out = args.out.resolve() if args.out else r3 / "primitive-property-review"
    require(out.is_relative_to(r3), "output must be a fresh r3 directory")
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out / "actual-source.py")
    started = time.monotonic()
    metadata = {"time": datetime.now(timezone(timedelta(hours=8))).isoformat(), "cwd": str(Path.cwd()),
                "root": str(root), "argv": sys.argv, "Python": sys.version, "platform": platform.platform(),
                "source_sha256": digest(Path(__file__))}
    try:
        result = run(root, out, started)
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        metadata["exit_code"] = 0
        print(json.dumps({key: result[key] for key in ("completed", "seconds", "common_safe_groups",
                                                       "changed_common_groups", "all_alias_groups_safe",
                                                       "changed_property_occurrences_by_category")}))
        return 0
    except Exception as error:
        metadata["exit_code"] = 1
        (out / "failure.json").write_text(json.dumps({"error": str(error), "traceback": traceback.format_exc()}, indent=2) + "\n")
        print(traceback.format_exc(), file=sys.stderr)
        return 1
    finally:
        metadata["elapsed_seconds"] = round(time.monotonic() - started, 6)
        (out / "execution.json").write_text(json.dumps(metadata, indent=2) + "\n")
        rows = [{"path": file.name, "bytes": file.stat().st_size, "sha256": digest(file)}
                for file in sorted(out.iterdir()) if file.is_file()]
        (out / "manifest.json").write_text(json.dumps({"files": rows}, indent=2) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())

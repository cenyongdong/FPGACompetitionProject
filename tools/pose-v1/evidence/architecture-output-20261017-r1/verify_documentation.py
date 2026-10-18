"""Verify this documentation-only revision without touching runtime artifacts."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


before = json.loads((OUT / "before.json").read_text(encoding="utf-8"))
protected = json.loads((OUT / "protected-before.json").read_text(encoding="utf-8"))
new_path = "ADR/ADR_49.md"
changes = []
links = []
errors = []
for row in before + [{"path": new_path, "sha256": None, "bytes": None}]:
    rel = row["path"]
    p = ROOT / rel
    content = p.read_text(encoding="utf-8")
    new_sha = digest(p)
    changes.append({
        "path": rel, "before_sha256": row["sha256"],
        "after_sha256": new_sha, "after_bytes": p.stat().st_size,
        "kind": "added" if row["sha256"] is None else "revised",
        "reason": "Record approved ADR_49 architecture; preserve paused implementation and actual validation boundaries",
    })
    if row["sha256"] == new_sha:
        errors.append("Expected document revision missing: " + rel)
    # Check every local link in the new ADR, and only changed lines in old files.
    if rel == new_path:
        scope = content
    elif rel == "Agents.md":
        scope = "\n".join(x for x in content.splitlines() if x.startswith("- 用户已明确确认[ADR_49"))
    else:
        previous = (OUT / row["snapshot"]).read_text(encoding="utf-8")
        old_lines = set(previous.splitlines())
        scope = "\n".join(x for x in content.splitlines() if x not in old_lines)
    for target in re.findall(r"\]\(([^\n]+?)\)", scope):
        target = target.strip().strip("<>")
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", target) or target.startswith("#"):
            continue
        candidate = (p.parent / unquote(target.split("#", 1)[0])).resolve()
        ok = candidate.exists()
        links.append({"source": rel, "target": target, "exists": ok})

unchanged = []
for row in protected:
    p = ROOT / row["path"]
    current = digest(p) if p.exists() else None
    ok = current == row["sha256"]
    unchanged.append({"path": row["path"], "sha256": current, "unchanged": ok})
    if not ok:
        errors.append("Protected file changed: " + row["path"])

adr = (ROOT / new_path).read_text(encoding="utf-8")
agents = (ROOT / "Agents.md").read_text(encoding="utf-8")
progress = (ROOT / "PROJECT-PROGRESS.md").read_text(encoding="utf-8")
checks = {
    "user_confirmation_quoted": "请你先将当前的讨论进行记录。" in adr,
    "approved_architecture_not_implemented": "工程切换与下一阶段实施尚未开始" in adr,
    "hdmi_retained": "板端HDMI本地输出＋骨架数据网络输出后由PC独立渲染" in adr,
    "no_source_switch_claim": "本轮没有停用或替换" in adr,
    "old_DATA_independently_paused": "旧DATA调查独立保持暂停" in adr,
    "optional_PL_work_not_authorized": "没有批准新增RTL" in adr,
    "numeric_gate_preserved": "ADR_48 v2" in adr,
    "last_actual_board_date_preserved": "最后实际板测为2026-10-16" in progress,
    "agents_execution_pause_preserved": "待用户明确要求执行后恢复" in agents,
    "new_schema_and_transport_not_fixed": "没有锁定实现" in adr,
}
for name, ok in checks.items():
    if not ok:
        errors.append("State assertion failed: " + name)

save("document-revisions.json", changes)
save("protected-review.json", unchanged)
save("continuation-state.json", {
    "date": "2026-10-17", "timezone": "Asia/Shanghai",
    "architecture_decision": "ADR/ADR_49.md",
    "architecture_approved": True,
    "architecture": {
        "PS_NPU": "perception", "PL": "local HDMI real-time output",
        "PC": "independent high-quality 3D visualization",
        "future_formal_chain": "disable VPU encoding and RTSP; retain HDMI plus skeleton network output",
    },
    "authorized_this_turn": "record discussion and synchronize local documentation only",
    "source_chain_switched_this_turn": False,
    "next_stage_execution_allowed": False,
    "background_continuation_allowed": False,
    "resume_requires": "explicit user instruction to execute within specified scope; architecture already approved",
    "old_DATA_investigation": "remains paused",
    "last_actual_board_validation_date": "2026-10-16",
    "board_rechecked_this_turn": False,
    "no_new_EDA_SSH_UART_JTAG_boot_DMA_or_filesystem_repair": True,
    "previous_state_preserved": "../hdmi-handoff-docs-20261016-r1/continuation-state.json",
})
for row in links:
    source = ROOT / row["source"]
    target = unquote(row["target"].split("#", 1)[0])
    row["exists"] = (source.parent / target).resolve().exists()
    if not row["exists"]:
        errors.append("Broken changed link: " + row["source"] + " -> " + row["target"])
save("link-review.json", links)
formatting = []
for label, command in [
    ("default", ["git", "diff", "--check"]),
    ("existing_CRLF", ["git", "-c", "core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol", "diff", "--check"]),
]:
    run = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (OUT / ("format-" + label + ".stdout.txt")).write_bytes(run.stdout)
    (OUT / ("format-" + label + ".stderr.txt")).write_bytes(run.stderr)
    formatting.append({"label": label, "command": command, "exit_code": run.returncode})
    if label == "existing_CRLF" and run.returncode:
        errors.append("Whitespace check failed with existing CRLF recognized")
save("format-review.json", {
    "checks": formatting,
    "interpretation": "Default Git flags existing CR line endings in changed Markdown as whitespace; CRLF-aware check preserves file conventions and still checks real trailing blanks. No Git configuration or line-ending migration performed.",
})
save("verification.json", {
    "status": "pass" if not errors else "fail",
    "platform": "Windows local documentation only",
    "cwd": ROOT.as_posix(), "date": "2026-10-17",
    "revised_existing_documents": len(before), "new_ADR": new_path,
    "protected_files_checked": len(unchanged), "changed_local_links_checked": len(links),
    "state_assertions": checks, "errors": errors,
    "CRLF_aware_whitespace_check_exit_code": formatting[-1]["exit_code"],
    "runtime_tests_performed": False,
})
manifest = [{"path": p.relative_to(OUT).as_posix(), "bytes": p.stat().st_size,
             "sha256": digest(p)} for p in sorted(OUT.rglob("*"))
            if p.is_file() and p.name != "files.sha256.json"]
save("files.sha256.json", manifest)
print(json.dumps({"status": "pass" if not errors else "fail", "protected": len(unchanged),
                  "links": len(links), "assertions": len(checks), "errors": errors}, ensure_ascii=False))
if errors:
    raise SystemExit(1)

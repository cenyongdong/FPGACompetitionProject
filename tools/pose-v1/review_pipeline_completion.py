"""Review finite F0 evidence, including the failed fresh-process repeat.

Read-only with respect to raw evidence; writes two new review files. Never runs
hardware and never turns a conditional successful run into a stability claim.
"""
import hashlib
import json
import re
from pathlib import Path

import mixed_validation_gate as old


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    assert not path.exists(), path
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def main():
    ev = old.ROOT / "tools/pose-v1/evidence/pipeline-20261008-r6"
    first, repeated, compacted = (ev / name for name in ("combined", "repeat", "compacted"))
    failed_count = old.verify(repeated)
    assert (repeated / "exit.txt").read_text().strip() == "1"
    assert (repeated / "stderr.log").read_text().strip() == "STOP: poll device failure"
    out = repeated / "results"
    for name in ("inference.jsonl", "lifecycle.jsonl", "packets.jsonl"):
        assert not (out / name).read_bytes()
    events = old.lines(out / "encoder/events.jsonl")
    assert not any(x["event"] == "capture" for x in events)
    assert sum(x["event"] == "source_frame" for x in events) == 2
    assert [x["result"] for x in events if x["event"] == "abort_streamoff"] == [0, 0]
    before = (repeated / "dmesg.before.log").read_bytes()
    after = (repeated / "dmesg.after.log").read_bytes()
    assert after.startswith(before)
    new = after[len(before):].decode()
    assert "order:7" in new and "mvx_mmu_alloc_contiguous_pages" in new
    assert "__GFP_NORETRY" in new and "map_protocol_v2" in new
    assert not any(x in new for x in ("MMU ABORT", "Out of memory", "Killed process"))
    assert not (ev / "repeat.acceptance.json").exists()
    save(ev / "repeat-failure-review.json", dict(
        status="fresh_process_startup_failure_preserved", exit=1,
        returned_hashed_files=failed_count, Engine_created=False,
        inference_calls=0, capture_packets=0, submitted_NoInput_frames=2,
        abort_streamoff_returns=[0, 0], requested_contiguous_bytes=524288,
        diagnosis="MVX firmware map_protocol_v2 order7 GFP_NORETRY contiguous allocation failure",
        startup_order_alone_not_sufficient=True, automatic_retry=False))

    gates = [load(ev / f"{name}.acceptance.json") for name in ("combined", "compacted")]
    assert all(g["exit"] == 0 and g["stage"] == "combined" for g in gates)
    assert gates[0]["binary_sha256"] == gates[1]["binary_sha256"] == sha(repeated / "pose_pipeline_encode_check")
    assert gates[0]["package_manifest_sha256"] == gates[1]["package_manifest_sha256"]
    for name in ("video.h264", "submitted.nv12"):
        assert (first / "results/encoder" / name).read_bytes() == (compacted / "results/encoder" / name).read_bytes()
    video = first / "results/encoder"
    for line in (video / "video-transfer.sha256").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert sha(video / name) == digest
    review = load(ev / "host-video-review/review.json")
    assert review["all_encoded_IDs_correct"] and review["joint_visibility_checks"] == 112
    assert len(review["records"]) == 10 and review["warmup_frames"] == 2
    probe = load(video / "probe-mp4.json")
    assert probe["streams"][0]["nb_read_frames"] == "10"
    assert probe["streams"][0]["width"] == 1280 and probe["streams"][0]["height"] == 720

    diag = ev / "compaction-diagnostic"
    assert (diag / "exit.txt").read_text().strip() == "0"
    assert (diag / "dmesg.before.log").read_bytes() == (diag / "dmesg.after.log").read_bytes()
    elapsed = float((diag / "end.txt").read_text()) - float((diag / "start.txt").read_text())
    assert 0 < elapsed < 30
    def movable_orders(suffix):
        text = (diag / f"pagetypeinfo.{suffix}.txt").read_text()
        match = re.search(r"type\s+Movable\s+([\d\s]+)\n", text)
        values = [int(x) for x in match.group(1).split()]
        assert len(values) == 11
        return values
    orders_before, orders_after = movable_orders("before"), movable_orders("after")
    assert orders_after[10] > orders_before[10]
    save(ev / "completion-review.json", dict(
        status="finite_coupling_verified_startup_stability_unresolved",
        binary_sha256=gates[0]["binary_sha256"], package_manifest_sha256=gates[0]["package_manifest_sha256"],
        Host_cases=107, registry_records=12, CPU_output_values=59600,
        successful_finite_runs=2, failed_fresh_process_repeat=1,
        forward_calls_per_success=8, new_production_results_per_success=4,
        encoded_frames_per_success=10, explicit_NoInput_frames=2,
        startup_order="VPU capture observed before Engine creation",
        same_submitted_NV12_and_H264_between_successes=True,
        H264_sha256=sha(video / "video.h264"), MP4_sha256=sha(video / "review.mp4"),
        host_video_review=review["status"], compaction_diagnostic_seconds=elapsed,
        movable_orders_before=orders_before, movable_orders_after=orders_after,
        compaction_written_once=True, persistent_VM_configuration_changed=False,
        compaction_is_production_fix=False, stable_process_restart_verified=False,
        RTSP_online=False, HDMI=False, realtime_throughput_verified=False,
        next="Keep explicit startup failure; design one persistent VPU context/owned frame queue; do not silently compact or retry."))
    print("Finite F0 evidence verified; fresh-process startup stability remains unresolved.")


if __name__ == "__main__":
    main()

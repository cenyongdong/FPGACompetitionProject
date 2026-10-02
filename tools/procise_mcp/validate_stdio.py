"""Real SDK client integration test, including exactly one native LED build."""
import asyncio
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).parent
BASELINE = ROOT / "FPGA/lite_led_chaser/runs/build_20261001_120459_3fa8ba"
parser = argparse.ArgumentParser()
parser.add_argument("--sim-dir", type=Path, default=ROOT / "FPGA/lite_led_chaser/runs/sim_20261001_115631_342b3c")
SIM = parser.parse_args().sim_dir.resolve(strict=True)
OUTPUT = ROOT / "tools/mcp-validation/procise-stdio-validation.json"
RECORD = {"status": "running", "transport": "stdio", "calls": [],
          "started_unix": time.time(), "codex_configuration_changed": False, "board_action": "none"}


def save():
    OUTPUT.write_text(json.dumps(RECORD, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def main():
    server = StdioServerParameters(command=sys.executable, args=[str(SOURCE / "server.py")], cwd=str(ROOT))
    with (OUTPUT.parent / "procise-server.stderr.log").open("w", encoding="utf-8") as errors:
        async with stdio_client(server, errlog=errors) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=45) as client:
                init = await client.initialize()
                RECORD["initialize"] = init.model_dump(mode="json", by_alias=True)
                listed = await client.list_tools()
                RECORD["tools"] = listed.model_dump(mode="json", by_alias=True)
                names = {tool.name for tool in listed.tools}
                assert names == {"get_environment", "read_build_report", "start_led_build", "get_job_status",
                                 "tail_job_log", "list_artifacts", "review_led_build"}, names

                async def call(name, arguments=None, expect_error=False):
                    began = time.perf_counter()
                    result = await client.call_tool(name, arguments or {})
                    elapsed = time.perf_counter() - began
                    RECORD["calls"].append({"tool": name, "arguments": arguments or {}, "elapsed_seconds": elapsed,
                                           "result": result.model_dump(mode="json", by_alias=True)})
                    save()
                    assert bool(result.is_error) == expect_error, (name, result)
                    return result.structured_content if not expect_error else result

                env = await call("get_environment")
                assert env["native_probe"] == "passed" and env["mcp_sdk"] == "2.2.0"
                assert "32494" in env["banner"] and "2025.1.1" in env["banner"], env
                baseline = await call("read_build_report", {"build_dir": str(BASELINE)})
                raw = json.loads((BASELINE / "rundir/lite_led_chaser_route.json").read_text())
                assert baseline["native_timing"] == raw["Design Summary"]["item_data"]
                assert baseline["clock"] == raw["Clock Summary"]["item_data"]
                assert baseline["timing_checks"] == {i["Timing Check"]: i["Count"] for i in raw["Check Timing"]["item_data"]}
                assert baseline["bitstream_sha256"] == hashlib.sha256(Path(baseline["bitstream"]).read_bytes()).hexdigest()
                for arguments in [{"build_dir": str(ROOT)}, {"build_dir": str(BASELINE.parent / "build_missing")}]:
                    await call("read_build_report", arguments, expect_error=True)
                await call("get_job_status", {"job_id": "0" * 32}, expect_error=True)
                await call("get_job_status", {"job_id": "../invalid"}, expect_error=True)
                print("STDIO environment/report checks and error mapping passed", flush=True)

                started = await call("start_led_build")
                RECORD["job_id"] = started["job_id"]
                assert RECORD["calls"][-1]["elapsed_seconds"] < 5, "Build start did not return promptly"
                await call("start_led_build", expect_error=True)
                job_id = started["job_id"]
                deadline = time.monotonic() + 240
                last_state = None
                while True:
                    status = await call("get_job_status", {"job_id": job_id})
                    if status["state"] != last_state:
                        print("Native job state:", status["state"], status.get("build_directory"), flush=True)
                        last_state = status["state"]
                    if status["state"] != "running":
                        break
                    assert time.monotonic() < deadline, "Polling deadline reached; native job has NOT been cancelled"
                    await asyncio.sleep(3)
                assert status["state"] == "native_completed", status
                directory = Path(status["build_directory"])
                assert directory != BASELINE
                report = await call("read_build_report", {"build_dir": str(directory)})
                original = json.loads((directory / "rundir/lite_led_chaser_route.json").read_text())
                assert report["native_timing"] == original["Design Summary"]["item_data"]
                assert report["clock"] == original["Clock Summary"]["item_data"]
                assert report["internal_timing_pass"] and report["pin_constraints_match"]
                assert report["startup_clock"] == "JtagClk" and report["expected_led_output_exception"]
                await call("tail_job_log", {"job_id": job_id, "lines": 0}, expect_error=True)
                await call("tail_job_log", {"job_id": job_id, "lines": 12})
                await call("review_led_build", {"job_id": job_id, "sim_dir": str(ROOT)}, expect_error=True)
                reviewed = await call("review_led_build", {"job_id": job_id, "sim_dir": str(SIM)})
                assert reviewed["artifact_review"] == "passed" and reviewed["register_init_checked"] == 29
                artifacts = await call("list_artifacts", {"job_id": job_id})
                assert artifacts["state"] == "reviewed" and len(artifacts["artifacts"]) == 6
                for artifact in artifacts["artifacts"]:
                    data = Path(artifact["path"]).read_bytes()
                    assert artifact["bytes"] == len(data) and artifact["sha256"] == hashlib.sha256(data).hexdigest()
                # Repeating a review returns the already-reviewed result; no old board result is overwritten.
                assert await call("review_led_build", {"job_id": job_id, "sim_dir": str(SIM)}) == reviewed
                RECORD.update(status="passed", build_directory=str(directory), final_report=report,
                              review=reviewed, ended_unix=time.time())
                print("STDIO_VALIDATION_PASS", directory, flush=True)
    save()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except BaseException as exc:
        RECORD.update(status="failed", failure=repr(exc), ended_unix=time.time())
        save()
        raise

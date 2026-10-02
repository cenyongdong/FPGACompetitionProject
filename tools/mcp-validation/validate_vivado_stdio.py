"""Verify the unchanged installed Vivado MCP in an independent SDK client."""
import asyncio
import json
from pathlib import Path
import sys
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).parent / "vivado-stdio-validation.json"
PYTHON = r"C:\Users\cenyongdong\miniconda3\envs\VivadoMcp\python.exe"
VIVADO = r"D:\Xilinx\Vivado\2019.1\bin\vivado.bat"
RECORD = {"transport": "stdio", "status": "running", "calls": [],
          "scope": "Independent SDK client; does not prove the existing Codex MCP process works"}


def save():
    OUTPUT.write_text(json.dumps(RECORD, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def main():
    params = StdioServerParameters(command=PYTHON, args=["-m", "vivado_mcp"], cwd=str(ROOT),
                                  env={"VIVADO_PATH": VIVADO})
    with (OUTPUT.parent / "vivado-stdio-server.stderr.log").open("w", encoding="utf-8") as errors:
        async with stdio_client(params, errlog=errors) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=60) as client:
                initialized = await client.initialize()
                RECORD["initialize"] = initialized.model_dump(mode="json", by_alias=True)
                sid = "lite_sdk_aux_validation"
                async def call(name, arguments):
                    started = time.perf_counter()
                    result = await client.call_tool(name, arguments)
                    payload = result.model_dump(mode="json", by_alias=True)
                    RECORD["calls"].append({"tool": name, "arguments": arguments,
                                           "elapsed_seconds": time.perf_counter() - started, "result": payload})
                    save()
                    text = "\n".join(c.text for c in result.content if c.type == "text")
                    print(name, text[:700], flush=True)
                    return text
                startup = await call("start_session", {"session_id": sid, "mode": "tcl", "vivado_path": VIVADO, "timeout": 30})
                if "[ERROR]" in startup:
                    RECORD.update(status="startup_failed", note="isError flag must be checked together with ERROR text")
                    save()
                    return
                try:
                    version = await call("run_tcl", {"session_id": sid, "command": "version -short", "timeout": 15})
                    assert "2019.1" in version and "[ERROR]" not in version
                    error = await call("run_tcl", {"session_id": sid, "command": 'error "EXPECTED_MCP_VALIDATION_ERROR"', "timeout": 15})
                    assert "[ERROR]" in error and "EXPECTED_MCP_VALIDATION_ERROR" in error
                    recovered = await call("run_tcl", {"session_id": sid, "command": 'puts "AFTER_ERROR_OK"', "timeout": 15})
                    assert "AFTER_ERROR_OK" in recovered and "[ERROR]" not in recovered
                    command = 'exec {C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe} -NoProfile -NonInteractive -ExecutionPolicy Bypass -File {D:/FPGACompetitionProject/FPGA/lite_led_chaser/scripts/Simulate.ps1}'
                    sim = await call("run_tcl", {"session_id": sid, "command": command, "timeout": 45})
                    assert "SIMULATION_PASS" in sim and "[ERROR]" not in sim
                    RECORD.update(status="passed")
                finally:
                    await call("stop_session", {"session_id": sid})
                save()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except BaseException as exc:
        RECORD.update(status="failed", failure=repr(exc))
        save()
        raise

"""Start the unchanged installed MCP from Codex's actual resolved configuration."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).parent / "vivado-permanent-config-validation.json"
CODEX = r"C:\Users\cenyongdong\AppData\Local\OpenAI\Codex\bin\ca9abb0b4d8ac692\codex.exe"
record = {"status": "running", "calls": [], "existing_chat_server_reloaded": False,
          "temporary_vivado_wrapper_used": False, "system_environment_changed": False}


def save():
    OUTPUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def main():
    resolved = subprocess.run([CODEX, "mcp", "get", "vivado", "--json"],
        cwd=ROOT, capture_output=True, check=True, encoding="utf-8")
    config = json.loads(resolved.stdout)
    transport = config["transport"]
    assert transport["type"] == "stdio" and config["enabled"] is True
    assert transport["env"]["PROCESSOR_ARCHITECTURE"] == "AMD64"
    assert transport["env"]["VIVADO_PATH"] == "D:/Xilinx/Vivado/2019.1/bin/vivado.bat"
    record["resolved_vivado_configuration"] = config
    params = StdioServerParameters(command=transport["command"], args=transport["args"],
        env=transport["env"], cwd=transport.get("cwd") or str(ROOT))
    # Simulate the old missing-variable context in this test process only;
    # the corrected AMD64 value must therefore come from the actual configuration.
    keys = ["PROCESSOR_ARCHITECTURE", "PROCESSOR_ARCHITEW6432"]
    previous = {key: os.environ.pop(key, None) for key in keys}
    record["test_parent_architecture_variables_removed"] = keys
    try:
        with (OUTPUT.parent / "vivado-permanent-server.stderr.log").open("w", encoding="utf-8") as errors:
            async with stdio_client(params, errlog=errors) as (read, write):
                async with ClientSession(read, write, read_timeout_seconds=45) as client:
                    record["initialize"] = (await client.initialize()).model_dump(mode="json", by_alias=True)
                    sid = "permanent_config_validation"
                    async def call(name, arguments):
                        begin = time.perf_counter()
                        result = await client.call_tool(name, arguments)
                        record["calls"].append({"tool": name, "arguments": arguments,
                            "elapsed_seconds": time.perf_counter() - begin,
                            "result": result.model_dump(mode="json", by_alias=True)})
                        save()
                        text = "\n".join(block.text for block in result.content if block.type == "text")
                        assert not result.is_error and "[ERROR]" not in text, text
                        return text
                    try:
                        startup = await call("start_session", {"session_id": sid, "mode": "tcl", "timeout": 30})
                        assert "2019.1" in startup and "ready" in startup
                        answer = await call("run_tcl", {"session_id": sid, "timeout": 10,
                            "command": 'puts "CONFIG_VERSION [version -short]"\nputs "CONFIG_ARCH $::env(PROCESSOR_ARCHITECTURE)"'})
                        assert "CONFIG_VERSION 2019.1" in answer and "CONFIG_ARCH AMD64" in answer
                        record["status"] = "passed"
                        print("PERMANENT_CONFIG_VALIDATION_PASS: Vivado 2019.1; AMD64 from resolved config", flush=True)
                    finally:
                        await call("stop_session", {"session_id": sid})
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        save()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except BaseException as exc:
        record.update(status="failed", failure=repr(exc))
        save()
        raise

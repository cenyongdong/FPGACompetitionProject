"""Compare Windows console contexts without changing installed MCP or Vivado."""
import asyncio
import json
from pathlib import Path
import subprocess
import sys
from vivado_mcp.vivado.tcl_utils import wrap_command, make_sentinel_pattern

HERE = Path(__file__).resolve().parent


async def probe():
    process = await asyncio.create_subprocess_exec(r"D:\Xilinx\Vivado\2019.1\bin\vivado.bat",
        "-mode", "tcl", "-nojournal", "-nolog", stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = [], []
    sentinel = "VMCP_CONSOLE_PROBE"
    process.stdin.write(wrap_command('puts "VMCP_READY"', sentinel).encode())
    await process.stdin.drain()
    ready = False
    async def read_stdout():
        nonlocal ready
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip()
            stdout.append(text)
            if make_sentinel_pattern(sentinel).search(text):
                ready = True
                process.stdin.write(b"exit\n")
                await process.stdin.drain()
    async def read_stderr():
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            stderr.append(line.decode("utf-8", errors="replace").rstrip())
    readers = [asyncio.create_task(read_stdout()), asyncio.create_task(read_stderr())]
    timeout = False
    try:
        await asyncio.wait_for(process.wait(), 20)
    except asyncio.TimeoutError:
        timeout = True
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
        await process.wait()
    await asyncio.gather(*readers)
    return {"ready": ready, "exit_code": process.returncode, "timeout": timeout,
            "stdout": stdout, "stderr": stderr}


if __name__ == "__main__":
    if "--child" in sys.argv:
        print(json.dumps(asyncio.run(probe()), ensure_ascii=False))
    else:
        results = {}
        for label, flags in [("inherited_console", 0), ("no_console", subprocess.CREATE_NO_WINDOW)]:
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child"],
                cwd=HERE, capture_output=True, timeout=35, creationflags=flags)
            text = result.stdout.decode("utf-8", errors="replace")
            results[label] = {"parent_exit_code": result.returncode,
                              "probe": json.loads(text) if text else None,
                              "parent_stderr": result.stderr.decode("utf-8", errors="replace")}
        (HERE / "vivado-console-comparison.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(results, ensure_ascii=False))

"""Approved stdio MCP prototype. Protocol stdout must remain clean."""
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from typing import Any
import backend

server = MCPServer("procise-lite-prototype", version="0.1.0",
    instructions="Use Procise for Fudan FPGA implementation. LED-only prototype; no JTAG or arbitrary Tcl. "
    "Long builds return a job ID. Timeouts do not cancel jobs; restart recovery is unsupported.")
READ = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False)


@server.tool(annotations=WRITE, structured_output=True)
def get_environment() -> dict[str, Any]:
    """Run a fixed harmless Procise version/environment probe, saving local diagnostic logs."""
    return backend.get_environment()


@server.tool(annotations=READ, structured_output=True)
def read_build_report(build_dir: str) -> dict[str, Any]:
    """Read an existing approved LED build's native timing/pins/bitgen report and hashes."""
    return backend.read_build_report(build_dir)


@server.tool(annotations=WRITE, structured_output=True)
def start_led_build() -> dict[str, Any]:
    """Start the approved Lite LED Build.ps1 in a new run directory; no programming. One active job."""
    return backend.start_led_build()


@server.tool(annotations=WRITE, structured_output=True)
def get_job_status(job_id: str) -> dict[str, Any]:
    """Query an owned job and persist its status evidence. Native completion is distinct from review."""
    return backend.get_job_status(job_id)


@server.tool(annotations=WRITE, structured_output=True)
def tail_job_log(job_id: str, lines: int = 40) -> dict[str, Any]:
    """Return bounded launcher/native log tails and refresh local job status evidence."""
    return backend.tail_job_log(job_id, lines)


@server.tool(annotations=WRITE, structured_output=True)
def list_artifacts(job_id: str) -> dict[str, Any]:
    """List known owned build artifacts with SHA-256, refreshing local status evidence."""
    return backend.list_artifacts(job_id)


@server.tool(annotations=WRITE, structured_output=True)
def review_led_build(job_id: str, sim_dir: str) -> dict[str, Any]:
    """Review only this server's successful new LED job against an approved XSim run; writes review JSON."""
    return backend.review_led_build(job_id, sim_dir)


if __name__ == "__main__":
    server.run(transport="stdio")

"""Bounded read-only board identity/allocation audit; never initializes hardware."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

dest = Path(sys.argv[1])
assert not dest.exists()
dest.mkdir()
records = {}
for name, argv in {
    "uname": ["uname", "-a"], "module": ["modinfo", "amvx"],
    "module-path": ["modinfo", "-n", "amvx"], "modules": ["lsmod"],
    "processes": ["ps", "-eo", "pid,comm,args"],
}.items():
    try:
        result = subprocess.run(argv, capture_output=True, timeout=10)
        (dest / (name + ".stdout.txt")).write_bytes(result.stdout)
        (dest / (name + ".stderr.txt")).write_bytes(result.stderr)
        records[name] = dict(exit=result.returncode)
    except (OSError, subprocess.TimeoutExpired) as exc:
        records[name] = dict(unavailable=str(exc))
for name in ("cmdline", "meminfo", "buddyinfo", "pagetypeinfo", "vmstat", "iomem", "version"):
    (dest / (name + ".txt")).write_bytes((Path("/proc") / name).read_bytes())
for path in (Path("/proc/config.gz"), Path("/boot/config-" + subprocess.check_output(["uname", "-r"]).decode().strip())):
    if path.is_file():
        shutil.copyfile(path, dest / path.name)
reserved = Path("/sys/firmware/devicetree/base/reserved-memory")
tree = {}
if reserved.is_dir():
    for path in sorted(reserved.rglob("*")):
        if path.is_file():
            raw = path.read_bytes()
            assert len(raw) < 65536 and len(tree) < 256
            tree[str(path.relative_to(reserved))] = dict(hex=raw.hex(), bytes=len(raw))
(dest / "reserved-memory.json").write_text(json.dumps(tree, indent=2) + "\n")
module = dest / "module-path.stdout.txt"
if module.is_file():
    path = Path(module.read_text().strip())
    if path.is_file() and path.name.startswith("amvx.ko"):
        assert path.stat().st_size < 32 * 1024 * 1024
        shutil.copyfile(path, dest / path.name)
(dest / "audit.json").write_text(json.dumps(dict(read_only=True, commands=records,
    reserved_properties=len(tree), device_initialized=False), indent=2) + "\n")
files = sorted(p for p in dest.iterdir() if p.is_file())
(dest / "files.sha256").write_text("".join(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name + "\n" for p in files))
print("Read-only MVX/kernel memory identity audit saved", dest)

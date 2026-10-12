#!/bin/sh
set -eu
work=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
run="$work/run-manager"
test ! -e "$run"
mkdir "$run"
cp "$0" "$run/runner.sh"
python3 "$work/board_application_preflight.py" "$run/preflight.json"
python3 - "$work" "$run" <<'PY'
import pathlib,sys,json,hashlib
w,r=map(pathlib.Path,sys.argv[1:]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();b=json.loads((w/'build-result.json').read_text());p=json.loads((r/'preflight.json').read_text())
assert p['fpga_state']=='operating' and p['SDK_packages']==['customop arm64 3.39.0','icraft arm64 3.39.0']
assert next(x['sha256'] for x in p['boot_files'] if x['name']=='BOOT.BIN')=='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
assert sha(w/'pose_plddr_manager_check')==b['binary_sha256']
for name,expected in b['libraries'].items():assert sha(pathlib.Path('/usr/lib/aarch64-linux-gnu')/name)==expected
for rel,expected in b['headers_normalized_sha256'].items():assert hashlib.sha256((pathlib.Path('/usr/include')/rel).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==expected
assert not any(line.split()[1].startswith('pose_') for line in p['processes'].splitlines()[1:] if len(line.split())>=2)
PY
dmesg > "$run/dmesg.before.log"
for n in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$n" > "$run/before.$n"; done
ldd "$work/pose_plddr_manager_check" > "$run/ldd.txt"
if grep -q 'not found' "$run/ldd.txt"; then exit 1; fi
set +e
timeout --signal=TERM --kill-after=5s 30s "$work/pose_plddr_manager_check" "$run/results" --allow-device-init > "$run/stdout.log" 2> "$run/stderr.log"
code=$?
set -e
printf '%s\n' "$code" > "$run/exit.txt"
dmesg > "$run/dmesg.after.log"
for n in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$n" > "$run/after.$n"; done
ps -eo pid,comm,args > "$run/final.processes"
ss -ltnp > "$run/final.ports"
cd "$run"
find . -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256
exit "$code"

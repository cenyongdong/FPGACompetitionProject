#!/bin/sh
set -eu
cd /tmp/pose-producer-deployment-20261011-r3
test ! -e run-apply
mkdir run-apply
run="$PWD/run-apply"
sha256sum -c files.sha256 > "$run/package-check.log"
graph=/tmp/pose-read-phase-20261011-r3/package/graph/piw24_ZG.json
raw=/tmp/pose-read-phase-20261011-r3/package/graph/piw24_ZG.raw
# Paths/identities must match the approved retained model; no model copies or edits.
python3 - "$graph" "$raw" <<'PY'
import sys,pathlib,json,hashlib
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert sha('/tmp/pose-read-phase-20261011-r3/package/manifest.json')=='87a205662ad7c90749b172ea54dbc15035147a32afa336f50a2166fcca2c39e7'
assert sha(sys.argv[1])=='75ffdc37b93dcb4913678991d6e7cf5cd0ab09c59653224d07c7434345acb8a0'
assert sha(sys.argv[2])=='3991a679282a4c6b014aece59b717910bc53fd14e67c0fac5fb9f93d4ae054d3'
PY
python3 board_application_preflight.py "$run/preflight.json"
python3 - "$run/preflight.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]));assert p['fpga_state']=='operating' and p['SDK_packages']==['customop arm64 3.39.0','icraft arm64 3.39.0']
assert next(f['sha256'] for f in p['boot_files'] if f['name']=='BOOT.BIN')=='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
assert p['libraries']=={'libicraft_hostbackend.so':'d0fbf6c81e5b57b4a908f11aad27571b8f2e68a3ede7ba33c9a4f783ba266130','libicraft_zg330backend.so':'592ad913737a6d661ab9d913ff16617c8fb6bf65cc0dc8929c6886303c498a57','libicraft_xrt.so':'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96'}
assert not any(line.split()[1].startswith('pose_') for line in p['processes'].splitlines()[1:] if len(line.split())>1)
PY
ldd pose_producer_deployment_log > "$run/ldd.txt"
if grep -q 'not found' "$run/ldd.txt"; then exit 1; fi
dmesg > "$run/dmesg.before.log"
for n in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$n" > "$run/before.$n"; done
mkdir "$run/work"
cd "$run/work"
set +e
timeout --signal=TERM --kill-after=5s 300s /tmp/pose-producer-deployment-20261011-r3/pose_producer_deployment_log "$graph" "$raw" "$run/results" --allow-device-init > "$run/stdout.log" 2> "$run/stderr.log"
code=$?
set -e
printf '%s\n' "$code" > "$run/exit.txt"
dmesg > "$run/dmesg.after.log"
for n in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$n" > "$run/after.$n"; done
ps -eo pid,comm,args > "$run/processes.txt"
ss -ltnp > "$run/ports.txt"
cd "$run"
find . -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256
cd ..
tar -cf return-apply.tar run-apply
sha256sum return-apply.tar
printf 'Official SDK deployment log exit=%s; no forward or automatic retry.\n' "$code"
exit "$code"

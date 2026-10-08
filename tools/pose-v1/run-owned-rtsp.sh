#!/bin/sh
set -eu
cd "$(dirname "$0")"
test ! -e run-owned
mkdir run-owned
sha256sum -c files.sha256 > run-owned/package-check.log
python3 board_application_preflight.py run-owned/preflight.json
python3 - <<'PY'
import json
a=json.load(open('baseline-preflight.json'));b=json.load(open('run-owned/preflight.json'))
assert all(a[k]==b[k] for k in ('boot_files','libraries','SDK_packages','fpga_state'))
PY
dmesg > run-owned/dmesg.before.log
free -m > run-owned/memory.before.txt
ss -ltnp > run-owned/listeners.before.txt
cp pose_access_unit_selftest pose_owned_rtsp_check run-owned/
set +e
timeout --signal=TERM --kill-after=2s 10s ./pose_access_unit_selftest > run-owned/host.stdout.log 2> run-owned/host.stderr.log
code=$?
printf '%s\n' "$code" > run-owned/host.exit.txt
if [ "$code" -eq 0 ]; then
    timeout --signal=TERM --kill-after=2s 95s ./pose_owned_rtsp_check --allow-network-replay . run-owned/results > run-owned/stdout.log 2> run-owned/stderr.log
    code=$?
fi
set -e
printf '%s\n' "$code" > run-owned/exit.txt
dmesg > run-owned/dmesg.after.log
free -m > run-owned/memory.after.txt
ss -ltnp > run-owned/listeners.after.txt
find run-owned -type f ! -name files.sha256 -exec sha256sum '{}' \; > run-owned/files.sha256
printf 'Owned AU gate exit=%s; preserve evidence; no automatic retry.\n' "$code"
exit "$code"

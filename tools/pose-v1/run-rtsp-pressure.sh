#!/bin/sh
set -eu
cd "$(dirname "$0")"
test ! -e run-pressure
mkdir run-pressure
sha256sum -c files.sha256 > run-pressure/package-check.log
python3 board_application_preflight.py run-pressure/preflight.json
dmesg > run-pressure/dmesg.before.log
ss -ltnp > run-pressure/listeners.before.txt
free -m > run-pressure/memory.before.txt
cp pose_rtsp_pressure_check run-pressure/
set +e
timeout --signal=TERM --kill-after=2s 23s ./pose_rtsp_pressure_check --allow-network-pressure-test . run-pressure/results > run-pressure/stdout.log 2> run-pressure/stderr.log &
job=$!
tries=0
while test "$tries" -lt 80; do
    if grep -q '"event":"ready"' run-pressure/results/network/events.jsonl 2>/dev/null; then printf 'PRESSURE_READY\n'; break; fi
    if ! kill -0 "$job" 2>/dev/null; then break; fi
    tries=$((tries+1))
    sleep 0.1
done
wait "$job"
code=$?
set -e
printf '%s\n' "$code" > run-pressure/exit.txt
dmesg > run-pressure/dmesg.after.log
ss -ltnp > run-pressure/listeners.after.txt
free -m > run-pressure/memory.after.txt
find run-pressure -type f ! -name files.sha256 -exec sha256sum '{}' \; > run-pressure/files.sha256
printf 'Pressure program exit=%s; intentional rejection requires full review; no retry.\n' "$code"
exit 0

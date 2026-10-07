#!/bin/sh
set -eu
cd "$(dirname "$0")"
test ! -e run-replay
mkdir run-replay
sha256sum -c files.sha256 > run-replay/package-check.log
python3 board_application_preflight.py run-replay/preflight.json
dmesg > run-replay/dmesg.before.log
free -m > run-replay/memory.before.txt
ss -ltnp > run-replay/listeners.before.txt
set +e
timeout --signal=TERM --kill-after=2s 63s ./pose_rtsp_replay_check --allow-network-replay video.h264 index.tsv run-replay/results > run-replay/stdout.log 2> run-replay/stderr.log &
job=$!
tries=0
while [ "$tries" -lt 50 ]; do
    if grep -q '^READY ' run-replay/stdout.log; then cat run-replay/stdout.log; break; fi
    if ! kill -0 "$job" 2>/dev/null; then break; fi
    tries=$((tries+1))
    sleep 0.1
done
wait "$job"
code=$?
set -e
printf '%s\n' "$code" > run-replay/exit.txt
dmesg > run-replay/dmesg.after.log
free -m > run-replay/memory.after.txt
ss -ltnp > run-replay/listeners.after.txt
find run-replay -type f ! -name files.sha256 -exec sha256sum '{}' \; > run-replay/files.sha256
printf 'RTSP replay exit=%s; preserve logs, no automatic retry.\n' "$code"
exit "$code"

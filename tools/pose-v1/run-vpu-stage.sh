#!/bin/sh
# Run inside a new isolated board directory; never source into login shell.
set -eu
stage=${1:?negotiate or encode}
case "$stage" in negotiate|encode) ;; *) exit 2 ;; esac
cd "$(dirname "$0")"
test ! -e "run-$stage"
mkdir "run-$stage"
sha256sum -c files.sha256 > "run-$stage/package-check.log"
python3 board_application_preflight.py "run-$stage/preflight.json"
dmesg > "run-$stage/dmesg.before.log"
free -m > "run-$stage/memory.before.txt"
set +e
timeout --signal=TERM --kill-after=3s 30s ./pose_vpu_encode_check "$stage" --allow-vpu-stream frames.nv12 "run-$stage/results" > "run-$stage/stdout.log" 2> "run-$stage/stderr.log"
code=$?
set -e
printf '%s\n' "$code" > "run-$stage/exit.txt"
dmesg > "run-$stage/dmesg.after.log"
free -m > "run-$stage/memory.after.txt"
find "run-$stage" -type f ! -name files.sha256 -exec sha256sum '{}' \; > "run-$stage/files.sha256"
printf 'VPU %s exit=%s; preserve results, no automatic retry.\n' "$stage" "$code"
exit "$code"

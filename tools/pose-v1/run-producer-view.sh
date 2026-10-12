#!/bin/sh
set -eu
cd /tmp/pose-producer-contract-20261011-r2
test ! -e run-offline
mkdir run-offline
sha256sum -c files.sha256 > run-offline/package-check.log
python3 - <<'PY'
import pathlib,json,hashlib
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
b=json.load(open('build-result.json'))
assert sha('pose_producer_view_audit')==b['program_sha256'] and sha('piw24_ZG.json')==b['graph_sha256']
assert sha('/usr/lib/aarch64-linux-gnu/libicraft_xir.so')==b['XIR_library_sha256']
PY
ldd pose_producer_view_audit > run-offline/ldd.txt
if grep -E -q 'not found|libicraft_xrt|backend|libaxizg' run-offline/ldd.txt; then exit 1; fi
dmesg > run-offline/dmesg.before.log
set +e
timeout --signal=TERM --kill-after=5s 10s ./pose_producer_view_audit piw24_ZG.json > run-offline/views.json 2> run-offline/stderr.log
code=$?
set -e
printf '%s\n' "$code" > run-offline/exit.txt
dmesg > run-offline/dmesg.after.log
ps -eo pid,comm,args > run-offline/processes.txt
cd run-offline
find . -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256
cd ..
tar -cf return-offline.tar run-offline
sha256sum return-offline.tar
printf 'Public XIR offline view inspection exit=%s; no model/device execution.\n' "$code"
exit "$code"

#!/bin/sh
set -eu
cd /tmp/pose-producer-reference-20261011-r2
test ! -e run-raw
mkdir run-raw
sha256sum -c files.sha256 > run-raw/package-check.log
python3 - <<'PY'
import pathlib,json,hashlib
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
b=json.load(open('build-result.json'))
assert sha('pose_producer_raw_audit')==b['program_sha256']
assert sha('/usr/lib/aarch64-linux-gnu/libicraft_xir.so')==b['XIR_library_sha256']
for n,x in b['models'].items():assert sha('models/'+n)==x['sha256']
PY
ldd pose_producer_raw_audit > run-raw/ldd.txt
if grep -E -q 'not found|libicraft_xrt|backend|libaxizg' run-raw/ldd.txt; then exit 1; fi
dmesg > run-raw/dmesg.before.log
cat /proc/meminfo > run-raw/memory.before.txt
set +e
timeout --signal=TERM --kill-after=5s 30s ./pose_producer_raw_audit models run-raw/parameters > run-raw/parameters.jsonl 2> run-raw/stderr.log
code=$?
set -e
printf '%s\n' "$code" > run-raw/exit.txt
dmesg > run-raw/dmesg.after.log
cat /proc/meminfo > run-raw/memory.after.txt
ps -eo pid,comm,args > run-raw/processes.txt
cd run-raw
find . -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256
cd ..
tar -cf return-raw.tar run-raw
sha256sum return-raw.tar
printf 'Public RAW extraction exit=%s; no Device/Session/NPU.\n' "$code"
exit "$code"

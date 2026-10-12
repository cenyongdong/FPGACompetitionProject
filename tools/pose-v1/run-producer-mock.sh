#!/bin/sh
set -eu
cd /tmp/pose-producer-reference-20261011-r2/mock
test ! -e run-mock
mkdir run-mock
sha256sum -c files.sha256 > run-mock/package-check.log
python3 - <<'PY'
import pathlib,json,hashlib
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
b=json.load(open('build-result.json'));raw=json.load(open('../build-result.json'))
assert sha('pose_producer_mock_contract')==b['program_sha256'] and b['URL']=='mock://zg330'
for n,h in b['libraries'].items():assert sha('/usr/lib/aarch64-linux-gnu/'+n)==h
for n in ('piw24_ZG.json','piw24_ZG.raw'):assert sha('../models/'+n)==raw['models'][n]['sha256']
PY
dmesg > run-mock/dmesg.before.log
ldd pose_producer_mock_contract > run-mock/ldd.txt
test ! -e .icraft
set +e
timeout --signal=TERM --kill-after=5s 30s ./pose_producer_mock_contract ../models/piw24_ZG.json ../models/piw24_ZG.raw run-mock/results > run-mock/stdout.log 2> run-mock/stderr.log
code=$?
set -e
printf '%s\n' "$code" > run-mock/exit.txt
if test -d .icraft; then cp -r .icraft run-mock/sdk-logs; fi
dmesg > run-mock/dmesg.after.log
ps -eo pid,comm,args > run-mock/processes.txt
cat /proc/meminfo > run-mock/memory.after.txt
cd run-mock
find . -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256
cd ..
tar -cf return-mock.tar run-mock
sha256sum return-mock.tar
printf 'Mock-only deployment exit=%s; no physical device or forward.\n' "$code"
exit "$code"

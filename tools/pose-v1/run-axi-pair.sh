#!/bin/sh
set -eu
mode=${1:?host/copy/read/copy-vpu/read-vpu}
case "$mode" in host) previous=none; budget=30;; copy) previous=host; budget=30;; read) previous=copy; budget=30;; copy-vpu) previous=read; budget=180;; read-vpu) previous=copy-vpu; budget=180;; *) exit 2;; esac
work=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$work"
test ! -e "run-$mode"
mkdir "run-$mode"
run="$work/run-$mode"
cp "$0" "$run/executed-runner.sh"
sha256sum -c files.sha256 > "$run/package-check.log"
python3 - "$work" "$previous" <<'PY'
import pathlib,json,hashlib,sys
w=pathlib.Path(sys.argv[1]);previous=sys.argv[2];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((w/'package/manifest.json').read_text());b=json.loads((w/'build-result.json').read_text())
assert sha(w/'package/manifest.json')==b['manifest_sha256']
assert sha(w/'package/graph/piw24_ZG.json')==m['graph_sha256']
for n,h in b['programs'].items():assert sha(w/n)==h
for n,h in m['libraries'].items():assert sha(pathlib.Path('/usr/lib/aarch64-linux-gnu')/n)==h
for n,h in m['sdk_headers_normalized_sha256'].items():assert hashlib.sha256((pathlib.Path('/usr/include')/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h
if previous!='none':
    gate=json.loads((w/('review-'+previous+'.json')).read_text());assert gate['status']=='passed' and gate['manifest_sha256']==b['manifest_sha256'] and gate['stage']==previous
PY
python3 board_application_preflight.py "$run/preflight.json"
python3 - "$run/preflight.json" <<'PY'
import sys,json
p=json.load(open(sys.argv[1]));assert p['fpga_state']=='operating' and p['SDK_packages']==['customop arm64 3.39.0','icraft arm64 3.39.0']
assert next(f['sha256'] for f in p['boot_files'] if f['name']=='BOOT.BIN')=='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
assert not any(line.split()[1].startswith('pose_') for line in p['processes'].splitlines()[1:] if len(line.split())>=2)
PY
dmesg > "$run/dmesg.before.log"
for n in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$n" > "$run/before.$n"; done
if test "$mode" = host; then
    set -- "$work/pose_axi_pair_host_check" "$work/package/graph/piw24_ZG.json"
else
    set -- "$work/pose_axi_pair_check" "$mode" "$work/package/graph/piw24_ZG.json" "$run/results" --allow-device-init
    case "$mode" in *-vpu) set -- "$@" --allow-vpu-stream;; esac
fi
ldd "$1" > "$run/ldd.txt"
if grep -q 'not found' "$run/ldd.txt"; then exit 1; fi
printf '%s\n' "$@" > "$run/command.argv.txt"
set +e
timeout --signal=TERM --kill-after=5s "${budget}s" "$@" > "$run/stdout.log" 2> "$run/stderr.log"
code=$?
set -e
printf '%s\n' "$code" > "$run/exit.txt"
dmesg > "$run/dmesg.after.log"
for n in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$n" > "$run/after.$n"; done
ps -eo pid,comm,args > "$run/final.processes"
ss -ltnp > "$run/final.ports"
cd "$run"
find . -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256
cd "$work"
tar -cf "return-$mode.tar" "run-$mode"
sha256sum "return-$mode.tar"
printf 'AXI pair %s exit=%s; preserve; no automatic retry.\n' "$mode" "$code"
exit "$code"

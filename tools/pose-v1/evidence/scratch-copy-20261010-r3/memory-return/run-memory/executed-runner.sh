#!/bin/sh
set -eu
mode=${1:?contracts / memory / vpu}
case "$mode" in contracts) previous=baseline; seconds=10;; memory) previous=contracts; seconds=30;; vpu) previous=memory; seconds=180;; *) exit 2;; esac
work=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
run="$work/run-$mode"
test ! -e "$run"
mkdir "$run"
cp "$0" "$run/executed-runner.sh"
cd "$work/package"
sha256sum -c files.sha256 > "$run/package-check.log"
python3 - "$work" "$run" "$mode" "$previous" <<'PY'
import sys,pathlib,json,hashlib,shutil
work,run=map(pathlib.Path,sys.argv[1:3]);mode,previous=sys.argv[3:5]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((work/'package/manifest.json').read_text());b=json.loads((work/'build-result.json').read_text());gate=work/'gates'/(previous+'.acceptance.json');g=json.loads(gate.read_text())
assert b['package_manifest_sha256']==sha(work/'package/manifest.json')==g['package_manifest_sha256']
assert b['scratch_binary_sha256']==sha(work/'pose_scratch_copy_check')==g['scratch_binary_sha256']
assert b['scratch_selftest_sha256']==sha(work/'pose_scratch_copy_selftest')
assert g['stage']==previous and g['status']==('scratch_baseline_Host107_reused_exact_main_and_payload' if previous=='baseline' else 'scratch_stage_passed')
assert b['binary_sha256']==sha(work/'pose_live_pipeline_check')
assert sha(pathlib.Path('/usr/lib/aarch64-linux-gnu/libaxizg330aiu.so'))=='d55e48873da61314da712c584e62f8257f63794ecca481e64868361ee5fc7178'
headers={k:hashlib.sha256((pathlib.Path('/usr/include')/k).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for k in m['sdk_headers_normalized_sha256']};assert headers==m['sdk_headers_normalized_sha256']
shutil.copyfile(gate,run/'previous-acceptance.json');(run/'identity.json').write_text(json.dumps(dict(mode=mode,manifest_sha256=b['package_manifest_sha256'],scratch_binary_sha256=b['scratch_binary_sha256'],headers=len(headers)))+'\n')
PY
cd "$work"
python3 board_application_preflight.py "$run/preflight.json"
python3 - "$run/preflight.json" <<'PY'
import sys,json
p=json.load(open(sys.argv[1]));assert p['fpga_state']=='operating' and p['SDK_packages']==['customop arm64 3.39.0','icraft arm64 3.39.0']
assert next(f['sha256'] for f in p['boot_files'] if f['name']=='BOOT.BIN')=='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
assert p['libraries']=={'libicraft_hostbackend.so':'d0fbf6c81e5b57b4a908f11aad27571b8f2e68a3ede7ba33c9a4f783ba266130','libicraft_zg330backend.so':'592ad913737a6d661ab9d913ff16617c8fb6bf65cc0dc8929c6886303c498a57','libicraft_xrt.so':'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96'}
PY
dmesg > "$run/dmesg.before.log"
for n in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$n" > "$run/before.$n"; done
if test "$mode" = contracts; then
    cp "$work/pose_scratch_copy_selftest" "$run/pose_scratch_copy_selftest"
    set -- "$work/pose_scratch_copy_selftest" "$run/results"
else
    cp "$work/pose_scratch_copy_check" "$run/pose_scratch_copy_check"
    ldd "$work/pose_scratch_copy_check" > "$run/ldd.txt"
    if grep -q 'not found' "$run/ldd.txt"; then exit 1; fi
    set -- "$work/pose_scratch_copy_check" "$mode" "$run/results" --allow-device-init
    if test "$mode" = vpu; then set -- "$@" --allow-vpu-stream; fi
fi
printf '%s\n' "$@" > "$run/command.argv.txt"
set +e
timeout --signal=TERM --kill-after=5s "${seconds}s" "$@" > "$run/stdout.log" 2> "$run/stderr.log"
code=$?
set -e
printf '%s\n' "$code" > "$run/exit.txt"
dmesg > "$run/dmesg.after.log"
for n in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$n" > "$run/after.$n"; done
ps -eo pid,comm,args > "$run/final.processes"
ss -ltnp > "$run/final.ports"
cd "$run"
find . -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256
printf 'Scratch %s exit=%s; preserve %s; no automatic retry.\n' "$mode" "$code" "$run"
exit "$code"

#!/bin/sh
set -eu
mode=${1:?contracts / dynamic / vpu}
case "$mode" in contracts) previous=baseline; seconds=10;; dynamic) previous=contracts; seconds=30;; vpu) previous=dynamic; seconds=180;; *) exit 2;; esac
work=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
run="$work/run-$mode"
test ! -e "$run"
mkdir "$run"
cp "$0" "$run/executed-runner.sh"
cd "$work/package"
sha256sum -c files.sha256 > "$run/package-check.log"
python3 - "$work" "$run" "$previous" <<'PY'
import sys,pathlib,json,hashlib,shutil
w,r=map(pathlib.Path,sys.argv[1:3]);previous=sys.argv[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((w/'package/manifest.json').read_text());b=json.loads((w/'build-result.json').read_text());gate=w/'gates'/(previous+'.acceptance.json');g=json.loads(gate.read_text())
assert b['package_manifest_sha256']==sha(w/'package/manifest.json')==g['package_manifest_sha256']
assert b['position_binary_sha256']==sha(w/'pose_position_scratch_check')==g['position_binary_sha256']
assert b['position_selftest_sha256']==sha(w/'pose_plddr_position_selftest')
assert b['typed_selftest_sha256']==sha(w/'pose_typed_scratch_selftest')
assert sha(w/'manager.acceptance.json')==m['plddr_position']['manager_audit_sha256']
assert g['stage']==previous and g['status']==('position_baseline_exact_main_Host107_reused' if previous=='baseline' else 'position_stage_passed')
assert b['binary_sha256']==sha(w/'pose_live_pipeline_check')
assert sha(pathlib.Path('/usr/lib/aarch64-linux-gnu/libaxizg330aiu.so'))=='d55e48873da61314da712c584e62f8257f63794ecca481e64868361ee5fc7178'
for rel,expected in m['sdk_headers_normalized_sha256'].items():assert hashlib.sha256((pathlib.Path('/usr/include')/rel).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==expected
shutil.copyfile(gate,r/'previous-acceptance.json')
PY
cd "$work"
python3 board_application_preflight.py "$run/preflight.json"
python3 - "$run/preflight.json" <<'PY'
import sys,json
p=json.load(open(sys.argv[1]));assert p['fpga_state']=='operating' and p['SDK_packages']==['customop arm64 3.39.0','icraft arm64 3.39.0']
assert next(f['sha256'] for f in p['boot_files'] if f['name']=='BOOT.BIN')=='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
assert p['libraries']=={'libicraft_hostbackend.so':'d0fbf6c81e5b57b4a908f11aad27571b8f2e68a3ede7ba33c9a4f783ba266130','libicraft_zg330backend.so':'592ad913737a6d661ab9d913ff16617c8fb6bf65cc0dc8929c6886303c498a57','libicraft_xrt.so':'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96'}
assert not any(line.split()[1].startswith('pose_') for line in p['processes'].splitlines()[1:] if len(line.split())>=2)
PY
dmesg > "$run/dmesg.before.log"
for n in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$n" > "$run/before.$n"; done
if test "$mode" = contracts; then
    cp "$work/pose_plddr_position_selftest" "$run/pose_plddr_position_selftest"
    set +e
    timeout --signal=TERM --kill-after=5s 10s "$work/pose_plddr_position_selftest" > "$run/position.stdout.json" 2> "$run/position.stderr.log"
    code=$?
    set -e
    printf '%s\n' "$code" > "$run/position.exit.txt"
    if test "$code" = 0; then
        cp "$work/pose_typed_scratch_selftest" "$run/pose_typed_scratch_selftest"
        set -- "$work/pose_typed_scratch_selftest" "$run/results"
    else set -- false; fi
else
    cp "$work/pose_position_scratch_check" "$run/pose_position_scratch_check"
    ldd "$work/pose_position_scratch_check" > "$run/ldd.txt"
    if grep -q 'not found' "$run/ldd.txt"; then exit 1; fi
    set -- "$work/pose_position_scratch_check" "$mode" "$work/package/graph/piw24_ZG.json" "$run/results" --allow-device-init
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
printf 'Position %s exit=%s; preserve %s; no automatic retry.\n' "$mode" "$code" "$run"
exit "$code"

#!/bin/sh
set -eu
stage=${1:?contracts / picture}
case "$stage" in contracts) previous=baseline; seconds=10;; picture) previous=contracts; seconds=180;; *) exit 2;; esac
work=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
run="$work/run-$stage"
test ! -e "$run"
mkdir "$run"
cp "$0" "$run/executed-runner.sh"
cd "$work/package"
sha256sum -c files.sha256 > "$run/package-check.log"
python3 - "$work" "$run" "$previous" <<'PY'
import sys,pathlib,json,hashlib,shutil
w,r=map(pathlib.Path,sys.argv[1:3]);previous=sys.argv[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((w/'package/manifest.json').read_text());b=json.loads((w/'build-result.json').read_text());gate=w/'gates'/(previous+'.acceptance.json');g=json.loads(gate.read_text())
assert b['package_manifest_sha256']==sha(w/'package/manifest.json')==g['package_manifest_sha256']
assert b['read_picture_binary_sha256']==sha(w/'pose_picture_read_check')==g['read_picture_binary_sha256']
assert g['stage']==previous and g['status']==('picture_baseline_exact_main_Host107_reused' if previous=='baseline' else 'picture_contracts_passed')
for file,key in [('pose_live_pipeline_check','binary_sha256'),('pose_picture_sequence_selftest','picture_sequence_selftest_sha256'),('pose_picture_source_selftest','picture_source_selftest_sha256'),('pose_resident_producer_selftest','resident_producer_selftest_sha256'),('pose_model_load_selftest','load_selftest_sha256'),('pose_model_only_selftest','model_only_selftest_sha256')]:assert sha(w/file)==b[key]
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
set +e
if test "$stage" = contracts; then
    code=0
    for name in pose_input_read_selftest pose_input_read_sdk_selftest pose_input_read_host_check pose_picture_source_selftest pose_picture_sequence_selftest pose_resident_producer_selftest pose_model_load_selftest pose_model_only_selftest; do
        cp "$work/$name" "$run/$name"
        case "$name" in *sdk_selftest) set -- "$work/$name" "$work/package/graph/piw24_ZG.json";; *host_check) set -- "$work/$name" --graph "$work/package/graph/piw24_ZG.json" --fixtures "$work/package/fixtures" --output "$run/host";; *producer*) set -- "$work/$name" "$run/producer-tests";; *only*) set -- "$work/$name" "$run/run-tests";; *) set -- "$work/$name";; esac
        budget=10
        if test "$name" = pose_input_read_host_check; then budget=300; fi
        timeout --signal=TERM --kill-after=5s "$budget" "$@" > "$run/$name.stdout.json" 2> "$run/$name.stderr.log"
        code=$?
        printf '%s\n' "$code" > "$run/$name.exit.txt"
        if test "$code" != 0; then break; fi
    done
else
    cp "$work/pose_picture_read_check" "$run/pose_picture_read_check"
    ldd "$work/pose_picture_read_check" > "$run/ldd.txt"
    if grep -q 'not found' "$run/ldd.txt"; then code=1; else
        timeout --signal=TERM --kill-after=5s 180s "$work/pose_picture_read_check" "$work/package" "$run/results" --finite-check --allow-device-init --allow-vpu-stream > "$run/stdout.log" 2> "$run/stderr.log"
        code=$?
    fi
fi
set -e
printf '%s\n' "$code" > "$run/exit.txt"
dmesg > "$run/dmesg.after.log"
for n in buddyinfo pagetypeinfo meminfo vmstat; do cat "/proc/$n" > "$run/after.$n"; done
ps -eo pid,comm,args > "$run/final.processes"
ss -ltnp > "$run/final.ports"
cd "$run"
find . -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256
printf 'Owned picture lifecycle %s exit=%s; preserve %s; no retry.\n' "$stage" "$code" "$run"
exit "$code"

#!/bin/sh
set -eu
stage=${1:?host-check / resident-three / resident-27}
# Host107 reparses the fixed graph per case: measured2.45s/parse on Lite.
# Restore the already used300s Host budget; combined remains bounded180s.
case "$stage" in host-check) previous=build; seconds=420;; resident-three) previous=host-check; seconds=180;; resident-27) previous=resident-three; seconds=180;; *) exit 2;; esac
work=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
package="$work/package"
run="$work/run-$stage"
test ! -e "$run"
mkdir "$run"
cp "$0" "$run/executed-runner.sh"
cd "$package"
sha256sum -c files.sha256 > "$run/package-check.log"
python3 - "$package" "$work" "$run" "$stage" "$previous" <<'PY'
import sys,pathlib,json,hashlib,shutil
package,work,run=map(pathlib.Path,sys.argv[1:4]);stage,previous=sys.argv[4:6]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((package/'manifest.json').read_text());b=json.loads((work/'build-result.json').read_text())
assert b['stage']=='compiled_not_executed' and b['package_manifest_sha256']==sha(package/'manifest.json')
assert b['binary_sha256']==sha(work/'pose_resident_check')
gate=work/'gates'/(previous+'.acceptance.json');g=json.loads(gate.read_text())
assert g['binary_sha256']==b['binary_sha256'] and g['package_manifest_sha256']==b['package_manifest_sha256']
assert g['stage']==previous and g['status']==('pipeline_build_reviewed' if previous=='build' else 'pipeline_stage_passed')
shutil.copyfile(gate,run/'previous-acceptance.json')
headers={name:hashlib.sha256((pathlib.Path('/usr/include')/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for name in m['sdk_headers_normalized_sha256']}
assert headers==m['sdk_headers_normalized_sha256']
assert sha(pathlib.Path('/usr/lib/aarch64-linux-gnu/libicraft_hostbackend.so'))==m['host_library_sha256']
assert sha(pathlib.Path('/usr/lib/aarch64-linux-gnu/libicraft_zg330backend.so'))==m['zg_library_sha256']
(run/'run-identity.json').write_text(json.dumps(dict(stage=stage,previous=previous,program_sha256=b['binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],sdk_headers_checked=len(headers)))+'\n')
PY
python3 board_application_preflight.py "$run/preflight.json"
python3 - "$run/preflight.json" <<'PY'
import sys,json
p=json.load(open(sys.argv[1]))
assert p['fpga_state']=='operating' and p['SDK_packages']==['customop arm64 3.39.0','icraft arm64 3.39.0']
assert next(f['sha256'] for f in p['boot_files'] if f['name']=='BOOT.BIN')=='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
assert p['libraries']=={'libicraft_hostbackend.so':'d0fbf6c81e5b57b4a908f11aad27571b8f2e68a3ede7ba33c9a4f783ba266130','libicraft_zg330backend.so':'592ad913737a6d661ab9d913ff16617c8fb6bf65cc0dc8929c6886303c498a57','libicraft_xrt.so':'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96'}
PY
ldd "$work/pose_resident_check" > "$run/ldd.txt"
if grep -q 'not found' "$run/ldd.txt"; then exit 1; fi
cp "$work/pose_resident_check" "$run/pose_resident_check"
dmesg > "$run/dmesg.before.log"
free -m > "$run/memory.before.txt"
set -- "$work/pose_resident_check" "$stage" "$package" "$run/results" --finite-check
if test "$stage" != host-check; then set -- "$@" --allow-device-init --allow-vpu-stream; fi
printf '%s\n' "$@" > "$run/command.argv.txt"
set +e
timeout --signal=TERM --kill-after=5s "${seconds}s" "$@" > "$run/stdout.log" 2> "$run/stderr.log"
code=$?
set -e
printf '%s\n' "$code" > "$run/exit.txt"
dmesg > "$run/dmesg.after.log"
free -m > "$run/memory.after.txt"
cd "$run"
find . -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256
printf 'F0 %s exit=%s; preserve %s, no automatic retry.\n' "$stage" "$code" "$run"
exit "$code"

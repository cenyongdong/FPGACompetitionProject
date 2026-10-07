#!/bin/sh
# User-run single stage. Preserves evidence, no automatic retry or reset.
set -eu
stage=${1:?Usage: sh package/run-mixed-validation.sh STAGE}
case "$stage" in
  host-check) previous=build; seconds=300; mode=host-check;;
  offline-check) previous=host-check; seconds=30; mode=offline-check;;
  memory-check) previous=offline-check; seconds=30; mode=memory-check;;
  apply-check) previous=memory-check; seconds=300; mode=apply-check;;
  mixed-one) previous=apply-check; seconds=180; mode=mixed;;
  mixed-three) previous=mixed-one; seconds=300; mode=mixed;;
  *) printf 'Unknown stage; stop.\n' >&2; exit 1;;
esac
package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
work=$(dirname -- "$package")
binary="$work/pose_mixed_check"
run="$work/run-$stage"
test -f "$binary"
test ! -e "$run"
mkdir "$run"
cd "$package"
sha256sum -c files.sha256 > "$run/package-check.log" 2>&1
command -v timeout > "$run/timeout-path.txt"
timeout --version > "$run/timeout-version.txt"
grep -q 'GNU coreutils' "$run/timeout-version.txt"
python3 - "$package" "$run" "$stage" "$previous" <<'PY'
import sys,pathlib,json,hashlib,subprocess,shutil
package,run=map(pathlib.Path,sys.argv[1:3]); stage,previous=sys.argv[3:5]; work=package.parent
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v): p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
m=load(package/'manifest.json'); b=load(work/'build-result.json')
identity=digest(package/'manifest.json'); binary=digest(work/'pose_mixed_check')
assert b['stage']=='compiled_not_executed' and b['package_manifest_sha256']==identity and b['binary_sha256']==binary,'Build identity differs'
gate=work/'gates'/(previous+'.acceptance.json'); approved=load(gate)
assert approved['package_manifest_sha256']==identity and approved['binary_sha256']==binary,'Prior gate identity differs'
if previous=='build': assert approved['status']=='mixed_build_reviewed'
else: assert approved['status']=='stage_engineering_review_passed' and approved['stage']==previous
shutil.copyfile(gate,run/'previous-acceptance.json')
versions={p:subprocess.check_output(['dpkg-query','-W','-f=${Version}',p],universal_newlines=True) for p in ['icraft:arm64','customop:arm64']}
assert all(v=='3.39.0' for v in versions.values()),'SDK versions differ'
headers={rel:hashlib.sha256((pathlib.Path('/usr/include')/rel).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for rel in m['sdk_headers_normalized_sha256']}
assert headers==m['sdk_headers_normalized_sha256'],'Board headers differ'
host=digest(pathlib.Path('/usr/lib/aarch64-linux-gnu/libicraft_hostbackend.so'))
zg=digest(pathlib.Path('/usr/lib/aarch64-linux-gnu/libicraft_zg330backend.so'))
assert host==m['host_library_sha256'] and zg==m['zg_library_sha256'],'Backend libraries differ'
save(run/'sdk-audit.json',dict(versions=versions,headers_normalized_sha256=headers,host_sha256=host,zg_sha256=zg))
save(run/'run-identity.json',dict(stage=stage,package_manifest_sha256=identity,binary_sha256=binary,previous_stage=previous))
PY
ldd "$binary" > "$run/ldd.txt" 2>&1
if grep -q 'not found' "$run/ldd.txt"; then
    printf 'Unresolved dependency; preserve logs and stop.\n' >&2; exit 1
fi
free -m > "$run/memory.before.txt"
ps -eo pid,comm,args > "$run/processes.before.txt"
dmesg > "$run/dmesg.before.log"
cp "$binary" "$run/pose_mixed_check"
set -- "$binary" "$mode" --output "$run/results"
case "$stage" in
  host-check) set -- "$@" --graph "$package/graph/piw24_ZG.json" --fixtures "$package/fixtures" --capture-host-content;;
  memory-check) set -- "$@" --allow-device-init;;
  *) set -- "$@" --graph "$package/graph/piw24_ZG.json" --raw "$package/graph/piw24_ZG.raw" --inputs "$package/inputs" --reference-tokens "$package/reference";;
esac
case "$stage" in
  apply-check) set -- "$@" --allow-device-init;;
  mixed-one) set -- "$@" --allow-device-init --cases one --capture-host-content;;
  mixed-three) set -- "$@" --allow-device-init --cases three --capture-host-content;;
esac
printf '%s\n' "$@" > "$run/command.argv.txt"
set +e
timeout --signal=TERM --kill-after=5s "${seconds}s" "$@" > "$run/run.stdout.log" 2> "$run/run.stderr.log"
rc=$?
set -e
printf '%s\n' "$rc" > "$run/exit.txt"
free -m > "$run/memory.after.txt"
dmesg > "$run/dmesg.after.log"
cd "$run"
find . -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256
printf 'Stage %s exit=%s; return %s for review before proceeding. No automatic retry.\n' "$stage" "$rc" "$run"
exit "$rc"

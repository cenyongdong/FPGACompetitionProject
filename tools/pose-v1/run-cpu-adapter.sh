#!/bin/sh
# User-run, one bounded CPU-only invocation. No SSH/Device::Open/SDK changes.
set -eu
package=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
work=$(dirname -- "$package")
binary="$work/pose_cpu_adapter_check"
run="$work/cpu-run-20261005"
test -f "$binary"
test ! -e "$run"
mkdir "$run"
cd "$package"
sha256sum -c files.sha256 > "$run/package-check.log" 2>&1
command -v timeout > "$run/timeout-path.txt"
timeout --version > "$run/timeout-version.txt"
dpkg-query -W icraft:arm64 customop:arm64 > "$run/package-versions.txt"
python3 - "$package" "$run" <<'PY'
import sys,pathlib,json,hashlib,subprocess
package=pathlib.Path(sys.argv[1]);run=pathlib.Path(sys.argv[2])
m=json.loads((package/'manifest.json').read_text())
versions={p:subprocess.check_output(['dpkg-query','-W','-f=${Version}',p],text=True) for p in ['icraft:arm64','customop:arm64']}
assert all(v=='3.39.0' for v in versions.values()),versions
headers={rel:hashlib.sha256((pathlib.Path('/usr/include')/rel).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for rel in m['sdk_headers_normalized_sha256']}
assert headers==m['sdk_headers_normalized_sha256'],'Board headers differ'
host=hashlib.sha256(pathlib.Path('/usr/lib/aarch64-linux-gnu/libicraft_hostbackend.so').read_bytes()).hexdigest()
assert host==m['host_library_sha256'],'Board Host library baseline differs'
(run/'sdk-audit.json').write_text(json.dumps({'versions':versions,'headers_normalized_sha256':headers,'host_sha256':host},indent=2)+'\n')
PY
sha256sum "$binary" "$package/piw24_ZG.json" /usr/lib/aarch64-linux-gnu/libicraft_hostbackend.so > "$run/input-identities.sha256"
ldd "$binary" > "$run/ldd.txt" 2>&1
if grep -q 'not found' "$run/ldd.txt"; then
    printf '%s\n' 'STOP: unresolved dependency, do not install or change LD_LIBRARY_PATH automatically.' >&2
    exit 1
fi
if grep -Ei 'libicraft_zg330backend|libaxi.*330|libsocket.*330' "$run/ldd.txt"; then
    printf '%s\n' 'STOP: unexpected ZG dependency in Host-only candidate.' >&2
    exit 1
fi
free -m > "$run/memory.before.txt"
dmesg | tail -n 80 > "$run/dmesg.before.log"
cp "$binary" "$run/pose_cpu_adapter_check"
set +e
timeout --signal=TERM --kill-after=5s 300s "$binary" \
    --graph "$package/piw24_ZG.json" --fixtures "$package/fixtures" --output "$run/results" \
    > "$run/run.stdout.log" 2> "$run/run.stderr.log"
rc=$?
set -e
printf '%s\n' "$rc" > "$run/exit.txt"
free -m > "$run/memory.after.txt"
dmesg | tail -n 80 > "$run/dmesg.after.log"
cd "$run"
find . -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256
printf 'CPU-only checker exit=%s; preserve and return %s. No automatic retry.\n' "$rc" "$run"
exit "$rc"

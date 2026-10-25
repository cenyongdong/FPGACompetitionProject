#!/usr/bin/env bash
# Existing offline toolchain only. Never installs firmware or connects a router.
set -euo pipefail
cd /work/nexmon
source setup_env.sh
project=${2:-patches/bcm4366c0/10_10_122_20/nexmon_tx_absolute_20261022}
source_dir=${1:-/out/derivative-source}
if [ ! -e "$project" ]; then
    cp -a "$source_dir" "$project"
else
    # Preserve valid objects; only changed derivative sources need recompilation.
    cp -au "$source_dir/." "$project/"
fi
cd "$project"
if [ -f /out/build.log ]; then
    mv /out/build.log "/out/build-previous-$(date +%Y%m%d-%H%M%S).log"
    cp log/linker.err /out/linker-previous.err
fi
set +e
make -j1 GIT_VERSION="${3:-piwtx-1613d5f-absolute}" > /out/build.log 2>&1
build_status=$?
set -e
cp log/linker.err /out/linker.err
if [ "$build_status" -ne 0 ]; then exit "$build_status"; fi
cp dhd.ko dlarray_4366c0.bin /out/
cp gen/patch.elf /out/tx-patch.elf
sha256sum /out/dhd.ko /out/dlarray_4366c0.bin > /out/SHA256SUMS
printf 'TX_OFFLINE_BUILD_COMPLETE=1\n'

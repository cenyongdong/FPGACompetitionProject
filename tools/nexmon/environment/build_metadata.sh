#!/usr/bin/env bash
# Isolated derivative of the existing, pinned Linux volume. No device access.
# First export base.asm and csi.asm from nexmon_csi to /out, then run
# prepare_metadata.py on the host to populate /out's two diagnostic sources.
set -euo pipefail
cd /work/nexmon
source setup_env.sh
task_parent=patches/bcm4366c0/10_10_122_20
test "$(git -C "$task_parent/nexmon_csi" rev-parse HEAD)" = 1232edf2cf1e7ae0561676c49e4dd4eb22c8a27e
if [[ ! -d "$task_parent/nexmon_metadata" ]]; then
    cp -a "$task_parent/nexmon_csi" "$task_parent/nexmon_metadata"
fi
cd "$task_parent/nexmon_metadata"
cp /out/csi_extractor.c src/
cp /out/metadata.ucode.patch src/csi.ucode.bcm4366c0.10_10_122_20.patch
# Upstream Makefile ignores patch failures. Apply it natively with strict exit
# status before make, retaining both the original disassembly and patch log.
cp gen/ucode.asm src/csi.ucode.bcm4366c0.10_10_122_20.asm
patch -p1 src/csi.ucode.bcm4366c0.10_10_122_20.asm \
    < src/csi.ucode.bcm4366c0.10_10_122_20.patch > /out/native-patch.log 2>&1
make -j1 > /out/build.log 2>&1
if find src -name '*.rej' -print | grep -q .; then
    echo 'Rejected microcode patch; do not deploy' >&2
    exit 3
fi
cp dhd.ko dlarray_4366c0.bin /out/
cp log/ass.log log/linker.err /out/
aarch64-linux-gnu-gcc -std=gnu11 -O2 -Wall -Wextra -Werror -static \
    -DNEXMON_DIAGNOSTIC_SIDECAR /kit/router/capture_udp5500.c \
    -o /out/capture-metadata-aarch64
sha256sum /out/dhd.ko /out/dlarray_4366c0.bin /out/capture-metadata-aarch64 > /out/SHA256SUMS

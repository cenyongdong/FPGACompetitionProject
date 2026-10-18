#!/usr/bin/env bash
# Run only inside the isolated task container; never invokes install-firmware.
set -euo pipefail
mkdir -p /work /out
if [[ "${NEXMON_PREPARED:-0}" != 1 ]]; then
    if [[ -e /work/nexmon ]]; then
        echo 'Existing build session: inspect it instead of overwriting' >&2
        exit 2
    fi
    cp -a /input/nexmon /work/nexmon
else
    test -f /work/nexmon/setup_env.sh
fi
cd /work/nexmon
git config --global --add safe.directory /work/nexmon
git config core.symlinks true
git config core.filemode true
# prepare-source.sh already materializes the sparse Linux tree with proper
# symlinks and executable bits. checkout-index -a would fetch excluded devices.
test "$(git rev-parse HEAD)" = 68720406f54ff16cad28fd3c51f2392aefad9fb7
if [[ ! -e patches/bcm4366c0/10_10_122_20/nexmon_csi ]]; then
    cp -a /input/nexmon_csi patches/bcm4366c0/10_10_122_20/nexmon_csi
fi
test "$(git -C patches/bcm4366c0/10_10_122_20/nexmon_csi rev-parse HEAD)" = 1232edf2cf1e7ae0561676c49e4dd4eb22c8a27e
git config --global --add safe.directory /work/nexmon/patches/bcm4366c0/10_10_122_20/nexmon_csi
source setup_env.sh
chmod +x buildtools/gcc-arm-none-eabi-5_4-2016q2-linux-x86/bin/*
chmod +x buildtools/gcc-arm-none-eabi-5_4-2016q2-linux-x86/lib/gcc/arm-none-eabi/5.4.1/cc1
chmod +x buildtools/gcc-arm-none-eabi-5_4-2016q2-linux-x86/lib/gcc/arm-none-eabi/5.4.1/collect2
chmod +x buildtools/scripts/*
"${CC}gcc" --version
# Build the radio-specific tools rather than extracting every supported firmware.
make -C buildtools -j2 flash_patch_extractor ucode_extractor \
    b43-v2/assembler/b43-asm.bin b43-v2/disassembler/b43-dasm
make -C firmwares/bcm4366c0/10_10_122_20 -j2
cd patches/bcm4366c0/10_10_122_20/nexmon_csi
# Upstream init creates log/gen directories without parallel ordering edges.
make -B -j1
if find src -name '*.rej' -print | grep -q .; then
    echo 'Microcode patch rejection: stop before packaging' >&2
    exit 3
fi
if grep -E 'FAILED|malformed patch' log/patch.log; then
    echo 'Microcode patch failed despite upstream ignored exit status' >&2
    exit 3
fi
cp dhd.ko dlarray_4366c0.bin /out/
make -C utils/makecsiparams
cp utils/makecsiparams/makecsiparams /out/makecsiparams-x86_64
cd "$NEXMON_ROOT/utilities/libnexio"
aarch64-linux-gnu-gcc -O2 -c libnexio.c -o libnexio.o -DBUILD_ON_RPI
aarch64-linux-gnu-ar rcs libnexio.a libnexio.o
cd ../nexutil
# A private generated compatibility include avoids changing official source.
printf 'typedef unsigned int uint;\n' > /work/compat_uint.h
mkdir -p /work/compat-include
printf '#include <argp.h>\n' > /work/compat-include/argp-extern.h
aarch64-linux-gnu-gcc -static -O2 -include /work/compat_uint.h \
    -o /out/nexutil-aarch64 nexutil.c bcmutils.c bcmwifi_channels.c b64-encode.c b64-decode.c \
    -DBUILD_ON_RPI -DVERSION='"prep-20261017"' -I/work/compat-include -I. -I./include -I../libnexio \
    -I../../patches/include -L../libnexio -lnexio
cd "$NEXMON_ROOT/patches/bcm4366c0/10_10_122_20/nexmon_csi/utils/makecsiparams"
aarch64-linux-gnu-gcc -static -O2 -I. -o /out/makecsiparams-aarch64 makecsiparams.c bcmwifi_channels.c
cd /out
file dhd.ko nexutil-aarch64 makecsiparams-aarch64 makecsiparams-x86_64
sha256sum dhd.ko dlarray_4366c0.bin nexutil-aarch64 makecsiparams-aarch64 makecsiparams-x86_64 > SHA256SUMS
echo 'OFFLINE_BUILD_COMPLETE=1'

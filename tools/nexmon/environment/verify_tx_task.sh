#!/usr/bin/env bash
set -euo pipefail
cd /work/nexmon
objdump_cmd=buildtools/gcc-arm-none-eabi-5_4-2016q2-linux-x86/bin/arm-none-eabi-objdump
project=${1:-patches/bcm4366c0/10_10_122_20/nexmon_tx_absolute_20261022}
"$objdump_cmd" -t "$project/gen/patch.elf" | awk '/\*UND\*/ {print; if ($NF != "ucode_compressed_bin" && $NF != "ucode_compressed_bin_len") unexpected++} END {print "UNEXPECTED_UNDEFINED_COUNT=" unexpected+0; exit (unexpected>0)}'
"$objdump_cmd" -d "$project/gen/patch.elf" | sed -n '/<piw_read_tsf>:/,+5p'
file /out/dhd.ko
grep -E 'error:|warning:' "$project/log/compiler.log" | head -n 12 || true

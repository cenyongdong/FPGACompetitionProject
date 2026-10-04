"""REVIEW CANDIDATE ONLY: one read at the SDK-declared FPGA version register.

Not executed during the boot/preprocess audit. Address mapping still requires
user approval; no SDK Open/reset/check, DMA, model, HDMI or configuration write.
Without the explicit flag this only prints the proposed operation.
"""
import argparse
import json
import mmap
import os
import struct
import time

BASE = 0x40000000
VERSION_OFFSET = 0x1C


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute-reviewed-read', action='store_true')
    args = parser.parse_args()
    proposal = {'scope': 'single read, no register writes', 'address_hex': hex(BASE + VERSION_OFFSET),
                'mapping_basis': 'reference ZG URL base plus Icraft 3.39.0 zg330_device.h FPGA_VERSION_REG',
                'executed': False, 'runtime_compatibility_proven': False}
    if not args.execute_reviewed_read:
        print(json.dumps(proposal))
        return
    start = time.monotonic_ns()
    fd = os.open('/dev/mem', os.O_RDONLY | os.O_SYNC)
    try:
        with mmap.mmap(fd, mmap.PAGESIZE, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ, offset=BASE) as region:
            data = region[VERSION_OFFSET:VERSION_OFFSET+4]
    finally:
        os.close(fd)
    proposal.update(executed=True, bytes_hex=data.hex(), value_le_hex=hex(struct.unpack('<I', data)[0]),
                    read_duration_ns=time.monotonic_ns()-start)
    print(json.dumps(proposal))


if __name__ == '__main__':
    main()

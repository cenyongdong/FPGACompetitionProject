"""Independently check the pinned upstream module's embedded firmware region."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('patched', type=Path)
    parser.add_argument('firmware', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise SystemExit('Refusing to overwrite an existing report')
    original, patched, firmware = (p.read_bytes() for p in
                                   (args.original, args.patched, args.firmware))
    offset, size = 0x4E798, 0x10F4CF
    expected = b'vermagic=4.1.27 SMP preempt mod_unload aarch64\x00'
    checks = dict(same_module_length=len(original) == len(patched),
                  firmware_length=len(firmware) == size,
                  firmware_embedded_exactly=patched[offset:offset + size] == firmware,
                  prefix_unchanged=original[:offset] == patched[:offset],
                  suffix_unchanged=original[offset + size:] == patched[offset + size:],
                  firmware_changed=original[offset:offset + size] != firmware,
                  elf64_aarch64=patched[:6] == b'\x7fELF\x02\x01'
                  and patched[18:20] == b'\xb7\x00',
                  expected_vermagic=expected in patched)
    result = dict(passed=all(checks.values()), hardware_test=False, checks=checks,
                  offset=offset, size=size, original_sha256=hashlib.sha256(original).hexdigest(),
                  patched_sha256=hashlib.sha256(patched).hexdigest(),
                  firmware_sha256=hashlib.sha256(firmware).hexdigest(),
                  limitation='Pinned repository module only; no compatibility claim for an arrived router')
    args.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

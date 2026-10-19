"""Read ELF64 module metadata and embedded firmware symbols without loading it."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


def inspect(path):
    data = Path(path).read_bytes()
    if data[:6] != b'\x7fELF\x02\x01':
        raise ValueError('Require little-endian ELF64')
    shoff = struct.unpack_from('<Q', data, 40)[0]
    entsize, count, names_index = struct.unpack_from('<HHH', data, 58)
    sections = [struct.unpack_from('<IIQQQQIIQQ', data, shoff + i * entsize) for i in range(count)]
    names_section = sections[names_index]
    names = data[names_section[4]:names_section[4] + names_section[5]]

    def cstr(table, offset):
        return table[offset:table.index(b'\0', offset)].decode('utf-8', errors='replace')

    section_names = [cstr(names, section[0]) for section in sections]
    metadata, firmware, undefined = [], [], []
    for name, section in zip(section_names, sections):
        raw = data[section[4]:section[4] + section[5]]
        if name == '.modinfo':
            metadata = [part.decode(errors='replace') for part in raw.split(b'\0') if part]
        if section[1] == 2:
            linked = sections[section[6]]
            strings = data[linked[4]:linked[4] + linked[5]]
            for start in range(0, len(raw), section[9]):
                string_offset, info, _, index, value, size = struct.unpack_from('<IBBHQQ', raw, start)
                symbol = cstr(strings, string_offset)
                if index == 0 and symbol:
                    undefined.append(symbol)
                if re.search(r'dlarray|dlimage|4366|rtecdc|firmware', symbol, re.I) and index < len(sections):
                    # SHT_NOBITS occupies memory, not file bytes (e.g. BSS).
                    offset = sections[index][4] + value if index and sections[index][1] != 8 else None
                    entry = dict(name=symbol, size=size, section=index, value=value, file_offset=offset)
                    if size and offset is not None:
                        entry['sha256'] = hashlib.sha256(data[offset:offset + size]).hexdigest()
                    firmware.append(entry)
    version_lines = [chunk.decode(errors='replace') for chunk in re.findall(rb'[\x20-\x7e]{12,}', data)
                     if b'10.10.122.20' in chunk or b'nexmon.org/csi' in chunk]
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                machine=struct.unpack_from('<H', data, 18)[0], modinfo=metadata,
                has_symbol_versions='__versions' in section_names,
                firmware_symbols=firmware, version_strings=version_lines,
                undefined_symbols=sorted(undefined))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('modules', nargs='+', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    arguments = parser.parse_args()
    results = [inspect(path) for path in arguments.modules]
    with arguments.report.open('x', encoding='utf-8') as output:
        json.dump(results, output, indent=2)
    for result in results:
        print(json.dumps({key: value for key, value in result.items()
                          if key not in ('undefined_symbols', 'modinfo')}, ensure_ascii=False))
        print(json.dumps([value for value in result['modinfo']
                          if value.startswith(('vermagic=', 'depends=', 'srcversion='))]))


if __name__ == '__main__':
    main()

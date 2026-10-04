"""Offline bind the chosen BOOT, its PL partition, board hashes and boot log."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def bit_payload(data):
    offset = 2 + struct.unpack_from('>H', data, 0)[0]
    if struct.unpack_from('>H', data, offset)[0] != 1:
        raise ValueError('Unexpected bit header')
    offset += 2
    fields = {}
    for tag in 'abcde':
        if data[offset:offset+1] != tag.encode():
            raise ValueError('Unexpected bit header field')
        offset += 1
        width = 4 if tag == 'e' else 2
        length = int.from_bytes(data[offset:offset+width], 'big')
        offset += width
        value = data[offset:offset+length]
        if len(value) != length:
            raise ValueError('Truncated bit payload')
        if tag == 'e':
            if offset + length != len(data):
                raise ValueError('Trailing bit data')
            return value, fields
        fields[tag] = value.rstrip(b'\0').decode('ascii', 'replace')
        offset += length
    raise ValueError('Missing bit payload')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', required=True, type=Path)
    parser.add_argument('--old-audit', required=True, type=Path)
    parser.add_argument('--new-audit', required=True, type=Path)
    parser.add_argument('--log', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Preserve prior audit evidence')
    boot = (args.source_dir / 'BOOT.bin').read_bytes()
    old = json.loads(args.old_audit.read_text(encoding='utf-8-sig'))
    new = json.loads(args.new_audit.read_text(encoding='utf-8-sig'))
    previous = {f['name']: f for f in old['audit']['boot_partition']['files']}
    current = {f['name']: f for f in new['audit']['boot_partition']['files']}
    log = args.log.read_text(encoding='utf-8-sig')
    first_partition = log[log.index('Partition is unencrypted'):log.index('Partition Load Success')]
    offset_matches = re.findall(r'Data word offset: 0x([0-9a-fA-F]+)', first_partition)
    length = int(re.search(r'Total Data word length: 0x([0-9a-fA-F]+)', first_partition).group(1), 16) * 4
    offset = int(offset_matches[-1], 16) * 4
    pl = boot[offset:offset+length]
    payload, header = bit_payload((args.source_dir / 'ai7030_top_disable_icap.bit').read_bytes())
    if len(pl) != length or len(pl) % 4:
        raise ValueError('PL partition bounds invalid')
    swapped = b''.join(pl[i:i+4][::-1] for i in range(0, len(pl), 4))
    decoded_prefix_match = len(swapped) >= len(payload) and swapped[:len(payload)] == payload
    result = {
        'scope': 'offline identity and read-only board audit; not hardware runtime acceptance',
        'source_dir': str(args.source_dir), 'source_boot_sha256': sha(boot),
        'board_boot_sha256': current['BOOT.BIN']['sha256'],
        'board_boot_matches_selected_source': current['BOOT.BIN']['sha256'] == sha(boot),
        'source_files': [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
                         for p in sorted(args.source_dir.iterdir()) if p.is_file()],
        'changes_from_previous_audit': [{'name': name, 'unchanged': name in previous and
                                       item['sha256'] == previous[name]['sha256']}
                                      for name, item in current.items()],
        'pl_partition_from_supplied_log': {'byte_offset': offset, 'bytes': length, 'sha256': sha(pl),
                                         'bit_header': header, 'source_payload_sha256': sha(payload),
                                         'payload_equal': pl == payload, 'word_swapped_payload_equal': swapped == payload,
                                         'word_swapped_source_prefix_equal': decoded_prefix_match,
                                         'trailing_partition_padding_bytes': len(swapped) - len(payload),
                                         'trailing_partition_padding_hex': swapped[len(payload):].hex(),
                                         'decoded_source_length_sha256': sha(swapped[:len(payload)])},
        'log_sha256': sha(args.log.read_bytes()),
        'log_fsbl_pl_download_success': 'Download the PL bitstream is done' in log,
        'log_linux_started': 'Starting kernel' in log and 'Mounted root' in log,
        'secondary_bitstream_load': 'not confirmed; filesystem error after uEnv import',
        'loadbit_command': next(line for line in current['UENV.TXT']['text'].splitlines() if line.startswith('loadbit=')),
        'runtime_compatibility_verified': False, 'hdmi_screen_verified': False,
    }
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'boot_match': result['board_boot_matches_selected_source'],
                      'pl_payload_equal': pl == payload, 'pl_word_swapped_equal': swapped == payload,
                      'pl_source_prefix_equal_after_word_swap': decoded_prefix_match,
                      'changes': [r['name'] for r in result['changes_from_previous_audit'] if not r['unchanged']]}))


if __name__ == '__main__':
    main()

"""Bounded classic-PCAP verifier for the pinned Nexmon CSI 18-byte header.

This module validates acquisition, not the model's 30-carrier preprocessing.
Packed AC PHY values are decoded as sign * mantissa * 2**exponent; no AGC
normalization or MATLAB int32 autoscaling is applied. Original PCAP is retained.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import struct

HEADER = struct.Struct('<HbB6sHHHH')


def unpack_acphy(words, nman=12, nexp=6):
    """BCM4366c0 format=1; format=0 (9,5) is reference-only BCM4358."""
    mask = (1 << (nman - 1)) - 1
    values = []
    for word in words:
        exponent = word & ((1 << nexp) - 1)
        if exponent & (1 << (nexp - 1)):
            exponent -= 1 << nexp
        real = (word >> (nexp + nman)) & mask
        imag = (word >> nexp) & mask
        if word & (1 << (nexp + 2 * nman - 1)):
            real = -real
        if word & (1 << (nexp + nman - 1)):
            imag = -imag
        values.append(complex(math.ldexp(real, exponent), math.ldexp(imag, exponent)))
    return values


def parse_payload(payload, nfft, profile='current18'):
    if len(payload) != HEADER.size + nfft * 4:
        raise ValueError('CSI payload length mismatch')
    magic, rssi, fc, mac, seq, config, chanspec, chip = HEADER.unpack_from(payload)
    if magic != 0x1111:
        raise ValueError('CSI magic mismatch')
    if profile == 'legacy18':
        if payload[:4] != b'\x11' * 4:
            raise ValueError('Legacy magic mismatch')
        rssi, fc = None, None
    elif profile != 'current18':
        raise ValueError('Unknown explicit header profile')
    # BCM4366's microcode stores ((stream << 3) | core) << 8 in
    # SHM(0x1640); its extractor copies csiconf without shifting it back.
    # Other supported headers use the low byte. Do not auto-guess per packet.
    if chip == 106:
        if config & 0xc0ff:
            raise ValueError('Invalid BCM4366 core/stream reserved bits')
        chain_config = config >> 8
    else:
        chain_config = config
    words = struct.unpack_from('<' + 'I' * nfft, payload, HEADER.size)
    return dict(mac=mac.hex(':'), sequence_control=seq, core=chain_config & 7,
                stream=(chain_config >> 3) & 7, core_config_raw=config,
                chanspec=chanspec, chip=chip,
                rssi=rssi, frame_control_low=fc, words=words)


def pcap_udp(path, max_packets=20000, max_bytes=32 * 1024 * 1024):
    path = Path(path)
    if path.stat().st_size > max_bytes:
        raise ValueError('PCAP exceeds byte budget')
    magics = {b'\xd4\xc3\xb2\xa1': ('<', 1e6), b'\xa1\xb2\xc3\xd4': ('>', 1e6),
              b'\x4d\x3c\xb2\xa1': ('<', 1e9), b'\xa1\xb2\x3c\x4d': ('>', 1e9)}
    with path.open('rb') as f:
        raw = f.read(24)
        if len(raw) != 24 or raw[:4] not in magics:
            raise ValueError('Only classic PCAP is supported; PCAPNG is not accepted')
        endian, scale = magics[raw[:4]]
        major, minor, _, _, snaplen, link = struct.unpack(endian + 'HHIIII', raw[4:])
        if (major, minor) != (2, 4) or link != 1:
            raise ValueError('Require PCAP 2.4 with Ethernet link type 1')
        count = 0
        previous = -math.inf
        while True:
            header = f.read(16)
            if not header:
                return
            count += 1
            if count > max_packets or len(header) != 16:
                raise ValueError('PCAP packet budget exceeded or truncated header')
            sec, sub, captured, original = struct.unpack(endian + 'IIII', header)
            if captured != original or captured > snaplen or captured > 65535:
                raise ValueError('Truncated or excessive captured frame')
            if sub >= scale:
                raise ValueError('Invalid PCAP timestamp fraction')
            timestamp = sec + sub / scale
            if timestamp < previous:
                raise ValueError('Capture timestamps move backwards')
            previous = timestamp
            frame = f.read(captured)
            if len(frame) != captured or captured < 14:
                raise ValueError('Truncated Ethernet frame')
            offset, ethertype = 14, struct.unpack_from('!H', frame, 12)[0]
            for _ in range(2):
                if ethertype not in (0x8100, 0x88a8):
                    break
                if len(frame) < offset + 4:
                    raise ValueError('Truncated VLAN header')
                ethertype = struct.unpack_from('!H', frame, offset + 2)[0]
                offset += 4
            if ethertype != 0x0800:
                continue
            ip = frame[offset:]
            if len(ip) < 20 or ip[0] >> 4 != 4:
                raise ValueError('Invalid IPv4 header')
            ihl, total = (ip[0] & 15) * 4, struct.unpack_from('!H', ip, 2)[0]
            if ihl < 20 or total < ihl or len(ip) < total:
                raise ValueError('Invalid IPv4 lengths')
            if ip[9] != 17:
                continue
            if struct.unpack_from('!H', ip, 6)[0] & 0x3fff:
                raise ValueError('Fragmented UDP is not supported')
            udp = ip[ihl:total]
            if len(udp) < 8:
                raise ValueError('Truncated UDP header')
            _, port, length, _ = struct.unpack_from('!HHHH', udp)
            if port != 5500:
                continue
            if length < 8 or length != len(udp):
                raise ValueError('Invalid UDP length')
            yield timestamp, udp[8:]


def verify(path, nfft, cores, stream, expected_chip, source_mac, profile='current18',
           min_groups=20, group_gap_ms=20.0):
    required = set(cores)
    if not required or len(required) != len(cores) or not required <= set(range(4)):
        raise ValueError('Require unique RX core IDs in 0..3')
    if nfft not in (64, 128, 256) or stream not in range(4):
        raise ValueError('Unsupported FFT or stream')
    counts = collections.Counter()
    groups = {}
    times = []
    chips = set()
    previous_time = None
    for timestamp, payload in pcap_udp(path):
        counts['csi_records'] += 1
        record = parse_payload(payload, nfft, profile)
        chips.add(record['chip'])
        if record['chip'] != expected_chip:
            raise ValueError('CSI chip marker mismatch')
        if record['mac'] != source_mac.lower():
            raise ValueError('Unexpected original transmitter MAC')
        if record['core'] not in required or record['stream'] != stream:
            raise ValueError('Unexpected core/stream; verify capture mask')
        values = unpack_acphy(record['words'])
        if not all(math.isfinite(v.real) and math.isfinite(v.imag) for v in values):
            raise ValueError('Non-finite decoded CSI')
        if not any(v != 0 for v in values):
            counts['all_zero_records'] += 1
        key = (record['mac'], record['sequence_control'], record['chanspec'], stream)
        group = groups.get(key)
        if group is None or (timestamp - group['start']) * 1000 > group_gap_ms:
            if group is not None and group['cores'] != required:
                counts['incomplete_groups'] += 1
            group = dict(start=timestamp, cores=set(), invalid=False, counted=False)
            groups[key] = group
        if record['core'] in group['cores']:
            counts['duplicate_core_records'] += 1
            group['invalid'] = True
        group['cores'].add(record['core'])
        if group['cores'] == required and not group['invalid'] and not group['counted']:
            counts['complete_groups'] += 1
            group['counted'] = True
            times.append(timestamp)
        previous_time = timestamp
    counts['incomplete_groups'] += sum(g['cores'] != required for g in groups.values())
    passed = (counts['complete_groups'] >= min_groups and not counts['incomplete_groups']
              and not counts['duplicate_core_records'] and not counts['all_zero_records'])
    span = times[-1] - times[0] if len(times) > 1 else 0
    return dict(schema=1, acquisition_pass=passed, hardware_test=False,
                input_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                profile=profile, nfft=nfft, selected_cores=cores, stream=stream,
                expected_chip=expected_chip, source_mac=source_mac, counts=dict(counts),
                group_gap_ms=group_gap_ms, min_groups=min_groups,
                complete_group_arrival_rate_hz=(len(times) - 1) / span if span else None,
                timestamp_basis='PCAP arrival time, not radio sampling time',
                limitation='No sequence continuity, cross-receiver sync or model accuracy claim')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcap', type=Path)
    parser.add_argument('--nfft', type=int, choices=[64, 128, 256], required=True)
    parser.add_argument('--cores', type=int, nargs='+', required=True)
    parser.add_argument('--stream', type=int, default=0)
    parser.add_argument('--expected-chip', type=lambda v: int(v, 0), required=True)
    parser.add_argument('--source-mac', required=True)
    parser.add_argument('--profile', choices=['current18', 'legacy18'], default='current18')
    parser.add_argument('--min-groups', type=int, default=20)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('Refusing to overwrite an existing report')
    try:
        result = verify(args.pcap, args.nfft, args.cores, args.stream,
                        args.expected_chip, args.source_mac, args.profile, args.min_groups)
    except (ValueError, OSError, struct.error) as error:
        result = dict(schema=1, acquisition_pass=False, error=str(error))
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['acquisition_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

"""Read independent NMD1/NMD2 diagnostics and unchanged CSI/5500.

Does not generate model input or relax the existing acquisition validator.
TID is an 802.11 sequence-space identifier, not a hardware queue index.
"""
import argparse
import collections
import csv
import json
from pathlib import Path
import struct


def packets(path):
    with path.open('rb') as f:
        yield from packets_stream(f)


def packets_stream(f):
    header = f.read(24)
    if len(header) != 24 or struct.unpack('<I', header[:4])[0] != 0xa1b2c3d4:
        raise ValueError('Expected little-endian microsecond PCAP')
    if struct.unpack('<I', header[20:24])[0] != 1:
        raise ValueError('Expected Ethernet')
    while h := f.read(16):
        if len(h) != 16:
            raise ValueError('Truncated record header')
        sec, usec, n, original = struct.unpack('<4I', h)
        b = f.read(n)
        if len(b) != n or n != original:
            raise ValueError('Truncated packet')
        o, kind = 14, int.from_bytes(b[12:14], 'big')
        while kind in (0x8100, 0x88a8):
            kind = int.from_bytes(b[o+2:o+4], 'big'); o += 4
        if kind != 0x800 or b[o+9] != 17:
            continue
        ihl = (b[o] & 15) * 4
        u = o + ihl
        port = int.from_bytes(b[u+2:u+4], 'big')
        size = int.from_bytes(b[u+4:u+6], 'big')
        if size < 8 or u + size > len(b):
            raise ValueError('Bad UDP length')
        yield sec + usec / 1e6, port, b[u+8:u+size]


def decode(payload):
    if len(payload) < 8:
        raise ValueError('Truncated diagnostic payload')
    version, length = struct.unpack_from('<HH', payload, 4)
    if (payload[:4], version, length) not in ((b'NMD1',1,28),(b'NMD2',2,44)) or len(payload)!=length:
        raise ValueError('Diagnostic version/length mismatch')
    seq, config, channel, fc, qos, tsf, event = struct.unpack_from('<7H', payload, 14)
    if config not in (0, 256, 512):
        raise ValueError('Expected three cores, stream zero')
    tid = (qos & 15) if fc & 0x8c == 0x88 and qos != 0xffff else None
    result = dict(mac=payload[8:14].hex(':'), seq=seq, config=config,
                channel=channel, fc=fc, retry=bool(fc & 0x800),
                qos=qos, tid=tid, rx_tsf16=tsf, event16=event)
    if version==2:
        offset,count=struct.unpack_from('<HH',payload,28)
        if count!=3 or offset!=(28 if channel & 0x3800 == 0x1000 else 0):
            raise ValueError('Unexpected saved FFT word location')
        result.update(original_offset=offset,original_words=struct.unpack_from('<3I',payload,32))
    return result


def diagnose(path):
    csis, diags, pairs, issues = [], [], [], []
    pending = None
    for time, port, p in packets(path):
        if port == 5500:
            if len(p) != 274 or p[:2] != b'\x11\x11' or int.from_bytes(p[16:18], 'little') != 106:
                raise ValueError('CSI format changed or wrong bandwidth/chip')
            c = dict(time=time, mac=p[4:10].hex(':'), seq=int.from_bytes(p[10:12], 'little'),
                     config=int.from_bytes(p[12:14], 'little'), channel=int.from_bytes(p[14:16], 'little'))
            csis.append(c)
            if pending is not None:
                issues.append('CSI without following diagnostic')
            pending = c
        elif port == 5501:
            d = decode(p); d['time'] = time; diags.append(d)
            if pending is None or any(d[k] != pending[k] for k in ('mac','seq','config','channel')):
                issues.append('Diagnostic/CSI adjacency or identity mismatch')
            else:
                pairs.append(d)
            pending = None
    if pending is not None:
        issues.append('Trailing unpaired CSI')
    events = []
    for i in range(0, len(pairs), 3):
        g = pairs[i:i+3]
        fields = ('mac','seq','channel','fc','qos','rx_tsf16','event16')
        if len(g) != 3 or [d['config'] for d in g] != [0,256,512] or any(
                len({d[k] for d in g}) != 1 for k in fields):
            issues.append('Incomplete or inconsistent three-core event')
            continue
        events.append(g[0])
    repeats, seen = [], {}
    for i, e in enumerate(events):
        key = (e['mac'], e['seq'], e['channel'])
        old = seen.get(key)
        if old is not None and 0 <= e['time'] - events[old]['time'] <= .020:
            previous = events[old]
            repeats.append(dict(event_index=i, previous_index=old, seq=e['seq'],
                tid=e['tid'], previous_tid=previous['tid'], retry=e['retry'],
                previous_retry=previous['retry'], same_dump=e['event16']==previous['event16'],
                event_step=(e['event16']-previous['event16']) & 65535,
                rx_tsf_delta_mod65536=(e['rx_tsf16']-previous['rx_tsf16']) & 65535,
                host_gap_us=round((e['time']-previous['time'])*1e6, 3)))
        seen[key] = i
    return dict(csi_packets=len(csis), diagnostic_packets=len(diags), paired_packets=len(pairs),
                complete_events=len(events), issues=issues,
                field_counts=dict(fc=dict(collections.Counter(hex(e['fc']) for e in events)),
                    tid=dict(collections.Counter(str(e['tid']) for e in events)),
                    retry=dict(collections.Counter(str(e['retry']) for e in events))),
                rx_tsf_distinct=len({e['rx_tsf16'] for e in events}),
                event16_distinct=len({e['event16'] for e in events}),
                repeated_identity_events=len(repeats), repeats=repeats), events


if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('pcap', type=Path); a.add_argument('--output', type=Path, required=True)
    args = a.parse_args()
    result, events = diagnose(args.pcap)
    with args.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    if events:
        with args.output.with_suffix('.csv').open('x', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(events[0])); w.writeheader(); w.writerows(events)
    print(json.dumps({k:v for k,v in result.items() if k != 'repeats'}, indent=2))

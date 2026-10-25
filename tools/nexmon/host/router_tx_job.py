"""Create bounded own-router broadcast TX parameters, without network/device access.

Mode2 is the local absolute-slot derivative; delay denotes Hz here. The script
emits no command and never starts transmission. Frame body is experimental data.
"""
import argparse
import base64
import json
from pathlib import Path
import re
import struct


def make_job(source_mac, rate, seconds, label):
    if not re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', source_mac):
        raise ValueError('Require explicit radio MAC')
    mac = bytes.fromhex(source_mac.replace(':', ''))
    if mac[0] & 1 or mac in (bytes(6), b'\xff' * 6):
        raise ValueError('Require a unicast source radio MAC')
    if (rate, seconds) not in ((50, 2), (300, 10), (300, 60)):
        raise ValueError('Only 50Hz/2s, 300Hz/10s or 300Hz/60s bounded profiles')
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,24}', label):
        raise ValueError('Require a short diagnostic label')
    # Three-address Data, no DS/protection/retry flags; broadcast RA suppresses ACK.
    header = b'\x08\x00\x00\x00' + b'\xff' * 6 + mac + mac + b'\x00\x00'
    payload = b'\xaa\xaa\x03\x00\x00\x00\x88\xb5PIWTX1:' + label.encode('ascii')
    frame = header + payload
    ratespec = 0xc2010010  # Upstream VHT MCS0, NSS1, 20MHz with explicit override.
    params = struct.pack('<BBIII', 0, 2, rate, rate * seconds, ratespec) + frame
    return dict(schema=1, source_mac=source_mac.lower(), rate_hz=rate,
        intended_seconds=seconds, intended_slots=rate * seconds,
        frame_bytes=len(frame), parameter_bytes=len(params), ratespec=hex(ratespec),
        spatial_mode=0, spatial_streams=1, bandwidth_mhz=20,
        absolute_slot_mode=2, broadcast_data_only=True,
        parameters_base64=base64.b64encode(params).decode('ascii'),
        source_label=label,
        limits=['Enqueue deadlines do not certify air transmission or successful CSI reception.',
                'Actual RX clock/grid checks retain their original thresholds.',
                'Counters are not application IDs in the unchanged CSI metadata.'])


def decode_stats(encoded):
    raw = base64.b64decode(encoded.strip(), validate=True)
    if len(raw) != 48:
        raise ValueError('Require the local 48-byte TX status')
    values = struct.unpack('<12I', raw)
    if values[0] != 0x3158544e or values[-1] != 1:
        raise ValueError('TX status identity mismatch')
    keys = ('magic', 'running', 'rate_hz', 'remaining_slots', 'submitted_frames',
            'skipped_slots', 'error', 'max_enqueue_lateness_us', 'first_enqueue_tsf32',
            'last_enqueue_tsf32', 'query_tsf32', 'version')
    return dict(zip(keys, values))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-mac', required=True)
    p.add_argument('--rate', type=int, required=True)
    p.add_argument('--seconds', type=int, required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    job = make_job(a.source_mac, a.rate, a.seconds, a.label)
    with a.output.open('x', encoding='utf-8') as f:
        json.dump(job, f, indent=2)
    print(json.dumps({k: v for k, v in job.items() if k != 'parameters_base64'}))

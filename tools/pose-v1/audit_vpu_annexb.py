"""Inspect captured finite Annex B data before designing an RTSP packet bridge.

This is a bounded diagnostic, not a general H.264 access-unit assembler.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


def inspect(stage):
    data = (stage / 'results/video.h264').read_bytes()
    assert 0 < len(data) < 16 * 1024 * 1024
    captures = [json.loads(line) for line in (stage / 'results/events.jsonl').read_text().splitlines()
                if json.loads(line)['event'] == 'capture']
    assert sum(c['bytes'] for c in captures) == len(data)
    starts = list(re.finditer(b'\x00\x00(?:\x00)?\x01', data))
    assert starts and starts[0].start() == 0
    nals = []
    for i, start in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(data)
        payload = data[start.end():end]
        assert payload and not payload[0] & 0x80
        nals.append({'offset': start.start(), 'end': end, 'start_code_bytes': start.end() - start.start(),
                     'type': payload[0] & 31, 'payload_bytes': len(payload),
                     'payload_sha256': hashlib.sha256(payload).hexdigest()})
    chunks, offset = [], 0
    for i, capture in enumerate(captures):
        end = offset + capture['bytes']
        contained = [n for n in nals if offset <= n['offset'] < end]
        assert all(n['end'] <= end for n in contained), 'NAL crosses capture boundary; assembler required'
        chunks.append({'capture_index': i, 'offset': offset, 'bytes': capture['bytes'],
                       'pts_us': capture['pts_us'], 'flags': capture['flags'],
                       'nal_types': [n['type'] for n in contained],
                       'nal_payload_bytes': [n['payload_bytes'] for n in contained]})
        offset = end
    counts = Counter(n['type'] for n in nals)
    assert counts[7] >= 1 and counts[8] >= 1 and counts[5] >= 1
    return {'status': 'finite_capture_annexb_structure_audited', 'h264_sha256': hashlib.sha256(data).hexdigest(),
            'bytes': len(data), 'nal_type_counts': dict(counts), 'chunks': chunks, 'nals': nals,
            'limitations': 'Current capture boundaries inspected only; slice counts and timestamp groups alone are not a generic AU/picture parser. No SPS VUI color inference.'}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--stage', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists()
    result = inspect(args.stage)
    args.output.write_bytes((json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps({k: v for k, v in result.items() if k not in ('chunks', 'nals')}, indent=2))


if __name__ == '__main__':
    main()

"""Independently verify bounded real-video stages, descriptors and identities."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_manifest(root, path, prefix=None):
    count = 0
    for line in path.read_text().splitlines():
        digest, name = line.split('  ', 1)
        relative = PurePosixPath(name)
        if prefix:
            relative = relative.relative_to(prefix)
        assert not relative.is_absolute() and '..' not in relative.parts
        assert sha(root.joinpath(*relative.parts)) == digest, name
        count += 1
    return count


def review(stage, package):
    m = json.loads((package / 'manifest.json').read_text())
    frames = m['frames']
    assert frames == 54 and m['sources'] == 27
    payloads = check_manifest(package, package / 'files.sha256')
    events = [json.loads(line) for line in (stage / 'results/events.jsonl').read_text().splitlines()]
    encoded = events[-1]['event'] == 'encoding_complete'
    stage_hashes = check_manifest(stage, stage / 'files.sha256', 'run-encode' if encoded else 'run-negotiate')
    assert (stage / 'exit.txt').read_text().strip() == '0'
    assert not (stage / 'stderr.log').read_bytes()
    assert (stage / 'dmesg.before.log').read_bytes() == (stage / 'dmesg.after.log').read_bytes()
    identity = json.loads((stage / 'preflight.json').read_text())
    assert identity['SDK_packages'] == ['customop arm64 3.39.0', 'icraft arm64 3.39.0']
    assert identity['fpga_state'] == 'operating'
    assert next(f['sha256'] for f in identity['boot_files'] if f['name'] == 'BOOT.BIN') == 'ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
    assert identity['libraries'] == {
        'libicraft_hostbackend.so': 'd0fbf6c81e5b57b4a908f11aad27571b8f2e68a3ede7ba33c9a4f783ba266130',
        'libicraft_zg330backend.so': '592ad913737a6d661ab9d913ff16617c8fb6bf65cc0dc8929c6886303c498a57',
        'libicraft_xrt.so': 'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96'}
    assert sha(package / 'pose_vpu_sequence_check') == m['program_sha256']
    assert sha(package / 'frames.nv12') == m['input_sha256']
    formats = [e for e in events if e['event'] == 'format']
    assert [e['type'] for e in formats] == [10, 9]
    assert formats[0]['layout'] == [{'stride': 1280, 'size': 921600}, {'stride': 1280, 'size': 460800}]
    assert formats[1]['layout'] == [{'stride': 0, 'size': 2097152}]
    assert all((e['width'], e['height'], e['colorspace'], e['ycbcr_enc'], e['quantization'], e['xfer_func']) == (1280, 720, 1, 1, 2, 1) for e in formats)
    assert {e['id']: e['value'] for e in events if e['event'] == 'control'} == {10035200: 655360, 10029519: 2000000, 10029675: 0}
    final = events[-1]
    captures = []
    if encoded:
        assert final['queued'] == final['returned'] == frames and final['last']
        assert not final['npu'] and not final['hdmi']
        assert [e['frame'] for e in events if e['event'] == 'input_queued'] == list(range(frames))
        copies = [e for e in events if e['event'] == 'host_copy_check']
        assert [e['frame'] for e in copies] == list(range(frames)) and all(e['equal'] for e in copies)
        descriptors, owned, pending = {}, set(), None
        queues = 0
        for e in events:
            kind = e['event']
            if kind == 'querybuf':
                key = (e['type'], e['index'])
                assert key not in descriptors
                descriptors[key] = e['planes']
            elif kind == 'qbuf_enter':
                key = (e['type'], e['index'])
                assert key not in owned and pending is None
                original = descriptors[key]
                assert len(e['planes']) == len(original)
                for plane, expected in zip(e['planes'], original):
                    assert plane['mmap_cookie'] == expected['mmap_cookie']
                    assert plane['length'] == expected['length']
                    assert 0 <= plane['data_offset'] <= plane['bytesused'] <= plane['length']
                pending = key
            elif kind == 'qbuf_return':
                key = (e['type'], e['index'])
                assert pending == key
                owned.add(key)
                pending = None
                queues += 1
            elif kind == 'dqbuf':
                key = (e['type'], e['index'])
                assert key in owned and not (e['flags'] & 0x40)
                owned.remove(key)
            elif kind == 'streamoff':
                owned = {key for key in owned if key[0] != e['type']}
            elif kind in ('dqbuf_error', 'abort_streamoff'):
                raise AssertionError(e)
        assert pending is None and not owned and len(descriptors) == 12
        captures = [e for e in events if e['event'] == 'capture']
        assert captures[-1]['flags'] & 0x100000
        assert sum(e['bytes'] for e in captures) == final['bytes'] == (stage / 'results/video.h264').stat().st_size
        pts = [e['pts_us'] for e in captures if e['bytes']]
        assert set(pts) == set(range(0, frames * 100000, 100000))
        assert pts == sorted(pts)
        assert [e['type'] for e in events if e['event'] == 'streamoff'] == [10, 9]
    else:
        assert final == {'event': 'negotiation_complete', 'streamed': False}
        assert not any(e['event'] in ('querybuf', 'streamon') for e in events)
        queues = 0
    return {'status': 'real_video_stage_independently_verified', 'stage': stage.name,
            'package_payloads': payloads, 'returned_hashed_files': stage_hashes,
            'program_sha256': m['program_sha256'], 'input_sha256': m['input_sha256'],
            'package_sha256': sha(package / 'files.sha256'), 'exit': 0, 'stderr_empty': True,
            'kernel_unchanged': True, 'identity_checked': True, 'completion': final,
            'qbuf_descriptors_checked': queues, 'capture_chunks': len(captures),
            'h264_sha256': sha(stage / 'results/video.h264') if encoded else None}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--stage', type=Path, required=True)
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists()
    result = review(args.stage, args.package)
    args.output.write_bytes((json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

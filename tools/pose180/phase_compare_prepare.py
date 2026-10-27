"""Prepare paired offline inputs; labels never enter the C++ preprocessor.

Requires numpy/h5py and existing captures/dataset. Never opens a device.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'demo_v1/host'))
from prepare import aligned_payload
sys.path.insert(0, str(ROOT / 'tools/vitals'))
from audit_nexmon_vitals import load_segment


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def official_clips(data):
    groups = defaultdict(list)
    for name in (data / 'test_data/test_data_list.txt').read_text().split():
        groups[name.rsplit('_', 1)[0]].append(name)
    subjects = sorted({name.split('_')[0] for name in groups})
    clips = []
    # Fixed selection before inference: one clip per subject/environment prefix,
    # rotating target person count 1,2,3. First eligible sequence in list order.
    for index, subject in enumerate(subjects):
        wanted = index % 3 + 1
        selected = None
        for group, names in groups.items():
            if not group.startswith(subject + '_') or len(names) < 40:
                continue
            run = names[:40]
            nums = [int(n.rsplit('_', 1)[1]) for n in run]
            if np.any(np.diff(nums) != 1):
                continue
            if all(len(np.load(data / 'test_data/keypoint' / (n + '.npy'))) == wanted for n in run):
                selected = run
                break
        if selected is None:
            raise ValueError(f'No 40-frame contiguous {wanted}-person clip for {subject}')
        clips.append(('test', group, selected))
    # Existing demonstration clips are explicitly identified, not substituted
    # for held-out test results or chosen using this comparison's outputs.
    for split, folder in [('test', 'clip'), ('train', 'train-clip')]:
        existing = ROOT / '.local/pose-dataset-20261027-r1' / folder / 'dataset.json'
        rows = json.loads(existing.read_text())['samples']
        names = [r['name'] for r in rows]
        clips.append((split, names[0].rsplit('_', 1)[0] + '-demo', names))
    return clips


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--preprocess', type=Path, required=True)
    p.add_argument('--replay', type=Path, required=True)
    p.add_argument('--config', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    config = dict(line.split('=', 1) for line in a.config.read_text().splitlines() if '=' in line and not line.startswith('#'))
    gains = [float(config['gain' + str(i)]) for i in (1, 2, 3)]
    frames, clips = [], []
    raw_path, ids_path = a.output / 'raw.piwcsi2', a.output / 'identities.bin'
    epoch = 0
    with raw_path.open('wb') as raw, ids_path.open('wb') as ids:
        for split, clip_name, names in official_clips(a.data):
            epoch += 1
            start = len(frames)
            previous = None
            last_sample = -1
            overlaps = defaultdict(int)
            for name in names:
                base = a.data / (split + '_data')
                payload = aligned_payload(base / 'csi' / (name + '.mat'))
                pairs = np.frombuffer(payload, dtype='<f8').reshape(3, 3, 20, 30, 2)
                overlap = 0
                if previous is not None:
                    for length in range(20, 0, -1):
                        if np.array_equal(previous[:, :, -length:], pairs[:, :, :length]):
                            overlap = length
                            break
                overlaps[overlap] += 1
                sample = np.arange(last_sample + 1 - overlap, last_sample + 21 - overlap, dtype=np.uint64)
                last_sample = int(sample[-1])
                stamp = np.zeros((3, 20, 3), dtype='<u8')
                stamp[:, :, 0] = epoch
                stamp[:, :, 1] = sample
                stamp[:, :, 2] = np.rint(sample.astype(float) * 1e9 / 300).astype(np.uint64)
                ids.write(stamp.tobytes())
                raw.write(struct.pack('<8sIIQQ', b'PIWCSI2\0', 2, 86400, len(frames) + 1, int(stamp[0, -1, 2])))
                raw.write(payload)
                gt = np.load(base / 'keypoint' / (name + '.npy'))
                if gt.ndim != 3 or gt.shape[1:] != (14, 3) or not np.isfinite(gt).all():
                    raise ValueError('Invalid official ground truth: ' + name)
                frames.append(dict(index=len(frames), split=split, clip=clip_name, name=name, gt=gt.tolist()))
                previous = pairs
            clips.append(dict(clip=clip_name, split=split, first=start, count=len(frames)-start,
                              overlap_lengths=dict(overlaps), timeline='nominal 300Hz sample order; not measured RF time'))
            print('Prepared official', split, clip_name, len(names), dict(overlaps), flush=True)
        for capture in (1, 2, 3):
            epoch += 1
            clip_name = f'real-run300-{capture}'
            folder = a.output / clip_name
            folder.mkdir()
            pcaps = [ROOT / f'tools/nexmon/evidence/multirx-20261025-r1/rx{r}/run300-{capture}.pcap' for r in (1, 2, 3)]
            command = [str(a.replay), '--source-mac', config['source'], '--channel', config['channel'],
                       '--pcaps', *map(str, pcaps), '--gains', *map(str, gains), '--max-sequence-skew', '0',
                       '--output', str(folder / 'raw.piwcsi2'), '--report', str(folder / 'replay.json'),
                       '--ledger', str(folder / 'replay.jsonl')]
            subprocess.run(command, check=True)
            events = [load_segment(path)[0] for path in pcaps]
            clocks = []
            for event_list in events:
                clock = {}
                for e in event_list:
                    seq = int(e.meta['seq']) >> 4
                    if seq in clock:
                        raise ValueError('Capture sequence wraps; explicit extended identity map required')
                    clock[seq] = int(e.time_us) * 1000
                clocks.append(clock)
            start = len(frames)
            with (folder / 'raw.piwcsi2').open('rb') as source:
                for line in (folder / 'replay.jsonl').read_text().splitlines():
                    row = json.loads(line)
                    if row['approximate_points']:
                        raise ValueError('Phase comparison requires exact RF event association')
                    stamp = np.zeros((3, 20, 3), dtype='<u8')
                    for r in range(3):
                        for t, seq in enumerate(row['sequences'][r]):
                            stamp[r, t] = (epoch, seq, clocks[r][seq % 4096])
                    record = source.read(86432)
                    if len(record) != 86432:
                        raise ValueError('Short replay record')
                    raw.write(record)
                    ids.write(stamp.tobytes())
                    frames.append(dict(index=len(frames), split='real', clip=clip_name, name=str(row['frame']), gt=None))
                if source.read(1):
                    raise ValueError('Unlabelled replay records')
            clips.append(dict(clip=clip_name, split='real', first=start, count=len(frames)-start,
                              timeline='own RX metadata clock; same RF sequence across RX', gains=gains,
                              pcaps=[str(path.relative_to(ROOT)) for path in pcaps]))
    result = subprocess.run([str(a.preprocess), str(raw_path), str(ids_path), str(a.output / 'original.f32'),
                             str(a.output / 'continuous.f32')], capture_output=True, text=True, check=True)
    preprocessing = json.loads(result.stdout)
    original = np.memmap(a.output / 'original.f32', dtype='<f4', mode='r', shape=(len(frames), 180, 60))
    continuous = np.memmap(a.output / 'continuous.f32', dtype='<f4', mode='r', shape=original.shape)
    if not np.array_equal(original[:, :, :30].view('<u4'), continuous[:, :, :30].view('<u4')):
        raise ValueError('Amplitude changed')
    for clip in clips:
        lo, hi = clip['first'], clip['first'] + clip['count']
        diff = np.abs(np.angle(np.exp(1j*(original[lo:hi, :, 30:].astype(float)-continuous[lo:hi, :, 30:]))))
        clip['changed_frames'] = int(np.any(diff > 1e-5, axis=(1, 2)).sum())
        clip['phase_difference_p95_rad'] = float(np.percentile(diff, 95))
    hashes = {name: hashlib.sha256((a.output / name).read_bytes()).hexdigest()
              for name in ('original.f32', 'continuous.f32')}
    manifest = dict(schema='PIWPHASECOMPARE1', CSI_live=False, SDK=False, ground_truth_used_as_input=False,
                    input_shape=[1, 180, 60], dtype='float32 little-endian', frames=frames, clips=clips,
                    preprocessing=preprocessing, hashes=hashes, amplitude_bitwise_equal=True,
                    selection='one first eligible 40-frame sequence per subject prefix; target people cycles 1,2,3; plus two existing demo clips')
    save(a.output / 'manifest.json', manifest)
    print(json.dumps(preprocessing), flush=True)


if __name__ == '__main__':
    main()

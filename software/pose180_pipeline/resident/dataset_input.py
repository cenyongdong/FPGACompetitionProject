"""Prepare a finite official CSI clip. No devices, labels, inference or UI changes."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
RECORD_BYTES = 86432


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def validate_dataset(directory):
    directory = Path(directory)
    manifest = json.loads((directory/'dataset.json').read_text(encoding='utf-8'))
    if (manifest.get('schema') != 'PIWDATASET1' or manifest.get('input_source') != 'official_dataset'
            or manifest.get('file') != 'dataset.piwcsi2'
            or not 1 <= manifest.get('count', 0) <= 9000
            or len(manifest.get('samples', [])) != manifest['count']):
        raise ValueError('Invalid dataset manifest')
    data = directory/manifest['file']
    if data.stat().st_size != manifest['count']*RECORD_BYTES or sha(data) != manifest['sha256']:
        raise ValueError('Dataset bytes differ from prepared source')
    return manifest


def prepare_dataset(dataset_root, split, sequence, start, count, hz, output):
    # The official list is the selection authority; never interleave recordings.
    if split not in ('test', 'train') or (count is not None and not 1 <= count <= 9000) or not math.isfinite(hz) or not 1 <= hz <= 60:
        raise ValueError('Finite clip (1..9000) and playback rate (1..60 Hz) required')
    folder = Path(dataset_root)/(split+'_data')
    names = (folder/(split+'_data_list.txt')).read_text(encoding='utf-8-sig').splitlines()
    selected = {}
    for value in names:
        name = value.strip()
        if not name: continue
        if Path(name).name != name or '/' in name or '\\' in name:
            raise ValueError('Unexpected dataset list entry')
        stem = name[:-4] if name.endswith('.mat') else name
        prefix, number = stem.rsplit('_', 1)
        if prefix == sequence:
            index = int(number)
            if index in selected: raise ValueError('Duplicate sample in official list')
            selected[index] = stem
    if not selected: raise ValueError('Sequence not found in official split list')
    first = min(selected) if start is None else start
    if count is None:
        count=1
        while first+count in selected and count<9000: count+=1
    indices = list(range(first, first+count))
    if any(i not in selected for i in indices):
        raise ValueError('Clip crosses a missing sample or recording boundary; choose a shorter contiguous clip')
    sources = [folder/'csi'/(selected[i]+'.mat') for i in indices]
    if any(not p.is_file() for p in sources): raise ValueError('CSI MAT file missing')
    sys.path.insert(0, str(ROOT))
    from demo_v1.host.prepare import aligned_payload
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    data = output/'dataset.piwcsi2'
    with data.open('xb') as stream:
        for i, source in enumerate(sources):
            # Reuse the established raw MAT -> PIWCSI2 payload conversion.
            payload = aligned_payload(source)
            stamp = 1000000000+round(i*1000000000/hz)
            stream.write(struct.pack('<8sIIQQ', b'PIWCSI2\0', 2, 86400, i+1, stamp))
            stream.write(payload)
    manifest = dict(schema='PIWDATASET1', input_source='official_dataset', CSI_live=False,
        dataset='Person-in-WiFi 3D', dataset_root=str(Path(dataset_root).resolve()),
        split=split, sequence=sequence, first_sample=first, count=count, playback_hz=hz,
        source_time='synthetic clip timeline at playback_hz; not measured RF time',
        layout='RX,antenna,time,carrier,real-imag / float64 little-endian',
        file=data.name, bytes=data.stat().st_size, sha256=sha(data), ground_truth_used_as_input=False,
        samples=[dict(frame=i+1, name=selected[index]) for i,index in enumerate(indices)])
    (output/'dataset.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', type=Path, required=True, help='Official data/wifipose directory')
    parser.add_argument('--split', choices=('test','train'), default='test')
    parser.add_argument('--sequence', required=True, help='One recording prefix, e.g. S11_01')
    parser.add_argument('--start', type=int)
    parser.add_argument('--count', type=int, help='Default: continuous run from --start, capped at 9000')
    parser.add_argument('--hz', type=float, default=15)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = prepare_dataset(args.dataset_root,args.split,args.sequence,args.start,args.count,args.hz,args.output)
    print(json.dumps({k:v for k,v in result.items() if k!='samples'}, ensure_ascii=False))


if __name__ == '__main__': main()

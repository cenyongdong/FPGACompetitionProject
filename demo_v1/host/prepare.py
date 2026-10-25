"""MAT只整理为对齐复数窗口；不运行预处理、模型或注入GT。"""
from pathlib import Path
import argparse, hashlib, json
import h5py
import numpy as np
from collections import defaultdict

def aligned_payload(path):
    with h5py.File(path, 'r') as handle:
        raw = handle['csi_out'][()]
    if raw.shape != (20, 30, 3, 3) or not {'real', 'imag'}.issubset(raw.dtype.names or ()):
        raise ValueError('Unexpected original MAT layout: ' + str(path))
    # HDF5 T/N/A/R -> 对外R/A/T/N，保留复数双精度。
    pairs = np.stack((raw['real'].transpose(3, 2, 0, 1), raw['imag'].transpose(3, 2, 0, 1)), axis=-1).astype('<f8')
    if not np.isfinite(pairs).all(): raise ValueError('Non-finite raw CSI')
    return pairs.tobytes()

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, default=Path('D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/data/wifipose/test_data'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--limit', type=int, default=0)
    p.add_argument('--train', type=Path)
    p.add_argument('--train-limit', type=int, default=7824)
    p.add_argument('--base-cache', type=Path)
    a = p.parse_args(); a.output.mkdir(parents=True, exist_ok=False)
    if a.train:
        if not a.base_cache: raise ValueError('Combined run requires an existing test cache')
        base=json.loads((a.base_cache/'catalog.json').read_text())
        groups=defaultdict(list)
        for name in (a.train/'train_data_list.txt').read_text().split(): groups[name.rsplit('_',1)[0]].append(name)
        selected=[];count=len(groups)
        for i,(segment,names) in enumerate(groups.items()):
            budget=a.train_limit//count+int(i<a.train_limit%count)
            selected.extend(names[:budget])
        train=[];digest=hashlib.sha256()
        with (a.output/'aligned.bin').open('wb') as f:
            for i,name in enumerate(selected):
                source=a.train/'csi'/(name+'.mat');payload=aligned_payload(source)
                f.write(payload);digest.update(payload)
                train.append({'index':i,'name':name,'mat_sha256':hashlib.sha256(source.read_bytes()).hexdigest(), 'split':'train','payload_index':i})
                if (i+1)%1000==0: print('Training windows prepared',i+1,flush=True)
        by_split={}
        for split,rows in [('test',[dict(row,split='test',payload_index=row['index']) for row in base['samples']]),('train',train)]:
            grouped=defaultdict(list)
            for row in rows:grouped[row['name'].rsplit('_',1)[0]].append(row)
            by_split[split]=list(grouped.values())
        combined=[]
        for i in range(max(map(len,by_split.values()))):
            for split in ['test','train']:
                if i<len(by_split[split]):combined.extend(by_split[split][i])
        sources={'test':{'path':str((a.base_cache/'aligned.bin').resolve()),'count':len(base['samples']),'sha256':base['sha256']},
                 'train':{'path':str((a.output/'aligned.bin').resolve()),'count':len(train),'sha256':digest.hexdigest()}}
        manifest={'shape':[3,3,20,30],'dtype':'complex128/LE-real-imag-f64','payload_bytes':86400,
                  'sources':sources,'samples':combined,'training_selection':'Equal quota per original sequence, original order retained',
                  'sha256':hashlib.sha256(json.dumps({'sources':sources,'order':[(r['split'],r['payload_index']) for r in combined]},sort_keys=True).encode()).hexdigest()}
        (a.output/'catalog.json').write_text(json.dumps(manifest,indent=2))
        print('Prepared combined test/train',len(base['samples']),len(train),'sequences',len(groups),flush=True)
        return
    names = (a.data / 'test_data_list.txt').read_text().split()
    if a.limit: names = names[:a.limit]
    rows = []; digest = hashlib.sha256()
    with (a.output / 'aligned.bin').open('wb') as output:
        for i, name in enumerate(names):
            source = a.data / 'csi' / (name + '.mat')
            payload = aligned_payload(source)
            output.write(payload); digest.update(payload)
            rows.append({'index': i, 'name': name, 'mat_sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    (a.output / 'catalog.json').write_text(json.dumps({'shape': [3,3,20,30], 'dtype': 'complex128/LE-real-imag-f64',
        'payload_bytes': 86400, 'dataset': str(a.data.resolve()), 'sha256': digest.hexdigest(), 'samples': rows}, indent=2))
    print('Prepared', len(rows), 'aligned windows')

if __name__ == '__main__': main()

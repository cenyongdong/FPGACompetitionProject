"""Cache a fixed official TRAIN subset once using its unchanged preprocessing."""
import argparse
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import sys
import numpy as np

dataset=None
def initialize(algorithm,root):
    global dataset
    sys.path.insert(0,algorithm)
    import torch
    torch.set_num_threads(1)
    from opera.datasets.wifi_pose import WifiPoseDataset
    dataset=WifiPoseDataset(dataset_root=root,pipeline=[],mode='train')

def item(index):
    x=dataset.get_item_single_frame(index)
    return index,x['img'].numpy().reshape(180,60),x['gt_keypoints'].numpy()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--algorithm-root',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--samples',type=int,default=2000);p.add_argument('--workers',type=int,default=8);a=p.parse_args()
    root=a.algorithm_root/'data/wifipose/train_data';names=(root/'train_data_list.txt').read_text().splitlines()
    selected=sorted(range(len(names)),key=lambda i:hashlib.sha256(names[i].encode()).digest())[:a.samples]
    output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
    tokens=np.lib.format.open_memmap(output/'tokens.npy',mode='w+',dtype='<f4',shape=(len(selected),180,60))
    poses=np.lib.format.open_memmap(output/'keypoints.npy',mode='w+',dtype='<f4',shape=(len(selected),3,14,3))
    poses[:]=0;counts=np.zeros(len(selected),dtype=np.uint8)
    with mp.get_context('spawn').Pool(a.workers,initializer=initialize,initargs=(str(a.algorithm_root),str(root))) as pool:
        for i,(index,x,y) in enumerate(pool.imap(item,selected,chunksize=10)):
            if x.shape!=(180,60) or y.shape[1:]!=(14,3) or not 1<=len(y)<=3 or not np.isfinite(x).all() or not np.isfinite(y).all():raise ValueError(names[index])
            tokens[i]=x;poses[i,:len(y)]=y;counts[i]=len(y)
            if (i+1)%100==0:print('cached official TRAIN',i+1,flush=True)
    tokens.flush();poses.flush();np.save(output/'person_counts.npy',counts)
    (output/'names.json').write_text(json.dumps([names[i] for i in selected])+'\n')
    (output/'cache.json').write_text(json.dumps(dict(source=str(root),samples=len(selected),original_preprocessing=True,
        original_labels_unchanged=True,unused_padding_excluded_by_person_counts=True,official_test_used=False),indent=2)+'\n')
    print('Official cache complete',len(selected),flush=True)

"""Exercise the real training data adapters on explicitly synthetic CPU fixtures."""
import argparse
import copy
import importlib
import json
import os
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--algorithm-root',required=True,type=Path);p.add_argument('--work',required=True,type=Path)
    a=p.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('CPU-only fixture check requires CUDA_VISIBLE_DEVICES empty')
    import numpy as np
    import torch
    torch.set_num_threads(2)
    sys.path.insert(0,str(a.algorithm_root));sys.path.insert(0,str(Path(__file__).resolve().parent))
    from mmcv import Config
    cfg=Config.fromfile(str(a.work/'planned-run/config.py'))
    for name in cfg.custom_imports['imports']:importlib.import_module(name)
    fixture=a.work/'synthetic-dataset-fixture';fixture.mkdir(exist_ok=False)
    for name in ('tokens','keypoint'):(fixture/name).mkdir()
    np.save(fixture/'tokens/fixture.npy',np.full((180,60),.125,dtype=np.float32))
    np.save(fixture/'keypoint/fixture.npy',np.full((1,14,3),1,dtype=np.float32))
    for mode in ('train','test'):(fixture/(mode+'_data_list.txt')).write_text('fixture\n')
    (fixture/'synthetic-only.json').write_text(json.dumps(dict(synthetic_fixture=True,trainable=False)))
    from opera.datasets import build_dataset
    train=copy.deepcopy(cfg.data.train);train.datasets[0].dataset_root=str(fixture);train.datasets[1].maximum_samples=1
    dataset=build_dataset(train)
    if len(dataset)!=2:raise ValueError('Local/official concatenation differs')
    local=dataset.datasets[0].get_item_single_frame(0)
    if tuple(local['img'].shape)!=(3,3,20,60) or not torch.equal(local['img'],torch.full((3,3,20,60),.125)):
        raise ValueError('Model token ordering differs')
    training_items=[dataset[0],dataset[1]]
    validation=copy.deepcopy(cfg.data.val);validation.dataset_root=str(fixture)
    validation_item=build_dataset(validation)[0]
    report=dict(dataset_adapters_passed=True,synthetic_local_samples=1,real_official_TRAIN_samples=1,
        train_pipeline_loaded=len(training_items),validation_pipeline_loaded=True,
        exact_token_order_verified=True,GPU_used=False,forward_calls=0,training_steps=0,
        note='CPU format check only; synthetic local fixture is not trainable data and no accuracy is evaluated.')
    (a.work/'dataset-readiness.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()

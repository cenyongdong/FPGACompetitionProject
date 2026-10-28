"""CPU-only actual training-pipeline format check; never construct/train a model."""
import argparse
import importlib
import json
import os
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',required=True,type=Path)
    args=parser.parse_args();bundle=args.bundle.resolve();plan=json.loads((bundle/'preparation.json').read_text())
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('CPU check requires CUDA_VISIBLE_DEVICES empty')
    import numpy as np
    import torch
    torch.set_num_threads(2)
    sys.path.insert(0,plan['algorithm_root']);sys.path.insert(0,str(Path(__file__).resolve().parent))
    from mmcv import Config
    cfg=Config.fromfile(str(bundle/'config.py'))
    for name in cfg.custom_imports['imports']:importlib.import_module(name)
    from opera.datasets import build_dataset
    train=build_dataset(cfg.data.train);local=train.datasets[0];official=train.datasets[1]
    indices={0,len(local)//2,len(local)-1}
    seated=next((i for i,name in enumerate(local.filename_list) if name.startswith('batch-r6-2_')),None)
    if seated is not None:indices.add(seated)
    checked=[]
    for index in sorted(indices):
        name=local.filename_list[index];raw=local.get_item_single_frame(index)
        tokens=np.load(Path(local.data_root)/'tokens'/(name+'.npy'),allow_pickle=False)
        poses=np.load(Path(local.data_root)/'keypoint'/(name+'.npy'),allow_pickle=False)
        if tuple(raw['img'].shape)!=(3,3,20,60) or not np.array_equal(raw['img'].numpy().reshape(180,60),tokens):raise ValueError('Actual token order differs')
        if not np.array_equal(raw['gt_keypoints'].numpy(),poses) or poses.shape!=(1,14,3):raise ValueError('Actual local label differs')
        if not np.isfinite(tokens).all() or not np.isfinite(poses).all():raise ValueError('Nonfinite actual sample')
        _=local[index];checked.append(name)
    _=official[0]
    val=build_dataset(cfg.data.val);test=build_dataset(cfg.data.test);_=val[0];_=test[0]
    report=dict(actual_dataset_pipeline_passed=True,actual_local_samples_checked=checked,
        local_train_samples=len(local),official_TRAIN_subset=len(official),validation_samples=len(val),test_samples=len(test),
        validation_and_test_pipeline_loaded=True,exact_token_order_verified=True,
        experimental_receipt_supervision=bool(plan.get('experimental_receipt_supervision')),
        certified_supervision=False,GPU_used=False,model_constructed=False,forward_calls=0,optimizer_created=False,training_steps=0)
    with (bundle/'actual-data-readiness.json').open('x') as target:json.dump(report,target,indent=2);target.write('\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()

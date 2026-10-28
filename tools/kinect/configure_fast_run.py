"""Prepare a finite, cached, multi-GPU run from the unchanged epoch99 weights."""
import argparse,json
from pathlib import Path
from pprint import pformat

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--algorithm',required=True,type=Path)
    p.add_argument('--epochs',type=int,default=12);p.add_argument('--run-name',default='run')
    p.add_argument('--initialization',choices=['finetune','scratch'],default='finetune');p.add_argument('--local-only',action='store_true')
    p.add_argument('--batch-size',type=int,default=32)
    a=p.parse_args();root=a.root.resolve();algo=a.algorithm.resolve();data=root/'dataset';run=root/a.run_name
    manifest=json.loads((data/'dataset.json').read_text())
    if not manifest['experimental_trainable'] or manifest.get('synthetic_fixture') or manifest['storage']!='continuous_numpy_v1':raise ValueError('Actual experimental contiguous dataset required')
    if not 1<=a.epochs<=30:raise ValueError('Bounded training required')
    run.mkdir(exist_ok=False)
    checkpoint=algo/'result/piw24_pose180_shared_20261022_r1/best_mpjpe_epoch_99.pth'
    if not checkpoint.is_file():raise FileNotFoundError(checkpoint)
    trainpipe=[dict(type='opera.DefaultFormatBundle',extra_keys=['gt_keypoints','gt_labels']),dict(type='mmdet.Collect',keys=['img','gt_bboxes','gt_labels','gt_keypoints','gt_areas'],meta_keys=[])]
    testpipe=[dict(type='mmdet.MultiScaleFlipAug',scale_factor=1.,flip=False,transforms=[dict(type='opera.DefaultFormatBundle',extra_keys=['gt_keypoints','gt_labels']),dict(type='mmdet.Collect',keys=['img'],meta_keys=[])])]
    def ds(split,train=False,**kw):return dict(type='opera.KinectWifiMemmapDataset',dataset_root=str(data/split),mode='train' if train else 'test',pipeline=trainpipe if train else testpipe,**kw)
    settings=dict(_base_=str(algo/'configs/wifi/petr_wifi_pose180_shared.py'),custom_imports=dict(imports=['opera.models.pose180','paired_training','fast_training'],allow_failed_imports=False),
      model=dict(type='opera.PETR180FastScratch' if a.initialization=='scratch' else 'opera.PETR180FastFinetune',source_checkpoint=None if a.initialization=='scratch' else str(checkpoint)),
      data=dict(_delete_=True,samples_per_gpu=a.batch_size,workers_per_gpu=2,
        train=ds('train_data',True) if a.local_only else dict(type='mmdet.ConcatDataset',datasets=[ds('train_data',True),ds('official_train_data',True)]),
        val=ds('val_data',maximum_samples=1200,metrics_path=str(run/'validation.jsonl')),
        test=ds('test_data'),train_dataloader=dict(persistent_workers=True),
        val_dataloader=dict(samples_per_gpu=8,workers_per_gpu=2,persistent_workers=True)),
      optimizer=dict(lr=8e-5 if a.initialization=='scratch' else 1e-5),optimizer_config=dict(type='Pose180OptimizerHook',cumulative_iters=1,grad_clip=dict(max_norm=.1,norm_type=2)),
      runner=dict(type='EpochBasedRunner',max_epochs=a.epochs),lr_config=None,
      custom_hooks=[dict(type='KinectValidationLrHook',priority='VERY_LOW',metrics_path=str(run/'validation.jsonl'),baseline_path=str(run/'baseline.json'),metric='top1_mpjpe',
        warmup_iters=100,warmup_ratio=.1,improvement_fraction=.6 if a.initialization=='scratch' else .2,factor=.3,patience=2,cooldown=1,min_lr=2e-7,max_reductions=3),dict(type='KinectWallBudgetHook',priority='LOWEST',seconds=4800),dict(type='Pose180ProgressHook',priority='LOWEST')],
      checkpoint_config=dict(interval=1,max_keep_ckpts=2,save_last=True),evaluation=dict(interval=1,metric='mpjpe',save_best='top1_mpjpe',rule='less'),
      log_config=dict(interval=25,hooks=[dict(type='TextLoggerHook')]),find_unused_parameters=True,cudnn_benchmark=True,
      load_from=None,resume_from=None,auto_resume=False,work_dir=str(run),auto_scale_lr=dict(enable=False))
    source='import sys\nsys.path.insert(0, '+repr(str(root/'tools'))+')\n'
    source+='\n'.join(k+' = '+pformat(v,width=120,sort_dicts=False) for k,v in settings.items())+'\n'
    (run/'config.py').write_text(source)
    (run/'preparation.json').write_text(json.dumps(dict(dataset=str(data),algorithm_root=str(algo),starting_checkpoint=None if a.initialization=='scratch' else str(checkpoint),epochs=a.epochs,
      initialization=a.initialization,local_only=a.local_only,initial_lr=8e-5 if a.initialization=='scratch' else 1e-5,
      batch_size=a.batch_size,training_wall_budget_seconds=4800,site_calibration_verified=False,experimental_receipt_supervision=True,training_started=False),indent=2)+'\n')
    print('Prepared',run,flush=True)

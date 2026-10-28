"""Write a finite epoch99 fine-tuning configuration; no training is launched."""
import argparse
import json
from pathlib import Path
from pprint import pformat


def dataset_status(manifest,receipt_experiment=False):
    real=bool(manifest and not manifest.get('synthetic_fixture'))
    certified=bool(real and manifest.get('schema')=='KINECT-WIFI-FT1' and manifest.get('trainable'))
    experimental=bool(real and receipt_experiment and manifest.get('schema')=='KINECT-WIFI-RECEIPT-FT1' and manifest.get('experimental_trainable'))
    return dict(ready=certified or experimental,certified=certified,experimental=experimental)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--algorithm-root',required=True,type=Path)
    p.add_argument('--dataset',required=True,type=Path)
    p.add_argument('--checkpoint',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--epochs',type=int,default=10)
    p.add_argument('--allow-pending-data',action='store_true',help='Prepare configuration only, with data_ready=false')
    p.add_argument('--receipt-experiment',action='store_true',help='Explicit experimental local-scene/receipt-time supervision; does not certify physical alignment')
    a=p.parse_args();algo=a.algorithm_root.resolve();data=a.dataset.resolve();checkpoint=a.checkpoint.resolve()
    if not 1<=a.epochs<=20:raise ValueError('Initial fine-tuning configuration is bounded to 1..20 epochs')
    if not checkpoint.is_file():raise ValueError('Original checkpoint unavailable on this host')
    base=algo/'configs/wifi/petr_wifi_pose180_shared.py'
    if not base.is_file():raise ValueError('Existing 180-query training repository not found')
    manifest_path=data/'dataset.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8-sig')) if manifest_path.is_file() else None
    profile=dataset_status(manifest,a.receipt_experiment);ready=profile['ready']
    if not ready and not a.allow_pending_data:raise ValueError('Paired training data is not ready')
    if ready and (not manifest['recording_disjoint_splits'] or not all(manifest['counts'].get(s,0)>0 for s in ('train','val'))):
        raise ValueError('Independent training/validation recording sessions are required')
    output=a.output.resolve();output.mkdir(exist_ok=False)
    train_pipeline=[dict(type='opera.DefaultFormatBundle',extra_keys=['gt_keypoints','gt_labels']),
        dict(type='mmdet.Collect',keys=['img','gt_bboxes','gt_labels','gt_keypoints','gt_areas'],meta_keys=[])]
    test_pipeline=[dict(type='mmdet.MultiScaleFlipAug',scale_factor=1.0,flip=False,transforms=[
        dict(type='opera.DefaultFormatBundle',extra_keys=['gt_keypoints','gt_labels']),dict(type='mmdet.Collect',keys=['img'],meta_keys=[])])]
    local_count=manifest['counts']['train'] if ready else 2000
    dataset=dict(_delete_=True,samples_per_gpu=4,workers_per_gpu=2,
        train=dict(type='mmdet.ConcatDataset',datasets=[
            dict(type='opera.KinectWifiTokenDataset',dataset_root=str(data/'train_data'),mode='train',pipeline=train_pipeline),
            dict(type='opera.KinectOfficialSubset',dataset_root=str(algo/'data/wifipose/train_data'),mode='train',pipeline=train_pipeline,maximum_samples=min(2000,local_count))]),
        val=dict(type='opera.KinectWifiTokenDataset',dataset_root=str(data/'val_data'),mode='test',pipeline=test_pipeline,metrics_path=str(output/'validation.jsonl')),
        test=dict(type='opera.KinectWifiTokenDataset',dataset_root=str(data/'test_data'),mode='test',pipeline=test_pipeline))
    settings=dict(_base_=str(base),custom_imports=dict(imports=['opera.models.pose180','paired_training'],allow_failed_imports=False),
        model=dict(type='opera.PETR180Finetune',source_checkpoint=str(checkpoint)),data=dataset,
        optimizer=dict(lr=2e-6),optimizer_config=dict(type='Pose180OptimizerHook',cumulative_iters=2,grad_clip=dict(max_norm=.1,norm_type=2)),
        runner=dict(type='EpochBasedRunner',max_epochs=a.epochs),lr_config=dict(policy='step',step=[max(1,a.epochs-2)],gamma=.1),
        checkpoint_config=dict(interval=1,max_keep_ckpts=3,save_last=True),
        evaluation=dict(interval=1,metric='mpjpe',save_best='mpjpe',rule='less'),
        load_from=None,resume_from=None,auto_resume=False,work_dir=str(output))
    source='import sys\nsys.path.insert(0, '+repr(str(Path(__file__).resolve().parent))+')\n'
    source+='\n'.join(key+' = '+pformat(value,width=110,sort_dicts=False) for key,value in settings.items())+'\n'
    (output/'config.py').write_text(source,encoding='utf-8')
    report=dict(configuration_prepared=True,data_ready=ready,training_started=False,epochs=a.epochs,
        experimental_receipt_supervision=profile['experimental'],certified_supervision=profile['certified'],
        physical_time_alignment_verified=bool(ready and profile['certified']),
        supervision_profile='receipt_supervised_local_scene_experiment' if profile['experimental'] else 'strict_calibrated',
        starting_checkpoint=str(checkpoint),dataset=str(data),algorithm_root=str(algo),
        official_train_subset_maximum=min(2000,local_count),optimizer='fresh AdamW; original model weights retained strictly',
        held_out_test_available=bool(ready and manifest.get('held_out_test_available')),
        note='Regenerate configuration on the actual Linux training host after transferring paired data and these adapter sources.')
    (output/'preparation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()

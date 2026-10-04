"""Approved 10-epoch warm-start experiment, not a from-scratch reproduction."""
_base_ = ['./petr_wifi_tpami2026_pose.py']
custom_imports = dict(imports=['opera.models.tpami2026_transfer'], allow_failed_imports=False)
model = dict(
    type='opera.PETR2026Transfer',
    transfer_checkpoint='result/code_faithful/best_mpjpe_epoch_442.pth',
    bbox_head=dict(type='opera.PETRHead2026Transfer', transformer=dict(
        type='opera.PETRTransformer2026Transfer',
        refine_decoder=dict(type='opera.PetrRefineTransformerDecoder2026Transfer', num_layers=3))))
work_dir = 'result/tpami2026_transfer_20261003'
data = dict(samples_per_gpu=8, workers_per_gpu=4,
            train=dict(type='opera.WifiPoseTransferAuditDataset'),
            val=dict(type='opera.WifiPoseTransferAuditDataset', report_dir=work_dir),
            test=dict(type='opera.WifiPoseTransferAuditDataset', report_dir=work_dir))
optimizer = dict(_delete_=True, type='AdamW', constructor='PoseTransferOptimizerConstructor',
                 lr=2e-5, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-4)
optimizer_config = dict(_delete_=True, type='PoseTransferOptimizerHook',
                        grad_clip=dict(max_norm=0.1, norm_type=2), interval=50, expected_world=4)
lr_config = dict(_delete_=True, policy='Fixed', warmup=None)
runner = dict(max_epochs=10)
evaluation = dict(interval=1, save_best='mpjpe', rule='less')
checkpoint_config = dict(interval=1, max_keep_ckpts=10)
auto_scale_lr = dict(enable=False, base_batch_size=32)
load_from = None
resume_from = None
auto_resume = False
seed = 0

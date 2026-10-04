"""Approved fresh 500-epoch pose experiment with the paper's Adam recipe."""
_base_ = ['./petr_wifi_tpami2026_transfer.py']
custom_imports = dict(imports=['opera.models.tpami2026_scratch'], allow_failed_imports=False)
model = dict(type='opera.PETR2026Scratch', transfer_checkpoint=None,
             backbone=dict(init_cfg=None))
work_dir = 'result/tpami2026_scratch_20261004'
data = dict(samples_per_gpu=8, workers_per_gpu=4,
            val=dict(report_dir=work_dir), test=dict(report_dir=work_dir))
optimizer = dict(_delete_=True, type='Adam', lr=2e-5, betas=(0.9, 0.999),
                 eps=1e-8, weight_decay=1e-4)
optimizer_config = dict(_delete_=True, type='PoseScratchOptimizerHook',
                        grad_clip=dict(max_norm=0.1, norm_type=2),
                        interval=50, expected_world=4)
lr_config = dict(_delete_=True, policy='step', step=[450], gamma=0.1, warmup=None)
runner = dict(type='EpochBasedRunner', max_epochs=500)
evaluation = dict(interval=1, save_best='mpjpe', rule='less')
checkpoint_config = dict(interval=10, max_keep_ckpts=5, save_last=True)
auto_scale_lr = dict(enable=False, base_batch_size=32)
load_from = None
resume_from = None
auto_resume = False
seed = 0


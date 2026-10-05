"""Ten-epoch scratch control: only differentiation parameters have zero decay."""
_base_ = ['./petr_wifi_tpami2026_scratch.py']
custom_imports = dict(imports=['opera.models.tpami2026_scratch',
                              'opera.models.tpami2026_diff_nodecay'], allow_failed_imports=False)
work_dir = 'result/tpami2026_diff_nodecay_20261004'
data = dict(val=dict(report_dir=work_dir), test=dict(report_dir=work_dir))
optimizer = dict(_delete_=True, type='Adam', lr=2e-5, betas=(0.9, 0.999),
                 eps=1e-8, weight_decay=1e-4,
                 constructor='PoseDiffNoDecayOptimizerConstructor')
optimizer_config = dict(_delete_=True, type='PoseDiffNoDecayOptimizerHook',
                        grad_clip=dict(max_norm=0.1, norm_type=2), interval=50, expected_world=4)
runner = dict(type='EpochBasedRunner', max_epochs=10)

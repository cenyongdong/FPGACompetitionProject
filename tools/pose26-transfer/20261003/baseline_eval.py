_base_ = ['./petr_wifi.py']
custom_imports = dict(imports=['opera.models.transfer_support'], allow_failed_imports=False)
model = dict(backbone=dict(init_cfg=None))
data = dict(workers_per_gpu=4,
            test=dict(type='opera.WifiPoseTransferAuditDataset',
                      report_dir='result/tpami2026_transfer_20261003/baseline'))
evaluation = dict(_delete_=True, metric='mpjpe')

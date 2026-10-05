_base_ = ['./petr_wifi_tpami2026_diff_nodecay.py']
data = dict(train=dict(limit_samples=96))
runner = dict(max_epochs=1)
work_dir = 'result/tpami2026_diff_nodecay_20261004/smoke'
evaluation = dict(interval=2, save_best=None)
checkpoint_config = dict(interval=1, max_keep_ckpts=1)


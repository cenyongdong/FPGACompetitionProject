_base_ = ['./petr_wifi_tpami2026_transfer.py']
data = dict(train=dict(limit_samples=96))
runner = dict(max_epochs=1)
work_dir = 'result/tpami2026_transfer_20261003/smoke'

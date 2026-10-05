"""Read-only control consistency audit, saving evidence into the new run only."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import torch
from mmcv import Config

ROOT = Path('/public/cyd/Person-in-WiFi-3D-repo')
OUT = ROOT / 'result/tpami2026_diff_nodecay_20261004'
CONTROL = ROOT / 'result/tpami2026_scratch_20261004'
sys.path.insert(0, str(ROOT))
audit = json.loads((CONTROL / 'prelaunch-audit.json').read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
for name, expected in audit['source_hashes'].items():
    assert sha(ROOT / name) == expected, name
manifest = json.loads((ROOT / 'tools/pose26_diff_nodecay/manifest.json').read_text())
for name, expected in manifest['files'].items():
    assert sha(ROOT / name) == expected, name
old = Config.fromfile(str(CONTROL / 'resolved_config.py'))
new = Config.fromfile(str(ROOT / 'configs/wifi/petr_wifi_tpami2026_diff_nodecay.py'))
allowed = {'custom_imports', 'optimizer', 'optimizer_config', 'runner', 'work_dir', 'data'}
assert set(old) == set(new)
for key in old:
    if key not in allowed: assert old[key] == new[key], key
assert new.data.train == old.data.train
for key in ('samples_per_gpu', 'workers_per_gpu'): assert new.data[key] == old.data[key]
for split in ('val', 'test'):
    left, right = dict(old.data[split]), dict(new.data[split])
    left.pop('report_dir'); right.pop('report_dir')
    assert left == right
old_optimizer, new_optimizer = dict(old.optimizer), dict(new.optimizer)
assert new_optimizer.pop('constructor') == 'PoseDiffNoDecayOptimizerConstructor'
assert new_optimizer == old_optimizer
left, right = dict(old.optimizer_config), dict(new.optimizer_config)
left.pop('type'); right.pop('type')
assert left == right
assert new.runner.type == old.runner.type and new.runner.max_epochs == 10
assert torch.__version__ == '1.13.1+cu117'
gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used,utilization.gpu',
                               '--format=csv,noheader,nounits'], text=True)
for line in gpu.splitlines():
    fields = [x.strip() for x in line.split(',')]
    if int(fields[0]) in (1, 2, 3, 4):
        assert int(fields[2]) < 512 and int(fields[3]) < 10, line
assert not (OUT / 'pipeline-launch.json').exists()
assert not (OUT / 'pipeline-launched.lock').exists()
for name in ('unit_gate', 'ddp_gate'):
    assert json.loads((OUT / 'gates' / (name + '.json')).read_text())['passed']
record = dict(passed=True, time=datetime.datetime.now().isoformat(),
              control_source_hash_count=len(audit['source_hashes']),
              new_manifest_hash_count=len(manifest['files']),
              control_source_hashes_unchanged=True, parsed_config_difference_scope_checked=True,
              scientific_change='Only joint_differentiators weight_decay 1e-4 -> 0',
              operational_change='New paths and 10-epoch stop instead of 500',
              torch_version=torch.__version__, gpu_prelaunch=gpu)
(OUT / 'control-consistency.json').write_text(json.dumps(record, indent=2))
print(json.dumps(record))

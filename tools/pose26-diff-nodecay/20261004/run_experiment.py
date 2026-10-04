"""Exactly one authorized fresh 10-epoch run, without retries or resume."""
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'result/tpami2026_diff_nodecay_20261004'
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def status(stage, **kwargs):
    row = dict(stage=stage, time=datetime.datetime.now().isoformat(),
               supervisor_pid=os.getpid(), **kwargs)
    temp = OUT / 'pipeline-status.tmp'
    temp.write_text(json.dumps(row, indent=2))
    temp.replace(OUT / 'pipeline-status.json')
    with (OUT / 'pipeline-events.jsonl').open('a') as f:
        f.write(json.dumps(row) + '\n')
    print(json.dumps(row), flush=True)


def main():
    from mmcv import Config
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '1,2,3,4'
    with (OUT / 'pipeline-launched.lock').open('x') as f:
        f.write(str(os.getpid()))
    assert not list(OUT.glob('epoch_*.pth')) and not (OUT / 'evaluations.jsonl').exists()
    for name in ('unit_gate', 'ddp_gate'):
        assert json.loads((OUT / 'gates' / (name + '.json')).read_text())['passed']
    manifest = json.loads((ROOT / 'tools/pose26_diff_nodecay/manifest.json').read_text())
    for name, expected in manifest['files'].items():
        assert sha(ROOT / name) == expected, name
    paths = dict(manifest['files'])
    for folder in ('opera', 'configs/_base_', 'configs/wifi'):
        for path in (ROOT / folder).rglob('*.py'):
            paths[str(path.relative_to(ROOT))] = sha(path)
    for name in ('tools/train.py', 'tools/test.py',
                 'data/wifipose/train_data/train_data_list.txt',
                 'data/wifipose/test_data/test_data_list.txt'):
        paths[name] = sha(ROOT / name)
    snapshot = OUT / 'source_snapshot'
    snapshot.mkdir(exist_ok=False)
    for name in paths:
        target = snapshot / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    cfg = Config.fromfile('configs/wifi/petr_wifi_tpami2026_diff_nodecay.py')
    assert cfg.runner.max_epochs == 10
    assert cfg.data.samples_per_gpu == 8 and cfg.data.workers_per_gpu == 4
    assert cfg.get('fp16') is None and cfg.model.transfer_checkpoint is None
    assert cfg.model.type == 'opera.PETR2026Scratch' and cfg.model.backbone.init_cfg is None
    assert cfg.load_from is None and cfg.resume_from is None and not cfg.auto_resume
    assert cfg.optimizer.type == 'Adam' and cfg.optimizer.lr == 2e-5
    assert cfg.optimizer.weight_decay == 1e-4 and cfg.optimizer.constructor == 'PoseDiffNoDecayOptimizerConstructor'
    assert cfg.lr_config.step == [450] and cfg.lr_config.gamma == 0.1
    assert cfg.model.bbox_head.transformer.refine_decoder.num_layers == 3
    assert cfg.model.bbox_head.loss_kpt.loss_weight / cfg.model.bbox_head.loss_cls.loss_weight == 35
    cfg.dump(str(OUT / 'resolved_config.py'))
    modules = {name: str(Path(importlib.import_module(name).__file__).resolve())
               for name in ('opera.models.tpami2026_diff_nodecay', 'opera.models.tpami2026_scratch', 'opera.models.tpami2026_transfer',
                            'opera.models.transfer_support', 'opera.datasets.wifi_pose')}
    assert all(path.startswith(str(ROOT) + '/') for path in modules.values())
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used,utilization.gpu',
                                   '--format=csv,noheader,nounits'], text=True)
    for line in gpu.splitlines():
        fields = [x.strip() for x in line.split(',')]
        if int(fields[0]) in (1, 2, 3, 4):
            assert int(fields[2]) < 512 and int(fields[3]) < 10, 'GPU busy: ' + line
    audit = dict(source_hashes=paths, imported_modules=modules,
                 gpu_prelaunch=gpu, config_sha256=sha(OUT / 'resolved_config.py'),
                 checkpoint_loaded=False, optimizer_restored=False,
                 approved_epochs=10, approved_optimizer='Adam',
                 paper_page=7, reproduction_choices='tools/pose26_diff_nodecay/PLAN.md')
    (OUT / 'prelaunch-audit.json').write_text(json.dumps(audit, indent=2))
    command = [sys.executable, '-B', '-m', 'torch.distributed.run', '--standalone',
               '--nnodes=1', '--nproc_per_node=4', 'tools/train.py',
               'configs/wifi/petr_wifi_tpami2026_diff_nodecay.py', '--launcher', 'pytorch', '--seed', '0']
    with (OUT / 'train.stdout.log').open('x') as log:
        child = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                 stdout=log, stderr=subprocess.STDOUT)
        status('training', child_pid=child.pid, command=command, max_epochs=10,
               automatic_extension=False, automatic_retry=False)
        rc = child.wait()
    if rc:
        raise RuntimeError('Training failed with exit code ' + str(rc))
    assert all(sha(ROOT / name) == expected for name, expected in paths.items()), 'Source changed'
    status('finalizing', max_epochs=10)
    subprocess.run([sys.executable, '-B', 'tools/pose26_diff_nodecay/finalize.py'], cwd=ROOT, check=True)
    status('completed_10_epochs', report=str(OUT / 'final-report.json'),
           automatic_extension=False, next_action='Discuss results before further work')


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        traceback.print_exc()
        status('failed_stopped', error=str(error), automatic_retry=False)
        raise


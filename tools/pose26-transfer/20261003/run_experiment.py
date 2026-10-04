"""One approved 10-epoch run. No automatic retry, resume, or extension."""
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
OUT = ROOT / 'result/tpami2026_transfer_20261003'
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
    from opera.models.transfer_support import SOURCE_SHA256
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '1,2,3,4'
    for name in ('unit_gate', 'ddp_gate'):
        assert json.loads((OUT / 'gates' / (name + '.json')).read_text())['passed']
    baseline = [json.loads(x) for x in (OUT / 'baseline/evaluations.jsonl').read_text().splitlines()]
    assert len(baseline) == 1 and baseline[0]['frames'] == 7824
    assert abs(baseline[0]['metrics']['mpjpe'] - 123.085) < 0.05, baseline
    assert not list(OUT.glob('epoch_*.pth')), 'Refusing to mix formal runs'
    assert not (OUT / 'evaluations.jsonl').exists(), 'Refusing to append a second experiment'
    assert sha(ROOT / 'result/code_faithful/best_mpjpe_epoch_442.pth') == SOURCE_SHA256

    manifest = json.loads((ROOT / 'tools/pose26_transfer/manifest.json').read_text(encoding='utf-8-sig'))
    paths = {}
    for name, expected in manifest['files'].items():
        folder = ('opera/models' if name in ('tpami2026_transfer.py', 'transfer_support.py')
                  else 'configs/wifi' if name in ('baseline_eval.py', 'smoke.py', 'petr_wifi_tpami2026_transfer.py')
                  else 'tools/pose26_transfer')
        path = ROOT / folder / name
        assert sha(path) == expected, str(path)
        paths[str(path.relative_to(ROOT))] = expected
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

    cfg = Config.fromfile('configs/wifi/petr_wifi_tpami2026_transfer.py')
    assert cfg.runner.max_epochs == 10 and cfg.data.samples_per_gpu == 8
    assert cfg.data.workers_per_gpu == 4 and cfg.get('fp16') is None
    assert cfg.load_from is None and cfg.resume_from is None and not cfg.auto_resume
    assert cfg.optimizer.type == 'AdamW' and cfg.lr_config.policy == 'Fixed'
    cfg.dump(str(OUT / 'resolved_config.py'))
    modules = {name: str(Path(importlib.import_module(name).__file__).resolve())
               for name in ('opera.models.tpami2026_transfer', 'opera.models.transfer_support',
                            'opera.models.utils.transformer', 'opera.models.dense_heads.petr_head',
                            'opera.datasets.wifi_pose')}
    assert all(path.startswith(str(ROOT) + '/') for path in modules.values())
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used,utilization.gpu',
                                   '--format=csv,noheader,nounits'], text=True)
    for line in gpu.splitlines():
        fields = [x.strip() for x in line.split(',')]
        if int(fields[0]) in (1, 2, 3, 4):
            assert int(fields[2]) < 512 and int(fields[3]) < 10, 'GPU became busy: ' + line
    audit = dict(source_hashes=paths, imported_modules=modules,
                 baseline=baseline[0], gpu_prelaunch=gpu,
                 config_sha256=sha(OUT / 'resolved_config.py'),
                 checkpoint_sha256=SOURCE_SHA256,
                 paper_audit='tools/pose26_transfer/PAPER_AUDIT.md')
    (OUT / 'prelaunch-audit.json').write_text(json.dumps(audit, indent=2))
    command = [sys.executable, '-B', '-m', 'torch.distributed.run', '--standalone',
               '--nnodes=1', '--nproc_per_node=4', 'tools/train.py',
               'configs/wifi/petr_wifi_tpami2026_transfer.py', '--launcher', 'pytorch', '--seed', '0']
    with (OUT / 'train.stdout.log').open('x') as log:
        child = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                 stdout=log, stderr=subprocess.STDOUT)
        status('training', child_pid=child.pid, command=command, max_epochs=10)
        rc = child.wait()
    if rc:
        raise RuntimeError('Formal training failed with exit code ' + str(rc))
    changed = [name for name, expected in paths.items() if sha(ROOT / name) != expected]
    assert not changed, 'Source changed during run: ' + repr(changed)
    status('finalizing', max_epochs=10)
    subprocess.run([sys.executable, '-B', 'tools/pose26_transfer/finalize.py'], cwd=ROOT, check=True)
    status('completed_10_epochs', report=str(OUT / 'final-report.json'),
           automatic_extension=False, next_action='Discuss results with user before further training')


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        status('failed_stopped', error=repr(error), traceback=traceback.format_exc(), automatic_retry=False)
        raise

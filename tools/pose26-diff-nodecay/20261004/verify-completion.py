"""Independent read-only completed-run verification; cannot launch training."""
import csv
import datetime
import gc
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import torch

ROOT = Path('/public/cyd/Person-in-WiFi-3D-repo')
OUT = ROOT / 'result/tpami2026_diff_nodecay_20261004'
sys.path.insert(0, str(ROOT))
from opera.models.transfer_support import load_checkpoint_cpu
def load(name): return json.loads((OUT/name).read_text())
def rows(name): return [json.loads(x) for x in (OUT/name).read_text().splitlines() if x.strip()]
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''): h.update(block)
    return h.hexdigest()
def finite(value):
    if isinstance(value, dict): return all(finite(v) for v in value.values())
    if isinstance(value, (list, tuple)): return all(finite(v) for v in value)
    if torch.is_tensor(value): return bool(torch.isfinite(value).all())
    if isinstance(value, (float, int)): return math.isfinite(value)
    return True
status = load('pipeline-status.json')
assert status['stage'] == 'completed_10_epochs'
report = load('final-report.json')
init = load('initialization.json')
audit = load('prelaunch-audit.json')
evaluations, checks, diag = rows('evaluations.jsonl'), rows('epoch_parameter_checks.jsonl'), rows('branch_diagnostics.jsonl')
assert len(evaluations) == len(checks) == report['completed_epochs'] == 10
assert [x['evaluation_round'] for x in evaluations] == list(range(1, 11))
assert [x['epoch'] for x in checks] == list(range(1, 11))
assert all(x['frames'] == 7824 for x in evaluations) and all(x['ddp_equal'] for x in checks)
assert len(diag) == report['diagnostic_count'] == 563 and all(finite(x) for x in diag)
assert finite(evaluations) and finite(checks)
assert report['evaluations'] == evaluations and report['epoch_parameter_checks'] == checks
for name, expected in audit['source_hashes'].items():
    assert sha(ROOT/name) == sha(OUT/'source_snapshot'/name) == expected, name
assert sha(OUT/'resolved_config.py') == audit['config_sha256']
best_i = min(range(10), key=lambda i: evaluations[i]['metrics']['mpjpe'])
assert report['best_epoch'] == best_i+1 and report['best_mpjpe_mm'] == evaluations[best_i]['metrics']['mpjpe']
weights = []
for key, epoch, iterations in [('best_checkpoint', best_i+1, (best_i+1)*2811), ('final_checkpoint', 10, 28110)]:
    path = Path(report[key])
    path.resolve().relative_to(OUT.resolve())
    digest = sha(path)
    assert digest == report[key+'_sha256']
    checkpoint = load_checkpoint_cpu(path)
    assert checkpoint['meta']['epoch'] == epoch and checkpoint['meta']['iter'] == iterations
    assert finite(checkpoint['state_dict']) and finite(checkpoint['optimizer'])
    groups = checkpoint['optimizer']['param_groups']
    assert len(groups) == 2 and [g['weight_decay'] for g in groups] == [0.0, 1e-4]
    assert all(g['lr'] == 2e-5 for g in groups)
    assert [g['parameter_names'] for g in groups] == [g['parameter_names'] for g in init['optimizer_groups']]
    weights.append(dict(kind=key, path=str(path), bytes=path.stat().st_size,
                        sha256=digest, epoch=epoch, iterations=iterations, all_tensors_finite=True))
    del checkpoint
    gc.collect()
with (OUT/'metrics.csv').open(newline='') as f: metrics = list(csv.DictReader(f))
assert len(metrics) == 10
for i, row in enumerate(metrics):
    assert int(row['epoch']) == i+1
    assert abs(float(row['mpjpe_mm'])-evaluations[i]['metrics']['mpjpe']) < 1e-10
for name in ('training-curves.png','training-curves.svg'): assert (OUT/name).stat().st_size > 1000
launch = load('pipeline-launch.json')
old_startup = load('startup-verification.json')
pids = [launch['pid'], old_startup['torchrun']['pid'], *[x['pid'] for x in old_startup['ranks']]]
current = subprocess.check_output(['ps','-eo','pid,ppid,args'],text=True)
present = []
for line in current.splitlines()[1:]:
    fields = line.strip().split(None,2)
    if len(fields) != 3: continue
    if int(fields[0]) in pids:
        present.append(dict(pid=int(fields[0]), command=fields[2]))
assert not any('pose26_diff_nodecay' in p['command'] for p in present), present
live = [line for line in current.splitlines() if
        ('tools/train.py configs/wifi/petr_wifi_tpami2026_diff_nodecay.py' in line or
         'tools/pose26_diff_nodecay/run_experiment.py' in line)]
assert not live, live
control = [json.loads(x) for x in (ROOT/'result/tpami2026_scratch_20261004/evaluations.jsonl').read_text().splitlines()]
comparisons = [dict(epoch=i+1, control_mm=x['metrics']['mpjpe'], experiment_mm=evaluations[i]['metrics']['mpjpe'],
                    improvement_mm=x['metrics']['mpjpe']-evaluations[i]['metrics']['mpjpe'])
               for i,x in enumerate(control)]
summary = dict(passed=True, checked_at=datetime.datetime.now().isoformat(),
               pipeline_status=status, all_training_processes_exited=True, reused_pids=present,
               gpu_state=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu',
                                                  '--format=csv,noheader,nounits'],text=True),
               completed_epochs=10, completed_iterations=28110, evaluation_frames=7824,
               source_hash_count=len(audit['source_hashes']), current_snapshot_config_hashes_match=True,
               diagnostic_count=len(diag), all_diagnostics_finite=True, weights=weights,
               best_epoch=best_i+1, best_mpjpe_mm=report['best_mpjpe_mm'],
               final_mpjpe_mm=evaluations[-1]['metrics']['mpjpe'], comparisons=comparisons,
               first_zero_differentiate_after_nonzero=next((dict(epoch=x['epoch'],iter=x['iter']) for x in diag
                 if x['iter']>51 and x['gradient_after_clip']['differentiate']==0),None),
               zero_diff_gradient_samples_by_epoch={e:sum(x['epoch']==e and x['gradient_after_clip']['differentiate']==0 for x in diag)
                                                    for e in range(1,11)},
               epoch_last_diagnostics=[next(x for x in reversed(diag) if x['epoch']==e) for e in range(1,11)],
               best_evaluation=evaluations[best_i], final_evaluation=evaluations[-1])
print(json.dumps(summary))

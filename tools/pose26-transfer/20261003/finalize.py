"""Summarize exactly the authorized ten epochs; never launches training."""
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'result/tpami2026_transfer_20261003'
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))


def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    from opera.models.transfer_support import load_checkpoint_cpu
    evaluations = rows(OUT / 'evaluations.jsonl')
    parameters = rows(OUT / 'epoch_parameter_checks.jsonl')
    assert len(evaluations) == 10 and len(parameters) == 10
    assert [x['epoch'] for x in parameters] == list(range(1, 11))
    assert all(x['frames'] == 7824 for x in evaluations)
    baseline = rows(OUT / 'baseline/evaluations.jsonl')[0]['metrics']['mpjpe']
    best_index = min(range(10), key=lambda i: evaluations[i]['metrics']['mpjpe'])
    best = list(OUT.glob('best_mpjpe_epoch_*.pth'))
    assert len(best) == 1 and best[0].stem == 'best_mpjpe_epoch_' + str(best_index + 1)
    final = load_checkpoint_cpu(OUT / 'epoch_10.pth')
    assert final['meta']['epoch'] == 10
    assert {g['lr'] for g in final['optimizer']['param_groups']} == {2e-6, 2e-5}
    report = dict(completed_epochs=10, baseline_mpjpe_mm=baseline,
                  best_epoch=best_index + 1, best_mpjpe_mm=evaluations[best_index]['metrics']['mpjpe'],
                  improvement_mm=baseline - evaluations[best_index]['metrics']['mpjpe'],
                  best_checkpoint=str(best[0]), best_checkpoint_sha256=sha(best[0]),
                  final_checkpoint=str(OUT / 'epoch_10.pth'),
                  final_checkpoint_sha256=sha(OUT / 'epoch_10.pth'),
                  evaluations=evaluations, epoch_parameter_checks=parameters,
                  interpretation='Same legacy GT-informed all-100-candidate metric; not a deployment/person-count metric.',
                  next_action='Stop and discuss. No automatic extension.')
    (OUT / 'final-report.json').write_text(json.dumps(report, indent=2))
    with (OUT / 'metrics.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['epoch', 'mpjpe_mm', 'coarse_fixed_pair_mm', 'refine1_mm', 'refine2_mm', 'refine3_mm'])
        for i, row in enumerate(evaluations, 1):
            writer.writerow([i, row['metrics']['mpjpe'], *row['fixed_final_pairing_stage_mpjpe']])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    epochs = list(range(1, 11))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.3), constrained_layout=True)
    axes[0].plot(epochs, [x['metrics']['mpjpe'] for x in evaluations], 'o-', label='Refined pose')
    axes[0].axhline(baseline, color='grey', linestyle='--', label='2024 epoch 442')
    for i, label in enumerate(('Coarse', 'Refine 1', 'Refine 2', 'Refine 3')):
        axes[1].plot(epochs, [x['fixed_final_pairing_stage_mpjpe'][i] for x in evaluations], 'o-', label=label)
    for ax in axes:
        ax.set(xlabel='Epoch', ylabel='MPJPE (mm)', xticks=epochs)
        ax.grid(alpha=0.2)
        ax.legend()
    axes[0].set_title('Approved 10-epoch transfer experiment')
    axes[1].set_title('Coarse / refinement, fixed final pairing')
    fig.savefig(OUT / 'training-curves.png', dpi=180)
    fig.savefig(OUT / 'training-curves.svg')
    plt.close(fig)
    print(json.dumps({k: v for k, v in report.items() if k not in ('evaluations', 'epoch_parameter_checks')}))


if __name__ == '__main__':
    main()

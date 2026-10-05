"""Validate and summarize the approved 10 epochs; cannot launch training."""
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'result/tpami2026_diff_nodecay_20261004'
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
    assert len(evaluations) == len(parameters) == 10
    assert [x['epoch'] for x in parameters] == list(range(1, 11))
    assert all(x['ddp_equal'] for x in parameters)
    assert all(x['frames'] == 7824 for x in evaluations)
    baseline = 123.0853521290001
    best_index = min(range(10), key=lambda i: evaluations[i]['metrics']['mpjpe'])
    best = list(OUT.glob('best_mpjpe_epoch_*.pth'))
    assert len(best) == 1 and best[0].stem == 'best_mpjpe_epoch_' + str(best_index + 1)
    final = load_checkpoint_cpu(OUT / 'epoch_10.pth')
    assert final['meta']['epoch'] == 10
    assert all(abs(g['lr'] - 2e-5) < 1e-15 and g['weight_decay'] == (0.0 if i == 0 else 1e-4)
               for i, g in enumerate(final['optimizer']['param_groups']))
    assert len(final['optimizer']['param_groups']) == 2
    assert all(__import__('torch').isfinite(x).all() for x in final['state_dict'].values())
    assert all(__import__('torch').isfinite(x).all() for x in load_checkpoint_cpu(best[0])['state_dict'].values())
    diagnostics = rows(OUT / 'branch_diagnostics.jsonl')
    def finite_tree(value):
        import math
        if isinstance(value, dict): return all(finite_tree(x) for x in value.values())
        if isinstance(value, list): return all(finite_tree(x) for x in value)
        if isinstance(value, (float, int)): return math.isfinite(value)
        return True
    assert diagnostics and all(finite_tree(x) for x in diagnostics)
    control_evaluations = rows(ROOT / 'result/tpami2026_scratch_20261004/evaluations.jsonl')
    control_parameters = rows(ROOT / 'result/tpami2026_scratch_20261004/epoch_parameter_checks.jsonl')
    matched_control = [dict(epoch=i+1, control_mpjpe_mm=row['metrics']['mpjpe'],
                           experiment_mpjpe_mm=evaluations[i]['metrics']['mpjpe'],
                           control_differentiation_l2=control_parameters[i]['parameter_l2']['differentiate'],
                           experiment_differentiation_l2=parameters[i]['parameter_l2']['differentiate'])
                       for i, row in enumerate(control_evaluations)]
    report = dict(diagnostic_count=len(diagnostics), matched_epoch_control=matched_control,
                  comparison_limitation='Single seed, 10 epochs; compare matched epochs, not convergence.', completed_epochs=10, initialization='fresh', optimizer='Adam', zero_decay_prefix='bbox_head.transformer.joint_differentiators.',
                  baseline_mpjpe_mm=baseline, best_epoch=best_index + 1,
                  best_mpjpe_mm=evaluations[best_index]['metrics']['mpjpe'],
                  improvement_mm=baseline - evaluations[best_index]['metrics']['mpjpe'],
                  best_checkpoint=str(best[0]), best_checkpoint_sha256=sha(best[0]),
                  final_checkpoint=str(OUT / 'epoch_10.pth'),
                  final_checkpoint_sha256=sha(OUT / 'epoch_10.pth'),
                  evaluations=evaluations, epoch_parameter_checks=parameters,
                  metric_protocol='legacy_GT_greedy_all100_frame_mean',
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
    axes[0].plot(epochs, [x['metrics']['mpjpe'] for x in evaluations], label='Refined pose')
    axes[0].axhline(baseline, color='grey', linestyle='--', label='2024 epoch442')
    for i, label in enumerate(('Coarse', 'Refine 1', 'Refine 2', 'Refine 3')):
        axes[1].plot(epochs, [x['fixed_final_pairing_stage_mpjpe'][i] for x in evaluations], label=label)
    for ax in axes:
        ax.set(xlabel='Epoch', ylabel='MPJPE (mm)')
        ax.grid(alpha=0.2)
        ax.legend()
    axes[0].set_title('Approved fresh 10-epoch differentiation no-decay Adam experiment')
    axes[1].set_title('Fixed final pairing')
    fig.savefig(OUT / 'training-curves.png', dpi=180)
    fig.savefig(OUT / 'training-curves.svg')
    plt.close(fig)
    print(json.dumps({k: v for k, v in report.items() if k not in ('evaluations', 'epoch_parameter_checks')}))


if __name__ == '__main__':
    main()

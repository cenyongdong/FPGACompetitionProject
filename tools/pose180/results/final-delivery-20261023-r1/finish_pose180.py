"""Final reports from one new CPU analysis and two immutable existing controls."""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time

os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['OMP_NUM_THREADS'] = '2'
os.environ['MKL_NUM_THREADS'] = '2'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.nice(5)
import numpy as np

RUN = Path('/public/cyd/Person-in-WiFi-3D-repo/result/piw24_pose180_shared_20261022_r1')
DEST = RUN / 'final-delivery-20261023-r1'
ANALYSIS = RUN / 'analysis-final-best-epoch99-r1'
PATHS = [RUN / 'analysis-original100-epoch442-r1', RUN / 'analysis-epoch59-counts-r1', ANALYSIS]
LABELS = ['原100-query epoch442', '180-query第59轮', '180-query最终最佳第99轮']
KEYS = ['original442', 'epoch59', 'final99']


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def flatten_group(g, candidate_count):
    n = g['frames']
    d = g['spatial_detection']['200']
    return dict(frames=n, mean_selected=g['mean_selected'],
                count_mae=(g['count_deficit'] + g['count_excess']) / n,
                fewer_frames=g['fewer_frames'], fewer_rate=g['fewer_frames'] / n,
                more_frames=g['more_frames'], more_rate=g['more_frames'] / n,
                duplicate_frames_200mm=d['frames_with_duplicate_like'],
                duplicate_rate_200mm=d['frames_with_duplicate_like'] / n,
                fn_200mm=d['fn'], fp_200mm=d['fp'], tp_200mm=d['tp'],
                recall_200mm=d['recall'], precision_200mm=d['precision'],
                legacy_mpjpe_mm=g['legacy_all%d_mpjpe_mm' % candidate_count],
                confidence_matched_mpjpe_mm=g['confidence_matched_mpjpe_mm'])


def main():
    started = time.time()
    status = read(ANALYSIS / 'status.json')
    assert status['status'] == 'completed' and status['native_exit'] == 0
    assert status['completed_frames'] == 7824 and status['checkpoint_epoch'] == 99
    reports = [read(p / 'summary.json') for p in PATHS]
    assert [r['checkpoint_epoch'] for r in reports] == [442, 59, 99]
    assert all(r['frames'] == 7824 and r['score_threshold'] == .2 for r in reports)
    files = [read(p / 'filenames.json') for p in PATHS]
    assert files[0] == files[1] == files[2] and len(files[0]) == len(set(files[0])) == 7824
    truth = [np.load(p / 'ground_truth.npy', mmap_mode='r') for p in PATHS]
    counts = [np.load(p / 'ground_truth_counts.npy', mmap_mode='r') for p in PATHS]
    assert all(np.array_equal(truth[0], t) for t in truth[1:])
    assert all(np.array_equal(counts[0], t) for t in counts[1:])
    frames = []
    for p in PATHS:
        with (p / 'frames.csv').open(newline='') as stream:
            frames.append(list(csv.DictReader(stream)))
    for rows in frames:
        assert len(rows) == 7824
        for i, row in enumerate(rows):
            assert int(row['index']) == i and row['name'] == files[0][i]
            assert int(row['real_people']) == int(counts[0][i])
    evaluations = [json.loads(x) for x in (RUN / 'evaluations.jsonl').read_text().splitlines() if x.strip()]
    assert len(evaluations) == 100 and all(e['frames'] == 7824 for e in evaluations)
    best_epoch, best_eval = min(enumerate(evaluations, 1), key=lambda x: x[1]['metrics']['mpjpe'])
    assert best_epoch == 99
    a, b = reports[2]['overall'], best_eval['metrics']
    differences = dict(legacy_mpjpe_mm=a['legacy_mpjpe_mm'] - b['mpjpe'],
                       confidence_matched_mpjpe_mm=a['confidence_matched_mpjpe_mm'] - b['matched_mpjpe_at_0_2'],
                       count_mae=a['count_mae'] - b['count_mae_at_0_2'],
                       mean_selected=a['mean_selected'] - b['mean_selected_at_0_2'])
    assert abs(differences['legacy_mpjpe_mm']) < 1e-3
    assert abs(differences['confidence_matched_mpjpe_mm']) < 1e-3
    progress = [json.loads(x) for x in (RUN / 'progress.jsonl').read_text().splitlines() if x.strip()]
    bad = []
    gradient_rows = 0
    for row in progress:
        values = dict(row.get('metrics', {}))
        grad = row.get('gradient_sample')
        if grad:
            values.update(grad)
            gradient_rows += 1
        if any(isinstance(v, (int, float)) and not math.isfinite(v) for v in values.values()):
            bad.append(row['iter'])
    assert not bad
    native = read(RUN / 'jobs/formal-r1/state.json')
    ddp = read(RUN / 'ddp_completion.json')
    assert native['native_exit'] == 0 and ddp['epoch'] == 100 and ddp['iter'] == 562200
    assert len(ddp['ranks']) == 2 and len({r['query_sha256'] for r in ddp['ranks']}) == 1
    # Inspect the final checkpoint metadata without loading or running a model.
    import torch
    torch.set_num_threads(2)
    final_checkpoint = torch.load(DEST / 'checkpoints/epoch_100.pth', map_location='cpu')
    assert final_checkpoint['meta']['epoch'] == 100
    del final_checkpoint
    verification = dict(passed=True, frames=7824, exact_filenames=True, exact_ground_truth=True,
                        exact_ground_truth_counts=True, exact_csv_index_name_counts=True,
                        control_inference_reused=True, new_inference_only_epoch=99,
                        inference_device='cpu', inference_threads=2, best_over_100_epoch=best_epoch,
                        evaluation_metric_differences=differences, finite_progress_records=len(progress),
                        finite_gradient_records=gradient_rows, native_training_exit=0,
                        final_checkpoint_epoch=100, ddp_completion=ddp,
                        controls=[str(p) for p in PATHS[:2]], completed=time.time())
    write(ANALYSIS / 'verification.json', verification)
    write(DEST / 'verification.json', verification)
    comparison = DEST / 'comparison'
    comparison.mkdir(exist_ok=False)
    models = {}
    for key, label, p, r in zip(KEYS, LABELS, PATHS, reports):
        models[key] = dict(label=label, source=str(p), checkpoint=r['checkpoint'],
                           checkpoint_sha256=r['checkpoint_sha256'], candidate_count=r['candidate_count'],
                           overall=r['overall'], groups=r['groups'],
                           groups_flat={n: flatten_group(g, r['candidate_count']) for n, g in r['groups'].items()})
    deltas = {}
    for key in KEYS[:2]:
        deltas['final99_minus_' + key] = {}
        for n in ('1', '2', '3'):
            old, new = models[key]['groups_flat'][n], models['final99']['groups_flat'][n]
            deltas['final99_minus_' + key][n] = {k: new[k] - old[k] for k in new if k != 'frames'}
    write(comparison / 'comparison.json', dict(models=models, deltas=deltas,
          verification=verification, definitions=reports[2]['definitions'],
          main_spatial_threshold_mm=200, all_spatial_thresholds_mm=[100, 200, 300]))
    base_fields = ['index', 'name', 'real_people']
    metric_fields = [k for k in frames[0][0] if k not in base_fields]
    fields = base_fields + [key + '_' + f for key in KEYS for f in metric_fields]
    fields += ['final99_minus_' + key + '_' + f for key in KEYS[:2] for f in metric_fields]
    with (comparison / 'paired_frames.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for i in range(7824):
            row = {f: frames[0][i][f] for f in base_fields}
            for key, rows in zip(KEYS, frames):
                row.update({key + '_' + f: rows[i][f] for f in metric_fields})
            for key, old in zip(KEYS[:2], frames[:2]):
                for f in metric_fields:
                    x, y = frames[2][i][f], old[i][f]
                    row['final99_minus_' + key + '_' + f] = float(x) - float(y) if x != '' and y != '' else ''
            writer.writerow(row)
    flat = [models[k]['groups_flat'] for k in KEYS]
    lines = ['# 100轮最终最佳第99轮与epoch442、第59轮对比', '',
             '2026-10-23，Asia/Shanghai。正式训练native exit 0，100轮均完成7,824帧评估；两个DDP rank结束时query权重SHA256一致。', '',
             '全100轮原口径MPJPE最小的实际已保存权重为`best_mpjpe_epoch_99.pth`，不是第100轮。第99轮原口径MPJPE为%.6f mm，第100轮为%.6f mm。' % (best_eval['metrics']['mpjpe'], evaluations[-1]['metrics']['mpjpe']), '',
             '三个模型使用完全相同的7,824帧：1／2／3人分别2,586／3,184／2,054帧。仅第99轮重新CPU推理；epoch442和第59轮直接复用已有summary、逐帧统计、文件名和GT，已逐帧核对一致。', '',
             '所有三元组固定顺序为 **原100-query epoch442／180-query第59轮／180-query最终最佳第99轮**。分数严格使用`score > 0.2`，空间检出以200mm作为主要诊断口径。', '',
             '## 高分query完整数量分布', '', '| 高分query数 | 真实1人 | 真实2人 | 真实3人 |', '|---|---:|---:|---:|']
    maximum = max(int(k) for r in reports for g in r['groups'].values() for k in g['selected_count_histogram'])
    for c in range(maximum + 1):
        cells = ['／'.join(str(r['groups'][n]['selected_count_histogram'].get(str(c), 0)) for r in reports) for n in ('1', '2', '3')]
        lines.append('| %d | %s |' % (c, ' | '.join(cells)))
    lines += ['', '## 数量不足、多报和疑似重复', '',
              '数量不足/过多按高分query数与真实人数比较，疑似重复按200mm空间定义；表内为帧数（帧率）。', '',
              '| 真实人数 | 数量不足帧 | 数量过多帧 | 疑似重复帧 |', '|---|---:|---:|---:|']
    for n in ('1', '2', '3'):
        cells = []
        for count, rate in [('fewer_frames', 'fewer_rate'), ('more_frames', 'more_rate'), ('duplicate_frames_200mm', 'duplicate_rate_200mm')]:
            cells.append('／'.join('%d（%.2f%%）' % (f[n][count], f[n][rate] * 100) for f in flat))
        lines.append('| %s | %s |' % (n, ' | '.join(cells)))
    lines += ['', '| 真实人数 | 平均高分query数 | 人数MAE |', '|---|---:|---:|']
    for n in ('1', '2', '3'):
        lines.append('| %s | %s | %s |' % (n, '／'.join('%.4f' % f[n]['mean_selected'] for f in flat), '／'.join('%.4f' % f[n]['count_mae'] for f in flat)))
    lines += ['', '## 空间检出（200mm）', '',
              'FN/FP为真人数/预测数，召回率按真人加权；人数恰好一致也可能同时存在空间FN和FP。', '',
              '| 真实人数 | FN | FP | 召回率 | 精确率 |', '|---|---:|---:|---:|---:|']
    for n in ('1', '2', '3'):
        cells = ['／'.join(str(f[n][v]) for f in flat) for v in ('fn_200mm', 'fp_200mm')]
        cells += ['／'.join('%.2f%%' % (f[n][v] * 100) for f in flat) for v in ('recall_200mm', 'precision_200mm')]
        lines.append('| %s | %s |' % (n, ' | '.join(cells)))
    lines += ['', '## MPJPE（mm，越低越好）', '', '| 真实人数 | 原口径MPJPE | 分数阈值后匹配MPJPE |', '|---|---:|---:|']
    for n in ('1', '2', '3'):
        lines.append('| %s | %s | %s |' % (n, '／'.join('%.2f' % f[n]['legacy_mpjpe_mm'] for f in flat), '／'.join('%.2f' % f[n]['confidence_matched_mpjpe_mm'] for f in flat)))
    lines.append('| 整体 | %s | %s |' % ('／'.join('%.2f' % r['overall']['legacy_mpjpe_mm'] for r in reports), '／'.join('%.2f' % r['overall']['confidence_matched_mpjpe_mm'] for r in reports)))
    lines += ['', '## 改善与变差', '']
    metric_names = dict(fewer_frames='数量不足帧', more_frames='数量过多帧',
                        duplicate_frames_200mm='疑似重复帧', fn_200mm='空间FN',
                        fp_200mm='空间FP', legacy_mpjpe_mm='原口径MPJPE',
                        confidence_matched_mpjpe_mm='阈值匹配MPJPE', count_mae='人数MAE')
    for key, label in zip(KEYS[:2], LABELS[:2]):
        for n in ('1', '2', '3'):
            delta = deltas['final99_minus_' + key][n]
            improved = [name for metric, name in metric_names.items() if delta[metric] < -1e-8]
            worse = [name for metric, name in metric_names.items() if delta[metric] > 1e-8]
            equal = [name for metric, name in metric_names.items() if abs(delta[metric]) <= 1e-8]
            lines.append('- 相对%s，真实%s人：改善：%s；变差：%s；持平：%s。' %
                         (label, n, '、'.join(improved) or '无', '、'.join(worse) or '无', '、'.join(equal) or '无'))
    for key, label in zip(KEYS[:2], LABELS[:2]):
        lines += ['', '## 最终第99轮相对%s的差值' % label, '',
                  '帧数、人数与mm为新值减旧值；召回率是百分点。负的错误/问题数表示改善，正的召回率表示改善。', '',
                  '| 真实人数 | 数量不足帧 | 数量过多帧 | 疑似重复帧 | FN | FP | 召回率百分点 | 原口径mm | 阈值匹配mm |', '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
        for n in ('1', '2', '3'):
            d = deltas['final99_minus_' + key][n]
            cells = ['%+d' % d[v] for v in ('fewer_frames', 'more_frames', 'duplicate_frames_200mm', 'fn_200mm', 'fp_200mm')]
            cells += ['%+.2f' % (d['recall_200mm'] * 100), '%+.2f' % d['legacy_mpjpe_mm'], '%+.2f' % d['confidence_matched_mpjpe_mm']]
            lines.append('| %s | %s |' % (n, ' | '.join(cells)))
    lines += ['', '## 口径与限制', '',
              '- 原口径MPJPE：沿用原`calc_mpjpe`，对全部100/180个候选做GT辅助贪心一一匹配，再按帧平均。候选数不同会影响可选空间，原口径最优不代表检出全面最优。',
              '- 分数阈值后匹配MPJPE：先保留score > 0.2候选，再用Hungarian最小化14关节平均三维距离，只对已匹配人对计算均值；这里不再施加200mm门限，未匹配真人和多余候选不进入该均值。',
              '- 空间检出：100/200/300mm分别最大化门限内一一匹配数，再最小化距离；未配对真人为FN，未配对候选为FP。所有距离使用绝对坐标，无根节点对齐、尺度或刚体配准。',
              '- 疑似重复：未匹配的高分候选距离已被另一候选覆盖的某真人不超过所用空间门限，是诊断定义，不能替代人工重复标签。',
              '- 数量不足只揭示一部分漏检，数量过多不能直接等同于重复；必须结合空间FN/FP、疑似重复和两列MPJPE判断。',
              '- 100/200/300mm完整分组指标和精确差值见comparison.json；逐帧三组与差值见paired_frames.csv。此次没有重跑两组对照，也没有改变训练或统计门限。',
              '- CPU ONNX/ORT仅检验三个真实输入的结构与数值一致性，已保存完整输出。未部署Lite或做板端长期稳定性验证，本结果不能认定D47已根治。', '',
              '## 产物', '',
              '- 最佳与最终权重、配置、完整日志、逐轮评估和DDP结束记录：上级目录checkpoints/和training/。',
              '- 最终最佳7824帧原始预测、GT、状态、摘要与逐帧数据：`%s`。' % ANALYSIS,
              '- 无TopK完整ONNX及三帧PyTorch/ORT输出：上级目录onnx/。',
              '- 训练/评估曲线：上级目录training_curves.png，精确逐轮数据见evaluations.csv。',
              '- 检查点和ONNX传输身份：上级目录identities.json。', '']
    (comparison / 'REPORT.md').write_text('\n'.join(lines))
    # Curves are generated after the one new inference process has completed.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10})
    epochs = list(range(1, 101))
    train = [p for p in progress if 'loss' in p.get('metrics', {})]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    axes[0, 0].plot([p['iter'] / 5622 for p in train], [p['metrics']['loss'] for p in train], linewidth=.6)
    axes[0, 0].set(title='Training loss (logged samples)', xlabel='Epoch', ylabel='Loss')
    axes[0, 1].plot(epochs, [e['metrics']['mpjpe'] for e in evaluations], label='180-query: original metric')
    axes[0, 1].axhline(reports[0]['overall']['legacy_mpjpe_mm'], color='gray', linestyle='--', label='100-query epoch442')
    axes[0, 1].scatter([99], [best_eval['metrics']['mpjpe']], color='red', label='Selected epoch99')
    axes[0, 1].set(title='Original MPJPE (7824 frames / epoch)', xlabel='Epoch', ylabel='mm')
    axes[1, 0].plot(epochs, [e['metrics']['matched_mpjpe_at_0_2'] for e in evaluations], label='180-query: score > 0.2')
    axes[1, 0].axhline(reports[0]['overall']['confidence_matched_mpjpe_mm'], color='gray', linestyle='--', label='100-query epoch442')
    axes[1, 0].set(title='Confidence-matched MPJPE', xlabel='Epoch', ylabel='mm')
    axes[1, 1].plot(epochs, [e['metrics']['count_mae_at_0_2'] for e in evaluations], label='180-query')
    axes[1, 1].axhline(reports[0]['overall']['count_mae'], color='gray', linestyle='--', label='100-query epoch442')
    axes[1, 1].set(title='People count MAE (score > 0.2)', xlabel='Epoch', ylabel='People / frame')
    for ax in axes.flat:
        ax.grid(alpha=.25)
        if ax is not axes[0, 0]:
            ax.legend(fontsize=8)
    fig.suptitle('180-query shared joint decoder: 100 completed epochs')
    fig.savefig(DEST / 'training_curves.png', dpi=160)
    fig.savefig(DEST / 'training_curves.pdf')
    plt.close(fig)
    columns = ['epoch', 'frames', 'time'] + list(evaluations[0]['metrics'])
    with (DEST / 'evaluations.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for epoch, e in enumerate(evaluations, 1):
            writer.writerow(dict(epoch=epoch, frames=e['frames'], time=e['time'], **e['metrics']))
    identities = {'checkpoints/best_mpjpe_epoch_99.pth': reports[2]['checkpoint_sha256'],
                  'checkpoints/epoch_100.pth': digest(DEST / 'checkpoints/epoch_100.pth'),
                  'onnx/pose180_shared.onnx': digest(DEST / 'onnx/pose180_shared.onnx')}
    write(DEST / 'identities.json', identities)
    for f in ['summary.json', 'frames.csv', 'status.json', 'launch.json', 'verification.json', 'filenames.json', 'ground_truth.npy', 'ground_truth_counts.npy', 'stdout.log', 'stderr.log']:
        import shutil
        target = DEST / 'analysis-final-best-epoch99-r1'
        target.mkdir(exist_ok=True)
        shutil.copy2(ANALYSIS / f, target / f)
    # Raw scores/poses stay in the independent server analysis directory.
    write(DEST / 'completion.json', dict(status='completed', native_exit=0, best_epoch=99,
          training_native_exit=0, export_native_exit=read(DEST / 'export-status.json')['native_exit'],
          analysis_native_exit=status['native_exit'], comparison_verified=True,
          raw_predictions_server_directory=str(ANALYSIS), completed=time.time(),
          seconds=time.time() - started))
    print(json.dumps({'verification': verification, 'models_flat': {k: v['groups_flat'] for k, v in models.items()},
                     'overall': {k: v['overall'] for k, v in models.items()}, 'identities': identities}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()

"""Read-only analysis of frozen full-100 inference outputs; no model execution."""
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np

PROJECT = Path('D:/FPGACompetitionProject')
SOURCE = PROJECT / '.local/shared-refine-20261014-r1/shared_refine_20261014_r1'
REPO = Path('D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo')
OUT = Path(__file__).resolve().parent / 'results.json'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def greedy(distance):
    """Global minimum, one-to-one matching, as in calc_mpjpe, in float64."""
    d = distance.copy()
    n = d.shape[0]
    selected = np.full(n, -1, dtype=np.int64)
    for _ in range(n):
        row, col = np.unravel_index(np.argmin(d), d.shape)
        assert np.isfinite(d[row, col]) and d[row, col] < 50
        selected[row] = col
        d[row, :] = np.inf
        d[:, col] = np.inf
    return selected


def main():
    start = time.monotonic()
    assert not OUT.exists(), 'Do not overwrite a completed analysis'
    summary = json.loads((SOURCE / 'summary.json').read_text())
    rows = [json.loads(s) for s in (SOURCE / 'frames.jsonl').read_text().splitlines()]
    identities = {}
    for name in ('before.boxes.npy', 'before.poses.npy'):
        digest = sha(SOURCE / name)
        assert digest == summary['output_sha256'][name], name
        identities[name] = digest
    boxes = np.load(SOURCE / 'before.boxes.npy', mmap_mode='r', allow_pickle=False)
    poses = np.load(SOURCE / 'before.poses.npy', mmap_mode='r', allow_pickle=False)
    assert poses.shape == (7824, 100, 14, 3) and boxes.shape == (7824, 100, 5)
    assert len(rows) == len(poses)
    ks = (3, 5, 10, 20, 50, 100)
    records = []
    matched_ranks = []
    single_top1 = []
    score_counts = {str(t): [] for t in (0.1, 0.3, 0.5)}
    maximum_baseline_difference = 0.
    for i, row in enumerate(rows):
        assert time.monotonic() - start < 120, 'Offline analysis budget exceeded'
        assert row['index'] == i
        gt_path = REPO / 'data/wifipose/test_data/keypoint' / (row['sample'] + '.npy')
        assert sha(gt_path) == row['gt_sha256'], str(gt_path)
        gt = np.load(gt_path, allow_pickle=False).astype(np.float64)
        pred = poses[i].astype(np.float64)
        assert gt.shape == (row['persons'], 14, 3)
        assert np.isfinite(gt).all() and np.isfinite(pred).all()
        scores = boxes[i, :, 4]
        assert np.isfinite(scores).all() and (scores[:-1] >= scores[1:]).all()
        for threshold, counts in score_counts.items():
            counts.append(int((scores >= float(threshold)).sum()))
        distances = np.sqrt(np.square(gt[:, None] - pred[None]).sum(axis=-1)).mean(axis=-1)
        full_assignment = greedy(distances)
        full_metric = float(distances[np.arange(len(gt)), full_assignment].mean() * 1000)
        maximum_baseline_difference = max(maximum_baseline_difference,
            abs(full_metric - row['metric_mm']['before'][0]))
        ranks = full_assignment + 1
        matched_ranks.extend(ranks.tolist())
        if len(gt) == 1:
            single_top1.append(float(distances[0, 0] * 1000))
        items = {}
        for k in ks:
            choice = greedy(distances[:, :k])
            items[str(k)] = dict(mpjpe_mm=float(distances[np.arange(len(gt)), choice].mean() * 1000),
                                 retained=int((full_assignment < k).sum()),
                                 all_retained=bool((full_assignment < k).all()))
        records.append(dict(index=i, persons=len(gt), metrics=items))
    assert maximum_baseline_difference < 0.001, 'Independent metric did not reproduce saved baseline'
    groups = {}
    for people in (0, 1, 2, 3):
        subset = [r for r in records if people == 0 or r['persons'] == people]
        total_people = sum(r['persons'] for r in subset)
        metrics = {}
        for k in ks:
            metrics[str(k)] = dict(
                frame_mean_mpjpe_mm=float(np.mean([r['metrics'][str(k)]['mpjpe_mm'] for r in subset])),
                full100_matches_retained_percent=100 * sum(r['metrics'][str(k)]['retained'] for r in subset) / total_people,
                frames_all_full100_matches_retained_percent=100 * np.mean([r['metrics'][str(k)]['all_retained'] for r in subset]))
        groups[str(people) if people else 'all'] = dict(frames=len(subset), people=total_people, topk=metrics)
    ranks = np.asarray(matched_ranks)
    result = dict(
        status='completed', platform=platform.platform(), python=sys.version,
        numpy=np.__version__, cwd=str(Path.cwd()), elapsed_seconds=time.monotonic()-start,
        source=str(SOURCE), repository=str(REPO), source_sha256=identities,
        gt_hashes_verified=len(rows), maximum_baseline_difference_mm=maximum_baseline_difference,
        protocol='Frozen FP32 full100 outputs; float64 distances, original global greedy one-to-one GT matching; per-frame mean. TopK is final confidence rank, not original query ID. No reduced-query model executed.',
        groups=groups,
        full100_selected_rank_percentiles={str(q): float(np.percentile(ranks, q)) for q in (50, 90, 95, 99, 100)},
        single_person_top1_frame_mean_mpjpe_mm=float(np.mean(single_top1)),
        confidence_candidate_count={t: dict(mean=float(np.mean(v)), maximum=int(max(v)),
            p95=float(np.percentile(v,95))) for t,v in score_counts.items()},
        limits=['No query pruning or model/weights/configuration change.',
                'Does not estimate new-model runtime or accuracy after query removal.',
                'GT-assisted oracle metric is not confidence-driven detection accuracy.',
                'Smaller greedy candidate sets need not yield monotonically increasing error.'])
    OUT.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()

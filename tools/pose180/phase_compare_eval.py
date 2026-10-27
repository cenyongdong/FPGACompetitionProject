"""Fixed-model CPU ONNX comparison, including full outputs before scoring.

Top3 + score>0.2 reproduces the current raw candidate selection. Geometry
filtering/holding is not applied; GT is used only after the model forward.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import numpy as np
import onnxruntime as ort
from scipy.optimize import linear_sum_assignment


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')


def describe(values):
    values = np.asarray(values, dtype=float)
    if not values.size:
        return None
    return dict(n=int(values.size), mean=float(values.mean()), p50=float(np.median(values)),
                p95=float(np.percentile(values, 95)), max=float(values.max()))


def cost(a, b):
    return np.linalg.norm(a[:, None].astype(float)-b[None, :], axis=-1).mean(axis=-1)*1000


def selected(scores):
    indices = np.lexsort((np.arange(180), -scores))[:3]
    return indices[scores[indices] > np.float32(.2)]


def metrics(indices, frames, scores, poses):
    rows, variants = [], []
    gt_errors = [dict(), dict()]
    for v in range(2):
        counts, max_scores, errors, oracle, jumps = [], [], [], [], []
        people_gt = false_negative = false_positive = within200 = 0
        count_errors = []
        last = None
        for i in indices:
            frame = frames[i]
            keep = selected(scores[i, v])
            predicted = poses[i, v, keep]
            counts.append(len(keep))
            max_scores.append(float(scores[i, v].max()))
            row = dict(index=i, variant=v, count=len(keep), max_score=max_scores[-1], matched_mpjpe_mm=None)
            if frame['gt'] is not None:
                gt = np.asarray(frame['gt'], dtype=float)
                people_gt += len(gt)
                count_errors.append(abs(len(keep)-len(gt)))
                false_negative += max(0, len(gt)-len(keep))
                false_positive += max(0, len(keep)-len(gt))
                if len(keep):
                    distances = cost(predicted, gt)
                    pred_match, gt_match = linear_sum_assignment(distances)
                    matched = distances[pred_match, gt_match]
                    errors.extend(matched.tolist())
                    within200 += int((matched <= 200).sum())
                    row['matched_mpjpe_mm'] = float(matched.mean())
                    for g, e in zip(gt_match, matched):
                        gt_errors[v][(i, int(g))] = float(e)
                all_cost = cost(poses[i, v], gt)
                p, g = linear_sum_assignment(all_cost)
                oracle.extend(all_cost[p, g].tolist())
            if last is not None and frame['clip'] == last[0] and len(predicted) and len(last[1]):
                distances = cost(predicted, last[1])
                p, q = linear_sum_assignment(distances)
                jumps.extend(distances[p, q].tolist())
            last = (frame['clip'], predicted)
            rows.append(row)
        changes = sum(counts[j] != counts[j-1] for j in range(1, len(counts))
                      if frames[indices[j]]['clip'] == frames[indices[j-1]]['clip'])
        variants.append(dict(frames=len(indices), count_histogram={str(k): counts.count(k) for k in range(4)},
                             count_changes=changes, max_score=describe(max_scores),
                             adjacent_matched_pose_step_mm=describe(jumps),
                             count_mae=float(np.mean(count_errors)) if count_errors else None,
                             gt_people=people_gt or None, matched_people=len(errors) if people_gt else None,
                             missed_by_count=false_negative if people_gt else None,
                             extra_by_count=false_positive if people_gt else None,
                             matched_mpjpe_mm=describe(errors),
                             matched_gt_coverage=len(errors)/people_gt if people_gt else None,
                             matched_within200mm=within200 if people_gt else None,
                             all180_GT_assisted_oracle_mpjpe_mm=describe(oracle)))
    common = sorted(gt_errors[0].keys() & gt_errors[1].keys())
    pair = dict(common_matched_gt_people=len(common),
                original_mpjpe_mm=describe([gt_errors[0][k] for k in common]),
                continuous_mpjpe_mm=describe([gt_errors[1][k] for k in common]))
    if common:
        delta = np.array([gt_errors[1][k]-gt_errors[0][k] for k in common])
        pair.update(delta_mm=describe(delta), improved_people=int((delta < -1e-5).sum()),
                    worsened_people=int((delta > 1e-5).sum()))
    return dict(original=variants[0], continuous=variants[1], common_gt=pair), rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--corpus', type=Path, required=True)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--model-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    model_hash = hashlib.sha256(a.model.read_bytes()).hexdigest()
    if model_hash != a.model_sha256:
        raise ValueError('Model identity differs')
    manifest = json.loads((a.corpus / 'manifest.json').read_text())
    n = len(manifest['frames'])
    inputs = []
    for name in ('original.f32', 'continuous.f32'):
        path = a.corpus / name
        if path.stat().st_size != n*10800*4 or hashlib.sha256(path.read_bytes()).hexdigest() != manifest['hashes'][name]:
            raise ValueError('Transferred input identity differs: ' + name)
        inputs.append(np.memmap(path, mode='r', dtype='<f4', shape=(n, 1, 180, 60)))
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 2
    opts.inter_op_num_threads = 1
    opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    session = ort.InferenceSession(str(a.model), sess_options=opts, providers=['CPUExecutionProvider'])
    if len(session.get_inputs()) != 1 or session.get_inputs()[0].shape != [1, 180, 60]:
        raise ValueError('Model input port differs')
    ports = session.get_outputs()
    score_port = next(j for j, port in enumerate(ports) if port.shape == [1, 180])
    pose_port = next(j for j, port in enumerate(ports) if port.shape == [1, 180, 14, 3])
    scores = np.lib.format.open_memmap(a.output / 'scores.npy', mode='w+', dtype='<f4', shape=(n, 2, 180))
    poses = np.lib.format.open_memmap(a.output / 'poses.npy', mode='w+', dtype='<f4', shape=(n, 2, 180, 14, 3))
    state = dict(pid=os.getpid(), started_utc=datetime.now(timezone.utc).isoformat(), frames=n,
                 completed_frames=0, model_sha256=model_hash, providers=session.get_providers(), SDK=False, CSI_live=False)
    save(a.output / 'state.json', state)
    for i in range(n):
        for v in range(2):
            output = session.run(None, {session.get_inputs()[0].name: np.asarray(inputs[v][i])})
            if not all(np.isfinite(tensor).all() for tensor in output):
                raise ValueError(f'Non-finite actual output at frame={i}, variant={v}')
            scores[i, v] = output[score_port][0]
            poses[i, v] = output[pose_port][0]
        if (i+1) % 50 == 0 or i+1 == n:
            scores.flush()
            poses.flush()
            state.update(completed_frames=i+1, elapsed_s=time.time()-started)
            save(a.output / 'state.json', state)
            print('Actual paired model forwards', i+1, '/', n, 'elapsed_s', round(time.time()-started, 1), flush=True)
    scores.flush()
    poses.flush()
    if scores.min() < 0 or scores.max() > 1:
        raise ValueError('Expected probability output; do not silently change score interpretation')
    report = dict(model=str(a.model), model_sha256=model_hash, ort_version=ort.__version__,
                  providers=session.get_providers(), raw_outputs_saved=True, actual_forwards=n*2, CSI_live=False, SDK=False,
                  selection='Top3 by score descending / candidate index ascending; strict float32 score>0.2',
                  error='absolute coordinates, no root alignment; confidence-selected poses Hungarian matched by mean 14-joint Euclidean distance, mm',
                  temporal='adjacent selected poses Hungarian matched; descriptive change only, no GT accuracy claim',
                  all180_oracle='GT-assisted matching across all queries; diagnostic only, never inference selection',
                  results={}, clips={})
    all_rows = []
    for split in ('test', 'train', 'real'):
        indices = [i for i, frame in enumerate(manifest['frames']) if frame['split'] == split]
        report['results'][split], rows = metrics(indices, manifest['frames'], scores, poses)
        all_rows.extend(rows)
    for clip in manifest['clips']:
        indices = list(range(clip['first'], clip['first']+clip['count']))
        report['clips'][clip['clip']], _ = metrics(indices, manifest['frames'], scores, poses)
    save(a.output / 'perframe.json', all_rows)
    report['elapsed_s'] = time.time()-started
    save(a.output / 'report.json', report)
    state.update(complete=True, elapsed_s=report['elapsed_s'])
    save(a.output / 'state.json', state)
    print('Completed', n*2, 'actual CPU model forwards', flush=True)


if __name__ == '__main__':
    main()

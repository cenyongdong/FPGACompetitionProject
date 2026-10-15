"""Read all saved outputs independently; verify hashes, bounds and frame means."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
p = args.directory.resolve()
summary = json.loads((p / 'summary.json').read_text(encoding='utf-8'))
execution = json.loads((p / 'execution.json').read_text(encoding='utf-8'))
assert execution['status'] == 'complete' and execution['exit_code'] == 0
assert summary['frames'] == 7824 and summary['numerical_gate_passed']
assert summary['topk_retained'] == 2 and summary['candidates'] == 100
assert not (p / 'failure.json').exists()

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

for name, expected in summary['output_sha256'].items():
    assert sha(p / name) == expected, name
rows = [json.loads(s) for s in (p / 'frames.jsonl').read_text(encoding='utf-8').splitlines()]
assert [r['index'] for r in rows] == list(range(7824))
assert len({r['sample'] for r in rows}) == 7824
data = {}
for name, shape in [('boxes',(7824,100,5)),('poses',(7824,100,14,3)),('references',(7824,2,100,14,3))]:
    a = np.load(p / ('before.'+name+'.npy'), mmap_mode='r')
    b = np.load(p / ('after.'+name+'.npy'), mmap_mode='r')
    assert a.shape == b.shape == shape and a.dtype == b.dtype == np.dtype('<f4')
    max_abs, mismatch, changed_frames, max_joint_mm = 0., 0, 0, 0.
    for start in range(0,7824,128):
        x,y = a[start:start+128],b[start:start+128]
        assert np.isfinite(x).all() and np.isfinite(y).all()
        mask = x.view('u4') != y.view('u4')
        mismatch += int(np.count_nonzero(mask))
        changed_frames += int(mask.reshape(len(mask),-1).any(axis=1).sum())
        diff = y.astype(np.float64)-x.astype(np.float64)
        max_abs = max(max_abs,float(np.abs(diff).max()))
        if name == 'poses':
            max_joint_mm = max(max_joint_mm,float(np.sqrt(np.sum(diff*diff,axis=-1)).max())*1000)
        if name == 'boxes':
            assert x[:,:,4].tobytes() == y[:,:,4].tobytes()
    assert max_abs <= 1e-5
    data[name] = dict(max_abs=max_abs, mismatch_values=mismatch, changed_frames=changed_frames)
    if name == 'poses':
        data[name]['maximum_joint_displacement_mm'] = max_joint_mm
all_mismatch = sum(v['mismatch_values'] for v in data.values())
assert all_mismatch == summary['mismatch_values']
assert max(v['max_abs'] for v in data.values()) == summary['maximum_absolute_difference']
for mode in ('before','after'):
    mean = np.asarray([r['metric_mm'][mode] for r in rows]).mean(axis=0)
    assert mean.tolist() == list(summary['metrics'][mode].values())
groups = {}
for persons in (1,2,3):
    group = [r for r in rows if r['persons'] == persons]
    before = np.asarray([r['metric_mm']['before'][0] for r in group])
    after = np.asarray([r['metric_mm']['after'][0] for r in group])
    groups[str(persons)] = dict(frames=len(group), before_mpjpe=float(before.mean()),
        after_mpjpe=float(after.mean()),delta_mm=float(after.mean()-before.mean()),
        maximum_frame_abs_delta_mm=float(np.abs(after-before).max()))
deltas = np.asarray([r['metric_mm']['after'][0]-r['metric_mm']['before'][0] for r in rows])
result = dict(status='independent_full_delivery_verified',frames=len(rows),
              complete_raw_output_hashes=True,arrays=data,all_scores_bitwise=True,
              by_person_count=groups,mpjpe_delta_mm=summary['mpjpe_delta_mm'],
              changed_mpjpe_frames=int(np.count_nonzero(deltas)),
              maximum_frame_abs_mpjpe_delta_mm=float(np.abs(deltas).max()),
              numerical_bound_not_bitwise_deployment_acceptance=True,
              local_raw_directory=str(p),execution=execution)
args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))

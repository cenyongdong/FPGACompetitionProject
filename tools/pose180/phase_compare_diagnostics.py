"""Signal diagnostics on unique archived events, separate from pose accuracy."""
import argparse
import json
from pathlib import Path
import numpy as np


def circular(v):
    return np.angle(np.exp(1j*v))


def describe(v):
    return dict(count=int(v.size), p95_rad=float(np.percentile(v, 95)), max_rad=float(v.max())) if v.size else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--corpus', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Refusing to overwrite diagnostic output')
    manifest = json.loads((a.corpus / 'manifest.json').read_text())
    n = len(manifest['frames'])
    variants = [np.memmap(a.corpus / (name + '.f32'), mode='r', dtype='<f4', shape=(n, 3, 3, 20, 60))
                for name in ('original', 'continuous')]
    identities = np.memmap(a.corpus / 'identities.bin', mode='r', dtype='<u8', shape=(n, 3, 20, 3))
    result = dict(definition='unique events in source order, per RX, excluding source intervals>10ms; broad step: antenna0 >=15/30 circular carrier changes>0.25rad',
                  actual_accuracy_claim=False, clips={})
    for clip in manifest['clips']:
        per_rx = []
        for r in range(3):
            seen = set()
            phases = [[], []]
            times = []
            antenna_error = []
            for i in range(clip['first'], clip['first']+clip['count']):
                for t in range(20):
                    epoch, sample, time = map(int, identities[i, r, t])
                    if (epoch, sample) in seen:
                        continue
                    seen.add((epoch, sample))
                    times.append(time)
                    for v in range(2):
                        phases[v].append(variants[v][i, r, :, t, 30:].astype(float))
                    for b in (1, 2):
                        mask = (variants[0][i, r, 0, t, :30] > 0) & (variants[0][i, r, b, t, :30] > 0)
                        diff = circular(phases[0][-1][0]-phases[0][-1][b]-phases[1][-1][0]+phases[1][-1][b])
                        antenna_error.extend(abs(diff[mask]).tolist())
            valid = np.diff(times) <= 10000000
            if np.any(np.diff(times) <= 0):
                raise ValueError('Non-monotonic unique source timeline')
            stats = []
            for phase in phases:
                values = np.stack(phase)
                steps = np.abs(circular(np.diff(values, axis=0)))[valid, 0, :]
                stats.append(dict(broad_steps_over_point25=int((np.sum(steps > .25, axis=1) >= 15).sum()),
                                  antenna0_circular_steps=describe(steps)))
            per_rx.append(dict(receiver=r+1, unique_events=len(times), omitted_gaps=int((~valid).sum()),
                               original=stats[0], continuous=stats[1],
                               preserved_antenna_difference_max_rad=max(antenna_error, default=0)))
        result['clips'][clip['clip']] = dict(split=clip['split'], receivers=per_rx)
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({clip: [(r['original']['broad_steps_over_point25'], r['continuous']['broad_steps_over_point25'])
                            for r in row['receivers']] for clip, row in result['clips'].items()}))


if __name__ == '__main__':
    main()

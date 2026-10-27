"""Finite CPU benchmark on the target PS; never imports SDK or accesses devices.

Directory: pose_replay, filter_benchmark, identity.json, and raw/<dataset>/*.full.
stdout is one result object; full per-run data stays in results.json.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time


def main():
    root = Path(__file__).resolve().parent
    identity = json.loads((root / 'identity.json').read_text())
    for name, expected in identity['files'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Benchmark input mismatch: ' + name)
    for name in ('pose_replay', 'filter_benchmark'):
        (root / name).chmod(0o700)
    def optional(path):
        try:
            return Path(path).read_text().strip()
        except OSError:
            return None
    result = dict(started_unix=time.time(), uname=platform.uname()._asdict(),
        cpuinfo=optional('/proc/cpuinfo'), boot_id=optional('/proc/sys/kernel/random/boot_id'),
        governor=optional('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'),
        frequency_khz=optional('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'),
        affinity=sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else None,
        identity=identity, sdk_calls=0, BOOT_writes=0, new_inference=False, replays={})
    for folder in sorted((root / 'raw').iterdir()):
        runs=[]
        for trial in range(21):
            completed = subprocess.run([str(root / 'pose_replay'), *map(str, sorted(folder.glob('*.full')))],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=45, check=True)
            row=json.loads(completed.stderr);row['warmup_run']=trial==0;runs.append(row)
        kept=runs[1:]
        frames=sum(row['cpu_filter_frames'] for row in kept)
        coordinates=sum(row['cpu_filter_coordinates'] for row in kept)
        total_ns=sum(row['cpu_filter_total_ns'] for row in kept)
        result['replays'][folder.name]=dict(runs=runs, measured_runs=20,
            filter_frames=frames, filter_coordinates=coordinates,
            filter_mean_us=total_ns/1000/max(frames,1),
            filter_us_per_42_coordinates=total_ns/1000/max(coordinates/42,1),
            filter_max_us=max(row['cpu_filter_max_us'] for row in kept),
            postprocess_mean_us=sum(row['mean_compute_ms'] for row in kept)*1000/20,
            postprocess_max_us=max(row['max_compute_ms'] for row in kept)*1000)
    measured=subprocess.run([str(root / 'filter_benchmark')],stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,timeout=30,check=True)
    result['kernel_benchmark']=[json.loads(line) for line in measured.stdout.splitlines()]
    result['finished_unix']=time.time()
    (root / 'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('identity','cpuinfo','replays')}))
    for name, dataset in result['replays'].items():
        print(json.dumps(dict(dataset=name,**{k:v for k,v in dataset.items() if k!='runs'})))


if __name__=='__main__':
    main()

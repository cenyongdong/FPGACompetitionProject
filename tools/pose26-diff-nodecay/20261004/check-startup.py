"""Independently verify the live run and its captured sources; never restart it."""
import datetime
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path('/public/cyd/Person-in-WiFi-3D-repo')
OUT = ROOT / 'result/tpami2026_diff_nodecay_20261004'
def load(name): return json.loads((OUT / name).read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
status = load('pipeline-status.json')
assert status['stage'] == 'training', status
launch = load('pipeline-launch.json')
audit = load('prelaunch-audit.json')
for name, expected in audit['source_hashes'].items():
    assert sha(ROOT / name) == expected and sha(OUT / 'source_snapshot' / name) == expected, name
assert sha(OUT / 'resolved_config.py') == audit['config_sha256']
init = load('initialization.json')
assert init['checkpoint_loaded'] is False and init['optimizer_restored'] is False
groups = init['optimizer_groups']
assert len(groups) == 2 and [g['weight_decay'] for g in groups] == [0.0, 1e-4]
assert len(groups[0]['parameter_names']) == 56
assert all(n.startswith('bbox_head.transformer.joint_differentiators.') for n in groups[0]['parameter_names'])
assert all(not n.startswith('bbox_head.transformer.joint_differentiators.') for n in groups[1]['parameter_names'])
old_init = json.loads((ROOT / 'result/tpami2026_scratch_20261004/initialization.json').read_text())
assert init['module_parameter_l2'] == old_init['module_parameter_l2']
processes = subprocess.check_output(['ps', '-eo', 'pid,ppid,args'], text=True)
process_rows = []
for line in processes.splitlines()[1:]:
    fields = line.strip().split(None, 2)
    if len(fields) == 3:
        process_rows.append(dict(pid=int(fields[0]), ppid=int(fields[1]), command=fields[2]))
supervisor = next(p for p in process_rows if p['pid'] == launch['pid'])
child = next(p for p in process_rows if p['pid'] == status['child_pid'])
assert 'tools/pose26_diff_nodecay/run_experiment.py' in supervisor['command']
assert 'configs/wifi/petr_wifi_tpami2026_diff_nodecay.py' in child['command']
ranks = [p for p in process_rows if p['ppid'] == child['pid'] and 'tools/train.py' in p['command']]
assert len(ranks) == 4, ranks
rows = [json.loads(x) for x in (OUT / 'branch_diagnostics.jsonl').read_text().splitlines() if x.strip()]
def finite(value):
    if isinstance(value, dict): return all(finite(x) for x in value.values())
    if isinstance(value, list): return all(finite(x) for x in value)
    if isinstance(value, (int, float)): return math.isfinite(value)
    return True
assert rows and all(finite(x) for x in rows)
log = (OUT / 'train.stdout.log').read_text(errors='replace')
errors = [line for line in log.splitlines() if any(x in line for x in
          ('Traceback', 'Persistent branch collapse', 'Non-finite', 'ChildFailedError', 'DDP parameter divergence'))]
assert not errors, errors
record = dict(passed=True, checked_at=datetime.datetime.now().isoformat(),
              pipeline_status=status, launch=launch, source_hash_count=len(audit['source_hashes']),
              source_snapshot_and_current_hashes_match=True, resolved_config_hash_matches=True,
              initialization_matches_control=True, initialization=init,
              supervisor=supervisor, torchrun=child, ranks=ranks,
              gpu_state=subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.used,utilization.gpu',
                                                '--format=csv,noheader,nounits'], text=True),
              diagnostic_count=len(rows), first_diagnostic=rows[0], latest_diagnostic=rows[-1],
              all_recorded_diagnostics_finite=True, errors=errors,
              completed_evaluations=len((OUT/'evaluations.jsonl').read_text().splitlines())
                 if (OUT/'evaluations.jsonl').exists() else 0,
              log_tail=log.splitlines()[-12:], automatic_monitor_enabled=False)
(OUT / 'startup-verification.json').write_text(json.dumps(record, indent=2))
print(json.dumps({k: record[k] for k in ('passed', 'checked_at', 'source_hash_count', 'supervisor',
      'torchrun', 'ranks', 'gpu_state', 'diagnostic_count', 'first_diagnostic', 'latest_diagnostic', 'completed_evaluations')}))

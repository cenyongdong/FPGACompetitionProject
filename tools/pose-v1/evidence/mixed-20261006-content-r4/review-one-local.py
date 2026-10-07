"""Independent local review of returned r4 single-frame evidence; no board access."""
import hashlib
import json
from pathlib import Path
import numpy as np

base = Path(__file__).resolve().parent
run = base / 'mixed-one'
out = run / 'results'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x]
report_path = base / 'mixed-one-independent-review.json'
assert not report_path.exists()
checked = 0
for line in (run / 'files.sha256').read_text(encoding='utf-8').splitlines():
    digest, name = line.split(maxsplit=1)
    name = name.lstrip('*')
    p = run / name
    assert p.resolve().is_relative_to(run.resolve()) and sha(p) == digest
    checked += 1
assert (run / 'exit.txt').read_text().strip() == '0'
assert (run / 'run.stderr.log').stat().st_size == 0
assert sha(run / 'pose_mixed_check') == 'ba8d53985fabdfdc12939d794825d31a0ee29bf9516567be5ba9356c515dcea7'
content = json.loads((base / 'mixed-one-content-review.json').read_text(encoding='utf-8'))
assert len(content['records']) == 17 and content['first_mismatch'] is None
assert all(r['all_finite'] for r in content['records'])
input_rows = [r for r in content['records'] if r['kind'] in ('caller_input', 'input0_output')]
assert len(input_rows) == 2 and all(r['matches_fixed_reference'] for r in input_rows)
events = rows(out / 'operator-execution.jsonl')
assert len(events) == 14 and all(r['invocation'] == 0 and r['frame_id'] == 6 for r in events)
zg = sorted(r['op_id'] for r in events if 'ZG330BackendNode' in r['backend'])
host = sorted(r['op_id'] for r in events if 'HostBackendNode' in r['backend'])
assert zg == list(range(9185, 9192)) and host == [0,188,192,437,442,582,649]
bridge = rows(out / 'bridge.jsonl')
assert len(bridge) == 8 and sum(r['bytes'] for r in bridge) == 115360
assert all(r['action'] == 'input_to_host' and r['source']['pointer'] == 'ADDR'
           and r['destination']['pointer'] == 'CPTR' and r['invocation'] == 0 for r in bridge)
outputs = {}
for suffix, count in [('scores',100),('poses',4200)]:
    p = out / f'S11_01_308.{suffix}.f32'
    data = np.frombuffer(p.read_bytes(),dtype='<f4')
    assert len(data) == count and np.isfinite(data).all()
    old = base.parent / 'mixed-20261006-fusion-r3/mixed-one/results' / p.name
    assert old.exists()
    outputs[suffix] = dict(elements=count,sha256=sha(p),bitwise_equal_r3_single=p.read_bytes()==old.read_bytes())
assert (run / 'dmesg.before.log').read_bytes() == (run / 'dmesg.after.log').read_bytes()
report = dict(status='r4_single_content_independently_verified',exit=0,stderr_bytes=0,
    returned_files_verified=checked,package_files_verified=291,binary_sha256=sha(run/'pose_mixed_check'),
    sdk=json.loads((run/'sdk-audit.json').read_text()),device_version=json.loads((out/'device-version.json').read_text()),
    content_records=17,content_bytes=sum(r['bytes'] for r in content['records']),
    caller_and_actual_Input0_match_fixed_reference=True,input_alias_evidence=input_rows,
    zg_callback_ids=zg,host_callback_ids=host,bridge_input_copies=8,bridge_bytes=115360,
    supplied_output_writeback_exercised=False,outputs=outputs,
    timing=rows(out/'results.jsonl')[0],dmesg_unchanged=True,
    memory_before=(run/'memory.before.txt').read_text(),memory_after=(run/'memory.after.txt').read_text(),
    acceptance_sha256=sha(base/'mixed-one.acceptance.json'),
    continuous_input_freshness_verified=False,r3_failure_fixed=False,numerical_accepted=False,performance_accepted=False,
    agent_activity='Local evidence review only; no board access or rerun.',
    next_stage='User executes one 300-second three-case content diagnostic with repeated first frame in the same Session.')
report_path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(dict(returned_files=checked,content_records=17,content_bytes=report['content_bytes'],outputs=outputs),indent=2))

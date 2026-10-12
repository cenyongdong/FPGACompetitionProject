"""Independent prepared-path/consumption audit; no device or file repair."""
from pathlib import Path
import json, sys, hashlib

R = Path(__file__).resolve().parents[2]
E = R / 'tools/pose-v1/evidence/producer-prepared-20261011-r1'
mode = sys.argv[1]
assert mode in ('host', 'four', 'off', 'on')
D = E / (mode + '-return/run-' + mode)
load = lambda p: json.loads(p.read_text())
if mode == 'host':
    assert (D/'exit.txt').read_text().strip() == '0'
    assert '126 rejections' in (D/'directories-arm.txt').read_text()
    for count in (4, 100):
        p = D/'directories'/('valid-'+str(count))
        prepared = load(p/'directories.prepared.json')
        s = load(p/'directories.summary.json')
        assert prepared['count'] == s['count'] == s['consumed'] == count
        assert len(set(prepared['calls'])) == count and s['hot_filesystem_calls'] == 0
        for i in range(count):
            assert (p/('call-'+str(i))/'output.bin').read_bytes() == b'owned-output'
    assert not (D/'directories/collision/call-0').exists()
    refs = R/'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns'
    total = 0
    for pattern in range(2):
        for round_id in range(2):
            for v in (4386,4390):
                p = D/'read-host'/f'{pattern}-{round_id}-{v}.f32'
                assert p.read_bytes() == (refs/f'pattern-{pattern}'/f'output-{v}.f32').read_bytes()
                total += p.stat().st_size
    assert total == 188160
    report = {'status':'ARM_directories_and_Host_CPTR_read_passed', 'rejections':126,
              'Host_read_outputs':8, 'Host_read_bytes':total, 'physical_Device_Session':False}
else:
    P = D/'results'; prepared = load(P/'directories.prepared.json')
    s = load(P/'directories.summary.json'); result = load(P/'summary.json')
    count = 4 if mode == 'four' else 100
    root = f'/tmp/pose-producer-prepared-20261011-r1/run-{mode}/results'
    assert prepared['root'] == root and prepared['count'] == s['count'] == count
    assert prepared['calls'] == [root+'/call-'+str(i) for i in range(count)]
    assert prepared['exclusive_root'] and prepared['empty_at_preparation'] and s['prepared']
    assert prepared['hot_filesystem_calls'] == s['hot_filesystem_calls'] == 0
    assert 0 <= result['completed'] <= s['consumed'] <= min(count,result['completed']+1)
    life = [json.loads(x) for x in (P/'lifecycle.jsonl').read_text().splitlines()]
    initialized = next(x['time_ns'] for x in life if x['event']=='SDK_initialized')
    started = next(x['time_ns'] for x in life if x['event']=='fixed_sequence_started')
    assert initialized <= prepared['begin_ns'] <= prepared['end_ns'] < started
    for i in range(count):
        p = P/('call-'+str(i))
        assert p.is_dir() and not p.is_symlink()
        if i >= s['consumed']: assert not any(p.iterdir()), ('Unconsumed directory changed',i)
    events = [json.loads(x) for x in (P/'phases.jsonl').read_text().splitlines()]
    consumed = [x for x in events if x['phase']=='directory' and x['edge']=='end']
    assert len(consumed) == s['consumed'] and [x['invocation'] for x in consumed] == list(range(s['consumed']))
    assert all(not x['exceptional'] for x in consumed)
    report = {'status':'prepared_directory_ownership_and_consumption_verified', 'mode':mode,
              'prepared':count,'consumed':s['consumed'],'completed':result['completed'],
              'prepare_ms':(prepared['end_ns']-prepared['begin_ns'])/1e6,
              'hot_filesystem_calls':0,'unconsumed_paths_empty':True,
              'Directory_trace_semantics':'in-memory token consume, not mkdir',
              'data_saving_location_unchanged':True,'initial_gate_budget_seconds':50}
report['archive_sha256'] = hashlib.sha256((E/('return-'+mode+'.tar')).read_bytes()).hexdigest()
(E/(mode+'.directories-review.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(report)

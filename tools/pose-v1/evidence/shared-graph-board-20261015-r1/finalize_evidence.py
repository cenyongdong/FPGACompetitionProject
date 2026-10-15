"""Offline delivery audit; never retries the rejected board inference."""
from pathlib import Path
import ast, hashlib, json, tarfile

R = Path(r'D:\FPGACompetitionProject')
E = Path(__file__).resolve().parent
M = R / 'model/piw24_shared-20261015-r1'
X = Path(r'D:\Person-in-WIFI-3D\Person-in-WiFi-3D-repo\exportONNX\shared-refine-20261015-r1')
S = R / '.local/shared-source-20261015-r1'

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

source = read(E / 'source-manifest.json')
for name, h in source['files'].items():
    assert sha(S / name) == h, name
summary = read(M / 'summary.json')
assert all(s['exit_code'] == 0 for s in summary['stages'])
for name, h in read(M / 'files.json').items():
    assert sha(M / name) == h, name
model_checks = []
for step in summary['stages']:
    g = step['graph']
    jp, rp = M / g['json'], M / g['raw']
    assert sha(jp) == g['json_sha256'] and sha(rp) == g['raw_sha256']
    assert hashlib.md5(rp.read_bytes()).hexdigest() == g['raw_md5_verified']
    model_checks.append(dict(stage=step['stage'], exit=0, seconds=step['seconds'],
        logical_ops=g['logical_ops'], json=g['json'], raw=g['raw'],
        raw_bytes=rp.stat().st_size, json_sha256=sha(jp), raw_sha256=sha(rp)))
pkg = R / '.local/shared-delivery-20261015-r1'
for n in ('piw24_shared_ZG.json', 'piw24_shared_ZG.raw'):
    assert sha(M/n) == sha(pkg/'models'/n)
onnx = X / read(E/'export-summary.json')['file']
assert sha(onnx) == read(E/'export-summary.json')['sha256']
assert sha(onnx) == sha(M/'source'/onnx.name)
config_review = {}
for rel, h in read(E/'export-preflight.json')['pins'].items():
    p = X.parents[1] / rel
    if p.exists():
        if rel == 'result/code_faithful/petr_wifi.py':
            # Export used the pinned server config, not the local training config.
            server = E/'server-petr_wifi.py'
            assert sha(server) == h
            def assignments(path):
                return {n.targets[0].id: ast.dump(n.value) for n in ast.parse(path.read_text(encoding='utf-8')).body
                    if isinstance(n, ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0], ast.Name)}
            a, b = assignments(p), assignments(server)
            differing = sorted(k for k in a.keys()|b.keys() if a.get(k) != b.get(k))
            assert a['model'] == b['model']
            assert differing == ['data', 'gpu_ids', 'resume_from']
            config_review = dict(local_sha256=sha(p), server_sha256=sha(server),
                differing_assignments=differing, model_assignment_AST_equal=True,
                export_source='Pinned server config; strict explicit epoch442 checkpoint loading, CPU eval',
                local_config_overwritten=False)
            (E/'local-petr_wifi.py').write_bytes(p.read_bytes())
        else:
            assert sha(p) == h, rel
save(E/'config-identity-review.json', config_review)

shapes = {}
for label, d, prefix in [('noscatter', R/'model/piw24_noscatter-20261014-r3', 'piw24_noscatter'),
                         ('shared', M, 'piw24_shared')]:
    graph = read(d / (prefix + '_optimized.json'))
    shapes[label] = [dict(op_id=o['op_id'], inputs=[v['dtype']['shape'] for v in o['inputs']],
        outputs=[v['dtype']['shape'] for v in o['outputs']]) for o in graph['ops']
        if o['_type_key']=='icraft::xir::Matmul' and o['op_id'] > 450]
save(E/'icraft-refine-matmul-shapes.json', shapes)

archive = E/'source.tar.gz'
assert not archive.exists(), 'Do not replace an existing source archive'
with tarfile.open(archive, 'x:gz') as t:
    for p in sorted(S.rglob('*')):
        if p.is_file():
            t.add(p, arcname=p.relative_to(S).as_posix(), recursive=False)
symbols = (E/'symbol-audit.txt').read_text(encoding='utf-8-sig')
assert 'scatter' not in symbols.lower()
assert 'topK' in symbols and 'gatherElements' in symbols
state = (E/'99-final-state.txt').read_text(encoding='utf-8-sig')
assert state.rstrip().endswith('operating')
assert 'pose_shared_timing' not in state and 'board_run.py' not in state
assert (E/'docker-final-state.txt').read_text(encoding='utf-8-sig').strip() == 'exited'

# Preserve the first exploratory result and explicitly correct its unit label.
old = E/'first-output-differences.json'
v = read(old)
assert 'first_candidate_delta_mm' in v['poses']
corrected = dict(v)
corrected['poses'] = dict(v['poses'])
corrected['poses']['first_candidate_delta_model_units'] = corrected['poses'].pop('first_candidate_delta_mm')
corrected['correction'] = 'Original first_candidate_delta_mm field contains model units (metres); renamed here. Original retained. Use stopped-analysis.json for final millimetre metrics.'
save(E/'first-output-differences.corrected.json', corrected)
save(E/'unit-label-correction.json', dict(original=old.name, original_sha256=sha(old),
    corrected='first-output-differences.corrected.json', scope='Offline diagnostic field name only; no board or model bytes changed'))

a = read(E/'stopped-analysis.json')
assert a['actual_inferences']==1 and a['accepted_frames']==0 and a['board_exit']==1
save(E/'delivery-audit.json', dict(status='export_conversion_complete_board_numeric_gate_failed',
    planned=3, actual_inferences=1, accepted_frames=0, unexecuted=2, retry=False,
    stages=model_checks, source_files_verified=len(source['files']),
    source_archive=dict(file=archive.name, bytes=archive.stat().st_size, sha256=sha(archive)),
    onnx_sha256=sha(onnx), config_sha256=sha(M/'piw24_shared.toml'),
    RAW_reduction_percent=(1-(M/'piw24_shared_ZG.raw').stat().st_size/53200782)*100,
    board_cleanup='No task process remains; FPGA operating; unrelated user monitor retained',
    container_cleanup='FPAI restored to stopped after verifying bash was its only process',
    formal_demo_replaced=False, reboot=False, memory_compaction=False,
    old_DATA_investigation_resumed=False))
print('Delivery audit passed; board numerical gate remains FAILED.')

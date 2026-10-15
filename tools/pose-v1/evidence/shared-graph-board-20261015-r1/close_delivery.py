"""Record final document revisions and artifact identities without changing old ledgers."""
from pathlib import Path
import hashlib, json, re, subprocess

R = Path(r'D:\FPGACompetitionProject')
E = Path(__file__).resolve().parent
M = R/'model/piw24_shared-20261015-r1'
X = Path(r'D:\Person-in-WIFI-3D\Person-in-WiFi-3D-repo\exportONNX\shared-refine-20261015-r1')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def save(p, v):
    assert not p.exists(), p
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

before=load(E/'documentation-before.json')
revision=[]
for b in before:
    p=Path(b['Path']);h=sha(p)
    revision.append(dict(path=str(p),before_sha256=b['Hash'].lower(),after_sha256=h,
        changed=h!=b['Hash'].lower()))
assert not revision[0]['changed'], 'AGENTS must remain unchanged'
save(E/'documentation-revision.json',dict(reason='Record shared graph export, conversion and failed first board gate; preserve prior history',
    historical_completion_ledgers_modified=False,files=revision))

# Freeze original-only-no-Scatter pair, independently of the new candidate.
old=R/'model/piw24_noscatter-20261014-r3'
assert sha(old/'piw24_noscatter_ZG.json')=='0720b375edb7fddd7ee6f074be0e8fd0852592ae1fcbe600762525f276139ce5'
assert sha(old/'piw24_noscatter_ZG.raw')=='29dce9c1bd1fc940cdd1364d148353227d01ec0cef82861f7d2c9045e12ee1ce'

report=E/'REPORT.md'
assert report.exists() and (M/'README.md').exists() and (X/'README.md').exists()
missing=[]
for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
    if '://' not in target and not (E/target.split('#')[0]).exists():missing.append(target)
assert not missing,missing
diff=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True)
(E/'git-diff-check.txt').write_bytes(diff.stdout+diff.stderr)
assert diff.returncode==0

records={}
for base in [E,M,X]:
    for p in sorted(base.rglob('*')):
        if p.is_file() and p.name not in ('delivery-files.json','completion-review.json'):
            records[str(p)]=dict(bytes=p.stat().st_size,sha256=sha(p))
save(E/'delivery-files.json',records)
a=load(E/'delivery-audit.json')
assert a['status']=='export_conversion_complete_board_numeric_gate_failed'
save(E/'completion-review.json',dict(status=a['status'],
    requested_export_and_local_return='complete',Icraft_five_stages='all_exit_0',
    inference_timing='one_actual_saved_sample_only',board_numeric_acceptance='FAILED',
    actual_inferences=1,accepted_frames=0,unexecuted_frames=2,
    automatic_retry=False,strict_gate_relaxed=False,board_exit=1,
    board_cleanup_verified=True,FPAI_final_status='exited',formal_demo_replaced=False,
    old_noscatter_pair_unchanged=True,old_DATA_investigation_resumed=False,
    report=str(report),report_sha256=sha(report),delivery_file_count=len(records),
    delivery_manifest_sha256=sha(E/'delivery-files.json'),
    next_step_requires='Discussion of numerical discrepancy and acceptance/precision plan before new board validation'))
print(json.dumps(dict(status=a['status'],files=len(records),report=str(report)),ensure_ascii=False))

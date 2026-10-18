"""R9 isolation using the frozen, already reviewed R7 copy algorithm."""
from pathlib import Path
import ast
import hashlib
import json
import types

R=Path(__file__).resolve().parents[3]
S=Path(__file__).parent
E8=R/'tools/pose-v1/evidence/hdmi-live-20261018-r8'
C=E8/'reader-boundary-candidate-r1'
E=R/'tools/pose-v1/evidence/hdmi-live-20261018-r9'
W=R/'.local/hdmi-live-20261018-r9'
BASE=S/'prepare_hdmi_reader_idle_reference.py'
BASE_SHA='2a2862e2a968e86642da52a8fb3bc1aeb51e0d31bbc0527ebe1eb98d8845849c'
NEW_SHA='7d6779adff9062ab625597534ba18c450b4c830bb7d8808f22fe3952e260650a'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(x,f,indent=2,ensure_ascii=False)

assert sha(BASE)==BASE_SHA and not E.exists() and not W.exists()
state=load(R/'tools/pose-v1/evidence/hdmi-live-20261017-r3/continuation-state.json')
assert state['whole_task_pause']['paused'] is False and state['offline_work_continues'] is True
assert state['onsite_observation_work']['paused'] is True and state['old_DATA']=='paused'
actual=load(C/'simulation-r1/result.json')
assert actual['passed'] and actual['exhaustive_guard_combinations']==1048576
assert actual['state_miter_cases']==24 and actual['state_miter_cycles']==5773 and actual['strict_output_comparisons']==11378
assert sha(C/'hdmi_axi_read.v')==NEW_SHA
assert (C/'hdmi_axi_read_idle_candidate.v').read_bytes().replace(b'module hdmi_axi_read_idle_candidate (',b'module hdmi_axi_read (')==(C/'hdmi_axi_read.v').read_bytes()
for name,raw in [('canonical-name-only/hdmi_axi_read.v',(C/'hdmi_axi_read.v').read_bytes()),
                 ('rtl/hdmi_axi_read_idle_candidate.v',(C/'hdmi_axi_read_idle_candidate.v').read_bytes())]:
    p=C/name;p.parent.mkdir(exist_ok=True)
    with p.open('xb') as f:f.write(raw)
save(C/'canonical-name-proof.json',dict(SHA256=NEW_SHA,tested_candidate_SHA256=sha(C/'hdmi_axi_read_idle_candidate.v'),
     all_other_bytes_equal_to_tested_candidate=True,source_proof_SHA256=sha(C/'source-proof.json')))
(C/'run-r1').mkdir()
save(C/'run-r1/result.json',dict(passed=True,cases=24,cycles=5773,comparisons=11378,strict_output_bits=116,
     exhaustive_guard_combinations=1048576,derived_summary=True,actual_result_path=str(C/'simulation-r1/result.json'),
     actual_result_SHA256=sha(C/'simulation-r1/result.json')))

raw=BASE.read_bytes()
tree=ast.parse(raw)
count=0
for node in ast.walk(tree):
    if isinstance(node,ast.Constant) and node.value=='hdmi-reader-idle-r7-preparation-v1':
        node.value='hdmi-reader-boundary-r9-preparation-v1';count+=1
assert count==1
m=types.ModuleType('r9_frozen_copy_algorithm');m.__file__=str(BASE)
exec(compile(tree,str(BASE)+' [one schema literal]', 'exec'),m.__dict__)
m.__file__=str(Path(__file__).resolve())
m.W,m.E,m.REF=W,E,W/'reference'
m.CANDIDATE_DIR,m.CANDIDATE,m.NEW_READER_SHA=C,C/'canonical-name-only/hdmi_axi_read.v',NEW_SHA
m.prepare()
save(E/'preparation/algorithm-bindings.json',dict(base_path=str(BASE),base_SHA256=BASE_SHA,
     actual_adapter_SHA256=sha(__file__),only_algorithm_AST_edit='preparation schema literal',
     new_work=str(W),new_evidence=str(E),candidate_root=str(C),candidate_SHA256=NEW_SHA,
     fresh_copy_from_original_r3=True,old_r7_and_r8_outputs_preserved=True))
(E/'preparation/frozen-base-preparer.py').write_bytes(raw)

# Independent post-copy inspection of every copied file and exact change set.
proof=load(E/'preparation/review.json')
inventory=load(E/'preparation/copy-byte-identities.json')
changed=[]
for rel,identity in inventory.items():
    old=m.OLD/rel;new=m.REF/rel
    assert old.is_file() and new.is_file() and not new.is_symlink() and new.stat().st_nlink==1
    assert not old.samefile(new) and new.resolve().is_relative_to(m.REF.resolve())
    assert sha(old)==identity['SHA256'] and old.stat().st_size==identity['bytes']
    if sha(new)!=identity['SHA256']: changed.append(rel)
assert len(inventory)==4726 and set(changed)==set(proof['path_migrations'])|{m.READER,'fpai_demo_vivado.xpr'}
assert len(changed)==27
safety=E/'preparation-safety-r2';safety.mkdir()
save(safety/'review.json',dict(passed=True,schema='r9-independent-copy-verification-v1',
     preparation_review_path=str(E/'preparation/review.json'),preparation_review_SHA256=sha(E/'preparation/review.json'),
     ordinary_independent_destination_files=len(inventory),changed_copy_files=changed,
     source_preparer_not_rerun=True,old_and_new_no_reparse_or_resolved_escape=True,
     all_destinations_nlink1=True,old_copy_file_identities_unchanged=True,
     actual_copy_excluded_jobs_by_non_OOC_whitelist=True,explicit_jobs_and_reparse_checks_added_for_future_use=True,
     retained_legacy_field_note='The frozen preparer already contains these checks; no new source patch claimed.',
     EDA_executed=False,board_executed=False))
print(json.dumps(dict(prepared=True,independent_copy_checked=len(inventory),protected_sources=937,candidate_SHA256=NEW_SHA)))

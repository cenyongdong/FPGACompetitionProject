"""Prepare a compatible observer, without rerunning the failed board load."""
from pathlib import Path
import ast,hashlib,importlib.util,json,shutil,sys
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
N=E.parent/'shared-stability-20261015-r2';D=R/'.local/shared-stability-delivery-20261015-r2'
OLD=R/'.local/shared-stability-delivery-20261015-r1';T=R/'.local/shared-stability-transport-20261015-r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not N.exists() and not D.exists() and not T.exists()
N.mkdir();shutil.copytree(OLD,D,ignore=shutil.ignore_patterns('package.json'))
text=(E/'run_stage.py').read_text(encoding='utf-8')
old="""    return dict(pid=pid,status_kb=status,smaps_kb=smaps,fd_count=len(list((root/'fd').iterdir())),
                map_count=len((root/'maps').read_text().splitlines()),
                children=(root/'task'/str(pid)/'children').read_text().strip())"""
new="""    child_file=root/'task'/str(pid)/'children'
    try:
        children=child_file.read_text().strip();children_supported=True
    except FileNotFoundError:
        if not root.exists():raise
        children=None;children_supported=False
    return dict(pid=pid,status_kb=status,smaps_kb=smaps,fd_count=len(list((root/'fd').iterdir())),
                map_count=len((root/'maps').read_text().splitlines()),
                children=children,children_observation_supported=children_supported)"""
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace('except FileNotFoundError:\n                    if child.poll()',
                  'except (FileNotFoundError,ProcessLookupError):\n                    if child.poll()')
ast.parse(text)
(N/'run_stage.py').write_text(text,encoding='utf-8',newline='\n');shutil.copyfile(N/'run_stage.py',D/'run_stage.py')
sys.path.insert(0,str(D));spec=importlib.util.spec_from_file_location('fixed_observer',N/'run_stage.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
realPath=Path;tests=[]
def fake_proc(name,with_children=False,with_smaps=True):
    base=N/'test-fixtures'/name;base.mkdir(parents=True)
    p=base/'123';(p/'fd').mkdir(parents=True);(p/'task/123').mkdir(parents=True)
    (p/'status').write_text('VmRSS: 4096 kB\nThreads: 1\n')
    (p/'maps').write_text('one mapping\n')
    if with_smaps:(p/'smaps_rollup').write_text('Pss: 2048 kB\nPrivate_Dirty: 1024 kB\n')
    if with_children:(p/'task/123/children').write_text('234 235\n')
    module.Path=lambda value:base if value=='/proc' else realPath(value)
    return base
fake_proc('unsupported')
r=module.sample(123);assert r['children'] is None and not r['children_observation_supported'] and r['smaps_kb']['Pss']==2048
tests.append('Unsupported optional children file preserves mandatory RSS/PSS/FD/maps/threads')
fake_proc('supported',True)
r=module.sample(123);assert r['children']=='234 235' and r['children_observation_supported']
tests.append('Supported children observation retained')
fake_proc('required-missing',with_smaps=False)
try:module.sample(123);raise AssertionError('Mandatory PSS silently dropped')
except FileNotFoundError:tests.append('Missing mandatory smaps still fails')
try:module.sample(999);raise AssertionError('Exited process silently ignored by sampler')
except FileNotFoundError:tests.append('Vanished process is distinct from unsupported optional field')
save(N/'monitor-selftest.json',dict(status='4_compatibility_checks_passed',checks=tests))
p=json.loads((OLD/'package.json').read_text(encoding='utf-8'))
assert sha(D/'pose_shared_timing')==p['binary_sha256']
assert sha(D/'pose_shared_resident')==p['resident_binary_sha256']
changed=[]
for f in OLD.rglob('*'):
    if f.is_file() and f.name!='package.json' and sha(f)!=sha(D/f.relative_to(OLD)):changed.append(f.relative_to(OLD).as_posix())
assert changed==['run_stage.py'],changed
p.update(status='observer_compatibility_fix_prepared_awaiting_explicit_restart_authorization',
    previous_failure='r1 optional /proc task children interface absent; process terminated before complete inference',
    changed_package_files=changed)
p['files']={f.relative_to(D).as_posix():sha(f) for f in sorted(D.rglob('*')) if f.is_file()}
save(D/'package.json',p);shutil.copyfile(D/'package.json',N/'package.json')
T.mkdir();helper=(R/'.local/shared-stability-transport-20261015-r1/secure_transport.py').read_text(encoding='utf-8')
(T/'secure_transport.py').write_text(helper.replace('shared-stability-20261015-r1/','shared-stability-20261015-r2/'),encoding='utf-8')
for name in ('transport.py','plan.json'):
    if name.endswith('.py'):
        s=(E/name).read_text(encoding='utf-8').replace('shared-stability-20261015-r1','shared-stability-20261015-r2')
        (N/name).write_text(s,encoding='utf-8',newline='\n')
    else:shutil.copyfile(E/name,N/name)
save(N/'fix-review.json',dict(status='prepared_and_unit_checked_not_board_executed',
    changed_files=changed,original_binary_unchanged=True,resident_binary_unchanged=True,
    mandatory_memory_metrics_preserved=True,process_group_cleanup_unchanged=True,
    failed_evidence_preserved=True,requires_explicit_restart_authorization=True))
print(json.dumps(dict(fix=str(N),changed=changed,checks=len(tests),board_restarted=False)))

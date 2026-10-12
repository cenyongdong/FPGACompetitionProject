"""Correct a package filename mismatch, retaining r1 and reusing its verified ELF."""
from pathlib import Path
import hashlib,json,shutil,tarfile,ast
R=Path(__file__).resolve().parents[2];T=R/'tools/pose-v1'
old=R/'.local/pose-v1-build/producer-phase-20261011-r1';B=R/'.local/pose-v1-build/producer-phase-20261011-r2'
prev=T/'evidence/producer-phase-20261011-r1';E=T/'evidence/producer-phase-20261011-r2'
assert not B.exists() and not E.exists();shutil.copytree(old,B);E.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((B/'build-result.json').read_text())
assert sha(B/'pose_producer_phase_check')==m['program_sha256']
for p,h in m['sources'].items():assert sha(R/p)==h
for n in ('payload','schedule','observer','phase'):shutil.copyfile(prev/(n+'-native.txt'),E/(n+'-native.txt'))
transfer=E/'transfer';transfer.mkdir();shutil.copytree(T/'evidence/producer-reference-20261011-r2/patterns',transfer/'patterns')
paths=[B/'pose_producer_phase_check',B/'build-result.json',*[B/('pose_producer_'+n+'_selftest') for n in ('payload','schedule','observer','phase')],T/'board_application_preflight.py',T/'board_producer_phase_run.py']
for p in paths:shutil.copyfile(p,transfer/p.name)
assert (transfer/'board_producer_phase_run.py').exists() and not (transfer/'board_producer_vpu_run.py').exists()
(transfer/'files.sha256').write_text(''.join(sha(p)+'  '+p.relative_to(transfer).as_posix()+'\n' for p in sorted(transfer.rglob('*')) if p.is_file()),encoding='utf-8',newline='\n')
with tarfile.open(E/'transfer.tar','w') as f:
    for p in sorted(transfer.rglob('*')):
        if p.is_file():f.add(p,arcname=p.relative_to(transfer).as_posix())
(E/'transfer.identity.json').write_text(json.dumps({'archive_sha256':sha(E/'transfer.tar'),'build':m,'reused_verified_r1_ELF':True,'reason':'r1 package had old manager filename; no r1 device initialization'},indent=2)+'\n')
for name in ('execute_producer_phase','review_producer_phase_events'):
    p=T/(name+'_r2.py');assert not p.exists();s=(T/(name+'.py')).read_text().replace('producer-phase-20261011-r1','producer-phase-20261011-r2');ast.parse(s);p.write_text(s,encoding='utf-8',newline='\n')
p=T/'ssh_memory_transport.py';s=p.read_text();assert '/tmp/pose-producer-phase-20261011-r2/' not in s;p.write_text(s.replace("remote.startswith(('/tmp/pose-producer-phase-", "remote.startswith(('/tmp/pose-producer-phase-20261011-r2/','/tmp/pose-producer-phase-"),encoding='utf-8',newline='\n')
print('Corrected r2 package, same ELF',m['program_sha256'],'both manager name and hashes verified')

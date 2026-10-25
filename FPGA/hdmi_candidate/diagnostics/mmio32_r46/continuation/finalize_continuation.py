from pathlib import Path
import json,hashlib,tarfile,shutil
W=Path(__file__).resolve().parent;D=W/'continuation'
E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hp2-mmio32-20261024-r46')
def identity(p):return dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
cfg=json.loads((D/'config.json').read_text())
cfg['controller_files']['ps_release_board.py']=identity(D/'ps_release_board.py')
for p in (D/'package').glob('*.py'):
    compile(p.read_text(),str(p),'exec');cfg['files'][p.name]=identity(p)
compile((D/'ps_release_board.py').read_text(),'continuation-parent','exec')
(D/'config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
approval=dict(approved=True,boot_id=cfg['same_boot_continuation']['boot_id'],
    user_reply='同意按上述条件继续（建议）',scope=cfg['same_boot_continuation'],
    preserve_original_stop_and_failed_result=True,no_additional_candidate_start=True,
    maximum_SDK_Open_total=2,original_fallbacks_reserved=1)
(D/'continuation-authorization.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive=W/'continuation-r46.tar.gz'
with tarfile.open(archive,'x:gz') as t:
    for f in [D/'config.json',D/'ps_release_board.py',D/'continuation-authorization.json',*sorted((D/'package').glob('*.py'))]:
        t.add(f,arcname=f.relative_to(D).as_posix())
manifest=identity(archive)
(D/'archive-identity.json').write_text(json.dumps(manifest,indent=2)+'\n')
target=E/'continuation';target.mkdir(exist_ok=True)
for name in ('config.json','ps_release_board.py','continuation-authorization.json','offline-tests.json','archive-identity.json'):
    shutil.copyfile(D/name,target/name)
shutil.copyfile(W/'source-cause-proof.json',target/'source-cause-proof.json')
print(json.dumps(dict(ready=True,software_only=True,original_records_unchanged=True,archive=manifest)))

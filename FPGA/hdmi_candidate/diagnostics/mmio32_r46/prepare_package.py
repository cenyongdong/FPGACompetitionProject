from pathlib import Path
import json,hashlib,shutil,tarfile,subprocess
O=Path('D:/FPGACompetitionProject');W=Path(__file__).resolve().parent
C=Path('C:/Users/cenyongdong/.codex/worktrees/hdmi-s01-isolation/FPGACompetitionProject')
OLD=O/'tools/pose-v1/evidence/hp2-deferred-consume-20261024-r45'
E=O/'tools/pose-v1/evidence/hp2-mmio32-20261024-r46';E.mkdir(exist_ok=True)
BASE='/root/hp2-mmio32-20261024-r46';OLD_BASE='/root/hp2-deferred-consume-20261024-r45'
cfg=json.loads((OLD/'deploy/config.json').read_text())
closed=json.loads((OLD/'state.json').read_text());assert closed['original_runtime_verified'] and not closed['active']
cfg.update(package_id='hp2-mmio32-r46',base=BASE,scope='Bounded MMIO32 corrected same-boot consumption and AI to HDMI test')
cfg['caps']['candidate_starts']=2
cfg['board'].update(remote_root=BASE,pre_start_boot_id=closed['final_original_boot_id'])
cfg['asset_reuse']={name:OLD_BASE+'/package/'+name for name in cfg['files'] if not name.endswith('.py')}
d=E/'deploy';d.mkdir(exist_ok=True);package=d/'package';package.mkdir(exist_ok=True)
for src in (OLD/'deploy/package').glob('*.py'):shutil.copyfile(src,package/src.name)
shutil.copyfile(W/'gates/capture_deferred.py',package/'capture_deferred.py')
shutil.copyfile(W/'package/libmmio32.so',package/'libmmio32.so')
parent=(O/'.local/hp2-deferred-consume-20261024-r45/deploy/ps_release_board.py').read_text()
parent=parent.replace("'hp2-deferred-consume-r45'","'hp2-mmio32-r46'").replace('actual r45 package','actual r46 package')
parent=parent.replace('CAPS=dict(candidate_starts=3,','CAPS=dict(candidate_starts=2,').replace('1<=n<=3,','1<=n<=2,').replace('1<=starts<=3 and sdk<=2','1<=starts<=2 and sdk<=2')
compile(parent,'ps_release_board.py','exec')
(d/'ps_release_board.py').write_bytes(parent.encode())
def identity(path):return dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
for p in package.iterdir():cfg['files'][p.name]=identity(p)
cfg['controller_files']={'ps_release_board.py':identity(d/'ps_release_board.py'),
                         'package/libmmio32.so':identity(package/'libmmio32.so')}
cfg['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=C,text=True).strip()
cfg['native_MMIO32_required']=True
auth=dict(active=True,package_id=cfg['package_id'],scope=cfg['scope'],caps=cfg['caps'],
    user_authorization='2026-10-24 用户获知r45恢复原BOOT及MMIO32修正后明确指示：继续进行板测。本轮保守最多2候选+1原BOOT回退，仅健康未复现才下一次；实际消费及安全门通过才两图案和90窗/5Hz，最多2SDK、联合150秒、200ms期限。AI四路不变，未知/功能错误即停、不重试。复用r45合格BOOT，只修正软件访问。')
for name,value in [('config.json',cfg),('authorization.json',auth)]:
    (d/name).write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
with tarfile.open(W/'deploy-r46.tar.gz','x:gz') as t:
    for p in sorted(d.rglob('*')):
        if p.is_file():t.add(p,arcname=p.relative_to(d).as_posix())
state=dict(status='authorized_package_ready',active=True,uploaded=False,BOOT_written=False,
    authorization=auth['user_authorization'],caps=cfg['caps'],actual=dict(candidate_starts=0,original_fallbacks=0,SDK_Open=0),
    reused_hardware=str(OLD/'qualification.json'),BOOT_sha256=cfg['files']['BOOT-candidate.bin']['sha256'],
    AI_four_HC_unchanged=True,SDK_model_math_frame_protocol_unchanged=True,source_commit=cfg['source_commit'])
(E/'state.json').write_bytes((json.dumps(state,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(package_ready=True,active=True,uploaded=False,BOOT=state['BOOT_sha256'],caps=cfg['caps'],native_store=cfg['files']['libmmio32.so'])))

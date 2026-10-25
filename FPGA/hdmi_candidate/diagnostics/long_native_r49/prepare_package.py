from pathlib import Path
import json,shutil,hashlib,tarfile
W=Path(__file__).resolve().parent;O=Path('D:/FPGACompetitionProject')
E=O/'tools/pose-v1/evidence/hdmi-long-native-20261024-r49';E.mkdir(exist_ok=True)
D=W/'deploy';P=D/'package';P.mkdir(parents=True,exist_ok=True)
old=O/'tools/pose-v1/evidence/hp2-mmio32-20261024-r46/deploy'
cfg=json.loads((old/'config.json').read_text());BASE='/root/hdmi-long-native-20261024-r49'
cfg.update(package_id='hdmi-long-native-r49',base=BASE,scope='One candidate native RGB565 AI HDMI PC long stability run')
cfg['board'].update(remote_root=BASE,pre_start_boot_id='84eee0be-b1f1-446c-8fa1-85224c0b6cd5')
cfg['caps'].update(candidate_starts=1,original_fallbacks=1,SDK_Open=1,HDMI_long_term=True)
cfg['joint'].update(frames=52800,input_hz=30,hard_seconds=2100)
cfg.pop('component',None);cfg['actual_startup_discard_required']=False
cfg['healthy_startup_allowed']=True;cfg['no_failed_load_retry']=True
cfg['source_commit']='d244a42f';cfg['native_RGB565']=True
for name in ('hdmi_frame_probe','r45_diagnostic_stages.py'):cfg['files'].pop(name,None)
for name in cfg['files']:
    if name.endswith('.py'):shutil.copyfile(old/'package'/name,P/name)
for name in ('capture_deferred.py','consume_gate.py'):
    shutil.copyfile(O/'.local/hp2-mmio32-20261024-r46/continuation/package'/name,P/name)
shutil.copyfile(O/'.local/hp2-mmio32-20261024-r46/package/libmmio32.so',P/'libmmio32.so')
shutil.copyfile(O/'.local/hdmi-render-speed-20261024-r47/software-native-rgb565-final.tar.gz',P/'software.tar.gz')
for name in ('ps_release_board.py','bootstrap.py'):shutil.copyfile(W/name,D/name)
def identity(p):return dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
for p in P.iterdir():cfg['files'][p.name]=identity(p)
cfg['controller_files']={name:identity(D/name) for name in ('ps_release_board.py','bootstrap.py')}
cfg['asset_reuse']={name:'/root/hp2-mmio32-20261024-r46/package/'+name for name in cfg['files']
                    if name not in {p.name for p in P.iterdir()}}
auth=dict(active=True,package_id=cfg['package_id'],scope=cfg['scope'],caps=cfg['caps'],
    user_authorization='2026-10-24 用户明确同意主机权限修正后另做1候选+1SDK+1回退的30Hz/52800帧长测，异常即停、不自动重试。原先用户要求中止诊断，保留异常消费，将位流接入此前长时推理链验证整体稳定；随后要求直接RGB565、适当扩大画面空间但不放大骨架或关节标注。新包只1候选/1原BOOT回退/1SDK；沿原30Hz混合集52800窗，硬上限2100s，异常即停不重试。')
for name,value in (('config.json',cfg),('authorization.json',auth)):
    (D/name).write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
for p in [D/'ps_release_board.py',D/'bootstrap.py',*P.glob('*.py')]:compile(p.read_text(),str(p),'exec')
archive=W/'deploy-r49-board.tar.gz'
with tarfile.open(archive,'x:gz') as t:
    for p in [D/'config.json',D/'authorization.json',D/'ps_release_board.py',D/'bootstrap.py',*sorted(P.iterdir())]:
        if p.is_file():t.add(p,arcname=p.relative_to(D).as_posix())
for name in ('config.json','authorization.json','ps_release_board.py','bootstrap.py'):
    target=E/'deploy'/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(D/name,target)
shutil.copyfile(W/'bootstrap-tests.json',E/'bootstrap-tests.json')
state=dict(status='authorized_package_ready',active=True,BOOT_written=False,
    actual=dict(candidate_starts=0,original_fallbacks=0,SDK_Open=0),caps=cfg['caps'],
    remaining=dict(candidate_starts=1,original_fallbacks=1,SDK_Open=1),joint=cfg['joint'],
    AI_four_HC_unchanged=True,BOOT_sha256=cfg['files']['BOOT-candidate.bin']['sha256'],
    software_sha256=cfg['files']['software.tar.gz']['sha256'],original_runtime_boot_id=cfg['board']['pre_start_boot_id'],
    failed_r46_not_reclassified=True,hardware_rebuilt=False)
(E/'state.json').write_bytes((json.dumps(state,ensure_ascii=False,indent=2)+'\n').encode())
(E/'deployment-identity.json').write_bytes((json.dumps(identity(archive),indent=2)+'\n').encode())
print(json.dumps(dict(ready=True,SDK=0,BOOT=0,archive=identity(archive),caps=cfg['caps'],joint=cfg['joint'])))

from pathlib import Path
import re,shutil,subprocess,sys
w=Path(__file__).resolve().parent;old=w.with_name('hdmi-long-git-20261024-r52')
commit=sys.argv[1]
names=('ps_release_board.py','bootstrap.py','prepare_package.py','board_call.py','native_transport.py',
       'capture_uart.py','start_candidate.py','start_fallback.py','deploy_board.py','launch_long.py',
       'collect_board.py','poll_long.py','host_joint.py')
for name in names:
    s=(old/name).read_text().replace('hdmi-long-git-20261024-r52','hdmi-pipeline-20261024-r53')
    s=s.replace('hdmi-long-git-r52','hdmi-pipeline-r53').replace('deploy-r52','deploy-r53').replace('R52','R53')
    s=s.replace('ef19aa67-8848-40c6-b4a2-df9da7e4be68','a3835491-9c37-4ebe-a2d1-32b36b281ce2')
    if name=='prepare_package.py':
        s=s.replace('.local/hdmi-render-overlap-20261024-r51/software-native-overlap.tar.gz',
                    '.local/hdmi-pipeline-20261024-r53/software-pipeline.tar.gz')
        s=s.replace("cfg['source_commit']='1c4ec536'","cfg['source_commit']="+repr(commit))
        s=s.replace('One candidate native RGB565 AI HDMI PC long stability run','Single SDK thread inference and HDMI pipeline long validation')
        auth='2026-10-24 用户明确批准r53调度改动及单轮验证：单SDK线程推理/显示流水调度；离线验证缓冲区、末帧、错误清理及200ms期限后，最多1候选启动+1SDK、30Hz/52800帧、2100秒，最终1次原BOOT回退。AI四路、模型、帧协议不变、不丢帧，异常即停不自动重试；仍不保证30Hz。'
        s=re.sub(r"user_authorization='[^']*'",'user_authorization='+repr(auth),s,count=1)
    (w/name).write_text(s,encoding='utf-8')
for name in ('NativeAskpass.exe','bootstrap-tests.json','pacer_spawn_preflight.mjs'):
    shutil.copyfile(old/name,w/name)
subprocess.run([sys.executable,str(w/'prepare_package.py')],check=True)

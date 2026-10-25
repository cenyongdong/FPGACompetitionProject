from pathlib import Path
import re,shutil,subprocess,sys
w=Path(__file__).resolve().parent;old=w.with_name('hdmi-long-native-20261024-r49')
names=('ps_release_board.py','bootstrap.py','prepare_package.py','board_call.py','native_transport.py',
       'capture_uart.py','start_candidate.py','start_fallback.py','deploy_board.py','launch_long.py','collect_board.py','poll_long.py')
for name in names:
    s=(old/name).read_text().replace('hdmi-long-native-20261024-r49','hdmi-long-git-20261024-r52')
    s=s.replace('hdmi-long-native-r49','hdmi-long-git-r52').replace('deploy-r49','deploy-r52').replace('R49','R52')
    s=s.replace('84eee0be-b1f1-446c-8fa1-85224c0b6cd5','ef19aa67-8848-40c6-b4a2-df9da7e4be68')
    if name=='prepare_package.py':
        s=s.replace('.local/hdmi-render-speed-20261024-r47/software-native-rgb565-final.tar.gz',
                    '.local/hdmi-render-overlap-20261024-r51/software-native-overlap.tar.gz')
        s=s.replace("cfg['source_commit']='d244a42f'","cfg['source_commit']='1c4ec536'")
        auth='2026-10-24 用户明确批准r52：同一位流、AI四路不变，使用已通过像素回归的重叠渲染和Git转发；最多1候选+1SDK、30Hz/52800帧、2100秒，最终1次原BOOT回退；保持20ms发送节拍及200ms采纳门限，异常即停不自动重试。'
        s=re.sub(r"user_authorization='[^']*'",'user_authorization='+repr(auth),s,count=1)
    (w/name).write_text(s,encoding='utf-8')
for name in ('NativeAskpass.exe','bootstrap-tests.json','pacer_spawn_preflight.mjs'):
    shutil.copyfile(old/name,w/name)
subprocess.run([sys.executable,str(w/'prepare_package.py')],check=True)

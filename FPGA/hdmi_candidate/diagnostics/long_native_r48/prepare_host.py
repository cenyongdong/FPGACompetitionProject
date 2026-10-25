from pathlib import Path
import shutil
W=Path(__file__).resolve().parent;old=W.parent/'hp2-mmio32-20261024-r46'
for name in ('board_call.py','native_transport.py','capture_uart.py','start_candidate.py','start_fallback.py'):
    s=(old/name).read_text().replace('hp2-mmio32-20261024-r46','hdmi-long-native-20261024-r48').replace('R46','R48')
    s=s.replace('1<=cycle<=2','cycle==1')
    (W/name).write_bytes(s.encode())
shutil.copyfile(old/'NativeAskpass.exe',W/'NativeAskpass.exe')
s=(old/'host_joint.py').read_text().replace('hp2-mmio32-20261024-r46','hdmi-long-native-20261024-r48')
s=s.replace("'--stage','basic','--frames','90'","'--stage','stress','--frames','52800'")
s=s.replace("'demo_v1/data/full'","'demo_v1/data/mixed'").replace('frames=90,input_hz=5','frames=52800,input_hz=30')
s=s.replace('seconds_budget=240','seconds_budget=2310').replace('>230:', '>2300:')
s=s.replace('C:/Users/cenyongdong/miniconda3/python.exe','C:/Users/cenyongdong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
(W/'host_joint.py').write_bytes(s.encode())
print('Prepared single-start host controls and original30Hz long host; no board action.')

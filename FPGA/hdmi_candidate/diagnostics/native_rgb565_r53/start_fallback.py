from pathlib import Path
import json,shlex,subprocess,sys,time
W=Path(__file__).resolve().parent
E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-pipeline-20261024-r53')
BASE='/root/hdmi-pipeline-20261024-r53'
cycle=int(sys.argv[1]) if len(sys.argv)>1 else 1
if not cycle==1:raise ValueError('Outside bounded passive starts')
tag='fallback'
def ssh(name,command,timeout=90):
 subprocess.run([sys.executable,str(W/'board_call.py'),name,'ssh',command,'--timeout',str(timeout)],check=True)
marker=('HP2_R53_'+tag+'_UART_VERIFIED\n').encode()
code="import os;f=os.open('/dev/console',os.O_WRONLY|os.O_NOCTTY);print(os.write(f,"+repr(marker)+"));os.close(f)"
ssh(tag+'-uart-marker','python3 -c '+shlex.quote(code),20)
received=False
for _ in range(30):
 if marker.strip() in (E/('uart-'+tag)/'rx.bin').read_bytes():received=True;break
 time.sleep(.1)
proof=dict(marker_received=received,host_TX_bytes=0,physical_key=0,reboot_before_proof=0)
(E/('uart-'+tag)/'review.json').write_text(json.dumps(proof,indent=2)+'\n')
if not received:raise RuntimeError('No verified actual UART RX: leave original BOOT running')
print(json.dumps(proof),flush=True)
ssh('fallback-reboot','python3 '+BASE+'/ps_release_board.py fallback-reboot --cycle '+str(cycle),45)

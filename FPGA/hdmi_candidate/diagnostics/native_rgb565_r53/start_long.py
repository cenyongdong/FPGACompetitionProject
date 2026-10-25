from pathlib import Path
import json,subprocess,sys
w=Path(__file__).resolve().parent;e=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-pipeline-20261024-r53')
base='/root/hdmi-pipeline-20261024-r53'
runtime=json.loads((e/'host/runtime.json').read_text())
session=dict(session=runtime['session'],count=runtime['count'],hz=runtime['hz'])
if session['count']!=52800 or session['hz']!=30:raise RuntimeError('Host contract differs')
p=w/'host-session.json';p.write_text(json.dumps(session)+'\n')
def call(name,mode,source,dest=None):
    args=[sys.executable,str(w/'board_call.py'),name,mode,str(source)]
    if dest:args.append(dest)
    subprocess.run([*args,'--timeout','30'],check=True)
call('host-session-upload','put',p,base+'/host-session.json')
call('launcher-upload','put',w/'launch_long.py',base+'/launch_long.py')
call('poller-upload','put',w/'poll_long.py',base+'/poll_long.py')
call('collector-upload','put',w/'collect_board.py',base+'/collect_board.py')
call('long-start','ssh','python3 '+base+'/launch_long.py')

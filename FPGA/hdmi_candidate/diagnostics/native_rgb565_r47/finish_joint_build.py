from pathlib import Path
import json,subprocess,time,sys
W=Path(__file__).resolve().parent;E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-render-speed-20261024-r47')
D='C:/Program Files/Docker/Docker/resources/bin/docker.exe';remote='/tmp/hdmi-native-joint-20261024-r47';rows=[]
def run(stage,args):
    t=time.monotonic();p=subprocess.run([D,*args],capture_output=True)
    (E/(stage+'.stdout.log')).write_bytes(p.stdout);(E/(stage+'.stderr.log')).write_bytes(p.stderr)
    rows.append(dict(stage=stage,argv=args,native_exit=p.returncode,seconds=time.monotonic()-t))
    (E/'joint-final-build-execution.json').write_bytes((json.dumps(rows,indent=2)+'\n').encode())
    print(json.dumps(rows[-1]),flush=True)
    if p.returncode:raise RuntimeError(stage+': '+p.stderr.decode(errors='replace')[-1600:])
    return p.stdout
started=run('joint-final-container-before',['inspect','--format','{{.State.Status}}','FPAI']).strip()==b'exited'
if started:run('joint-final-container-start',['start','FPAI'])
try:
    run('joint-final-copy-main',['cp',str(W/'joint/main.cpp'),'FPAI:'+remote+'/main.cpp'])
    run('joint-final-compile',['exec','FPAI','cmake','--build',remote+'/build','--target','pose_demo_v1','--parallel','2'])
    run('joint-final-return',['cp','FPAI:'+remote+'/build/pose_demo_v1',str(W/'pose_demo_v1')])
    symbols=run('joint-final-symbols',['exec','FPAI','aarch64-linux-gnu-nm','-C',remote+'/build/pose_demo_v1']).decode()
    assert 'pose::hdmi::render(' in symbols
    assert 'pose::hdmi::canvas(' not in symbols and 'pose_v1::render::draw(' not in symbols and 'yuv420sp(' not in symbols
finally:
    if started:run('joint-final-container-stop',['stop','FPAI'])
subprocess.run([sys.executable,str(W/'package_joint.py')],check=True)

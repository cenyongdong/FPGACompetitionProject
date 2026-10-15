from pathlib import Path
import json,subprocess
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
S=R/'.local/shared-resident-source-20261015-r1';D=R/'.local/shared-stability-delivery-20261015-r1'
steps=[]
def call(name,args,timeout=120):
    p=subprocess.run(args,capture_output=True,timeout=timeout)
    (E/(name+'.txt')).write_bytes(p.stdout+p.stderr)
    steps.append(dict(stage=name,argv=args,exit=p.returncode));(E/'build-steps.json').write_text(json.dumps(steps,indent=2)+'\n')
    if p.returncode:raise RuntimeError('Build stage failed: '+name)
    return p.stdout.decode(errors='replace')
status=call('docker-initial',['docker','inspect','--format','{{.State.Status}}','FPAI'])
if status.strip()!='exited':raise RuntimeError('FPAI not in expected stopped state; review other work')
call('docker-start',['docker','start','FPAI'])
call('source-copy',['docker','cp',str(S),'FPAI:/tmp/shared-resident-20261015-r1'])
call('configure',['docker','exec','FPAI','cmake','-S','/tmp/shared-resident-20261015-r1',
    '-B','/tmp/shared-resident-20261015-r1/build','-DCMAKE_SYSTEM_NAME=Linux','-DCMAKE_SYSTEM_PROCESSOR=aarch64',
    '-DCMAKE_CXX_COMPILER=/usr/bin/aarch64-linux-gnu-g++','-DCMAKE_PREFIX_PATH=/usr/cmake','-DCMAKE_BUILD_TYPE=Release'])
call('build',['docker','exec','FPAI','cmake','--build','/tmp/shared-resident-20261015-r1/build','-j2'])
call('binary-copy',['docker','cp','FPAI:/tmp/shared-resident-20261015-r1/build/pose_shared_resident',str(D/'pose_shared_resident')])
print('Resident ARM build and copy complete')

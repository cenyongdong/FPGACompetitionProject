"""Export frozen Native NV12 from actual complete returned outputs, no SDK."""
import subprocess,shutil,argparse
from pathlib import Path
root=Path(__file__).resolve().parents[2];docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe';remote='/tmp/pose-v1-mixed-20261010-input-read-r1'
p=argparse.ArgumentParser();p.add_argument('--count',type=int,required=True);a=p.parse_args();assert 0<=a.count<=107
e=root/'tools/pose-v1/evidence/input-read-20261010-r1';build=root/'.local/pose-v1-build/mixed-20261010-input-read-r1';stage=e/'native-reference-export';assert not stage.exists();stage.mkdir();data=stage/'returned';data.mkdir()
results=e/'picture-return/run-picture/results'
for i in range(a.count):
    for suffix in ('scores','poses'):shutil.copyfile(results/f'result{i}.{suffix}.f32',data/f'result{i}.{suffix}.f32')
commands=[['cp',str(data),'FPAI:'+remote+'/reference-input'],['exec','FPAI','g++','-std=c++17','-O2','-ffp-contract=off','-Wall','-Wextra','-Wpedantic','-Werror','-I'+remote+'/source',remote+'/source/picture_reference_export.cpp',remote+'/source/skeleton_render.cpp','-o',remote+'/build/picture-reference.native'],['exec','FPAI',remote+'/build/picture-reference.native',remote+'/reference-input',remote+'/reference-output',str(a.count)],['cp','FPAI:'+remote+'/reference-output',str(stage/'references')],['cp','FPAI:'+remote+'/build/picture-reference.native',str(stage/'picture-reference.native')]]
for i,c in enumerate(commands):
    r=subprocess.run([docker,*c],capture_output=True);(stage/f'step{i}.stdout.log').write_bytes(r.stdout);(stage/f'step{i}.stderr.log').write_bytes(r.stderr);assert r.returncode==0,r.stderr.decode(errors='replace')
print('Native reference exported',a.count)

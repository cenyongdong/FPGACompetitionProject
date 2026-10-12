"""Frozen Native render from every actual returned value; no SDK."""
import argparse,subprocess,shutil,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('stage',choices=['process-three','load-103']);a=p.parse_args()
root=Path(__file__).resolve().parents[2];e=root/'tools/pose-v1/evidence/upstream-boundary-20261011-r4';remote='/tmp/pose-v1-mixed-20261011-upstream-boundary-r3';docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe';stage=e/(a.stage+'-native-reference');assert not stage.exists();stage.mkdir();data=stage/'returned';data.mkdir()
results=e/(a.stage+'-return')/('run-'+a.stage)/'results';count=len([json.loads(x) for x in (results/'inference.jsonl').read_text().splitlines()]);assert 1<=count<=103
for i in range(count):
    for suffix in ('scores','poses'):shutil.copyfile(results/f'result{i}.{suffix}.f32',data/f'result{i}.{suffix}.f32')
commands=[['cp',str(data),'FPAI:'+remote+'/'+a.stage+'-reference-input'],['exec','FPAI','g++','-std=c++17','-O2','-ffp-contract=off','-Wall','-Wextra','-Wpedantic','-Werror','-I'+remote+'/source',remote+'/source/picture_reference_export.cpp',remote+'/source/skeleton_render.cpp','-o',remote+'/build/'+a.stage+'-reference.native'],['exec','FPAI',remote+'/build/'+a.stage+'-reference.native',remote+'/'+a.stage+'-reference-input',remote+'/'+a.stage+'-reference-output',str(count)],['cp','FPAI:'+remote+'/'+a.stage+'-reference-output',str(stage/'references')]]
for i,c in enumerate(commands):
    r=subprocess.run([docker,*c],capture_output=True);(stage/f'step{i}.stdout.log').write_bytes(r.stdout);(stage/f'step{i}.stderr.log').write_bytes(r.stderr);assert r.returncode==0,r.stderr.decode(errors='replace')
for actual in (results/'frames').glob('*.nv12'):
    assert actual.read_bytes()==(stage/'references'/actual.name).read_bytes(),actual
print('Native full picture reference and sparse ARM bytes verified',a.stage,count)

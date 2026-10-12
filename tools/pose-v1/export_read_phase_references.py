"""Frozen renderer and actual returned transport IDs, in a new local container path."""
import argparse,subprocess,shutil,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('stage',choices=['process-three','load-103']);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--remote',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];e=a.evidence;remote=a.remote;assert remote in ['/tmp/pose-v1-mixed-20261011-read-phase-r2','/tmp/pose-v1-mixed-20261011-read-phase-r3'];docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
stage=e/(a.stage+'-mapped-native-reference');assert not stage.exists();stage.mkdir();data=stage/'returned';data.mkdir()
results=e/(a.stage+'-return')/('run-'+a.stage)/'results';calls=[json.loads(x) for x in (results/'inference.jsonl').read_text().splitlines()];count=len(calls);assert 1<=count<=103
for i in range(count):
    for suffix in ('scores','poses'):shutil.copyfile(results/f'result{i}.{suffix}.f32',data/f'result{i}.{suffix}.f32')
(data/'transport-ids.txt').write_text(''.join(str(x['frame_id'])+'\n' for x in calls),encoding='utf-8',newline='\n')
commands=[['cp',str(root/'tools/pose-v1/picture_reference_export_transport.cpp'),'FPAI:'+remote+'/picture_reference_export_transport.cpp'],['cp',str(data),'FPAI:'+remote+'/'+a.stage+'-mapped-reference-input'],['exec','FPAI','g++','-std=c++17','-O2','-ffp-contract=off','-Wall','-Wextra','-Wpedantic','-Werror','-I'+remote+'/source',remote+'/picture_reference_export_transport.cpp',remote+'/source/skeleton_render.cpp','-o',remote+'/build/'+a.stage+'-mapped-reference.native'],['exec','FPAI',remote+'/build/'+a.stage+'-mapped-reference.native',remote+'/'+a.stage+'-mapped-reference-input',remote+'/'+a.stage+'-mapped-reference-output',str(count)],['cp','FPAI:'+remote+'/'+a.stage+'-mapped-reference-output',str(stage/'references')]]
for i,c in enumerate(commands):
    r=subprocess.run([docker,*c],capture_output=True);(stage/f'step{i}.stdout.log').write_bytes(r.stdout);(stage/f'step{i}.stderr.log').write_bytes(r.stderr);assert r.returncode==0,r.stderr.decode(errors='replace')
for actual in (results/'frames').glob('*.nv12'):assert actual.read_bytes()==(stage/'references'/actual.name).read_bytes(),actual
print('Native pictures with actual transport identity match sparse ARM bytes',a.stage,count)

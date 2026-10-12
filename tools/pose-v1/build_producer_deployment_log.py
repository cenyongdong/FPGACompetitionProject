"""Link a new public-log entry with exact frozen r3 objects; never rebuild math."""
from pathlib import Path
import subprocess,json,hashlib,shlex,shutil,tarfile
R=Path(__file__).resolve().parents[2];B=R/'.local/pose-v1-build/producer-deployment-20261011-r1';E=R/'tools/pose-v1/evidence/producer-contract-20261011-r2';assert not B.exists();B.mkdir()
D='C:/Program Files/Docker/Docker/resources/bin/docker.exe';old='/tmp/pose-v1-mixed-20261011-read-phase-r3';new='/tmp/pose-producer-deployment-20261011-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
    p=subprocess.run([D,*args],capture_output=True)
    with (B/'build.log').open('ab') as f:f.write((repr(args)+'\n').encode()+p.stdout+p.stderr)
    assert p.returncode==0,(args,p.stderr[-2000:]);return p.stdout
original=json.loads((R/'.local/pose-v1-build/mixed-20261011-read-phase-r3/build-result.json').read_text())
for path,h in original['source_sha256'].items():
    if path.startswith('software/'):assert sha(R/path)==h,(path,'Frozen source changed')
run(['exec','FPAI','test','!','-e',new]);run(['exec','FPAI','mkdir',new]);src=R/'software/pose_v1/src/producer_deployment_log.cpp';run(['cp',str(src),'FPAI:'+new+'/producer_deployment_log.cpp'])
run(['exec','FPAI','aarch64-linux-gnu-g++','-std=gnu++17','-O2','-DNDEBUG','-Wall','-Wextra','-Wpedantic','-Werror','-ffp-contract=off','-I'+old+'/source','-c',new+'/producer_deployment_log.cpp','-o',new+'/entry.o'])
command=shlex.split(run(['exec','FPAI','cat',old+'/build/CMakeFiles/pose_read_phase_check.dir/link.txt']).decode())
objects={};replaced=0
for i,arg in enumerate(command):
    if arg.endswith('.o'):
        full=arg if arg.startswith('/') else old+'/build/'+arg
        if arg.endswith('/read_phase_check.cpp.o'):command[i]=new+'/entry.o';replaced+=1
        else:command[i]=full;objects[full]=run(['exec','FPAI','sha256sum',full]).decode().split()[0]
    if i and command[i-1]=='-o':command[i]=new+'/pose_producer_deployment_log'
assert replaced==1 and objects
run(['exec','FPAI',*command]);run(['cp','FPAI:'+new+'/pose_producer_deployment_log',str(B/'pose_producer_deployment_log')])
dynamic=run(['exec','FPAI','aarch64-linux-gnu-readelf','-d',new+'/pose_producer_deployment_log']);(B/'dynamic.txt').write_bytes(dynamic)
result={'program_sha256':sha(B/'pose_producer_deployment_log'),'entry_sha256':sha(src),'frozen_parent_sha256':original['binary_sha256'],'frozen_sources_sha256':original['source_sha256'],'objects_sha256':objects,'entry_replacements':replaced,'no_frozen_objects_modified':True,'full_model_forward':False}
(B/'build-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
bundle=E/'deployment-transfer';assert not bundle.exists();bundle.mkdir()
for p in (B/'pose_producer_deployment_log',B/'build-result.json',R/'tools/pose-v1/run-producer-deployment.sh',R/'tools/pose-v1/board_application_preflight.py'):shutil.copyfile(p,bundle/p.name)
(bundle/'files.sha256').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(bundle.iterdir())),encoding='utf-8',newline='\n')
with tarfile.open(E/'deployment-transfer.tar','w') as t:
    for p in sorted(bundle.iterdir()):t.add(p,arcname=p.name)
(E/'deployment-transfer.identity.json').write_text(json.dumps({'archive_sha256':sha(E/'deployment-transfer.tar'),'build':result},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Public deployment logger linked with frozen objects',len(objects),result['program_sha256'],sha(E/'deployment-transfer.tar'))

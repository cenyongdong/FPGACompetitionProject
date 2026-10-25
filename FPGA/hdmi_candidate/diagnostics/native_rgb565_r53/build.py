"""Compile only new scheduler and display driver; run SDK-free boundary tests."""
from pathlib import Path
import hashlib,io,json,shutil,subprocess,tarfile,time
w=Path(__file__).resolve().parent;o=Path('D:/FPGACompetitionProject')
c=Path('C:/Users/cenyongdong/.codex/worktrees/hdmi-s01-isolation/FPGACompetitionProject')
e=o/'tools/pose-v1/evidence/hdmi-pipeline-20261024-r53';e.mkdir(exist_ok=True)
if not (w/'display').exists():
    shutil.copytree(c/'FPGA/hdmi_candidate/diagnostics/native_rgb565_r53/display',w/'display')
    shutil.copytree(o/'.local/hdmi-render-overlap-20261024-r51/native-render',w/'native-render')
d='C:/Program Files/Docker/Docker/resources/bin/docker.exe';r='/tmp/hdmi-pipeline-20261024-r53'
base='/tmp/hp2-deferred-consume-20261024-r45/source';execution=[]
def run(name,args):
    start=time.monotonic();p=subprocess.run([d,*args],capture_output=True)
    (e/(name+'.stdout.log')).write_bytes(p.stdout);(e/(name+'.stderr.log')).write_bytes(p.stderr)
    execution.append(dict(stage=name,argv=args,native_exit=p.returncode,seconds=time.monotonic()-start))
    (e/'build-execution.json').write_text(json.dumps(execution,indent=2)+'\n')
    print(json.dumps(execution[-1]),flush=True)
    if p.returncode:raise RuntimeError(name+': '+p.stderr.decode(errors='replace')[-1500:])
    return p.stdout
started=run('container-before',['inspect','--format','{{.State.Status}}','FPAI']).strip()==b'exited'
if started:run('container-start',['start','FPAI'])
try:
    run('fresh-directory',['exec','FPAI','mkdir',r])
    for name in ('joint','display','native-render','scheduler_tests.cpp'):
        run('copy-'+name.replace('.','-'),['cp',str(w/name),'FPAI:'+r+'/'+name])
    run('state-test-compile',['exec','FPAI','g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic',
        r+'/display/adoption_state_test.cpp','-o',r+'/adoption_state_test'])
    run('state-test',['exec','FPAI',r+'/adoption_state_test'])
    run('scheduler-test-compile',['exec','FPAI','g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic','-pthread',
        r+'/scheduler_tests.cpp','-o',r+'/scheduler_test'])
    run('scheduler-test',['exec','FPAI',r+'/scheduler_test'])
    run('configure',['exec','FPAI','cmake','-S',r+'/joint','-B',r+'/build',
        '-DCMAKE_SYSTEM_NAME=Linux','-DCMAKE_SYSTEM_PROCESSOR=aarch64','-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++',
        '-DCMAKE_PREFIX_PATH=/usr/cmake','-DCMAKE_BUILD_TYPE=Release','-DBASE_SOURCE='+base,
        '-DNATIVE_SOURCE='+r+'/native-render','-DPIPE_DISPLAY='+r+'/display',
        '-DNATIVE_CHECKPOINT=/tmp/hdmi-render-overlap-20261024-r51/build'])
    run('compile',['exec','FPAI','cmake','--build',r+'/build','--target','pose_demo_v1','--parallel','2'])
    run('reused-objects',['exec','FPAI','cat',r+'/build/reused-objects.txt'])
    run('return-binary',['cp','FPAI:'+r+'/build/pose_demo_v1',str(w/'pose_demo_v1')])
finally:
    if started:run('container-stop',['stop','FPAI'])
binary=(w/'pose_demo_v1').read_bytes()
with tarfile.open(o/'.local/hdmi-render-overlap-20261024-r51/software-native-overlap.tar.gz') as src:
    identity=json.load(src.extractfile('software/identity.json'))
    identity['files']['pose_demo_v1']=hashlib.sha256(binary).hexdigest()
    replacements={'software/pose_demo_v1':binary,'software/identity.json':(json.dumps(identity,indent=2)+'\n').encode()}
    out=w/'software-pipeline.tar.gz'
    with tarfile.open(out,'x:gz') as dst:
        for member in src:
            if member.name in replacements:
                data=replacements[member.name];member.size=len(data);dst.addfile(member,io.BytesIO(data))
            else:dst.addfile(member,src.extractfile(member) if member.isfile() else None)
result=dict(compiled=True,SDK_executed=False,hardware_rebuilt=False,AI_four_HC_unchanged=True,
    model_math_SDK_NPU_wire_unchanged=True,single_SDK_thread=True,
    binary_sha256=identity['files']['pose_demo_v1'],software_archive_sha256=hashlib.sha256(out.read_bytes()).hexdigest())
(e/'build-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

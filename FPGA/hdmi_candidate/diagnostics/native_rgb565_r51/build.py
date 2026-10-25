"""Incremental software + CPU-only regression; original r45/r47 objects stay read-only."""
from pathlib import Path
import hashlib, io, json, shutil, subprocess, tarfile, time
w=Path(__file__).resolve().parent;o=Path('D:/FPGACompetitionProject')
c=Path('C:/Users/cenyongdong/.codex/worktrees/hdmi-s01-isolation/FPGACompetitionProject')
s=c/'FPGA/hdmi_candidate/diagnostics/native_rgb565_r51'
e=o/'tools/pose-v1/evidence/hdmi-render-overlap-20261024-r51';e.mkdir(exist_ok=True)
if not (w/'joint').exists():
    shutil.copytree(s/'joint',w/'joint')
    (w/'native-render').mkdir()
    for name in ('hdmi_renderer.hpp','hdmi_renderer.cpp','raster565.hpp','font5x7.hpp'):
        shutil.copyfile(c/'software/core/display'/name,w/'native-render'/name)
    shutil.copyfile(s/'cpu_regression.cpp',w/'cpu_regression.cpp')
    shutil.copytree(o/'.local/hdmi-render-speed-20261024-r47/fixtures',w/'fixtures')
    (w/'golden').mkdir()
    with tarfile.open(o/'tools/pose-v1/evidence/hdmi-render-speed-20261024-r47/cpu-evidence.tar.gz') as t:
        for ident in ('308','309','310'):
            (w/'golden'/('native-'+ident+'.rgb565')).write_bytes(t.extractfile('cpu-output/native-'+ident+'.rgb565').read())
d='C:/Program Files/Docker/Docker/resources/bin/docker.exe';r='/tmp/hdmi-render-overlap-20261024-r51'
base='/tmp/hp2-deferred-consume-20261024-r45/source';execution=[]
def run(name,args):
    start=time.monotonic();p=subprocess.run([d,*args],capture_output=True)
    (e/(name+'.stdout.log')).write_bytes(p.stdout);(e/(name+'.stderr.log')).write_bytes(p.stderr)
    execution.append(dict(stage=name,argv=args,native_exit=p.returncode,seconds=time.monotonic()-start))
    (e/'build-execution.json').write_text(json.dumps(execution,indent=2)+'\n')
    print(json.dumps(execution[-1]),flush=True)
    if p.returncode:raise RuntimeError(name+': '+p.stderr.decode(errors='replace')[-1600:])
    return p.stdout
started=run('container-before',['inspect','--format','{{.State.Status}}','FPAI']).strip()==b'exited'
if started:run('container-start',['start','FPAI'])
try:
    run('fresh-directory',['exec','FPAI','mkdir',r])
    for name in ('joint','native-render','fixtures','golden','cpu_regression.cpp'):
        run('copy-'+name.replace('.','-'),['cp',str(w/name),'FPAI:'+r+'/'+name])
    run('compiler',['exec','FPAI','aarch64-linux-gnu-g++','--version'])
    run('cpu-cross-compile',['exec','FPAI','aarch64-linux-gnu-g++','-std=c++17','-O3','-DNDEBUG',
        '-ffp-contract=off','-Wall','-Wextra','-Wpedantic','-I'+r+'/native-render','-I'+base+'/display',
        r+'/cpu_regression.cpp',r+'/native-render/hdmi_renderer.cpp',r+'/joint/projection.cpp','-o',r+'/renderer_overlap_bench'])
    run('return-cpu',['cp','FPAI:'+r+'/renderer_overlap_bench',str(w/'renderer_overlap_bench')])
    deps=run('cpu-ELF',['exec','FPAI','aarch64-linux-gnu-readelf','-h','-d',r+'/renderer_overlap_bench'])
    if b'icraft' in deps:raise RuntimeError('CPU regression unexpectedly links SDK')
    run('joint-configure',['exec','FPAI','cmake','-S',r+'/joint','-B',r+'/build',
        '-DCMAKE_SYSTEM_NAME=Linux','-DCMAKE_SYSTEM_PROCESSOR=aarch64','-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++',
        '-DCMAKE_PREFIX_PATH=/usr/cmake','-DCMAKE_BUILD_TYPE=Release','-DBASE_SOURCE='+base,'-DNATIVE_SOURCE='+r+'/native-render'])
    run('joint-compile',['exec','FPAI','cmake','--build',r+'/build','--target','pose_demo_v1','--parallel','2'])
    run('return-joint',['cp','FPAI:'+r+'/build/pose_demo_v1',str(w/'pose_demo_v1')])
    run('reused-objects',['exec','FPAI','cat',r+'/build/reused-objects.txt'])
finally:
    if started:run('container-stop',['stop','FPAI'])
binary=(w/'pose_demo_v1').read_bytes();source=o/'.local/hdmi-render-speed-20261024-r47/software-native-rgb565-final.tar.gz'
with tarfile.open(source) as src:
    identity=json.load(src.extractfile('software/identity.json'))
    identity['files']['pose_demo_v1']=hashlib.sha256(binary).hexdigest()
    replacements={'software/pose_demo_v1':binary,'software/identity.json':(json.dumps(identity,indent=2)+'\n').encode()}
    out=w/'software-native-overlap.tar.gz'
    with tarfile.open(out,'x:gz') as dst:
        for member in src:
            if member.name in replacements:
                data=replacements[member.name];member.size=len(data);dst.addfile(member,io.BytesIO(data))
            else:dst.addfile(member,src.extractfile(member) if member.isfile() else None)
with tarfile.open(w/'cpu-package.tar.gz','x:gz') as t:
    for name in ('renderer_overlap_bench','fixtures','golden'):t.add(w/name,arcname=name)
result=dict(compiled=True,SDK_executed=False,hardware_rebuilt=False,model_math_SDK_NPU_wire_unchanged=True,
            binary_sha256=identity['files']['pose_demo_v1'],software_archive_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
            cpu_archive_sha256=hashlib.sha256((w/'cpu-package.tar.gz').read_bytes()).hexdigest())
(e/'build-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

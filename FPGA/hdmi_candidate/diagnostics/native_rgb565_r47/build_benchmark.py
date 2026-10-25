"""Existing container/toolchain, CPU-only renderer build, no SDK/NPU/BOOT."""
from pathlib import Path
import subprocess,time,json,hashlib,tarfile
W=Path(__file__).resolve().parent
E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-render-speed-20261024-r47');E.mkdir(exist_ok=True)
D='C:/Program Files/Docker/Docker/resources/bin/docker.exe';remote='/tmp/hdmi-render-speed-20261024-r47'
records=[]
def run(name,args):
    start=time.monotonic();p=subprocess.run([D,*args],capture_output=True)
    (E/(name+'.stdout.log')).write_bytes(p.stdout);(E/(name+'.stderr.log')).write_bytes(p.stderr)
    records.append(dict(stage=name,argv=args,native_exit=p.returncode,seconds=time.monotonic()-start))
    (E/'build-execution.json').write_bytes((json.dumps(records,indent=2)+'\n').encode())
    print(json.dumps(records[-1]),flush=True)
    if p.returncode:raise RuntimeError(name+' failed: '+p.stderr.decode(errors='replace')[-2000:])
    return p.stdout
status=run('container-before',['inspect','--format','{{.State.Status}}','FPAI']).strip()
started=status==b'exited'
if started:run('container-start',['start','FPAI'])
try:
    run('fresh-build-directory',['exec','FPAI','mkdir',remote])
    for name in ('benchmark','native-render','fixtures'):
        run('copy-'+name,['cp',str(W/name),'FPAI:'+remote+'/'+name])
    run('copy-main',['cp',str(W/'benchmark_main.cpp'),'FPAI:'+remote+'/benchmark_main.cpp'])
    sources=[remote+'/benchmark_main.cpp',remote+'/benchmark/skeleton_render.cpp',remote+'/benchmark/hdmi_canvas.cpp',remote+'/native-render/hdmi_renderer.cpp']
    common=['-std=c++17','-O3','-DNDEBUG','-ffp-contract=off','-Wall','-Wextra','-Wpedantic','-I'+remote+'/benchmark','-I'+remote+'/native-render',*sources]
    run('compiler-version',['exec','FPAI','aarch64-linux-gnu-g++','--version'])
    run('build-aarch64',['exec','FPAI','aarch64-linux-gnu-g++',*common,'-o',remote+'/renderer_bench'])
    run('build-host-linux',['exec','FPAI','g++',*common,'-o',remote+'/renderer_bench_host'])
    run('host-preview-directory',['exec','FPAI','mkdir',remote+'/host-output'])
    output=run('host-CPU-check',['exec','FPAI',remote+'/renderer_bench_host',remote+'/fixtures',remote+'/host-output','3'])
    result=json.loads(output.decode().strip().splitlines()[-1]);(E/'host-cpu.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    run('return-binary',['cp','FPAI:'+remote+'/renderer_bench',str(W/'renderer_bench')])
    run('return-host-previews',['cp','FPAI:'+remote+'/host-output',str(W/'host-output')])
    dynamic=run('native-ELF',['exec','FPAI','aarch64-linux-gnu-readelf','-h','-d',remote+'/renderer_bench'])
    assert b'icraft' not in dynamic and b'customop' not in dynamic
    (E/'binary-identity.json').write_bytes((json.dumps(dict(bytes=(W/'renderer_bench').stat().st_size,
        sha256=hashlib.sha256((W/'renderer_bench').read_bytes()).hexdigest(),SDK_linked=False,MMIO=False),indent=2)+'\n').encode())
finally:
    if started:run('container-stop',['stop','FPAI'])
    run('container-after',['inspect','--format','{{.State.Status}}','FPAI'])

"""Build the finite public-SDK DMA probe with same-device observer capture."""
from pathlib import Path
import subprocess,time,json,hashlib,shutil
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r2/build-monitor-probe'
W=R/'.local/hdmi-live-20261017-r1/monitor-probe-source-r2'
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
for name in ['ai_dma_probe.cpp','ai_monitor_sdk.hpp']:
 shutil.copyfile(R/'FPGA/hdmi_candidate/software'/name,W/name)
(W/'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.24)
project(ai_dma_probe LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
find_package(icraft-zg330backend 3.39.0.0 EXACT REQUIRED)
add_executable(ai_dma_probe ai_dma_probe.cpp)
target_compile_options(ai_dma_probe PRIVATE -Wall -Wextra -Werror)
target_link_options(ai_dma_probe PRIVATE -Wl,--no-as-needed)
target_link_libraries(ai_dma_probe PRIVATE Icraft::ZG330Backend)
''')
shutil.copytree(W,E/'source')
docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe';steps=[]
def run(label,args,budget=90):
 start=time.monotonic();p=subprocess.run([docker,*args],capture_output=True,timeout=budget)
 (E/(label+'.stdout.txt')).write_bytes(p.stdout);(E/(label+'.stderr.txt')).write_bytes(p.stderr)
 steps.append(dict(label=label,args=args,exit=p.returncode,seconds=time.monotonic()-start,budget=budget))
 (E/'execution.json').write_text(json.dumps(steps,indent=2))
 if p.returncode:raise RuntimeError(label+' failed; preserve and stop')
 return p.stdout
assert run('state',['inspect','--format','{{.State.Status}}','FPAI']).strip()==b'exited','Do not interrupt another container owner'
run('start',['start','FPAI'],30)
try:
 expected=json.loads((R/'tools/pose-v1/evidence/hdmi-register-probe-20261015-r3/expected.json').read_text())['libraries']
 actual=run('SDK',['exec','FPAI','sha256sum',*['/usr/lib/aarch64-linux-gnu/'+n for n in expected]]).decode()
 assert {Path(x.split()[1]).name:x.split()[0] for x in actual.splitlines()}==expected
 dest='/tmp/hdmi-live-monitor-probe-20261017-r2'
 run('fresh',['exec','FPAI','test','!','-e',dest]);run('copy',['cp',str(W),'FPAI:'+dest])
 run('configure',['exec','FPAI','cmake','-S',dest,'-B',dest+'/build','-DCMAKE_SYSTEM_NAME=Linux','-DCMAKE_SYSTEM_PROCESSOR=aarch64','-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++','-DCMAKE_PREFIX_PATH=/usr/cmake'])
 run('build',['exec','FPAI','cmake','--build',dest+'/build','--parallel','2'])
 run('binary',['cp','FPAI:'+dest+'/build/ai_dma_probe',str(E/'ai_dma_probe')])
 elf=run('ELF',['exec','FPAI','aarch64-linux-gnu-readelf','-h','-d',dest+'/build/ai_dma_probe'])
 assert b'AArch64' in elf and b'libicraft_zg330backend.so' in elf
 result={'compiled':True,'board_executed':False,'binary_sha256':hashlib.sha256((E/'ai_dma_probe').read_bytes()).hexdigest(),'SDK':expected}
 (E/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
finally:
 run('stop',['stop','FPAI'],30)

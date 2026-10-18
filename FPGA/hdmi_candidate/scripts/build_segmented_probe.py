"""Build the bounded r11 SDK diagnostic in the existing FPAI container."""
from pathlib import Path
import hashlib,json,shutil,subprocess,time

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'tools/pose-v1/evidence/hdmi-segmented-20261018-r11'
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
WORK=OUT/'build'; WORK.mkdir(exist_ok=False)
steps=[]
def run(label,args):
    start=time.monotonic()
    with (WORK/(label+'.log')).open('xb') as log:
        p=subprocess.Popen([str(x) for x in args],stdout=log,stderr=subprocess.STDOUT)
        while p.poll() is None:
            try:p.wait(timeout=30)
            except subprocess.TimeoutExpired:print(label+' still running PID '+str(p.pid),flush=True)
    row=dict(label=label,argv=[str(x) for x in args],exit_code=p.returncode,seconds=time.monotonic()-start)
    steps.append(row);(WORK/'execution.json').write_text(json.dumps(steps,indent=2))
    if p.returncode:raise RuntimeError(label+' failed; original log preserved')
    return (WORK/(label+'.log')).read_text(errors='replace')

status=run('initial-state',[DOCKER,'inspect','FPAI','--format','{{.State.Status}}']).strip()
if status!='exited':raise RuntimeError('FPAI already owned/running; do not alter it')
source=ROOT/'FPGA/hdmi_candidate/software'
for n in ('ai_read_segmented_probe.cpp','ai_read_monitor_sdk.hpp','ai_monitor_sdk.hpp','dma_probe_evidence.hpp'):
    shutil.copyfile(source/n,WORK/n)
(WORK/'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.24)
project(segmented_probe LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
find_package(icraft-zg330backend 3.39.0.0 EXACT REQUIRED)
add_executable(ai_read_segmented_probe ai_read_segmented_probe.cpp)
target_compile_options(ai_read_segmented_probe PRIVATE -Wall -Wextra -Werror)
target_link_options(ai_read_segmented_probe PRIVATE -Wl,--no-as-needed)
target_link_libraries(ai_read_segmented_probe PRIVATE Icraft::ZG330Backend)
''')
owned=False
try:
    run('start',[DOCKER,'start','FPAI']);owned=True
    expected=json.loads((ROOT/'tools/pose-v1/evidence/hdmi-live-20261018-r9/remote-read-v3-sources-r9r1/configuration.json').read_text())['board']['SDK']
    actual=run('SDK',[DOCKER,'exec','FPAI','sha256sum',*['/usr/lib/aarch64-linux-gnu/'+n for n in expected]])
    got={Path(line.split()[1]).name:line.split()[0] for line in actual.splitlines()}
    if got!=expected:raise RuntimeError('Protected container SDK changed')
    dest='/tmp/hdmi-segmented-20261018-r11'
    run('copy-source',[DOCKER,'cp',str(WORK),'FPAI:'+dest])
    run('configure',[DOCKER,'exec','FPAI','cmake','-S',dest,'-B',dest+'/obj','-DCMAKE_SYSTEM_NAME=Linux','-DCMAKE_SYSTEM_PROCESSOR=aarch64','-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++','-DCMAKE_PREFIX_PATH=/usr/cmake'])
    run('compile',[DOCKER,'exec','FPAI','cmake','--build',dest+'/obj','--parallel','2'])
    elf=OUT/'ai_read_segmented_probe'
    run('copy-ELF',[DOCKER,'cp','FPAI:'+dest+'/obj/ai_read_segmented_probe',str(elf)])
    native=run('readelf',[DOCKER,'exec','FPAI','aarch64-linux-gnu-readelf','-h','-d',dest+'/obj/ai_read_segmented_probe'])
    if 'AArch64' not in native or 'libicraft_zg330backend.so' not in native:raise RuntimeError('ELF target/link mismatch')
    (WORK/'result.json').write_text(json.dumps(dict(compiled=True,binary_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),binary_bytes=elf.stat().st_size,SDK=got),indent=2))
finally:
    if owned:
        # All synchronous build commands above have finished. Inspect before stop.
        top=run('container-processes',[DOCKER,'top','FPAI','-eo','pid,comm,args'])
        if any(x in top for x in ('cc1plus','cmake --build','aarch64-linux-gnu-g++')):raise RuntimeError('Build still executing: preserve container and inspect')
        run('stop-owned-container',[DOCKER,'stop','FPAI'])
print('SEGMENTED_PROBE_BUILD_PASS',flush=True)

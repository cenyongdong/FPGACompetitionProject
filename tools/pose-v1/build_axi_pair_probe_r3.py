"""Isolated build/package with exact source, public headers and libraries recorded."""
from pathlib import Path
import hashlib,json,subprocess,shutil,re
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.local/pose-v1-build/axi-pair-20261011-r3'
PKG=ROOT/'.local/pose-v1-axi-pair/package-20261011-r3'
assert not OUT.exists() and not PKG.exists();OUT.mkdir();PKG.mkdir()
D='C:/Program Files/Docker/Docker/resources/bin/docker.exe';remote='/tmp/pose-v1-axi-pair-20261011-r3'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=OUT/'source';source.mkdir();mappings={}
cmake=ROOT/'tools/pose-v1/axi-pair-CMakeLists.txt'
queue=[ROOT/'software/pose_v1/src'/name for name in set(re.findall(r'\b\w+\.cpp\b',cmake.read_text()))]
queue=[ROOT/'software/pose_v1/src/scratch_copy_pattern_r3.cpp' if p.name=='scratch_copy_pattern.cpp' else p for p in queue]
while queue:
    p=queue.pop();rel=p.relative_to(ROOT).as_posix()
    if rel in mappings:continue
    destination='scratch_copy_pattern.cpp' if p.name=='scratch_copy_pattern_r3.cpp' else ('scratch_copy_pattern.hpp' if p.name=='scratch_copy_pattern_r3.hpp' else p.name)
    if p.name=='scratch_copy_pattern.hpp':p=ROOT/'software/pose_v1/include/scratch_copy_pattern_r3.hpp';rel=p.relative_to(ROOT).as_posix()
    mappings[rel]={'destination':destination,'sha256':sha(p)};shutil.copyfile(p,source/destination)
    for h in re.findall(r'#include "([^\"]+)"',p.read_text(encoding='utf-8')):
        queue.append(ROOT/'software/pose_v1/include'/h)
shutil.copyfile(cmake,source/'CMakeLists.txt');mappings[cmake.relative_to(ROOT).as_posix()]={'destination':'CMakeLists.txt','sha256':sha(cmake)}
toolchain='set(CMAKE_SYSTEM_NAME Linux)\nset(CMAKE_SYSTEM_PROCESSOR aarch64)\nset(CMAKE_CXX_COMPILER /usr/bin/aarch64-linux-gnu-g++)\n'
(source/'toolchain.cmake').write_text(toolchain,encoding='utf-8',newline='\n')
old=ROOT/'.local/pose-v1-plddr-position/package-20261010-r1';baseline=json.loads((old/'manifest.json').read_text());(PKG/'graph').mkdir();shutil.copyfile(old/'graph/piw24_ZG.json',PKG/'graph/piw24_ZG.json')
manifest={'build_files':mappings,'generated_toolchain_sha256':sha(source/'toolchain.cmake'),'graph_sha256':sha(PKG/'graph/piw24_ZG.json'),'sdk_headers_normalized_sha256':baseline['sdk_headers_normalized_sha256'],'libraries':{'libaxizg330aiu.so':'d55e48873da61314da712c584e62f8257f63794ecca481e64868361ee5fc7178','libicraft_xrt.so':'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96','libicraft_hostbackend.so':baseline['host_library_sha256'],'libicraft_zg330backend.so':baseline['zg_library_sha256']},'no_model_execution':True}
(PKG/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
def run(args):
    p=subprocess.run([D,*args],capture_output=True)
    with (OUT/'build.log').open('ab') as f:f.write(('argv: '+repr(args)+'\n').encode()+p.stdout+p.stderr)
    assert p.returncode==0,(args,p.stderr[-2000:]);return p.stdout
run(['exec','FPAI','test','!','-e',remote]);run(['exec','FPAI','mkdir',remote]);run(['cp',str(source),'FPAI:'+remote+'/source'])
sdk=OUT/'sdk';sdk.mkdir()
for pkg in ('icraft:arm64','customop:arm64'):assert run(['exec','FPAI','dpkg-query','-W','-f=${Version}',pkg])==b'3.39.0'
for lib,digest in manifest['libraries'].items():run(['cp','-L','FPAI:/usr/lib/aarch64-linux-gnu/'+lib,str(sdk/lib)]);assert sha(sdk/lib)==digest
for h,digest in manifest['sdk_headers_normalized_sha256'].items():
    p=sdk/h;p.parent.mkdir(parents=True,exist_ok=True);run(['cp','-L','FPAI:/usr/include/'+h,str(p)]);assert hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest
run(['exec','FPAI','aarch64-linux-gnu-g++','--version']);run(['exec','FPAI','cmake','--version'])
run(['exec','FPAI','cmake','-S',remote+'/source','-B',remote+'/build','-DCMAKE_TOOLCHAIN_FILE='+remote+'/source/toolchain.cmake','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_FLAGS_RELEASE=-O2 -DNDEBUG','-DCMAKE_PREFIX_PATH=/usr/cmake'])
run(['exec','FPAI','cmake','--build',remote+'/build','--parallel','2'])
for name in ('pose_axi_pair_check','pose_axi_pair_host_check'):run(['cp','FPAI:'+remote+'/build/'+name,str(OUT/name)]);run(['exec','FPAI','aarch64-linux-gnu-readelf','-d',remote+'/build/'+name])
result={'status':'compiled_not_executed','sources':mappings,'manifest_sha256':sha(PKG/'manifest.json'),'libraries':manifest['libraries'],'programs':{name:sha(OUT/name) for name in ('pose_axi_pair_check','pose_axi_pair_host_check')},'device_opened':False}
(OUT/'build-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Build complete:',len(mappings),'sources;',result['programs'])


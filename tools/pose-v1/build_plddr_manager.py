"""Build the independent public allocator audit; never execute ARM on the host."""
from pathlib import Path
import hashlib,json,subprocess,shutil
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.local/pose-v1-build/plddr-manager-20261010-r1'
REMOTE='/tmp/pose-plddr-manager-20261010-r1'
DOCKER=r'C:/Program Files/Docker/Docker/resources/bin/docker.exe'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
    p=subprocess.run([DOCKER,*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    with (OUT/'build.log').open('ab') as f:f.write(p.stdout)
    if p.returncode:raise RuntimeError(p.stdout.decode(errors='replace'))
    return p.stdout
assert not OUT.exists();OUT.mkdir(parents=True);source=OUT/'source';source.mkdir()
files={'software/pose_v1/src/plddr_manager_check.cpp':'plddr_manager_check.cpp','tools/pose-v1/plddr-manager-CMakeLists.txt':'CMakeLists.txt'}
for f,d in files.items():shutil.copyfile(ROOT/f,source/d)
toolchain=ROOT/'.local/pose-v1-build/mixed-20261010-typed-scratch-r1/source/toolchain.cmake';shutil.copyfile(toolchain,source/'toolchain.cmake')
run(['exec','FPAI','test','!','-e',REMOTE]);run(['exec','FPAI','mkdir',REMOTE]);run(['cp',str(source),'FPAI:'+REMOTE+'/source'])
m=json.loads((ROOT/'.local/pose-v1-typed-scratch/package-20261010-r1/manifest.json').read_text())
snap=OUT/'sdk';snap.mkdir();headers={}
for rel,expected in m['sdk_headers_normalized_sha256'].items():
    dest=snap/rel;dest.parent.mkdir(parents=True,exist_ok=True);run(['cp','-L','FPAI:/usr/include/'+rel,str(dest)])
    actual=hashlib.sha256(dest.read_bytes().replace(b'\r\n',b'\n')).hexdigest();assert actual==expected;headers[rel]=actual
libraries={}
for name,expected in {'libicraft_hostbackend.so':m['host_library_sha256'],'libicraft_zg330backend.so':m['zg_library_sha256'],'libicraft_xrt.so':'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96','libaxizg330aiu.so':'d55e48873da61314da712c584e62f8257f63794ecca481e64868361ee5fc7178'}.items():
    dest=snap/name;run(['cp','-L','FPAI:/usr/lib/aarch64-linux-gnu/'+name,str(dest)]);assert sha(dest)==expected;libraries[name]=expected
for pkg in ['icraft:arm64','customop:arm64']:assert run(['exec','FPAI','dpkg-query','-W','-f=${Version}',pkg]).strip()==b'3.39.0'
# Complete bounded function regions retained as bytes, not console excerpts.
sections={'Tensor-mallocOn':('libicraft_xrt.so',0x681f0,0x682f8),'Default-malloc':('libicraft_xrt.so',0x3aee8,0x3c088),'CreateMemChunk':('libicraft_xrt.so',0x379d0,0x37c20),'Default-info':('libicraft_xrt.so',0x358e0,0x358e8),'PLDDR-malloc':('libaxizg330aiu.so',0x2b2c8,0x2b320),'PLDDR-init':('libaxizg330aiu.so',0x3e388,0x3ea10)}
for title,(lib,begin,end) in sections.items():
    (OUT/(title+'.asm')).write_bytes(run(['exec','FPAI','aarch64-linux-gnu-objdump','-d','-C','--start-address='+hex(begin),'--stop-address='+hex(end),'/usr/lib/aarch64-linux-gnu/'+lib]))
run(['exec','FPAI','cmake','-S',REMOTE+'/source','-B',REMOTE+'/build','-DCMAKE_TOOLCHAIN_FILE='+REMOTE+'/source/toolchain.cmake','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_PREFIX_PATH=/usr/cmake'])
run(['exec','FPAI','cmake','--build',REMOTE+'/build','--parallel','2']);run(['cp','FPAI:'+REMOTE+'/build/pose_plddr_manager_check',str(OUT/'pose_plddr_manager_check')])
report=dict(status='compiled_not_executed',binary_sha256=sha(OUT/'pose_plddr_manager_check'),source_sha256={p:sha(ROOT/p) for p in files},headers_normalized_sha256=headers,libraries=libraries,toolchain_sha256=sha(toolchain),disassembly_sha256={p.name:sha(p) for p in OUT.glob('*.asm')})
(OUT/'build-result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

"""Complete symbol-sized windows, preserving the original bounded capture."""
from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'tools/pose-v1/evidence/axi-read-audit-20261011-r1/complete'
assert not OUT.exists();OUT.mkdir()
D='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
windows={'Tensor-read':('libicraft_xrt.so',0x6bf90,0x410),'Tensor-copyFrom':('libicraft_xrt.so',0x682f8,0x70),'MemChunk-read':('libicraft_xrt.so',0x3a428,0x104),'MemRegion-read':('libicraft_xrt.so',0x365d0,0x48),'PL-init':('libaxizg330aiu.so',0x3e388,0x42c),'Reg-read':('libaxizg330aiu.so',0x4ea80,0x3b8),'Reg-write':('libaxizg330aiu.so',0x4e6c0,0x3c0)}
for name,(lib,start,size) in windows.items():
    p=subprocess.run([D,'exec','FPAI','aarch64-linux-gnu-objdump','-d','-C','--start-address='+hex(start),'--stop-address='+hex(start+size),'/usr/lib/aarch64-linux-gnu/'+lib],capture_output=True)
    (OUT/(name+'.stdout')).write_bytes(p.stdout);(OUT/(name+'.stderr')).write_bytes(p.stderr);assert p.returncode==0
p=subprocess.run([D,'exec','FPAI','aarch64-linux-gnu-objdump','-s','--start-address=0x56ea0','--stop-address=0x56ec0','/usr/lib/aarch64-linux-gnu/libaxizg330aiu.so'],capture_output=True);assert p.returncode==0;(OUT/'region-name.stdout').write_bytes(p.stdout)
(OUT/'identity.json').write_text(json.dumps({'windows':windows,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file()},'read_only':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Exact symbol windows saved')

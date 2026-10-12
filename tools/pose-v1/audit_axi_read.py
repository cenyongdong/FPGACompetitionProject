"""Read-only matching library audit. No ARM execution, device open or register access."""
from pathlib import Path
import hashlib,json,subprocess,re
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'tools/pose-v1/evidence/axi-read-audit-20261011-r1'
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
assert not OUT.exists();OUT.mkdir();sdk=OUT/'sdk';sdk.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,name):
    p=subprocess.run([DOCKER,*args],capture_output=True)
    (OUT/(name+'.stdout')).write_bytes(p.stdout);(OUT/(name+'.stderr')).write_bytes(p.stderr)
    assert p.returncode==0,(name,p.stderr)
    return p.stdout
expected={'libaxizg330aiu.so':'d55e48873da61314da712c584e62f8257f63794ecca481e64868361ee5fc7178','libicraft_xrt.so':'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96'}
for name,digest in expected.items():
    run(['cp','-L','FPAI:/usr/lib/aarch64-linux-gnu/'+name,str(sdk/name)],'copy-'+name)
    assert sha(sdk/name)==digest
    run(['exec','FPAI','aarch64-linux-gnu-nm','-D','-S','-C','/usr/lib/aarch64-linux-gnu/'+name],name+'-symbols')
for pkg in ['icraft:arm64','customop:arm64']:assert run(['exec','FPAI','dpkg-query','-W','-f=${Version}',pkg],pkg.replace(':','-'))==b'3.39.0'
sections={'PL-read':('libaxizg330aiu.so',0x53e20,0x53f9c),'DMA-read':('libaxizg330aiu.so',0x53860,0x53e20),'UDMA-read':('libaxizg330aiu.so',0x2c4f8,0x2c780),'UDMA-write':('libaxizg330aiu.so',0x2c780,0x2ca04),'PL-init':('libaxizg330aiu.so',0x3e388,0x3ea10),'UDMA-init':('libaxizg330aiu.so',0x29d00,0x29d04),'MemRegion-read':('libicraft_xrt.so',0x365d0,0x365f0),'MemChunk-read':('libicraft_xrt.so',0x3a428,0x3a49c),'Tensor-read':('libicraft_xrt.so',0x6bf90,0x6c318)}
for title,(lib,start,end) in sections.items():
    run(['exec','FPAI','aarch64-linux-gnu-objdump','-d','-C','--start-address='+hex(start),'--stop-address='+hex(end),'/usr/lib/aarch64-linux-gnu/'+lib],title)
    # Raw bounded function window; symbol sizes additionally checked in review.
for name in expected:run(['exec','FPAI','strings','-t','x','/usr/lib/aarch64-linux-gnu/'+name],name+'-strings')
write=json.dumps(dict(status='read_only_library_audit_captured',libraries=expected,sections=sections,files_SHA256={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()},no_device_execution=True,no_register_access=True),indent=2)+'\n'
(OUT/'identity.json').write_text(write,encoding='utf-8',newline='\n')
print('Matching AXI/XRT bounded read audit saved',OUT)

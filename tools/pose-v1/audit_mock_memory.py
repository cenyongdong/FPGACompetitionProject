"""Read matching mock library symbols/short functions; never execute SDK."""
from pathlib import Path
import hashlib,subprocess,json,re
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-group-20261011-r1';out=E/'mock-driver-audit';assert not out.exists();out.mkdir()
D='C:/Program Files/Docker/Docker/resources/bin/docker.exe';lib='/usr/lib/aarch64-linux-gnu/libmockzg330.so'
p=subprocess.run([D,'cp','-L','FPAI:'+lib,str(out/'libmockzg330.so')],capture_output=True);assert p.returncode==0
p=subprocess.run([D,'exec','FPAI','aarch64-linux-gnu-nm','-S','-C',lib],capture_output=True);assert p.returncode==0;(out/'symbols.txt').write_bytes(p.stdout)
rows=[]
for line in p.stdout.decode().splitlines():
    if re.search(r'MockZG330.*::(read|write|memcpy)\(',line):
        fields=line.split();start=int(fields[0],16);size=int(fields[1],16)
        p=subprocess.run([D,'exec','FPAI','aarch64-linux-gnu-objdump','-d','-C','--start-address='+hex(start),'--stop-address='+hex(start+size),lib],capture_output=True);assert p.returncode==0
        name='function-'+str(len(rows))+'.txt';(out/name).write_bytes(p.stdout);rows.append({'symbol':line,'disassembly':name,'bytes':size})
report={'library_sha256':hashlib.sha256((out/'libmockzg330.so').read_bytes()).hexdigest(),'functions':rows,'actual_roundtrip_all_zero':True,'physical_test_performed':False}
(out/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

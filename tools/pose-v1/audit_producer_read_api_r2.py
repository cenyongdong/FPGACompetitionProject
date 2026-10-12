"""Verify current ARM headers/libraries against matched allocator evidence."""
from pathlib import Path
import hashlib,json,subprocess,shutil
R=Path(__file__).resolve().parents[2];B=R/'.local/pose-v1-build/producer-source-read-20261011-r2';E=R/'tools/pose-v1/evidence/producer-source-read-20261011-r2'
assert E.exists() and not (E/'api-audit.json').exists();out=B/'api';out.mkdir();D='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
base=R/'.local/pose-v1-build/plddr-manager-20261010-r1';m=json.loads((base/'build-result.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
headers={}
for rel in ('icraft-xrt/core/device.h','icraft-xrt/core/tensor.h','icraft-xrt/dev/zg330_device.h'):
    dest=out/Path(rel).name;subprocess.run([D,'cp','-L','FPAI:/usr/include/'+rel,str(dest)],check=True,capture_output=True)
    h=hashlib.sha256(dest.read_bytes().replace(b'\r\n',b'\n')).hexdigest();assert h==m['headers_normalized_sha256'][rel];headers[rel]=h
current=json.loads((B/'build-result.json').read_text());assert current['libraries']['libicraft_xrt.so']==m['libraries']['libicraft_xrt.so'] and current['libraries']['libaxizg330aiu.so']==m['libraries']['libaxizg330aiu.so']
asm={}
for name in ('PLDDR-malloc.asm','Default-malloc.asm','CreateMemChunk.asm','Region-CreateMemChunk.asm','MemChunk-constructor.asm'):
    p=base/name;assert p.is_file();shutil.copyfile(p,E/name);asm[name]=sha(p)
old_accept=R/'tools/pose-v1/evidence/plddr-position-20261010-r1/manager.acceptance.json';assert json.loads(old_accept.read_text())['status']=='public_allocator_audit_passed'
report={'status':'matched_ARM_public_allocator_evidence_reused','headers_normalized_sha256':headers,'library_sha256':current['libraries'],'prior_acceptance_sha256':sha(old_accept),'assembly_sha256':asm,
        'prefix_bytes':104*1024*1024,'band':[104*1024*1024,105*1024*1024],'declared_capacity_not_full_physical_validation':True,
        'automatic_allocation_only':True,'prefix_data_access_calls':0,'Linux_CMA_allocation':False,'Device_Session_opened_by_this_audit':False}
(E/'api-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('ARM device/tensor/ZG headers and allocator library identities matched; API evidence archived')

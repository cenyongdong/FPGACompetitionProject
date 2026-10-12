"""Build isolated group and SDK-free payload contracts; no physical execution."""
from pathlib import Path
import hashlib,json,subprocess,shutil,tarfile
R=Path(__file__).resolve().parents[2];tag='20261011-r1'
B=R/('.local/pose-v1-build/producer-group-'+tag);E=R/('tools/pose-v1/evidence/producer-group-'+tag)
assert not B.exists() and not E.exists();B.mkdir();E.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D='C:/Program Files/Docker/Docker/resources/bin/docker.exe';remote='/tmp/pose-producer-group-build-'+tag
files=['software/pose_v1/'+n for n in ('include/producer_payload.hpp','src/producer_payload.cpp','src/producer_payload_selftest.cpp','include/producer_sdk.hpp','src/producer_sdk.cpp','src/producer_group_check.cpp','include/mixed_fusion_baseline.hpp')]
s=B/'source';s.mkdir()
for p in files:shutil.copyfile(R/p,s/Path(p).name)
def run(args):
    p=subprocess.run([D,*args],capture_output=True)
    with (B/'build.log').open('ab') as f:f.write((repr(args)+'\n').encode()+p.stdout+p.stderr)
    assert p.returncode==0,p.stderr[-3000:];return p.stdout
run(['exec','FPAI','test','!','-e',remote]);run(['exec','FPAI','mkdir',remote]);run(['cp',str(s),'FPAI:'+remote+'/source'])
ref=R/'tools/pose-v1/evidence/producer-reference-20261011-r2';run(['cp',str(ref/'patterns'),'FPAI:'+remote+'/patterns'])
flags=['-std=gnu++17','-O2','-DNDEBUG','-Wall','-Wextra','-Wpedantic','-Werror','-I'+remote+'/source']
payload=[remote+'/source/producer_payload.cpp',remote+'/source/producer_payload_selftest.cpp']
run(['exec','FPAI','g++',*flags,*payload,'-o',remote+'/payload.native'])
native=run(['exec','FPAI',remote+'/payload.native',remote+'/patterns']);(E/'native.txt').write_bytes(native)
run(['exec','FPAI','aarch64-linux-gnu-g++',*flags,*payload,'-o',remote+'/pose_producer_payload_selftest'])
run(['exec','FPAI','aarch64-linux-gnu-g++',*flags,remote+'/source/producer_payload.cpp',remote+'/source/producer_sdk.cpp',remote+'/source/producer_group_check.cpp','-Wl,--no-as-needed','-licraft_zg330backend','-licraft_xrt','-licraft_xir','-licraft_utils','-o',remote+'/pose_producer_group_check'])
for name in ('pose_producer_group_check','pose_producer_payload_selftest'):run(['cp','FPAI:'+remote+'/'+name,str(B/name)])
headers={}
for rel in ('icraft-xrt/core/tensor.h','icraft-xrt/core/session.h','icraft-xrt/core/device.h','icraft-xrt/dev/host_device.h','icraft-xrt/dev/zg330_device.h','icraft-backends/zg330backend/zg330backend.h'):
    target=B/Path(rel).name;run(['cp','FPAI:/usr/include/'+rel,str(target)]);arm=target.read_bytes().replace(b'\r\n',b'\n');win=(Path('C:/Icraft/CLI v3.39.0/include')/rel).read_bytes().replace(b'\r\n',b'\n');assert arm==win;headers[rel]=hashlib.sha256(arm).hexdigest()
libs={}
for n in ('libicraft_zg330backend.so','libicraft_xrt.so','libicraft_xir.so','libaxizg330aiu.so'):
    run(['cp','-L','FPAI:/usr/lib/aarch64-linux-gnu/'+n,str(B/n)]);libs[n]=sha(B/n)
baseline=json.loads((R/'tools/pose-v1/mixed-fusion-baseline.json').read_text());assert libs['libicraft_zg330backend.so']==baseline['zg_library_sha256']
m={'program_sha256':sha(B/'pose_producer_group_check'),'selftest_sha256':sha(B/'pose_producer_payload_selftest'),'sources':{p:sha(R/p) for p in files},'headers_normalized_sha256':headers,'libraries':libs,'graph_sha256':baseline['graph_sha256'],'raw_sha256':baseline['raw_sha256'],'reference_review_sha256':sha(ref/'reference-review.json'),'physical_device_opened':False,'NPU_executed':False}
(B/'build-result.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
t=E/'transfer';t.mkdir();shutil.copytree(ref/'patterns',t/'patterns')
for p in (B/'pose_producer_group_check',B/'pose_producer_payload_selftest',B/'build-result.json',R/'tools/pose-v1/board_application_preflight.py',R/'tools/pose-v1/board_producer_run.py'):shutil.copyfile(p,t/p.name)
(t/'files.sha256').write_text(''.join(sha(p)+'  '+p.relative_to(t).as_posix()+'\n' for p in sorted(t.rglob('*')) if p.is_file()),encoding='utf-8',newline='\n')
with tarfile.open(E/'transfer.tar','w') as archive:
    for p in sorted(t.rglob('*')):
        if p.is_file():archive.add(p,arcname=p.relative_to(t).as_posix())
(E/'transfer.identity.json').write_text(json.dumps({'archive_sha256':sha(E/'transfer.tar'),'build':m},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Payload Native passed; new ARM group built',m['program_sha256'])

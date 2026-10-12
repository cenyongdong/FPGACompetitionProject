"""Build mock-only SDK deployment inspector; do not execute on real hardware."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile
R=Path(__file__).resolve().parents[2];B=R/'.local/pose-v1-build/producer-mock-20261011-r1';E=R/'tools/pose-v1/evidence/producer-reference-20261011-r2'
assert not B.exists();B.mkdir();s=B/'source';s.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=['software/pose_v1/src/producer_mock_contract.cpp','software/pose_v1/include/mixed_fusion_baseline.hpp']
for p in files:shutil.copyfile(R/p,s/Path(p).name)
D='C:/Program Files/Docker/Docker/resources/bin/docker.exe';remote='/tmp/pose-producer-mock-build-20261011-r1'
def run(args):
    p=subprocess.run([D,*args],capture_output=True)
    with (B/'build.log').open('ab') as f:f.write((repr(args)+'\n').encode()+p.stdout+p.stderr)
    assert p.returncode==0,p.stderr[-3000:];return p.stdout
run(['exec','FPAI','test','!','-e',remote]);run(['exec','FPAI','mkdir',remote]);run(['cp',str(s),'FPAI:'+remote+'/source'])
run(['exec','FPAI','aarch64-linux-gnu-g++','-std=gnu++17','-O2','-DNDEBUG','-Wall','-Wextra','-Wpedantic','-Werror','-I'+remote+'/source',remote+'/source/producer_mock_contract.cpp','-Wl,--no-as-needed','-licraft_zg330backend','-licraft_xrt','-licraft_xir','-licraft_utils','-o',remote+'/pose_producer_mock_contract'])
run(['cp','FPAI:'+remote+'/pose_producer_mock_contract',str(B/'pose_producer_mock_contract')])
manifest={'sources':{p:sha(R/p) for p in files},'program_sha256':sha(B/'pose_producer_mock_contract'),'URL':'mock://zg330','physical_device_opened':False,'forward_called':False,'libraries':{}}
for n in ('libicraft_zg330backend.so','libicraft_xrt.so','libicraft_xir.so'):
    run(['cp','-L','FPAI:/usr/lib/aarch64-linux-gnu/'+n,str(B/n)]);manifest['libraries'][n]=sha(B/n)
(B/'build-result.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
t=E/'mock-transfer';assert not t.exists();t.mkdir()
for p in (B/'pose_producer_mock_contract',B/'build-result.json',R/'tools/pose-v1/run-producer-mock.sh'):shutil.copyfile(p,t/p.name)
(t/'files.sha256').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(t.iterdir())),encoding='utf-8',newline='\n')
with tarfile.open(E/'mock-transfer.tar','w') as archive:
    for p in sorted(t.iterdir()):archive.add(p,arcname=p.name)
print('Mock-only inspector built:',manifest['program_sha256'])

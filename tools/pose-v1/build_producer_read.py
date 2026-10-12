"""Build isolated pre-reset diagnostic; frozen sources preserved."""
from pathlib import Path
import hashlib,json,subprocess,shutil,tarfile,re
R=Path(__file__).resolve().parents[2];tag='20261011-r1';B=R/('.local/pose-v1-build/producer-source-read-'+tag);E=R/('tools/pose-v1/evidence/producer-source-read-'+tag)
assert not B.exists() and not E.exists();B.mkdir();E.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D='C:/Program Files/Docker/Docker/resources/bin/docker.exe';remote='/tmp/pose-producer-source-read-build-'+tag
names=['producer_payload.cpp','producer_payload_selftest.cpp','producer_read_sdk.cpp','producer_read_check.cpp','producer_phase_trace.cpp','producer_phase_selftest.cpp','producer_address_contract.cpp','producer_address_sdk.cpp','producer_address_selftest.cpp','producer_read_contract.cpp','producer_read_selftest.cpp','producer_output_source.cpp','producer_read_host_check.cpp','producer_schedule_selftest.cpp','vpu_ioctl_observation.cpp','vpu_ioctl_observation_selftest.cpp','scratch_vpu_load.cpp','timed_resident_encoder.cpp']
sources=[R/'software/pose_v1/src'/n for n in names];s=B/'source';s.mkdir();mapping={}
while sources:
    p=sources.pop();rel=p.relative_to(R).as_posix()
    if rel in mapping:continue
    mapping[rel]=sha(p);shutil.copyfile(p,s/p.name)
    for h in re.findall(r'#include "([^\"]+)"',p.read_text(encoding='utf-8')):sources.append(R/'software/pose_v1/include'/h)
old=json.loads((R/'.local/pose-v1-build/producer-group-20261011-r2/build-result.json').read_text())
for p,h in old['sources'].items():
    if p in mapping:assert mapping[p]==h
vpu=json.loads((R/'tools/pose-v1/evidence/axi-pair-20261011-r4/build-result.json').read_text())
for p in ('software/pose_v1/src/scratch_vpu_load.cpp','software/pose_v1/src/timed_resident_encoder.cpp'):
    assert mapping[p]==vpu['sources'][p]['sha256']
def run(args):
    p=subprocess.run([D,*args],capture_output=True)
    with (B/'build.log').open('ab') as f:f.write((repr(args)+'\n').encode()+p.stdout+p.stderr)
    assert p.returncode==0,p.stderr[-3500:];return p.stdout
run(['exec','FPAI','test','!','-e',remote]);run(['exec','FPAI','mkdir',remote]);run(['cp',str(s),'FPAI:'+remote+'/source'])
ref=R/'tools/pose-v1/evidence/producer-reference-20261011-r2';run(['cp',str(ref/'patterns'),'FPAI:'+remote+'/patterns'])
flags=['-std=gnu++17','-O2','-DNDEBUG','-Wall','-Wextra','-Wpedantic','-Werror','-pthread','-I'+remote+'/source']
tests={'payload':['producer_payload.cpp','producer_payload_selftest.cpp'],'schedule':['producer_schedule_selftest.cpp'],'observer':['vpu_ioctl_observation.cpp','vpu_ioctl_observation_selftest.cpp'],'phase':['producer_phase_trace.cpp','producer_phase_selftest.cpp'],'address':['producer_address_contract.cpp','producer_address_selftest.cpp'],'read':['producer_read_contract.cpp','producer_read_selftest.cpp']}
for name,files in tests.items():
    files=[remote+'/source/'+p for p in files]
    run(['exec','FPAI','g++',*flags,*files,'-o',remote+'/'+name+'.native'])
    args=[remote+'/'+name+'.native']+([remote+'/patterns'] if name=='payload' else ([remote+'/'+name+'-native'] if name in ('observer','phase') else []))
    (E/(name+'-native.txt')).write_bytes(run(['exec','FPAI',*args]))
    run(['exec','FPAI','aarch64-linux-gnu-g++',*flags,*files,'-o',remote+'/pose_producer_'+name+'_selftest'])
    run(['cp','FPAI:'+remote+'/pose_producer_'+name+'_selftest',str(B/('pose_producer_'+name+'_selftest'))])
run(['exec','FPAI','aarch64-linux-gnu-g++',*flags,remote+'/source/producer_payload.cpp',remote+'/source/producer_read_host_check.cpp','-licraft_xrt','-licraft_xir','-licraft_utils','-o',remote+'/pose_producer_read_host_check'])
run(['cp','FPAI:'+remote+'/pose_producer_read_host_check',str(B/'pose_producer_read_host_check')])
objects={}
for n in ('producer_payload.cpp','producer_read_sdk.cpp','producer_read_check.cpp','producer_phase_trace.cpp','producer_address_contract.cpp','producer_address_sdk.cpp','producer_read_contract.cpp','producer_output_source.cpp','vpu_ioctl_observation.cpp','scratch_vpu_load.cpp','timed_resident_encoder.cpp'):
    target=remote+'/'+n+'.o';extra=['-ffp-contract=off'] if n in ('scratch_vpu_load.cpp','timed_resident_encoder.cpp') else []
    run(['exec','FPAI','aarch64-linux-gnu-g++',*flags,*extra,'-c',remote+'/source/'+n,'-o',target]);run(['cp','FPAI:'+target,str(B/(n+'.o'))]);objects[n]=sha(B/(n+'.o'))
run(['exec','FPAI','aarch64-linux-gnu-g++','-pthread',*[remote+'/'+n+'.o' for n in objects],'-Wl,--wrap=ioctl','-Wl,--no-as-needed','-licraft_zg330backend','-licraft_xrt','-licraft_xir','-licraft_utils','-o',remote+'/pose_producer_read_check'])
run(['cp','FPAI:'+remote+'/pose_producer_read_check',str(B/'pose_producer_read_check')])
# Static caller audit: only the frozen encoder object has undefined ioctl.
symbols=run(['exec','FPAI','aarch64-linux-gnu-nm','-C',remote+'/timed_resident_encoder.cpp.o']).decode();assert ' U ioctl' in symbols;(B/'encoder-symbols.txt').write_text(symbols)
elf=run(['exec','FPAI','aarch64-linux-gnu-readelf','-Ws',remote+'/pose_producer_read_check']).decode();assert '__wrap_ioctl' in elf;(B/'symbols.txt').write_text(elf)
libs={}
for n,h in old['libraries'].items():run(['cp','-L','FPAI:/usr/lib/aarch64-linux-gnu/'+n,str(B/n)]);assert sha(B/n)==h;libs[n]=h
m={'program_sha256':sha(B/'pose_producer_read_check'),'selftests':{name:sha(B/('pose_producer_'+name+'_selftest')) for name in tests},'sources':mapping,'objects':objects,'libraries':libs,'graph_sha256':old['graph_sha256'],'raw_sha256':old['raw_sha256'],'fixed_calls':100,'pace_hz':'5.05','ioctl_scope':'static VPU calls only; SDK DSO calls unchanged','device_opened':False,'NPU_executed':False}
(B/'build-result.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
t=E/'transfer';t.mkdir();shutil.copytree(ref/'patterns',t/'patterns')
for p in [B/'pose_producer_read_check',B/'build-result.json',B/'pose_producer_read_host_check',*[B/('pose_producer_'+n+'_selftest') for n in tests],R/'tools/pose-v1/board_application_preflight.py',R/'tools/pose-v1/board_producer_read_run.py']:shutil.copyfile(p,t/p.name)
(t/'files.sha256').write_text(''.join(sha(p)+'  '+p.relative_to(t).as_posix()+'\n' for p in sorted(t.rglob('*')) if p.is_file()),encoding='utf-8',newline='\n')
with tarfile.open(E/'transfer.tar','w') as f:
    for p in sorted(t.rglob('*')):
        if p.is_file():f.add(p,arcname=p.relative_to(t).as_posix())
(E/'transfer.identity.json').write_text(json.dumps({'archive_sha256':sha(E/'transfer.tar'),'build':m},indent=2)+'\n')
print('Native contracts and fixed100 candidate built',m['program_sha256'])

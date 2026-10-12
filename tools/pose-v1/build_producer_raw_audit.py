"""Build XIR-only RAW exporter and pin all three existing models; no execution."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile
R=Path(__file__).resolve().parents[2]
B=R/'.local/pose-v1-build/producer-raw-20261011-r1'
E=R/'tools/pose-v1/evidence/producer-reference-20261011-r1'
assert not B.exists() and not E.exists();B.mkdir();E.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=B/'source';source.mkdir()
files=['software/pose_v1/src/producer_raw_audit.cpp','software/pose_v1/include/mixed_fusion_baseline.hpp']
for p in files:shutil.copyfile(R/p,source/Path(p).name)
D='C:/Program Files/Docker/Docker/resources/bin/docker.exe';remote='/tmp/pose-producer-raw-build-20261011-r1'
def run(args):
    p=subprocess.run([D,*args],capture_output=True)
    with (B/'build.log').open('ab') as f:f.write((repr(args)+'\n').encode()+p.stdout+p.stderr)
    assert p.returncode==0,p.stderr[-3000:];return p.stdout
run(['exec','FPAI','test','!','-e',remote]);run(['exec','FPAI','mkdir',remote]);run(['cp',str(source),'FPAI:'+remote+'/source'])
run(['exec','FPAI','aarch64-linux-gnu-g++','-std=gnu++17','-O2','-DNDEBUG','-Wall','-Wextra','-Wpedantic','-Werror','-I'+remote+'/source',remote+'/source/producer_raw_audit.cpp','-licraft_xir','-licraft_utils','-o',remote+'/pose_producer_raw_audit'])
run(['cp','FPAI:'+remote+'/pose_producer_raw_audit',str(B/'pose_producer_raw_audit')])
dynamic=run(['exec','FPAI','aarch64-linux-gnu-readelf','-d',remote+'/pose_producer_raw_audit']).decode();assert not any(x in dynamic for x in ('libicraft_xrt','backend','axizg','liveMedia'))
(B/'dynamic.txt').write_text(dynamic)
for rel in ('icraft-xir/core/data.h','icraft-xir/core/network.h','icraft-xir/ops/hard_op.h','icraft-xir/core/data_type.h'):
    dst=B/Path(rel).name;run(['cp','FPAI:/usr/include/'+rel,str(dst)])
    arm=dst.read_bytes().replace(b'\r\n',b'\n');win=(Path('C:/Icraft/CLI v3.39.0/include')/rel).read_bytes().replace(b'\r\n',b'\n');assert arm==win
run(['cp','-L','FPAI:/usr/lib/aarch64-linux-gnu/libicraft_xir.so',str(B/'libicraft_xir.so')])
bundle=E/'transfer';bundle.mkdir();models=bundle/'models';models.mkdir()
origin=Path('D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/result/icraft_2024')
models_info={}
old=json.loads((R/'.local/pose-v1-inference/package-20261005/manifest.json').read_text())
for kind in ('ZG','adapted','optimized'):
    for ext in ('json','raw'):
        name='piw24_'+kind+'.'+ext;p=origin/name;h=sha(p)
        if kind!='adapted':assert next(x['sha256'] for x in old['files'] if x['relative_path']=='models/'+name)==h
        shutil.copyfile(p,models/name);models_info[name]={'sha256':h,'bytes':p.stat().st_size,'source':str(p)}
manifest={'sources':{p:sha(R/p) for p in files},'models':models_info,'program_sha256':sha(B/'pose_producer_raw_audit'),'XIR_library_sha256':sha(B/'libicraft_xir.so'),'Device_opened':False,'Session_created':False,'NPU_executed':False,'headers':{n:sha(B/n) for n in ('data.h','network.h','hard_op.h','data_type.h')}}
(B/'build-result.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
for p in (B/'pose_producer_raw_audit',B/'build-result.json',R/'tools/pose-v1/run-producer-raw.sh'):shutil.copyfile(p,bundle/p.name)
(bundle/'files.sha256').write_text(''.join(sha(p)+'  '+p.relative_to(bundle).as_posix()+'\n' for p in sorted(bundle.rglob('*')) if p.is_file()),encoding='utf-8',newline='\n')
with tarfile.open(E/'transfer.tar','w') as t:
    for p in sorted(bundle.rglob('*')):
        if p.is_file():t.add(p,arcname=p.relative_to(bundle).as_posix())
(E/'transfer.identity.json').write_text(json.dumps({'archive_sha256':sha(E/'transfer.tar'),'build':manifest},indent=2)+'\n',encoding='utf-8',newline='\n')
print('XIR-only RAW exporter built; no execution',manifest['program_sha256'])

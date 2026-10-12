"""Build only the XIR offline view inspector; no SDK device code or execution."""
from pathlib import Path
import subprocess,json,hashlib,shutil,tarfile
R=Path(__file__).resolve().parents[2];B=R/'.local/pose-v1-build/producer-view-20261011-r2';E=R/'tools/pose-v1/evidence/producer-contract-20261011-r2';assert not B.exists();B.mkdir();source=B/'source';source.mkdir()
D='C:/Program Files/Docker/Docker/resources/bin/docker.exe';remote='/tmp/pose-producer-view-build-20261011-r2';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=['software/pose_v1/src/producer_view_audit.cpp','software/pose_v1/include/mixed_fusion_baseline.hpp']
for p in files:shutil.copyfile(R/p,source/Path(p).name)
def run(args):
    p=subprocess.run([D,*args],capture_output=True)
    with (B/'build.log').open('ab') as f:f.write((repr(args)+'\n').encode()+p.stdout+p.stderr)
    assert p.returncode==0,(args,p.stderr[-2000:]);return p.stdout
run(['exec','FPAI','test','!','-e',remote]);run(['exec','FPAI','mkdir',remote]);run(['cp',str(source),'FPAI:'+remote+'/source'])
run(['exec','FPAI','aarch64-linux-gnu-g++','-std=gnu++17','-O2','-DNDEBUG','-Wall','-Wextra','-Wpedantic','-Werror','-I'+remote+'/source',remote+'/source/producer_view_audit.cpp','-licraft_xir','-licraft_utils','-o',remote+'/pose_producer_view_audit'])
run(['cp','FPAI:'+remote+'/pose_producer_view_audit',str(B/'pose_producer_view_audit')])
dynamic=run(['exec','FPAI','aarch64-linux-gnu-readelf','-d',remote+'/pose_producer_view_audit']).decode();assert not any(x in dynamic for x in ('libicraft_xrt','backend','axizg','liveMedia'));(B/'dynamic.txt').write_text(dynamic)
run(['cp','-L','FPAI:/usr/lib/aarch64-linux-gnu/libicraft_xir.so',str(B/'libicraft_xir.so')])
graph=R/'.local/pose-v1-axi-pair/package-20261011-r4/graph/piw24_ZG.json'
manifest={'sources':{p:sha(R/p) for p in files},'program_sha256':sha(B/'pose_producer_view_audit'),'graph_sha256':sha(graph),'XIR_library_sha256':sha(B/'libicraft_xir.so'),'no_XRT_dynamic_dependency':True,'no_backend_dynamic_dependency':True,'Device_open':False,'RAW_loaded':False,'Session_created':False}
(B/'build-result.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
bundle=E/'transfer';assert not bundle.exists();bundle.mkdir()
for p in (B/'pose_producer_view_audit',B/'build-result.json',graph,R/'tools/pose-v1/run-producer-view.sh'):shutil.copyfile(p,bundle/p.name)
(bundle/'files.sha256').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(bundle.iterdir())),encoding='utf-8',newline='\n')
with tarfile.open(E/'transfer.tar','w') as t:
    for p in sorted(bundle.iterdir()):t.add(p,arcname=p.name)
(E/'transfer.identity.json').write_text(json.dumps({'sha256':sha(E/'transfer.tar'),'build':manifest},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Offline inspector built',manifest['program_sha256'],'archive',sha(E/'transfer.tar'))


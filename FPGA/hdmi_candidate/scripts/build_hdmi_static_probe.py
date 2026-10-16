"""Build separate ARM static bring-up utility; preserve SDK and container state."""
from pathlib import Path
import subprocess,time,json,hashlib,shutil,sys
R=Path(__file__).resolve().parents[3]
revision=sys.argv[1] if len(sys.argv)>1 else 'r1';assert revision in ('r1','engine-ready-r2')
suffix='' if revision=='r1' else '-'+revision
E=R/('tools/pose-v1/evidence/hdmi-integration-20261016-r1/static-probe-build'+suffix);W=R/('.local/hdmi-integration-20261016-r1/static-probe'+suffix)
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
for name in ['CMakeLists.txt','static_probe.cpp']:shutil.copyfile(R/'FPGA/hdmi_candidate/software'/name,W/name)
remote='/tmp/hdmi-integration-20261016-r1-static-probe'+suffix;steps=[]
docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
def run(name,args,budget=90):
 t=time.monotonic();p=subprocess.run([docker,*args],capture_output=True,timeout=budget)
 (E/(name+'.stdout.txt')).write_bytes(p.stdout);(E/(name+'.stderr.txt')).write_bytes(p.stderr)
 steps.append({'name':name,'args':args,'exit':p.returncode,'seconds':time.monotonic()-t,'budget':budget})
 (E/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 if p.returncode:raise RuntimeError(name+' failed; stop')
 return p.stdout
state=run('01-container-state',['inspect','--format','{{.State.Status}}','FPAI']).strip()
if state!=b'exited':raise SystemExit('FPAI in use; do not interrupt another owner')
run('02-container-start',['start','FPAI']);owned=True
try:
 run('03-fresh-directory',['exec','FPAI','test','!','-e',remote])
 expected=json.loads((R/'tools/pose-v1/evidence/hdmi-register-probe-20261015-r3/expected.json').read_text())['libraries']
 text=run('04-sdk-identities',['exec','FPAI','sha256sum',*['/usr/lib/aarch64-linux-gnu/'+n for n in expected]]).decode()
 got={Path(line.split()[1]).name:line.split()[0] for line in text.splitlines()}
 assert got==expected,'Build SDK differs from board frozen SDK'
 run('05-copy-source',['cp',str(W),'FPAI:'+remote])
 run('06-configure',['exec','FPAI','cmake','-S',remote,'-B',remote+'/build','-DCMAKE_SYSTEM_NAME=Linux','-DCMAKE_SYSTEM_PROCESSOR=aarch64','-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++','-DCMAKE_PREFIX_PATH=/usr/cmake','-DCMAKE_BUILD_TYPE=Release'])
 run('07-build',['exec','FPAI','cmake','--build',remote+'/build','--parallel','2'])
 run('08-copy-binary',['cp','FPAI:'+remote+'/build/hdmi_static_probe',str(E/'hdmi_static_probe')])
 elf=run('09-readelf',['exec','FPAI','aarch64-linux-gnu-readelf','-h','-d',remote+'/build/hdmi_static_probe'])
 assert b'AArch64' in elf and b'libicraft_zg330backend.so' in elf
 (E/'result.json').write_text(json.dumps({'compiled':True,'board_executed':False,'binary_sha256':hashlib.sha256((E/'hdmi_static_probe').read_bytes()).hexdigest(),'SDK_libraries':got},indent=2)+'\n')
 print('ARM static probe compiled; board execution pending',flush=True)
finally:
 if owned:run('10-container-stop',['stop','FPAI'],30)

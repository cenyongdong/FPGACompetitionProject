"""Build a new bounded HDMI read probe with the existing locked ARM SDK."""
from pathlib import Path
import hashlib,json,shutil,subprocess,time,sys
R=Path(__file__).resolve().parents[2]
REV=sys.argv[1] if len(sys.argv)>1 else 'r1'
assert REV in ('r1','r2','r3')
E=R/('tools/pose-v1/evidence/hdmi-register-probe-20261015-'+REV)
S=R/('.local/hdmi-register-probe-20261015-'+REV)
D='/tmp/hdmi-register-probe-20261015-'+REV
steps=[]
def run(name,args,timeout=90):
    t=time.monotonic();p=subprocess.run(args,capture_output=True,timeout=timeout)
    (E/(name+'.stdout.txt')).write_bytes(p.stdout);(E/(name+'.stderr.txt')).write_bytes(p.stderr)
    steps.append({'name':name,'argv':args,'exit':p.returncode,'seconds':time.monotonic()-t,'timeout':timeout})
    (E/'build-steps.json').write_text(json.dumps(steps,indent=2)+'\n',encoding='utf-8')
    if p.returncode:raise RuntimeError(name+' failed; stop')
    return p.stdout
def main():
    E.mkdir(exist_ok=False);S.mkdir(exist_ok=False)
    for n in ('CMakeLists.txt','readonly_probe.cpp'):shutil.copyfile(Path(__file__).with_name(n),S/n)
    state=run('container-initial',['docker','inspect','--format','{{.State.Status}}','FPAI']).strip()
    if state!=b'exited':raise RuntimeError('Expected stopped FPAI; do not interrupt other work')
    run('container-start',['docker','start','FPAI'])
    try:
        sys.path.insert(0,str(R/'software/demo'))
        from build_support import Docker,auditSdk
        sdk_logs=E/'sdk-audit';sdk_logs.mkdir()
        libraries=auditSdk(json.loads((R/'software/demo/baseline-lock.json').read_text()),Docker(sdk_logs),E)
        run('fresh-directory',['docker','exec','FPAI','test','!','-e',D])
        run('copy',['docker','cp',str(S),'FPAI:'+D])
        run('configure',['docker','exec','FPAI','cmake','-S',D,'-B',D+'/build','-DCMAKE_SYSTEM_NAME=Linux','-DCMAKE_SYSTEM_PROCESSOR=aarch64','-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++','-DCMAKE_PREFIX_PATH=/usr/cmake','-DCMAKE_BUILD_TYPE=Release'])
        run('build',['docker','exec','FPAI','cmake','--build',D+'/build','--parallel','2'])
        run('return-binary',['docker','cp','FPAI:'+D+'/build/hdmi_readonly_probe',str(E/'hdmi_readonly_probe')])
        elf=run('readelf',['docker','exec','FPAI','aarch64-linux-gnu-readelf','-h','-d',D+'/build/hdmi_readonly_probe'])
        if b'libicraft_zg330backend.so' not in elf or b'AArch64' not in elf:
            raise RuntimeError('ARM architecture or backend registration dependency missing; do not deploy')
        result={'compiled':True,'board_executed':False,'libraries':libraries,'binary_sha256':hashlib.sha256((E/'hdmi_readonly_probe').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((S/'readonly_probe.cpp').read_bytes()).hexdigest()}
        (E/'build-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print('ARM probe compiled; not board executed',flush=True)
    finally:run('container-stop',['docker','stop','FPAI'],30)
if __name__=='__main__':main()

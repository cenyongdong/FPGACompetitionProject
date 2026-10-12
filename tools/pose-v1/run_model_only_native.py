"""Execute real SDK-free scheduling/ownership/persistence contracts in FPAI."""
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'tools/pose-v1/evidence/model-only-20261010-r1/native';remote='/tmp/pose-v1-mixed-20261010-model-only-r1';docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
assert not out.exists();out.mkdir(parents=True)
args=['g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic','-Werror','-pthread','-I'+remote+'/source',*[remote+'/source/'+p for p in ['model_only_selftest.cpp','model_only_run.cpp','invocation_evidence.cpp']],'-o',remote+'/build/model-only.native']
p=subprocess.run([docker,'exec','FPAI',*args],capture_output=True);(out/'build.stdout.log').write_bytes(p.stdout);(out/'build.stderr.log').write_bytes(p.stderr);assert p.returncode==0,p.stderr.decode(errors='replace')
p=subprocess.run([docker,'exec','FPAI',remote+'/build/model-only.native',remote+'/native-model-only-results'],capture_output=True);(out/'stdout.json').write_bytes(p.stdout);(out/'stderr.log').write_bytes(p.stderr);(out/'exit.txt').write_text(str(p.returncode)+'\n');assert p.returncode==0,p.stderr.decode(errors='replace')
for src,dest in [(remote+'/native-model-only-results',out/'results'),(remote+'/build/model-only.native',out/'model-only.native')]:
    p=subprocess.run([docker,'cp','FPAI:'+src,str(dest)],capture_output=True);assert p.returncode==0
print((out/'stdout.json').read_text())

"""Native lifecycle and original finite-window contracts, actual outputs only."""
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2];base=root/'tools/pose-v1/evidence/model-vpu-20261010-r2';remote='/tmp/pose-v1-mixed-20261010-model-vpu-r2';docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
for label,sources,arguments in [('load',['model_load_selftest.cpp','model_load_lifecycle.cpp'],[]),('run',['model_only_selftest.cpp','model_only_run.cpp','invocation_evidence.cpp'],[remote+'/native-run-results'])]:
    out=base/('native-'+label);assert not out.exists();out.mkdir(parents=True);binary=remote+'/build/'+label+'.native'
    p=subprocess.run([docker,'exec','FPAI','g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic','-Werror','-pthread','-I'+remote+'/source',*[remote+'/source/'+s for s in sources],'-o',binary],capture_output=True);(out/'build.stdout.log').write_bytes(p.stdout);(out/'build.stderr.log').write_bytes(p.stderr);assert p.returncode==0,p.stderr.decode(errors='replace')
    p=subprocess.run([docker,'exec','FPAI',binary,*arguments],capture_output=True);(out/'stdout.json').write_bytes(p.stdout);(out/'stderr.log').write_bytes(p.stderr);(out/'exit.txt').write_text(str(p.returncode)+'\n');assert p.returncode==0,p.stderr.decode(errors='replace')
    for src,dest in [(binary,out/(label+'.native'))]+([(arguments[0],out/'results')] if arguments else []):
        p=subprocess.run([docker,'cp','FPAI:'+src,str(dest)],capture_output=True);assert p.returncode==0
    print(label,(out/'stdout.json').read_text().strip())

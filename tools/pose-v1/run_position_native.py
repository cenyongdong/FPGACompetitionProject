"""Run SDK-free position and frozen byte contracts in native FPAI executables."""
import subprocess,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'tools/pose-v1/evidence/plddr-position-20261010-r1';remote='/tmp/pose-v1-mixed-20261010-plddr-position-r1'
docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
def execute(args):
    p=subprocess.run([docker,'exec','FPAI',*args],capture_output=True);assert p.returncode==0,p.stderr.decode(errors='replace');return p
for label,sources,args in [('position',['plddr_position_selftest.cpp','plddr_position_contract.cpp'],[]),('typed',['typed_scratch_selftest.cpp','typed_scratch_pattern.cpp','scratch_copy_pattern.cpp'],[remote+'/native-typed-results'])]:
    fresh=out/('native-'+label);assert not fresh.exists();fresh.mkdir();binary=remote+'/build/native-'+label
    p=execute(['g++','-std=c++17','-O2','-ffp-contract=off','-Wall','-Wextra','-Wpedantic','-Werror','-I'+remote+'/source',*[remote+'/source/'+s for s in sources],'-o',binary]);(fresh/'build.stdout.log').write_bytes(p.stdout);(fresh/'build.stderr.log').write_bytes(p.stderr)
    p=subprocess.run([docker,'exec','FPAI',binary,*args],capture_output=True);(fresh/'stdout.json').write_bytes(p.stdout);(fresh/'stderr.log').write_bytes(p.stderr);(fresh/'exit.txt').write_text(str(p.returncode)+'\n');assert p.returncode==0,p.stderr.decode(errors='replace')
    if args:
        p=subprocess.run([docker,'cp','FPAI:'+args[0],str(fresh/'results')],capture_output=True);assert p.returncode==0
    p=subprocess.run([docker,'cp','FPAI:'+binary,str(fresh/('native-'+label))],capture_output=True);assert p.returncode==0
    print(label,p.returncode,(fresh/'stdout.json').read_text().strip())

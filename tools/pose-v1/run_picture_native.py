"""Execute actual SDK-free lifecycle and bounds contracts in the existing FPAI."""
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2];base=root/'tools/pose-v1/evidence/picture-20261010-r1';remote='/tmp/pose-v1-mixed-20261010-picture-r1';docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
for label,sources,arg in [('source',['picture_source_selftest.cpp','picture_source.cpp','picture_marker.cpp'],None),('sequence',['picture_sequence_selftest.cpp','picture_sequence.cpp','model_load_lifecycle.cpp'],None),('producer',['resident_producer_count_selftest.cpp','resident_producer_count_observation.cpp'],'producer-tests'),('load',['model_load_selftest.cpp','model_load_lifecycle.cpp'],None),('run',['model_only_selftest.cpp','model_only_run.cpp','invocation_evidence.cpp'],'run-tests')]:
    out=base/('native-'+label);assert not out.exists();out.mkdir(parents=True);binary=remote+'/build/'+label+'.native'
    p=subprocess.run([docker,'exec','FPAI','g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic','-Werror','-pthread','-I'+remote+'/source',*[remote+'/source/'+s for s in sources],'-o',binary],capture_output=True);(out/'build.stdout.log').write_bytes(p.stdout);(out/'build.stderr.log').write_bytes(p.stderr);assert p.returncode==0,p.stderr.decode(errors='replace')
    args=[remote+'/native-'+arg] if arg else []
    p=subprocess.run([docker,'exec','FPAI',binary,*args],capture_output=True);(out/'stdout.json').write_bytes(p.stdout);(out/'stderr.log').write_bytes(p.stderr);(out/'exit.txt').write_text(str(p.returncode)+'\n',newline='\n');assert p.returncode==0,p.stderr.decode(errors='replace')
    for src,dest in [(binary,out/(label+'.native'))]+([(args[0],out/'tests')] if arg else []):
        p=subprocess.run([docker,'cp','FPAI:'+src,str(dest)],capture_output=True);assert p.returncode==0
    print(label,(out/'stdout.json').read_text().strip())

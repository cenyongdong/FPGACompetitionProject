"""Run the real frozen IPC/AU/TCP modules as Native contracts, no SDK/device."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[2];e=root/'tools/pose-v1/evidence/combined-read-20261010-r1';remote='/tmp/pose-v1-mixed-20261010-combined-read-r1';docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
tests=[('display-worker',['display_worker.cpp','display_protocol.cpp','skeleton_render.cpp'],None),('AU',['access_unit_selftest.cpp','h264_access_unit.cpp','access_unit_channel.cpp'],[]),('TCP',['tcp_transport_check.cpp','tcp_receiver.cpp'],['--self-test']),('IPC',['display_process_selftest.cpp','display_process.cpp','display_protocol.cpp','skeleton_render.cpp'],[remote+'/build/display-worker.native',remote+'/native-IPC-tests']),('bounded',['bounded_load_selftest.cpp','display_process.cpp','display_protocol.cpp','skeleton_render.cpp'],[remote+'/build/display-worker.native',remote+'/native-bounded-tests'])]
for label,sources,args in tests:
    out=e/('native-'+label);assert not out.exists();out.mkdir(parents=True);binary=remote+'/build/'+label+'.native'
    p=subprocess.run([docker,'exec','FPAI','g++','-std=c++17','-O2','-ffp-contract=off','-Wall','-Wextra','-Wpedantic','-Werror','-pthread','-I'+remote+'/source',*[remote+'/source/'+f for f in sources],'-o',binary],capture_output=True)
    (out/'build.stdout.log').write_bytes(p.stdout);(out/'build.stderr.log').write_bytes(p.stderr);assert p.returncode==0,p.stderr.decode(errors='replace')
    if args is not None:
        p=subprocess.run([docker,'exec','FPAI',binary,*args],capture_output=True,timeout=60);(out/'stdout.json').write_bytes(p.stdout);(out/'stderr.log').write_bytes(p.stderr);(out/'exit.txt').write_text(str(p.returncode)+'\n',newline='\n');assert p.returncode==0,p.stderr.decode(errors='replace');print(label,(out/'stdout.json').read_text().strip())
    p=subprocess.run([docker,'cp','FPAI:'+binary,str(out/(label+'.native'))],capture_output=True);assert p.returncode==0
    if label in ('IPC','bounded'):
        p=subprocess.run([docker,'cp','FPAI:'+args[-1],str(out/'tests')],capture_output=True);assert p.returncode==0

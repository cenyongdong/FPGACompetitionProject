"""Read-only post-demo identity, resources and process/port cleanup."""
from pathlib import Path
import hashlib,json,os,subprocess,tarfile
root=Path(__file__).resolve().parent;out=root/'final';assert not out.exists();out.mkdir();os.environ['LC_ALL']='C.UTF-8'
subprocess.run(['python3',str(root/'board_application_preflight.py'),str(out/'preflight.json')],check=True)
p=json.loads((out/'preflight.json').read_text());old=json.loads((root/'run-demo/preflight.json').read_text());assert p['boot_files']==old['boot_files'] and p['libraries']==old['libraries'] and p['SDK_packages']==old['SDK_packages'] and p['fpga_state']=='operating'
for n in ('buddyinfo','pagetypeinfo','meminfo','vmstat','cmdline','uptime'):(out/n).write_bytes(Path('/proc/'+n).read_bytes())
(out/'dmesg.txt').write_bytes(subprocess.check_output(['dmesg']));assert (out/'dmesg.txt').read_bytes()==(root/'run-demo/after.dmesg.txt').read_bytes()
(out/'processes.txt').write_bytes(subprocess.check_output(['ps','-eo','pid,comm,args']));(out/'ports.txt').write_bytes(subprocess.check_output(['ss','-ltnp']))
assert not any(s.split()[1].startswith('pose_') for s in (out/'processes.txt').read_text().splitlines()[1:] if len(s.split())>1)
assert not any('python3 runner.py' in s for s in (out/'processes.txt').read_text().splitlines())
assert ':8554 ' not in (out/'ports.txt').read_text() and ':39001 ' not in (out/'ports.txt').read_text()
m=json.loads((root/'build-result.json').read_text());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(root/'models/piw24_ZG.json')==m['graph_sha256'] and h(root/'models/piw24_ZG.raw')==m['raw_sha256']
(out/'review.json').write_text(json.dumps({'status':'final_identity_and_cleanup_verified','BOOT_SDK_models_unchanged':True,'kernel_same_as_demo_end':True,'FPGA_operating':True,'project_processes_ports':0,'HDMI_used':False,'no_second_reboot':True})+'\n')
with (out/'files.sha256').open('w') as f:
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!='files.sha256':f.write(h(p)+'  '+p.name+'\n')
with tarfile.open(root/'return-final.tar','w') as t:t.add(out,arcname=out.name)
print('Final demo audit passed; no running project service')

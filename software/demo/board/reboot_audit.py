"""Read-only evidence before/after explicitly authorized single reboot."""
from pathlib import Path
import json,os,subprocess,tarfile
root=Path(__file__).resolve().parent;stage=__import__('sys').argv[1];assert stage in ('before','after')
out=root/('reboot-'+stage);assert not out.exists();out.mkdir();os.environ['LC_ALL']='C.UTF-8'
subprocess.run(['python3',str(root/'board_application_preflight.py'),str(out/'preflight.json')],check=True)
processes=subprocess.check_output(['ps','-eo','pid,comm,args']);ports=subprocess.check_output(['ss','-ltnp'])
assert not any(line.split()[1].startswith('pose_') for line in processes.decode().splitlines()[1:] if len(line.split())>1)
assert not any('python3 runner.py' in line for line in processes.decode().splitlines())
assert ':8554 ' not in ports.decode() and ':39001 ' not in ports.decode()
(out/'processes.txt').write_bytes(processes);(out/'ports.txt').write_bytes(ports)
for name in ('buddyinfo','pagetypeinfo','meminfo','vmstat','cmdline','uptime'):(out/name).write_bytes(Path('/proc/'+name).read_bytes())
(out/'boot-id.txt').write_bytes(Path('/proc/sys/kernel/random/boot_id').read_bytes())
(out/'dmesg.txt').write_bytes(subprocess.check_output(['dmesg']))
if stage=='after':
    old=json.loads((root/'reboot-before/preflight.json').read_text());new=json.loads((out/'preflight.json').read_text())
    assert old['boot_files']==new['boot_files'] and old['libraries']==new['libraries'] and old['SDK_packages']==new['SDK_packages']
    assert new['fpga_state']=='operating' and (root/'reboot-before/boot-id.txt').read_bytes()!=(out/'boot-id.txt').read_bytes()
with tarfile.open(root/('return-reboot-'+stage+'.tar'),'w') as t:t.add(out,arcname=out.name)
print('Reboot',stage,'audit saved; no project process or listener')

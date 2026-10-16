"""Read only uEnv from the existing FAT16 parser; no mount/config/register write."""
from pathlib import Path
import json, shlex, subprocess, sys, time, shutil

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
W = R / '.local/hdmi-integration-20261016-r1'
O = E / 'startup-readonly'
O.mkdir(exist_ok=False)
original = (E / 'board-resume-readonly/board-readonly-code.py').read_text(encoding='utf-8')
code = original[:original.index('expected=')]
needle = "remaining=struct.unpack_from('<I',e,28)[0];cluster="
assert code.count(needle)==1
code = code.replace(needle, "if name!='UENV.TXT':continue\n            assert struct.unpack_from('<I',e,28)[0]<=65536,'uEnv unexpectedly large'\n            chunks=[]\n            " + needle)
assert code.count('h.update(block);remaining-=len(block);')==1
code = code.replace('h.update(block);remaining-=len(block);','h.update(block);chunks.append(block);remaining-=len(block);')
assert code.count('sha256=h.hexdigest()))')==1
code = code.replace('sha256=h.hexdigest()))', "sha256=h.hexdigest(),text=b''.join(chunks).decode('utf-8')))")
code += "\nfiles=fat_files()\nassert len(files)==1,'uEnv missing or duplicated'\nprint(json.dumps({'uEnv':files[0],'cmdline':pathlib.Path('/proc/cmdline').read_text(),'boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'scope':'Read-only FAT root/uEnv and proc; no mount/SDK/MMIO/configuration writes'},indent=2))\n"
(O / 'remote-code.py').write_text(code, encoding='utf-8')
t = time.monotonic()
p = subprocess.run([sys.executable, str(W / 'secure_transport.py'), 'ssh', 'python3 -c ' + shlex.quote(code),
                    '--timeout','30','--log',str(O / 'remote.txt')], capture_output=True, timeout=40)
(O / 'stdout.txt').write_bytes(p.stdout)
(O / 'stderr.txt').write_bytes(p.stderr)
(O / 'execution.json').write_text(json.dumps({'exit':p.returncode,'seconds':time.monotonic()-t,
    'transport_budget_seconds':30,'outer_budget_seconds':40,'configuration_writes':False},indent=2)+'\n')
shutil.copyfile(Path(__file__), O / Path(__file__).name)
assert p.returncode==0,'Read-only startup inspection failed; preserve and stop dependent startup work'
data = json.loads((O / 'remote.txt').read_text(encoding='utf-8'))
(O / 'review-input.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'uEnv_sha256':data['uEnv']['sha256'],'uEnv_bytes':data['uEnv']['size'],
    'boot_id':data['boot_id'],'boot_lines':[s for s in data['uEnv']['text'].splitlines()
       if s.startswith(('loadbit=','bootcmd=','uenvcmd=','boot_targets='))]},indent=2))

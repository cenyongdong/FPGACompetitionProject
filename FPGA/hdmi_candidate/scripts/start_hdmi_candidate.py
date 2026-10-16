"""One authorized candidate reboot, followed by a bounded SSH readiness watch."""
from pathlib import Path
import json
import shlex
import subprocess
import sys
import time
import datetime
import shutil

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-board-candidate-20261016-r1'
W = R / '.local/hdmi-board-candidate-20261016-r1'
C = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
D = E / 'candidate-startup'
D.mkdir(exist_ok=False)
assert json.loads((E / 'install/execution.json').read_text())['exit'] == 0
assert json.loads((E / 'uart-startup/ready.json').read_text(encoding='utf-8-sig'))['opened']
assert not (E / 'uart-startup/reader.json').exists(), 'UART no longer capturing'
state_path = E / 'continuation-state.json'
state = json.loads(state_path.read_text())
assert state['candidate_startup_reboots_used'] == 0
state.update(phase='Candidate reboot command reserved; startup watch active',
             candidate_startup_reboot_command_attempts=1, BOOT_changed=True,
             candidate_startup_reboots_used=1, runtime_candidate_loaded='not yet confirmed',
             updated_local=datetime.datetime.now().isoformat())
state_path.write_text(json.dumps(state, indent=2) + '\n')
definitions = (C / 'board-candidate-readonly/remote-code.py').read_text(encoding='utf-8').split('expected=', 1)[0]
code = definitions + r'''
import os
boot_id=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert boot_id=='8974fbf7-cbe9-4fc9-954d-4682c45b045f'
assert next(x for x in fat_files() if x['name']=='BOOT.BIN')['sha256']=='22035d99f2dacdcb1817a0c08ae8b04c3b024e51bf2f1b522f0fcb9baf252135'
assert not any(v.split()[0]=='/dev/mmcblk0p1' for v in pathlib.Path('/proc/mounts').read_text().splitlines())
owners=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:items=list((p/'fd').iterdir())
 except OSError:continue
 for item in items:
  try:target=os.readlink(item)
  except OSError:continue
  if target.startswith(('/dev/mem','/dev/udma','/dev/u-dma','/dev/video','/dev/fb','/dev/dri','/dev/xdma')):owners.append({'pid':p.name,'target':target})
assert not owners,repr(owners)
print(json.dumps({'preflight':'pass','boot_id':boot_id,'device_owners':owners,'boot_partition_unmounted':True,'one_candidate_reboot_command':True}),flush=True)
subprocess.run(['/usr/bin/sync'],check=True,timeout=10)
subprocess.run(['/usr/sbin/reboot'],check=True,timeout=10)
'''
(D / 'reboot-code.py').write_text(code, encoding='utf-8')
start = time.monotonic()
proc = subprocess.run([sys.executable, str(W / 'secure_transport.py'), 'ssh',
                       'python3 -c ' + shlex.quote(code), '--timeout', '25', '--log', str(D / 'reboot-ssh.txt')],
                      capture_output=True, timeout=35)
(D / 'reboot-stdout.txt').write_bytes(proc.stdout)
(D / 'reboot-stderr.txt').write_bytes(proc.stderr)
(D / 'reboot-execution.json').write_text(json.dumps({'exit': proc.returncode,
    'seconds': time.monotonic() - start, 'one_command_attempt_only': True,
    'disconnect_does_not_prove_reboot_completed': True}, indent=2) + '\n')
assert b'"preflight": "pass"' in proc.stdout, 'Reboot preflight not observed; preserve and stop'
attempts = []
deadline = time.monotonic() + 180
new = None
while time.monotonic() < deadline:
    index = len(attempts)
    command = "python3 -c " + shlex.quote("import pathlib,json;print(json.dumps({'boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'uptime':pathlib.Path('/proc/uptime').read_text().strip()}))")
    p = subprocess.run([sys.executable, str(W / 'secure_transport.py'), 'ssh', command,
                        '--timeout', '8', '--log', str(D / ('watch-' + str(index) + '.txt'))],
                       capture_output=True, timeout=15)
    (D / ('watch-' + str(index) + '-stdout.txt')).write_bytes(p.stdout)
    (D / ('watch-' + str(index) + '-stderr.txt')).write_bytes(p.stderr)
    item = {'index': index, 'exit': p.returncode, 'elapsed_since_reboot_command': time.monotonic() - start}
    if p.returncode == 0:
        data = json.loads((D / ('watch-' + str(index) + '.txt')).read_text(encoding='utf-8'))
        item.update(data)
        if data['boot_id'] != '8974fbf7-cbe9-4fc9-954d-4682c45b045f':
            new = data
    attempts.append(item)
    (D / 'watch.json').write_text(json.dumps(attempts, indent=2) + '\n')
    if new:
        break
    time.sleep(3)
result = {'new_boot_observed': new is not None, 'new_boot': new,
          'seconds_since_command': time.monotonic() - start, 'watch_budget_seconds': 180,
          'reboot_command_attempts': 1, 'candidate_ABI_not_yet_read': True}
(D / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
shutil.copyfile(Path(__file__), D / Path(__file__).name)
print(json.dumps(result, indent=2))
assert new, 'No new SSH boot within budget: preserve UART and stop; no automatic repeated reboot'
state.update(phase='New Linux boot observed; restore original BOOT file before SDK access',
             candidate_startup_reboot_confirmed=True, new_boot_id=new['boot_id'],
             runtime_candidate_loaded='not yet ABI confirmed', next='hdmi_candidate_board.py restore, then fresh readonly identity audit, then read-only probe',
             updated_local=datetime.datetime.now().isoformat())
state_path.write_text(json.dumps(state, indent=2) + '\n')

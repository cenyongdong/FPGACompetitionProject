"""One SSH connection, 60 seconds maximum; preserve raw output even on failure."""
from pathlib import Path
import hashlib
import json
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
revision = sys.argv[1] if len(sys.argv)>1 else 'r1'
assert revision in ('r1', 'r2')
namespace = 'hdmi-stage1-20261015-' + revision
E = ROOT / 'tools/pose-v1/evidence' / namespace
assert not (E/'execution.json').exists() and not (E/'probe.stdout.json').exists()
script = (E/'remote_probe.py').read_text(encoding='utf-8')
command = 'python3 -c ' + shlex.quote(script)
start = time.monotonic()
try:
    p = subprocess.run([sys.executable,str(ROOT/'.local'/namespace/'secure_transport.py'),'ssh',command,'--timeout','60','--log',str(E/'probe.stdout.json')],capture_output=True,timeout=70)
    (E/'transport.stdout.txt').write_bytes(p.stdout)
    (E/'transport.stderr.txt').write_bytes(p.stderr)
    result={'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-start,'timeout_seconds':60,'remote_working_directory':'login default; no remote files created','device_writes':False,'remote_probe_sha256':hashlib.sha256((E/'remote_probe.py').read_bytes()).hexdigest()}
except subprocess.TimeoutExpired as exc:
    (E/'transport.stdout.txt').write_bytes(exc.stdout or b'')
    (E/'transport.stderr.txt').write_bytes(exc.stderr or b'')
    result={'exit_code':None,'controller_timeout':True,'elapsed_seconds':time.monotonic()-start}
(E/'execution.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
if result.get('exit_code') != 0:
    raise SystemExit('Probe failed; preserve evidence and stop, no automatic retry')
r=json.loads((E/'probe.stdout.json').read_text(encoding='utf-8'))
old=json.loads((ROOT/'tools/pose-v1/evidence/video-sequence-20261007-r1/hdmi-audit/preflight.json').read_text(encoding='utf-8'))
boot=next(x for x in r['identity']['boot_files'] if x['name']=='BOOT.BIN')
expected=next(x for x in old['boot_files'] if x['name']=='BOOT.BIN')
review={'boot_identity_matches':boot==expected,'SDK_libraries_match':r['identity']['libraries']==old['libraries'],'packages':r['identity']['packages'],'fpga_state':r['fpga_state'],'drm_count':len(r['drm']),'framebuffers':r['framebuffer_devices'],'clock_summary_available':r['clock_summary'] is not None,'pixel_clock_measured':False,'PLL_lock_measured':False,'next_pattern_test_permitted':False,'reason':'No verified current-bitstream pixel-clock/PLL observation or hardware read completion / safe-stop contract'}
(E/'review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
print(json.dumps(review))
assert review['boot_identity_matches'] and review['SDK_libraries_match'], 'Identity changed; stop'

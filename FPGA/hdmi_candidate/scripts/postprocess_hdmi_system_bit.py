"""Explicit one-input Procise ICAP patch; verify changed configuration payload."""
from pathlib import Path
import sys, hashlib, json, shutil, subprocess, os, time

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
W = R / '.local/hdmi-integration-20261016-r1'
revision = sys.argv[1] if len(sys.argv)>1 else 'r5'
assert revision in ('r4','r5')
assert json.loads((E / ('system-bit-'+revision) / 'execution.json').read_text())['exit'] == 0
assert json.loads((E / ('system-route-'+revision) / 'review.json').read_text())['bit_generation_prerequisite_pass']
O = E / ('candidate-bit-'+revision)
P = W / ('candidate-bit-'+revision)
O.mkdir(exist_ok=False)
P.mkdir(exist_ok=False)
sys.path.insert(0, str(R / 'tools/pose-v1'))
from inspect_selected_boot import bit_payload

source = W / ('reference/fpai_demo_vivado.runs/impl_hdmi_'+revision+'/ai7030_edif_top.bit')
inp = P / ('hdmi-integrated-'+revision+'.bit')
out = P / ('hdmi-integrated-'+revision+'_disable_icap.bit')
shutil.copyfile(source, inp)
input_sha = hashlib.sha256(inp.read_bytes()).hexdigest()
assert input_sha == hashlib.sha256(source.read_bytes()).hexdigest()
code = r'''
if {[catch {
 set_device JFMQL30TAI676H
 increment_bit_cfg_v3 {INPUT} {OUTPUT} -disable_icap
 puts "HDMI_PROCISE_ICAP_RETURNED"
} result]} {puts "HDMI_ICAP_FAILED $result";exit 1}
exit
'''.replace('INPUT', inp.as_posix()).replace('OUTPUT', out.as_posix())
(P / 'patch.tcl').write_text(code, encoding='ascii')
shutil.copyfile(P / 'patch.tcl', O / 'patch.tcl')
root = Path('C:/FudanMicro/Procise')
env = os.environ.copy()
env.update(APP_DIR=str(root), ICTIME_HOME=str(root), FMSH_DB=str(root / 'db'), TCL_LIBRARY=str(root / 'tcl8.4'))
env['PATH'] = str(root / 'dll') + ';' + env['PATH']
start = time.monotonic()
timed = False
with (O / 'stdout.txt').open('wb') as stdout, (O / 'stderr.txt').open('wb') as stderr:
    proc = subprocess.Popen([str(root / 'bin/procise.exe'), 'patch.tcl'], cwd=P, env=env,
                            stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        proc.wait(timeout=180)
    except subprocess.TimeoutExpired:
        timed = True
        killed = subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True, timeout=20)
        (O / 'cleanup.txt').write_bytes(killed.stdout + killed.stderr)
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            pass
execution = {'exit': proc.poll(), 'seconds': time.monotonic() - start, 'budget_seconds':180,
             'timeout':timed, 'target':'JFMQL30TAI676H', 'input_sha256':input_sha, 'board_or_BOOT_operations':False}
(O / 'execution.json').write_text(json.dumps(execution, indent=2) + '\n')
assert proc.poll() == 0 and not timed and out.is_file(), execution
assert hashlib.sha256(inp.read_bytes()).hexdigest() == input_sha
baseline = R / 'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1/rollback/ai7030_top_disable_icap.bit'
assert hashlib.sha256(baseline.read_bytes()).hexdigest() == '6818b7f8dea8e0f9dbda1b0d11127255ee1ba8876326bc7708a633641784f72e'
payload, fields = bit_payload(out.read_bytes())
base_payload, _ = bit_payload(baseline.read_bytes())
assert 'Patched=DISABLE_ICAP' in fields['a']
different = payload != base_payload
assert different, 'Reference-identical payload is not the HDMI candidate'
products = {}
for p in [inp, out]:
    shutil.copyfile(p, O / p.name)
    data = p.read_bytes()
    config, header = bit_payload(data)
    products[p.name] = {'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest(),
                        'payload_bytes':len(config), 'payload_sha256':hashlib.sha256(config).hexdigest(), 'header':header}
review = {'Procise_execution':execution, 'products':products, 'payload_differs_from_original_BOOT':different,
          'baseline_payload_sha256':hashlib.sha256(base_payload).hexdigest(),
          'new_payload_sha256':hashlib.sha256(payload).hexdigest(),
          'not_downloaded_or_physical_display_verified':True}
(O / 'review.json').write_text(json.dumps(review, indent=2) + '\n')
shutil.copyfile(Path(__file__), O / Path(__file__).name)
print(json.dumps(review, indent=2))

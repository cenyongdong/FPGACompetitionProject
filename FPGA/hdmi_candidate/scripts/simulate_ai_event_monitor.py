"""Bounded RTL verification of the passive, independent diagnostic endpoint."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r1/sim-ai-monitor-r1'
W=R/'.local/hdmi-live-20261017-r1/sim-ai-monitor-r1'
E.mkdir();W.mkdir()
sources=[R/'.local/hdmi-integration-20261016-r1/reference/rtl/utils/mna_itf.sv',
         R/'FPGA/hdmi_candidate/diagnostics/ai_event_monitor.sv',
         R/'FPGA/hdmi_candidate/sim/tb_ai_event_monitor.sv']
for p in sources:shutil.copyfile(p,W/p.name)
(E/'sources.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2))
(W/'run.tcl').write_text('run all\nquit\n')
B=Path('D:/vivado18.3/Vivado/2018.3/bin');env=os.environ.copy();env['XILINX_VIVADO']=str(B.parent)
for key in list(env):
    if key.startswith('RDI_'):env.pop(key)
steps=[]
for label,args in [
    ('compile',[str(B/'xvlog.bat'),'--sv',*[p.name for p in sources]]),
    ('elaborate',[str(B/'xelab.bat'),'tb_ai_event_monitor','--timescale','1ns/1ps','--snapshot','tb_ai_event_monitor']),
    ('simulate',[str(B/'xsim.bat'),'tb_ai_event_monitor','--tclbatch','run.tcl'])]:
    start=time.monotonic();p=subprocess.run(args,cwd=W,env=env,capture_output=True,timeout=90)
    (E/(label+'.stdout.txt')).write_bytes(p.stdout);(E/(label+'.stderr.txt')).write_bytes(p.stderr)
    steps.append({'step':label,'exit':p.returncode,'seconds':time.monotonic()-start,'budget':90})
    (E/'execution.json').write_text(json.dumps(steps,indent=2))
    if p.returncode:raise SystemExit(label+' failed; preserve evidence')
assert b'AI_EVENT_MONITOR_PASS' in p.stdout and b'Fatal:' not in p.stdout
(E/'result.json').write_text(json.dumps({'passed':True,'board':False,'existing_HDMI_or_AI_data_path_changed':False}))
print(p.stdout.decode(errors='replace')[-1500:])

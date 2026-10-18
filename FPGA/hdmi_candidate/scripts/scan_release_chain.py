"""Bounded Procise read-only cable enumeration and chain scan, never program."""
from pathlib import Path
import json, os, subprocess, time, shutil, sys, re
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1/chain-scan'
if len(sys.argv)>1:
 assert sys.argv[1] in ('host-permission-r2','device-enumerated-r3','ai-monitor-v2')
 E=(R/'tools/pose-v1/evidence/hdmi-live-20261017-r2/chain-scan') if sys.argv[1]=='ai-monitor-v2' else E.parent/('chain-scan-'+sys.argv[1])
E.mkdir(exist_ok=False)
proc=Path('C:/FudanMicro/Procise')
code='''get_cable_info
if {[catch {init_chain -cable_type usb-jtag-hs1 -serial_number 210512180081} result]} {
 puts "CHAIN_SCAN_FAIL $result"
 exit 1
}
puts "CHAIN_SCAN_COMPLETED"
exit
'''
(E/'scan.tcl').write_text(code,encoding='ascii')
env=os.environ.copy();env.update(APP_DIR=str(proc),TCL_LIBRARY=str(proc/'tcl8.4'),ICTIME_HOME=str(proc),FMSH_DB=str(proc/'db'))
env['PATH']=str(proc/'dll')+';'+env['PATH']
t=time.monotonic()
with (E/'stdout.log').open('wb') as out,(E/'stderr.log').open('wb') as err:
 p=subprocess.Popen([str(proc/'bin/procise.exe'),'scan.tcl'],cwd=E,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:p.wait(timeout=45)
 except subprocess.TimeoutExpired:
  subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True);p.wait(timeout=10)
  (E/'timeout.json').write_text(json.dumps({'pid':p.pid,'budget':45,'seconds':time.monotonic()-t})+'\n')
  raise SystemExit('Scan timed out; preserve and stop')
log=(E/'stdout.log').read_text(errors='replace')
result={'exit':p.returncode,'seconds':time.monotonic()-t,'read_only_scan':True,'programmed':False,
 'scan_completed':'CHAIN_SCAN_COMPLETED' in log,'expected_cable_present':bool(re.search(r'serial number\s*:\s*210512180081',log)),
 'expected_FPGA_ID_present':'0x9372c093' in log,'expected_PS_DAP_ID_present':'0x6ba00477' in log,
 'note':'Read actual part index from full stdout before any subsequent programming'}
(E/'result.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copyfile(Path(__file__),E/Path(__file__).name)
print(json.dumps(result)); print(log[-5000:])
if p.returncode or not result['scan_completed']:raise SystemExit(1)

"""Read actual Procise command availability/help, never pass bitstream inputs."""
from pathlib import Path
import json,os,subprocess,time
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/procise-command-review';W=R/'.local/hdmi-jfm-route2-20261016-r1/procise-command-review';E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
tcl='''
puts "INCREMENT_COMMAND [info commands increment_bit_cfg_v3]"
puts "BOOT_COMMANDS [info commands *boot*]"
puts "IMAGE_COMMANDS [info commands *image*]"
if {[llength [info commands increment_bit_cfg_v3]]} {
 if {[catch {help increment_bit_cfg_v3} r]} {puts "HELP_EXCEPTION $r"} else {puts "HELP_RETURN $r"}
}
puts "COMMAND_REVIEW_COMPLETE_NO_BIT_INPUT"
exit
'''
(W/'query.tcl').write_text(tcl,encoding='ascii');(E/'query.tcl').write_text(tcl,encoding='ascii')
root='C:/FudanMicro/Procise';env=os.environ.copy();env.update(APP_DIR=root,ICTIME_HOME=root,FMSH_DB=root+'/db',TCL_LIBRARY=root+'/tcl8.4');env['PATH']=root+'/dll;'+env['PATH']
t=time.monotonic()
p=subprocess.run([root+'/bin/procise.exe','query.tcl'],cwd=W,env=env,capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
(E/'stdout.txt').write_bytes(p.stdout);(E/'stderr.txt').write_bytes(p.stderr)
result={'exit':p.returncode,'seconds':time.monotonic()-t,'budget_seconds':180,'bit_input_or_image_build':False}
(E/'execution.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));print(p.stdout.decode('utf-8',errors='replace')[-2500:])
if p.returncode:raise SystemExit('Command review failed; evidence preserved')

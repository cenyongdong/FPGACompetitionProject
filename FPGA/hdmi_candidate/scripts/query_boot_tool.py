"""Bounded local command introspection; no boot image creation or hardware access."""
from pathlib import Path
import os, subprocess, json,time,sys
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1/boot-tool-query'
if len(sys.argv)>1:
 assert sys.argv[1] in ('help','help-switch')
 E=E.parent/('boot-tool-'+sys.argv[1])
E.mkdir(exist_ok=False)
P=Path('C:/FudanMicro/Procise');env=os.environ.copy();env.update(APP_DIR=str(P),TCL_LIBRARY=str(P/'tcl8.4'),ICTIME_HOME=str(P),FMSH_DB=str(P/'db'));env['PATH']=str(P/'dll')+';'+env['PATH']
code='puts "BOOT_COMMANDS [info commands *boot*]"\nputs "IMAGE_COMMANDS [info commands *image*]"\nputs "BIF_COMMANDS [info commands *bif*]"\nputs "QUERY_COMPLETE"\nexit\n'
if len(sys.argv)>1:code='help create_boot_image\nhelp dump_boot_image\nputs "HELP_COMPLETE"\nexit\n'
if len(sys.argv)>1 and sys.argv[1]=='help-switch':code='catch {create_boot_image -help} m\nputs "CREATE_HELP_RESULT $m"\ncatch {dump_boot_image -help} m\nputs "DUMP_HELP_RESULT $m"\nputs "HELP_COMPLETE"\nexit\n'
(E/'query.tcl').write_text(code,encoding='ascii')
t=time.monotonic()
with (E/'stdout.log').open('wb') as out,(E/'stderr.log').open('wb') as err:
 p=subprocess.Popen([str(P/'bin/procise.exe'),'query.tcl'],cwd=E,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:p.wait(timeout=45)
 except subprocess.TimeoutExpired:
  subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True);p.wait(timeout=10);raise
(E/'exit.json').write_text(json.dumps({'exit':p.returncode,'seconds':time.monotonic()-t,'budget':45})+'\n')
print((E/'stdout.log').read_text(errors='replace')[-4000:])

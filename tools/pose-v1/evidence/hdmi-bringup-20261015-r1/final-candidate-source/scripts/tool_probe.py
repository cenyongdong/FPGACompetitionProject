from pathlib import Path
import json,os,subprocess,time,sys
R=Path(__file__).resolve().parents[3]
REV=sys.argv[1] if len(sys.argv)>1 else 'r1'
assert REV in ('r1','r2','r3','r4')
E=R/('tools/pose-v1/evidence/hdmi-procise-api-20261015-'+REV)
W=R/('.local/hdmi-procise-api-20261015-'+REV)
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
script='puts "PROC_API_BEGIN"\nputs "COMMANDS [info commands *run*]"\nforeach c {launch_run load_design} {\n if {[catch {help $c} r]} {puts "HELP_ERROR $c $r"} else {puts "HELP_RESULT $c $r"}\n if {[catch {$c -help} r]} {puts "OPTION_HELP $c $r"} else {puts "OPTION_RESULT $c $r"}\n}\nputs "PROC_API_END"\nexit\n'
if REV=='r3':
 script='puts "LIBRARY_QUERY_COMMANDS [info commands *lib*]"\nputs "PROPERTY_QUERY_COMMANDS [info commands *property*]"\nforeach c {get_lib_cells get_lib_pins read_lib list_library set_device} {if {[catch {help $c} r]} {puts "HELP_ERROR $c $r"} else {puts "HELP_RESULT $c $r"}}\nexit\n'
if REV=='r4':
 script='foreach c {export_sim_libs read_unimacro_lib compile_simlib_vlg} {if {[catch {$c -help} r]} {puts "HELP_ERROR $c $r"} else {puts "HELP_RESULT $c $r"}}\nexit\n'
(W/'query.tcl').write_text(script,encoding='ascii')
env=os.environ.copy();root='C:/FudanMicro/Procise'
env.update(APP_DIR=root,TCL_LIBRARY=root+'/tcl8.4',ICTIME_HOME=root,FMSH_DB=root+'/db')
env['PATH']=root+'/dll;'+env['PATH']
t=time.monotonic()
p=subprocess.run([root+'/bin/procise.exe','query.tcl'],cwd=W,env=env,capture_output=True,timeout=60)
(E/'stdout.txt').write_bytes(p.stdout);(E/'stderr.txt').write_bytes(p.stderr)
(E/'execution.json').write_text(json.dumps({'exit':p.returncode,'seconds':time.monotonic()-t,'timeout':60})+'\n')
print(p.stdout.decode(errors='replace')[-6500:]);print('exit',p.returncode)
if p.returncode:raise SystemExit('Procise query failed; stop')

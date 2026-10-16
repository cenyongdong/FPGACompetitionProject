"""Read procedure definitions through the installed Vivado Tcl source loader.
No invocation of replace/hook/upgrade procedures. Deny Tcl filesystem writes,
external commands, library loads and project/configuration mutation while loading.
"""
from pathlib import Path
import json,os,shutil,subprocess,time,hashlib,sys
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[3]
revision=sys.argv[1] if len(sys.argv)>1 else 'r1'
assert revision in ('r1','r2')
W=R/('.local/hdmi-jfm-pin-review-20261015-'+revision)
E=R/('tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-'+revision)
if revision!='r1':W.mkdir(exist_ok=False);E.mkdir(exist_ok=False)
kit=R/'Docs/26嵌赛开发/JFM_Kits/JFM_Kits/ip_patch'
source=kit/'all_src_files.tcl'
if revision=='r2':
 source=W/'kit/ip_patch/all_src_files.tcl';source.parent.mkdir(parents=True)
 shutil.copyfile(kit/'all_src_files.tcl',source)
 for name in ('ip_patch.cfg','ip_patch_version.log','run.tcl'):
  if (kit/name).exists():shutil.copyfile(kit/name,source.parent/name)
 assert hashlib.sha256(source.read_bytes()).hexdigest()==hashlib.sha256((kit/'all_src_files.tcl').read_bytes()).hexdigest()
def tp(p):return '{'+p.as_posix()+'}'
tcl='''
set audit_out OUTDIR
set audit_source SOURCEFILE
package require md5
# Create output channels before write guards; use only these channels below.
set audit_result [open [file join $audit_out procedure-inspection.txt] w]
set audit_body [open [file join $audit_out replace_7z030ai_file.body.tcl] w]
set audit_calls [open [file join $audit_out blocked-mutations.txt] w]
set audit_procs [open [file join $audit_out dependency-procedures.tcl] w]
rename open audit_original_open
proc open {path args} {
 set mode r
 if {[llength $args]>0} {set mode [lindex $args 0]}
 if {$mode!="r" && $mode!="rb"} {error "READ_ONLY_GUARD open $path $mode"}
 return [eval [linsert $args 0 audit_original_open $path]]
}
rename file audit_original_file
proc file {subcmd args} {
 if {[lsearch -exact {copy delete rename mkdir attributes mtime atime link} $subcmd]>=0} {
  error "READ_ONLY_GUARD file $subcmd $args"
 }
 return [eval [linsert $args 0 audit_original_file $subcmd]]
}
proc audit_deny {name args} {
 puts $::audit_calls [list $name $args]
 flush $::audit_calls
 error "READ_ONLY_GUARD command $name"
}
foreach name {exec load cd set_property set_param create_project open_project save_project save_project_as
 add_files read_ip upgrade_ip upgrade_bd_cells generate_target launch_runs launch_run synth_design
 write_edif write_bitstream write_checkpoint reset_project close_project} {
 if {[llength [info commands $name]]} {
  rename $name audit_original_$name
  interp alias {} $name {} audit_deny $name
 }
}
set status [catch {source $audit_source} result]
puts $audit_result "SOURCE_STATUS $status"
puts $audit_result "SOURCE_RESULT $result"
if {$status} {puts $audit_result "SOURCE_ERRORINFO $::errorInfo"}
puts $audit_result "REPLACE_COMMANDS [info commands *replace*]"
puts $audit_result "HOOK_COMMANDS [info commands *hook*]"
if {[llength [info procs replace_7z030ai_file]]==1} {
 puts $audit_body [info body replace_7z030ai_file]
 puts $audit_result "REPLACE_ARGUMENTS [info args replace_7z030ai_file]"
 puts $audit_result "REPLACE_BODY_READ 1"
} else {puts $audit_result "REPLACE_BODY_READ 0"}
foreach name [lsort [info procs]] {
 if {[regexp {replace|database|backup|unisim|030|fmsh|migrate|migration|get_vivado|check_version} $name]} {
  puts $audit_procs [list proc $name [info args $name] [info body $name]]
 }
}
close $audit_procs
close $audit_result
close $audit_body
close $audit_calls
puts "JFM_PROCEDURE_INSPECTION_FINISHED source_status=$status"
exit
'''.replace('OUTDIR',tp(E)).replace('SOURCEFILE',tp(source))
(W/'inspect.tcl').write_text(tcl,encoding='utf-8');shutil.copyfile(W/'inspect.tcl',E/'inspect.tcl')
env=os.environ.copy();env['PROCESSOR_ARCHITECTURE']='AMD64'
env['JFM_PATH']=source.parent.parent.as_posix()
args=['D:/Xilinx/Vivado/2019.1/bin/vivado.bat','-mode','batch','-nojournal','-log',str(E/'inspect-vivado.log'),'-source',str(W/'inspect.tcl')]
t=time.monotonic();timeout=False
with (E/'inspect.stdout.txt').open('wb') as out,(E/'inspect.stderr.txt').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=p.wait(timeout=60)
 except subprocess.TimeoutExpired:
  timeout=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  (E/'inspect.cleanup.txt').write_bytes(k.stdout+k.stderr);code=p.wait(timeout=15)
result={'exit':code,'seconds':time.monotonic()-t,'timeout':timeout,'budget':60,
 'replace_procedure_invoked':False,'all_src_source_sha256':hashlib.sha256((kit/'all_src_files.tcl').read_bytes()).hexdigest(),
 'filesystem_mutations_guarded':True,'board_operation':False}
(E/'inspect.execution.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
if (E/'procedure-inspection.txt').exists():print((E/'procedure-inspection.txt').read_text(errors='replace')[-3500:])
if code or timeout:raise SystemExit('Read-only procedure inspection failed; preserve and stop')

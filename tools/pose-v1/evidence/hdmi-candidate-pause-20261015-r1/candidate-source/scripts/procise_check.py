"""Native Procise front-end/synthesis only, no bitgen or device operations."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[3]
profile=sys.argv[1];revision=sys.argv[2] if len(sys.argv)>2 else 'r1'
assert profile in ('core','clock') and revision in ('r1','r2','r3')
tag='hdmi-candidate-procise-'+profile+'-20261015-'+revision
E=R/'tools/pose-v1/evidence'/tag;W=R/'.local'/tag
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
if profile=='core':
 names=['hdmi_axi_read.v','hdmi_command_mailbox.v','hdmi_scan_control.v','hdmi_candidate_core.v','hdmi_register_bank.v','hdmi_candidate_register_core.v'];top='hdmi_candidate_register_core'
else:names=['hdmi_clock_fmsh.v'];top='hdmi_clock_fmsh'
for n in names:shutil.copyfile(R/'FPGA/hdmi_candidate/rtl'/n,W/n)
script='''set root [pwd]
if {[catch {
 create_project -name PROJECT -device JFMQL30TAI676H
 add_design_file -file SOURCES
 set_top -top TOP
 save_project
 load_design -stage_elaborate -no_hier
 launch_run -stage synthesis
} r]} {puts "CANDIDATE_NATIVE_FAIL $r";exit 1}
puts "CANDIDATE_NATIVE_SYNTHESIS_RETURNED"
exit
'''.replace('PROJECT','candidate_'+profile).replace('SOURCES',' '.join(names)).replace('TOP',top)
(W/'build.tcl').write_text(script,encoding='ascii')
root='C:/FudanMicro/Procise';env=os.environ.copy()
env.update(APP_DIR=root,TCL_LIBRARY=root+'/tcl8.4',ICTIME_HOME=root,FMSH_DB=root+'/db')
env['PATH']=root+'/dll;'+env['PATH']
start=time.monotonic();timed_out=False
with (E/'stdout.txt').open('wb') as out,(E/'stderr.txt').open('wb') as err:
 p=subprocess.Popen([root+'/bin/procise.exe','build.tcl'],cwd=W,env=env,stdout=out,stderr=err,
                    creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  timed_out=True
  subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  code=p.wait(timeout=15)
result={'profile':profile,'exit':code,'timed_out':timed_out,'seconds':time.monotonic()-start,'budget':180,
 'device':'JFMQL30TAI676H','tool':'Procise2025.1.1temp/SVN32494','stage_requested':'synthesis',
 'implementation_timing_signoff':False,'bitgen':False,'download':False,
 'sources':{n:hashlib.sha256((W/n).read_bytes()).hexdigest() for n in names}}
(E/'execution.json').write_text(json.dumps(result,indent=2)+'\n')
shutil.copytree(W,E/'returned-project')
print(json.dumps(result),flush=True)
print((E/'stdout.txt').read_text(errors='replace')[-6500:])
if timed_out or code:raise SystemExit('Native check failed; preserve artifacts and stop')

"""Same-configuration MIG OOC prerequisite with bounded autonomous timeout review.
No top implementation, global IP replacement, DRC waiver, bit patch or download.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[3];B=R/'tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1';ROOT=R/'.local/hdmi-jfm-route2-20261016-r1';ref=ROOT/'reference'
E=B/'mig-ooc';W=ROOT/'mig-ooc';E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parameters(p):
 root=ET.parse(p).getroot();d={}
 for node in root.iter():
  if node.tag.split('}')[-1]=='configurableElementValue':
   name=next((v for k,v in node.attrib.items() if k.split('}')[-1]=='referenceId'),None)
   if name and not name.startswith(('RUNTIME_PARAM.','PROJECT_PARAM.')):d[name]=node.text
 return d
xci=ref/'rtl/ip/mig_7series_0/mig_7series_0.xci';before=parameters(xci);assert before
prjs={p.relative_to(ref).as_posix():sha(p) for p in xci.parent.glob('*.prj')}
dump(E/'configuration-before.json',{'XCI_parameters':before,'PRJ_SHA':prjs})
tcl='''
if {[catch {
 open_project {REF/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 set ip [get_ips mig_7series_0]
 if {[get_property IS_LOCKED $ip]} {error "MIG unexpectedly locked"}
 generate_target synthesis $ip
 create_ip_run $ip
 set run [get_runs mig_7series_0_synth_1]
 if {[get_property STEPS.SYNTH_DESIGN.TCL.PRE $run] ne ""} {error "Unexpected IP synthesis pre-hook; do not execute"}
 launch_runs $run -jobs 1
 wait_on_run $run
 puts "MIG_RUN_STATUS [get_property STATUS $run]"
 puts "MIG_RUN_PROGRESS [get_property PROGRESS $run]"
 if {![string match {*Complete*} [get_property STATUS $run]]} {error "MIG OOC synthesis did not complete"}
 set d [get_property DIRECTORY $run]
 set files [glob -nocomplain $d/*.dcp]
 if {[llength $files]!=1} {error "Expected one actual MIG OOC checkpoint"}
 set f [open {OUT/checkpoint-path.txt} w];puts $f [lindex $files 0];close $f
 close_project
 puts "MIG_SAME_CONFIGURATION_OOC_COMPLETE"
} result]} {puts "MIG_OOC_FAILED $result";exit 1}
exit
'''.replace('REF',ref.as_posix()).replace('OUT',E.as_posix())
(W/'build.tcl').write_text(tcl,encoding='utf-8');shutil.copyfile(W/'build.tcl',E/'build.tcl')
env=os.environ.copy();env['PROCESSOR_ARCHITECTURE']='AMD64';env['XILINX_VIVADO']='D:/vivado18.3/Vivado/2018.3';env['JFM_PATH']=str(ref)
args=['D:/vivado18.3/Vivado/2018.3/bin/vivado.bat','-mode','batch','-nojournal','-log',str(E/'vivado.log'),'-source',str(W/'build.tcl')]
start=time.monotonic();initial=180;deadline=initial;ceiling=540;last_size=0;decisions=[];timeout=False;code=None
with (E/'stdout.txt').open('wb') as out,(E/'stderr.txt').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 dump(E/'owned-process.json',{'pid':p.pid,'initial_budget_seconds':initial,'autonomous_max_seconds':ceiling,'reason':'Same configuration MIG OOC prerequisite; one EDA job, two tool threads'})
 while p.poll() is None:
  elapsed=time.monotonic()-start
  if elapsed>=deadline:
   logs=list((ref/'fpai_demo_vivado.runs/mig_7series_0_synth_1').glob('*.log'))
   size=sum(f.stat().st_size for f in logs);age=min((time.time()-f.stat().st_mtime for f in logs),default=999999)
   error=any('ERROR:' in f.read_text(encoding='utf-8',errors='replace')[-20000:] for f in logs)
   extend=elapsed<ceiling and size>last_size and age<180 and not error
   decision={'elapsed_seconds':elapsed,'previous_budget_seconds':deadline,'new_budget_seconds':min(deadline+180,ceiling) if extend else deadline,
    'log_bytes':size,'youngest_log_age_seconds':age,'error_seen':error,'action':'continue original process' if extend else 'stop and preserve',
    'basis':'Recent progress in owned MIG synthesis log, no error; bounded to one job' if extend else 'No qualifying progress or maximum reached'}
   decisions.append(decision);dump(E/'timeout-decisions.json',decisions);print(json.dumps(decision),flush=True)
   if extend:deadline=min(deadline+180,ceiling);last_size=size
   else:
    timeout=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
    (E/'cleanup.txt').write_bytes(k.stdout+k.stderr)
    try:code=p.wait(timeout=15)
    except subprocess.TimeoutExpired:pass
    break
  time.sleep(1)
 if code is None:code=p.poll()
result={'exit':code,'seconds':time.monotonic()-start,'initial_budget_seconds':initial,'actual_final_budget_seconds':deadline,'timeout':timeout,
 'autonomous_extensions':decisions,'top_implementation_or_hardware_pass':False}
dump(E/'execution.json',result);print(json.dumps(result),flush=True)
print((E/'stdout.txt').read_text(encoding='utf-8',errors='replace')[-1500:],flush=True)
if code or timeout:raise SystemExit('MIG stage stopped; inspect evidence under current policy')
assert parameters(xci)==before,'Unexpected MIG configuration change'
for n,h in prjs.items():assert sha(ref/n)==h,n
checkpoint=Path((E/'checkpoint-path.txt').read_text(encoding='utf-8').strip());assert checkpoint.is_file()
shutil.copyfile(checkpoint,E/checkpoint.name)
dump(E/'contract-review.json',{'same_non_runtime_XCI_parameters':True,'same_DDR_PRJ_bytes':True,'actual_checkpoint':checkpoint.name,'checkpoint_sha256':sha(checkpoint),
 'IP_revision_upgraded':False,'top_hooks_executed':False,'global_IP_libraries_modified':False})

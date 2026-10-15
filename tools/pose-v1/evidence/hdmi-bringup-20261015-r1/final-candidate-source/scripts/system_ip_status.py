"""Fresh isolated Vivado front-end status only; no upgrades, hooks or database changes."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[3];S=R/'Docs/26嵌赛开发/fpai_demo_fpga'
W=R/'.local/hdmi-system-20261015-r1';E=R/'tools/pose-v1/evidence/hdmi-system-20261015-r1'
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
ref=W/'reference';shutil.copytree(S,ref)
manifest={p.relative_to(S).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in S.rglob('*') if p.is_file()}
(E/'original-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
copy={p.relative_to(ref).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in ref.rglob('*') if p.is_file()}
assert copy==manifest,'Reference copy differs; stop'
repo=[]
for p in ref.rglob('component.xml'):
 repo.append({'path':str(p),'bytes':p.stat().st_size})
xpr=ET.parse(ref/'fpai_demo_vivado.xpr')
ip=[];bd=[]
for f in xpr.findall('.//FileSet[@Name="sources_1"]/File'):
 raw=f.attrib['Path'];p=Path(raw.replace('$PPRDIR',ref.as_posix()).replace('$PSRCDIR',(ref/'fpai_demo_vivado.srcs').as_posix()))
 if p.suffix=='.xci':ip.append(p)
 if p.suffix=='.bd':bd.append(p)
assert len(bd)==1
def tclpath(p):return '{'+p.as_posix()+'}'
tcl='''set out [file normalize OUTDIR]
if {[catch {
 create_project hdmi_ip_status PROJECTDIR -part xc7z030ffg676-2
 set_property ip_repo_paths [list REPO] [current_project]
 set_property ip_cache_permissions {} [current_project]
 update_ip_catalog
 foreach ip [list IPFILES] {read_ip $ip}
 add_files -norecurse BDFILE
 open_bd_design BDFILE
 report_ip_status -file [file join $out IP-status.rpt]
 foreach ip [get_ips -all] {
  puts "IP_STATUS|$ip|[get_property IPDEF $ip]|[get_property IS_LOCKED $ip]|[get_property IP_FILE $ip]"
 }
 puts "SYSTEM_IP_STATUS_COMPLETE"
 close_project
} result]} {puts "SYSTEM_IP_STATUS_FAIL $result";exit 1}
exit
'''.replace('OUTDIR',tclpath(E)).replace('PROJECTDIR',tclpath(W/'project')).replace('REPO',tclpath(ref/'PS_AI IP')).replace('IPFILES',' '.join(tclpath(p) for p in ip)).replace('BDFILE',tclpath(bd[0]))
(W/'query.tcl').write_text(tcl,encoding='ascii');shutil.copyfile(W/'query.tcl',E/'query.tcl')
(E/'scope.json').write_text(json.dumps({'user_authorized_isolated_IP_rebuild':True,'this_stage':'status query only',
 'copied_files':len(manifest),'reference_bytes':sum(p.stat().st_size for p in S.rglob('*') if p.is_file()),
 'top_XCI_files':len(ip),'BD_files':len(bd),'custom_components':repo,'no_global_database_changes':True,
 'no_IP_upgrade':True,'no_JFM_hook_execution':True,'no_board_or_BOOT_operations':True},indent=2)+'\n')
env=os.environ.copy();env['PROCESSOR_ARCHITECTURE']='AMD64'
args=['D:/Xilinx/Vivado/2019.1/bin/vivado.bat','-mode','batch','-nojournal','-log',str(E/'vivado.log'),'-source',str(W/'query.tcl')]
t=time.monotonic();timed_out=False
with (E/'stdout.txt').open('wb') as out,(E/'stderr.txt').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  timed_out=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  (E/'cleanup.txt').write_bytes(k.stdout+k.stderr);code=p.wait(timeout=15)
result={'exit':code,'timed_out':timed_out,'seconds':time.monotonic()-t,'budget':180,'IP_generation':False,'IP_upgrade':False}
(E/'execution.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
print((E/'stdout.txt').read_text(errors='replace')[-5500:])
if timed_out or code:raise SystemExit('Isolated IP status failed; preserve and stop without retry')

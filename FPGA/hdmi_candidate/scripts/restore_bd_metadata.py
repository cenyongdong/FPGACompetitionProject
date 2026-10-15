"""Fresh-copy restoration of original AXI capability annotations and stale clock links.
No source/IP revision upgrade and no synthesis/output target generation.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[3]
OLD=R/'.local/hdmi-bd-validation-20261015-r1/reference'
PRE=R/'tools/pose-v1/evidence/hdmi-ip-revision-20261015-r1'
W=R/'.local/hdmi-bd-metadata-20261015-r1';E=R/'tools/pose-v1/evidence/hdmi-bd-metadata-20261015-r1'
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False);ref=W/'reference';shutil.copytree(OLD,ref)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
save(E/'source-before.json',{p.relative_to(ref).as_posix():sha(p) for p in ref.rglob('*') if p.is_file()})
ips=[]
for f in ET.parse(ref/'fpai_demo_vivado.xpr').findall('.//FileSet[@Name="sources_1"]/File'):
 p=Path(f.attrib['Path'].replace('$PPRDIR',ref.as_posix()).replace('$PSRCDIR',(ref/'fpai_demo_vivado.srcs').as_posix()))
 if p.suffix=='.xci':ips.append(p)
bd=ref/'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd'
def tp(p):return '{'+p.as_posix()+'}'
helper=(PRE/'upgrade.tcl').read_text();helper=helper[helper.index('proc dump_ips'):helper.index('if {[catch')]
tcl='set out [file normalize '+tp(E)+']\n'+helper+'''
if {[catch {
 create_project hdmi_metadata PROJECTDIR -part xc7z030ffg676-2
 set_property ip_repo_paths [list REPO] [current_project]
 set_property ip_cache_permissions {} [current_project]
 update_ip_catalog
 foreach ip [list IPFILES] {read_ip $ip}
 add_files -norecurse BDFILE
 open_bd_design BDFILE
 set pin [get_bd_intf_pins /axi_interconnect_4/m00_couplers/m00_regslice/M_AXI]
 if {[llength $pin]!=1} {error "Expected exact M_AXI role missing"}
 report_property $pin
 puts "RESTORE_ORIGINAL_M_AXI_OUTSTANDING 2 2"
 set_property CONFIG.NUM_READ_OUTSTANDING 2 $pin
 set_property CONFIG.NUM_WRITE_OUTSTANDING 2 $pin
 set port [get_bd_ports gp_axi_aclk]
 set original [get_property CONFIG.ASSOCIATED_BUSIF $port]
 set kept {}
 foreach name [split $original :] {
  if {$name=="gp0_monitor" || $name=="gp1_monitor"} {
   if {[llength [get_bd_intf_ports -quiet $name]]!=0} {error "Monitor interface unexpectedly exists $name"}
  } else {lappend kept $name}
 }
 puts "CLOCK_ASSOCIATION_BEFORE $original"
 puts "CLOCK_ASSOCIATION_AFTER [join $kept :]"
 set_property CONFIG.ASSOCIATED_BUSIF [join $kept :] $port
 validate_bd_design
 dump_ips [file join $out config-restored.tsv]
 puts "RESTORED_M_AXI_READ [get_property CONFIG.NUM_READ_OUTSTANDING $pin]"
 puts "RESTORED_M_AXI_WRITE [get_property CONFIG.NUM_WRITE_OUTSTANDING $pin]"
 if {[get_property CONFIG.NUM_READ_OUTSTANDING $pin]!=2 || [get_property CONFIG.NUM_WRITE_OUTSTANDING $pin]!=2} {
  error "Tool did not retain original outstanding metadata"
 }
 save_bd_design
 file copy BDFILE [file join $out bd-restored.json]
 report_ip_status -file [file join $out IP-status.rpt]
 close_project
 puts "BD_METADATA_RESTORATION_COMPLETE_NO_GENERATION"
} result]} {puts "BD_METADATA_RESTORATION_FAIL $result";exit 1}
exit
'''.replace('PROJECTDIR',tp(W/'project')).replace('REPO',tp(ref/'PS_AI IP')).replace('IPFILES',' '.join(tp(p) for p in ips)).replace('BDFILE',tp(bd))
(W/'restore.tcl').write_text(tcl,encoding='ascii');shutil.copyfile(W/'restore.tcl',E/'restore.tcl')
save(E/'scope.json',{'restore_only':'original M_AXI outstanding=2; remove two associations to nonexistent monitor ports',
 'no_wire_or_address_edits':True,'no_board_activity':True,'no_target_generation':True,'budget':180})
env=os.environ.copy();env['PROCESSOR_ARCHITECTURE']='AMD64'
args=['D:/Xilinx/Vivado/2019.1/bin/vivado.bat','-mode','batch','-nojournal','-log',str(E/'vivado.log'),'-source',str(W/'restore.tcl')]
t=time.monotonic();timed_out=False
with (E/'stdout.txt').open('wb') as out,(E/'stderr.txt').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  timed_out=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  (E/'cleanup.txt').write_bytes(k.stdout+k.stderr);code=p.wait(timeout=15)
save(E/'execution.json',{'exit':code,'timed_out':timed_out,'seconds':time.monotonic()-t,'budget':180,'formal_generation':False})
print(json.dumps({'exit':code,'timed_out':timed_out,'seconds':time.monotonic()-t}),flush=True)
print((E/'stdout.txt').read_text(errors='replace')[-5500:])
if code or timed_out:raise SystemExit('Metadata restoration failed; preserve and stop without generation')

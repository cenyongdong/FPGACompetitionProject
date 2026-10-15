"""Approved revision whitelist in a fresh copy; capture exact CONFIG before/after.
No generation until the independent strict configuration gate has passed.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[3];S=R/'Docs/26嵌赛开发/fpai_demo_fpga'
W=R/'.local/hdmi-ip-revision-20261015-r1';E=R/'tools/pose-v1/evidence/hdmi-ip-revision-20261015-r1'
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False);ref=W/'reference';shutil.copytree(S,ref)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
manifest={p.relative_to(S).as_posix():sha(p) for p in S.rglob('*') if p.is_file()}
assert manifest=={p.relative_to(ref).as_posix():sha(p) for p in ref.rglob('*') if p.is_file()}
save(E/'original-manifest.json',manifest)
original_bd=ref/'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd'
xpr=ET.parse(ref/'fpai_demo_vivado.xpr');ips=[]
for f in xpr.findall('.//FileSet[@Name="sources_1"]/File'):
 raw=f.attrib['Path'];p=Path(raw.replace('$PPRDIR',ref.as_posix()).replace('$PSRCDIR',(ref/'fpai_demo_vivado.srcs').as_posix()))
 if p.suffix=='.xci':ips.append(p)
assert len(ips)==13
roots=['afifo_16i_64o_largebuf','afifo_24w_4096d','afifo_64i_16o_128','clk_wiz_0','cmos_clkgen_742_5',
 'fifo_1','mgtclk','mig_7series_0','mna_idfifo_w12','rindex_buf_2b_16w','sys_clk','windex_buf_2b_16w']
def tp(p):return '{'+p.as_posix()+'}'
script='''set out [file normalize OUTDIR]
proc dump_ips {dest} {
 set f [open $dest w]
 foreach ip [lsort [get_ips -all]] {
  foreach prop [concat {IPDEF IS_LOCKED} [lsort [list_property $ip CONFIG.*]]] {
   set val [get_property $prop $ip];binary scan [encoding convertto utf-8 $val] H* h
   puts $f "$ip\\t$prop\\t$h"
  }
 }
 close $f
}
if {[catch {
 create_project hdmi_revision PROJECTDIR -part xc7z030ffg676-2
 set_property ip_repo_paths [list REPO] [current_project]
 set_property ip_cache_permissions {} [current_project]
 update_ip_catalog
 foreach ip [list IPFILES] {read_ip $ip}
 add_files -norecurse BDFILE
 open_bd_design BDFILE
 dump_ips [file join $out config-before.tsv]
 save_bd_design
 file copy BDFILE [file join $out bd-before-tool.json]
 set whitelist [list ROOTS]
 foreach name $whitelist {
  set ip [get_ips $name]
  if {[llength $ip]!=1 || ![get_property IS_LOCKED $ip]} {error "Unexpected whitelist/lock $name"}
  puts "REVISION_UPGRADE_ROOT $name [get_property IPDEF $ip]"
  upgrade_ip $ip
 }
 set cells {}
 foreach cell [get_bd_cells -hier] {
  set v [get_property VLNV $cell]
  if {$v=="xilinx.com:ip:axi_interconnect:2.1" || $v=="xilinx.com:ip:xlconcat:2.1"} {lappend cells $cell}
 }
 if {[llength $cells]!=4} {error "Unexpected BD whitelist count $cells"}
 puts "REVISION_UPGRADE_BD $cells"
 upgrade_bd_cells $cells
 dump_ips [file join $out config-after.tsv]
 report_ip_status -file [file join $out IP-status-after.rpt]
 save_bd_design
 file copy BDFILE [file join $out bd-after-tool.json]
 close_project
 puts "REVISION_UPGRADE_COMPLETE_NO_GENERATION"
} result]} {puts "REVISION_UPGRADE_FAIL $result";exit 1}
exit
'''.replace('OUTDIR',tp(E)).replace('PROJECTDIR',tp(W/'project')).replace('REPO',tp(ref/'PS_AI IP')).replace('IPFILES',' '.join(tp(p) for p in ips)).replace('BDFILE',tp(original_bd)).replace('ROOTS',' '.join(roots))
(W/'upgrade.tcl').write_text(script,encoding='ascii');shutil.copyfile(W/'upgrade.tcl',E/'upgrade.tcl')
save(E/'authorization.json',{'user_approved_whitelist_revision_upgrade':True,'standalone_roots':roots,'BD_roots':4,
 'PS_custom_IP_upgrade':False,'AI_Mate_change':False,'global_database_change':False,'generation_before_gate':False,'budget':180})
env=os.environ.copy();env['PROCESSOR_ARCHITECTURE']='AMD64'
args=['D:/Xilinx/Vivado/2019.1/bin/vivado.bat','-mode','batch','-nojournal','-log',str(E/'vivado.log'),'-source',str(W/'upgrade.tcl')]
t=time.monotonic();timed_out=False
with (E/'stdout.txt').open('wb') as out,(E/'stderr.txt').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  timed_out=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  (E/'cleanup.txt').write_bytes(k.stdout+k.stderr);code=p.wait(timeout=15)
save(E/'execution.json',{'exit':code,'timed_out':timed_out,'seconds':time.monotonic()-t,'budget':180,'generation_executed':False})
print(json.dumps({'exit':code,'timed_out':timed_out,'seconds':time.monotonic()-t}),flush=True)
print((E/'stdout.txt').read_text(errors='replace')[-5000:])
if code or timed_out:raise SystemExit('Revision upgrade failed; preserve without retry or generation')
def snapshot(p):
 d={}
 for line in p.read_text(encoding='utf-8').splitlines():
  name,key,value=line.split('\t');d.setdefault(name,{})[key]=bytes.fromhex(value).decode('utf-8')
 return d
before=snapshot(E/'config-before.tsv');after=snapshot(E/'config-after.tsv');diff=[]
for name,properties in before.items():
 if name not in after:diff.append({'IP':name,'change':'instance removed/renamed'});continue
 for key,val in properties.items():
  if key.startswith('CONFIG.') and after[name].get(key)!=val:diff.append({'IP':name,'key':key,'before':val,'after':after[name].get(key)})
 if after[name].get('IPDEF')!=properties.get('IPDEF'):diff.append({'IP':name,'change':'IPDEF changed','before':properties.get('IPDEF'),'after':after[name].get('IPDEF')})
for name in after.keys()-before.keys():diff.append({'IP':name,'change':'new instance'})
unlocked=all(v.get('IS_LOCKED')=='0' for v in after.values())
ba=json.loads((E/'bd-before-tool.json').read_text())['design'];bb=json.loads((E/'bd-after-tool.json').read_text())['design']
bd_diff=[k for k in ('ports','interface_ports','nets','interface_nets','addressing') if ba.get(k)!=bb.get(k)]
protected=[p for p in ref.rglob('*') if p.is_file() and ('PS_AI IP' in p.parts or p.name=='AI_Mate.edif')]
protected_changed=[p.relative_to(ref).as_posix() for p in protected if p.relative_to(ref).as_posix() in manifest and sha(p)!=manifest[p.relative_to(ref).as_posix()]]
gate={'IP_count_before':len(before),'IP_count_after':len(after),'all_unlocked':unlocked,'CONFIG_or_identity_differences':diff,
 'BD_contract_differences':bd_diff,'protected_PS_or_AI_files_changed':protected_changed,
 'passed':not diff and not bd_diff and not protected_changed and unlocked,'generation_executed':False}
save(E/'strict-config-gate.json',gate)
save(E/'updated-source-manifest.json',{p.relative_to(ref).as_posix():sha(p) for p in ref.rglob('*') if p.is_file()})
print(json.dumps(gate,ensure_ascii=False),flush=True)
if not gate['passed']:raise SystemExit('Strict CONFIG gate rejected differences; stop before generation')

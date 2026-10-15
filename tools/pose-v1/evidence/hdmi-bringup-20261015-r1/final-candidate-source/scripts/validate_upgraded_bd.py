"""Independent fresh-copy diagnostic: propagate/validate BD, never generate targets.
The prior strict rejection is preserved. Compare derived child IP by BD role.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[3]
OLD=R/'.local/hdmi-ip-revision-20261015-r1/reference'
PRE=R/'tools/pose-v1/evidence/hdmi-ip-revision-20261015-r1'
W=R/'.local/hdmi-bd-validation-20261015-r1';E=R/'tools/pose-v1/evidence/hdmi-bd-validation-20261015-r1'
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False);ref=W/'reference';shutil.copytree(OLD,ref)
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
save(E/'copied-upgrade-manifest.json',{p.relative_to(ref).as_posix():sha(p) for p in ref.rglob('*') if p.is_file()})
ip=[]
for f in ET.parse(ref/'fpai_demo_vivado.xpr').findall('.//FileSet[@Name="sources_1"]/File'):
 p=Path(f.attrib['Path'].replace('$PPRDIR',ref.as_posix()).replace('$PSRCDIR',(ref/'fpai_demo_vivado.srcs').as_posix()))
 if p.suffix=='.xci':ip.append(p)
bd=ref/'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd'
def tp(p):return '{'+p.as_posix()+'}'
helper=(PRE/'upgrade.tcl').read_text();helper=helper[helper.index('proc dump_ips'):helper.index('if {[catch')]
tcl='set out [file normalize '+tp(E)+']\n'+helper+'''
if {[catch {
 create_project hdmi_bd_validation PROJECTDIR -part xc7z030ffg676-2
 set_property ip_repo_paths [list REPO] [current_project]
 set_property ip_cache_permissions {} [current_project]
 update_ip_catalog
 foreach ip [list IPFILES] {read_ip $ip}
 add_files -norecurse BDFILE
 open_bd_design BDFILE
 dump_ips [file join $out config-opened.tsv]
 puts "BD_VALIDATE_BEGIN_NO_GENERATION"
 validate_bd_design
 dump_ips [file join $out config-validated.tsv]
 save_bd_design
 file copy BDFILE [file join $out bd-validated.json]
 report_ip_status -file [file join $out IP-status.rpt]
 close_project
 puts "BD_VALIDATE_COMPLETE_NO_GENERATION"
} result]} {puts "BD_VALIDATE_FAIL $result";exit 1}
exit
'''.replace('PROJECTDIR',tp(W/'project')).replace('REPO',tp(ref/'PS_AI IP')).replace('IPFILES',' '.join(tp(p) for p in ip)).replace('BDFILE',tp(bd))
(W/'validate.tcl').write_text(tcl,encoding='ascii');shutil.copyfile(W/'validate.tcl',E/'validate.tcl')
save(E/'scope.json',{'purpose':'diagnose derived defaults and serialization after approved revision upgrade',
 'original_strict_gate_rejection_preserved':True,'fresh_project_and_copy':True,
 'generation_executed':False,'new_upgrade_executed':False,'board_activity':False,'budget':180})
env=os.environ.copy();env['PROCESSOR_ARCHITECTURE']='AMD64'
args=['D:/Xilinx/Vivado/2019.1/bin/vivado.bat','-mode','batch','-nojournal','-log',str(E/'vivado.log'),'-source',str(W/'validate.tcl')]
t=time.monotonic();timed_out=False
with (E/'stdout.txt').open('wb') as out,(E/'stderr.txt').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  timed_out=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  (E/'cleanup.txt').write_bytes(k.stdout+k.stderr);code=p.wait(timeout=15)
save(E/'execution.json',{'exit':code,'timed_out':timed_out,'seconds':time.monotonic()-t,'budget':180,'formal_generation':False})
print(json.dumps({'exit':code,'timed_out':timed_out,'seconds':time.monotonic()-t}),flush=True)
print((E/'stdout.txt').read_text(errors='replace')[-4500:])
if code or timed_out:raise SystemExit('BD validation failed; preserve and stop before generation')
def snapshot(p):
 d={}
 for line in p.read_text(encoding='utf-8').splitlines():
  n,k,v=line.split('\t');d.setdefault(n,{})[k]=bytes.fromhex(v).decode('utf-8')
 return d
before=snapshot(PRE/'config-before.tsv');after=snapshot(E/'config-validated.tsv')
a=json.loads((PRE/'bd-before-tool.json').read_text())['design'];b=json.loads((E/'bd-validated.json').read_text())['design']
def roles(d):
 out={}
 def walk(node,path):
  for name,cell in node.get('components',{}).items():
   role=path+'/'+name
   if 'xci_name' in cell:out[role]=cell['xci_name']
   walk(cell,role)
 walk(d,'');return out
ra,rb=roles(a),roles(b);mapping={};renames=[]
assert ra.keys()==rb.keys(),'BD component roles changed'
for role,name in ra.items():
 mapping[name]=rb[role]
 if name!=rb[role]:renames.append({'role':role,'before':name,'after':rb[role]})
diff=[]
for name,props in before.items():
 newname=mapping.get(name,name)
 if newname not in after:diff.append({'IP':name,'after_name':newname,'change':'missing after validation'});continue
 for k,v in props.items():
  if (k.startswith('CONFIG.') or k=='IPDEF') and after[newname].get(k)!=v:
   diff.append({'IP':name,'after_name':newname,'key':k,'before':v,'after':after[newname].get(k)})
def wiring(d):
 return {k:{n:sorted(v.get('ports',[])) for n,v in d.get(k,{}).items()} for k in ('nets','interface_nets')}
def portshape(d,k):return {n:{a:v for a,v in p.items() if a!='parameters'} for n,p in d[k].items()}
contract={'wire_membership_equal':wiring(a)==wiring(b),
 'port_declarations_equal':portshape(a,'ports')==portshape(b,'ports'),
 'interface_declarations_equal':portshape(a,'interface_ports')==portshape(b,'interface_ports'),
 'addressing_equal':a.get('addressing')==b.get('addressing')}
unlocked=all(p.get('IS_LOCKED')=='0' for p in after.values())
gate={'derived_role_renames':renames,'CONFIG_differences':diff,'BD_contract':contract,'all_unlocked':unlocked,
 'passed':not diff and all(contract.values()) and unlocked,'formal_generation':False,'prior_rejection_preserved':True}
save(E/'post-validation-config-gate.json',gate);print(json.dumps(gate,ensure_ascii=False),flush=True)
if not gate['passed']:raise SystemExit('Post-validation configuration gate still rejected; no generation')

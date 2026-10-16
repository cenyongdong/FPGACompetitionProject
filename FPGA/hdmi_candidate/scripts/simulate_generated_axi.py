"""Use unmodified generated AXI3 interconnect and vendor simulation models.
One transaction outstanding; 2 sources x 32 IDs x full 16-beat read/write bursts.
"""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[3]
factory2018=len(sys.argv)>1 and sys.argv[1]=='--factory2018'
if factory2018:
    S=R/'.local/hdmi-jfm-build-20261016-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai'
    E=R/'tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/generated-axi2018'
    W=R/'.local/hdmi-jfm-build-20261016-r1/generated-axi2018'
    V=Path('D:/vivado18.3/Vivado/2018.3/bin')
    assert json.loads((E.parent/'generated-contract-reviewed.json').read_text())['gate_pass']
else:
    S=R/'.local/hdmi-ip-generation-20261015-r3/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai'
    revision=sys.argv[1] if len(sys.argv)>1 else 'r1'
    assert revision in ('r1','r2','r3')
    E=R/('tools/pose-v1/evidence/hdmi-generated-axi-20261015-'+revision)
    W=R/('.local/hdmi-generated-axi-20261015-'+revision)
    V=Path('D:/Xilinx/Vivado/2019.1/bin')
    assert json.loads((R/'tools/pose-v1/evidence/hdmi-ip-generation-20261015-r3/post-generation-contract.json').read_text())['parameter_and_port_gate_passed']
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
bd=(S/'synth/ps_ai.v').read_text()
match=re.search(r'\bmodule ps_ai_axi_interconnect_3_0\b(.*?)endmodule',bd,re.S)
assert match
ports=re.findall(r'^\s*(input|output)\s*(?:wire\s*)?(\[[^\]]+\])?\s*(\w+)\s*;',match.group(),re.M)
assert len(ports)>100
special={name for direction,_,name in ports if name.endswith(('ACLK','ARESETN'))}
special.update(('S00_AXI_rready','S01_AXI_rready','S00_AXI_bready','S01_AXI_bready',
                'M00_AXI_arready','M00_AXI_awready','M00_AXI_wready','M00_AXI_rvalid',
                'M00_AXI_rid','M00_AXI_rdata','M00_AXI_rresp','M00_AXI_rlast',
                'M00_AXI_bvalid','M00_AXI_bid','M00_AXI_bresp'))
tb=(R/'FPGA/hdmi_candidate/sim/tb_generated_axi3.sv').read_text()
tb=tb.replace('// GENERATED_DECLARATIONS','\n'.join(
    ('wire' if direction=='output' or name in special and name not in ('M00_AXI_rvalid','M00_AXI_rid','M00_AXI_rdata','M00_AXI_rresp','M00_AXI_rlast','M00_AXI_bvalid','M00_AXI_bid','M00_AXI_bresp') else 'reg')+
    ' '+width+' '+name+';' for direction,width,name in ports))
tb=tb.replace('// GENERATED_CONNECTIONS','ps_ai_axi_interconnect_3_0 dut(\n'+',\n'.join('.'+name+'('+name+')' for _,_,name in ports)+'\n);')
tb=tb.replace('// GENERATED_CLOCK_RESET','\n'.join('assign '+name+' = '+('clk' if name.endswith('ACLK') else 'rstn')+';' for name in sorted(special) if name.endswith(('ACLK','ARESETN'))))
tb=tb.replace('// GENERATED_INPUT_INITIALIZATION','\n'.join(name+"='0;" for direction,_,name in ports if direction=='input' and name not in special))
(W/'tb.sv').write_text(tb,encoding='ascii')
files=[]
for stem in ('axi_infrastructure_v1_1_vl_rfs','generic_baseblocks_v2_1_vl_rfs','axi_crossbar_v2_1_vl_rfs','axi_register_slice_v2_1_vl_rfs','axi_data_fifo_v2_1_vl_rfs'):
    found=list((S/'ipshared').rglob(stem+'.v'));assert len(found)==1
    files+=found
if factory2018:
    modules=dict(re.findall(r'\bmodule\s+(\w+)\b(.*?)\bendmodule\b',bd,re.S))
    pending=['ps_ai_axi_interconnect_3_0'];seen=set();leaves=set()
    while pending:
        name=pending.pop()
        if name in seen:continue
        seen.add(name)
        for dep in set(re.findall(r'\b\w+\b',modules[name])):
            if dep in modules and dep not in seen:pending.append(dep)
            elif dep.startswith('ps_ai_') and (S/'ip'/dep/'synth'/(dep+'.v')).is_file():leaves.add(dep)
    assert len(leaves)==4,leaves
    dependencies=sorted(leaves)
    (E/'roles.json').write_text(json.dumps({'reachable_modules':sorted(seen),'actual_generated_wrappers':dependencies},indent=2)+'\n')
else:dependencies=('ps_ai_xbar_7','ps_ai_s00_regslice_7','ps_ai_s01_regslice_0','ps_ai_m00_regslice_0')
for name in dependencies:
    files.append(S/'ip'/name/'synth'/(name+'.v'))
files.append(S/'synth/ps_ai.v')
manifest={}
for p in (S/'ipshared').rglob('*.vh'):
    if (W/p.name).exists():assert (W/p.name).read_bytes()==p.read_bytes()
    shutil.copyfile(p,W/p.name)
    manifest[p.name]={'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for p in files:
    shutil.copyfile(p,W/p.name)
    manifest[p.name]={'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(E/'sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
(E/'scope.json').write_text(json.dumps({'budget_per_stage':90,'outstanding_global':1,'actual_generated_model':True,'physical_board':False,'candidate_STOP_integrated':False},indent=2)+'\n')
(W/'run.tcl').write_text('run all\nquit\n')
steps=[]
for stage,args in (
 ('compile',[str(V/'xvlog.bat'),*[p.name for p in files]]),
 ('compile_tb',[str(V/'xvlog.bat'),'--sv','tb.sv']),
 ('elaborate',[str(V/'xelab.bat'),'tb_generated_axi3','--timescale','1ns/1ps','-L','unisims_ver','-L','secureip','--snapshot','generated_axi']),
 ('simulate',[str(V/'xsim.bat'),'generated_axi','--tclbatch','run.tcl'])):
    start=time.monotonic();timeout=False
    p=subprocess.Popen(args,cwd=W,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    try:out,err=p.communicate(timeout=90)
    except subprocess.TimeoutExpired:
        timeout=True
        k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
        (E/(stage+'.cleanup.txt')).write_bytes(k.stdout+k.stderr)
        out,err=p.communicate(timeout=15)
    (E/(stage+'.stdout.txt')).write_bytes(out);(E/(stage+'.stderr.txt')).write_bytes(err)
    steps.append({'stage':stage,'exit':p.returncode,'seconds':time.monotonic()-start,'budget':90,'timeout':timeout})
    (E/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
    print(stage,json.dumps(steps[-1]),flush=True)
    if p.returncode or timeout:
        shutil.copytree(W,E/'simulation-copy',ignore=shutil.ignore_patterns('xsim.dir','*.wdb','*.pb'))
        print(out.decode(errors='replace')[-4000:])
        raise SystemExit('Contract simulation stage failed; preserve and stop')
out=(E/'simulate.stdout.txt').read_text(errors='replace')
passed='GENERATED_AXI3_CONTRACT_PASS' in out and 'Fatal:' not in out
(E/'result.json').write_text(json.dumps({'passed':passed,'read_bursts':64 if passed else None,'write_bursts':64 if passed else None,'real_board':False,'full_system':False},indent=2)+'\n')
shutil.copytree(W,E/'simulation-copy',ignore=shutil.ignore_patterns('xsim.dir','*.wdb','*.pb'))
print(out[-2500:],flush=True)
if not passed:raise SystemExit('Generated AXI test failed; preserve and stop')

"""Bounded read-stream verification of the actual 2018.3 generated HP2 fabric.

No FPGA implementation, board access or installation changes. Fresh evidence only.
"""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,time,os,sys

R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r3/generated-axi-stream-r1'
W=R/'.local/hdmi-live-20261017-r3/generated-axi-stream-r1'
S=R/'.local/hdmi-live-20261017-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai'
BASE=R/'.local/hdmi-jfm-build-20261016-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai'
V=Path('D:/vivado18.3/Vivado/2018.3/bin')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')

def run(stage,args,steps):
    begin=time.monotonic();timed_out=False
    with (E/(stage+'.stdout.txt')).open('wb') as out,(E/(stage+'.stderr.txt')).open('wb') as err:
        p=subprocess.Popen(args,cwd=W,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        try:p.wait(timeout=90)
        except subprocess.TimeoutExpired:
            timed_out=True
            cleanup=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
            (E/(stage+'.cleanup.txt')).write_bytes(cleanup.stdout+cleanup.stderr)
            try:p.wait(timeout=15)
            except subprocess.TimeoutExpired:pass
    row={'stage':stage,'pid':p.pid,'exit':p.poll(),'seconds':time.monotonic()-begin,'budget_seconds':90,'timeout':timed_out,'args':args}
    steps.append(row);dump(E/'execution.json',steps);print(json.dumps(row),flush=True)
    if p.poll()!=0 or timed_out:raise RuntimeError('Stage failed/stopped; dependent verification stopped')

def main():
    assert not E.exists() and not W.exists(),'Fresh stage required'
    assert json.loads((E.parent/'resume-evidence-identity.json').read_text())['passed']
    assert json.loads((E.parent/'toolchain-identity.json').read_text())['passed']
    tb_path=R/'FPGA/hdmi_candidate/sim/tb_generated_axi3_stream.sv'
    assert tb_path.is_file(),'Independent stream testbench must exist before execution'
    E.mkdir();W.mkdir()
    dump(E/'scope.json',{'platform':'Windows Vivado XSim2018.3','source':str(S),'working_directory':str(W),'board':False,
        'budget_each_stage_seconds':90,'FPGA_implementation':False,'source_mutations':False,
        'pass':'All actual upstream/downstream AR/R handshakes scoreboards, coverage and finite watchdog pass',
        'stop':'Nonzero tool exit, timeout, protocol/data/scoreboard failure or identity mismatch; no automatic failed load retry'})
    bd=(S/'synth/ps_ai.v').read_text();match=re.search(r'\bmodule ps_ai_axi_interconnect_3_0\b(.*?)endmodule',bd,re.S);assert match
    ports=re.findall(r'^\s*(input|output)\s*(?:wire\s*)?(\[[^\]]+\])?\s*(\w+)\s*;',match.group(),re.M);assert len(ports)>100
    modules=dict(re.findall(r'\bmodule\s+(\w+)\b(.*?)\bendmodule\b',bd,re.S));pending=['ps_ai_axi_interconnect_3_0'];seen=set();leaves=set()
    while pending:
        name=pending.pop()
        if name in seen:continue
        seen.add(name)
        for dep in set(re.findall(r'\b\w+\b',modules[name])):
            if dep in modules and dep not in seen:pending.append(dep)
            elif dep.startswith('ps_ai_') and (S/'ip'/dep/'synth'/(dep+'.v')).is_file():leaves.add(dep)
    assert leaves=={'ps_ai_xbar_4','ps_ai_s00_regslice_1','ps_ai_s01_regslice_0','ps_ai_m00_regslice_0'},leaves
    wrapper=(S/'ip/ps_ai_xbar_4/synth/ps_ai_xbar_4.v').read_text()
    expected={'C_NUM_SLAVE_SLOTS':2,'C_NUM_MASTER_SLOTS':1,'C_AXI_ID_WIDTH':6,'C_AXI_ADDR_WIDTH':32,
        'C_AXI_DATA_WIDTH':64,'C_AXI_PROTOCOL':1,'C_M_AXI_BASE_ADDR':0,'C_M_AXI_ADDR_WIDTH':30,
        'C_S_AXI_BASE_ID':32<<32,'C_S_AXI_THREAD_ID_WIDTH':(5<<32)|5,'C_S_AXI_SINGLE_THREAD':0,
        'C_S_AXI_READ_ACCEPTANCE':(8<<32)|8,'C_M_AXI_READ_ISSUING':8}
    actual={}
    for key,value in expected.items():
        matches=re.findall(r'\.'+key+r'\(([^)]+)\)',wrapper);assert len(matches)==1,key
        token=matches[0].strip();parts=re.fullmatch(r"\d+'[hH]([0-9a-fA-F]+)",token)
        actual[key]=int(parts[1],16) if parts else int(token)
        assert actual[key]==value,(key,actual[key],value)
    dump(E/'generated-parameter-contract.json',{'expected':expected,'actual':actual,'passed':True})
    files=[]
    for stem in ('axi_infrastructure_v1_1_vl_rfs','generic_baseblocks_v2_1_vl_rfs','axi_crossbar_v2_1_vl_rfs','axi_register_slice_v2_1_vl_rfs','axi_data_fifo_v2_1_vl_rfs'):
        found=list((S/'ipshared').rglob(stem+'.v'));assert len(found)==1;files.extend(found)
    files.extend(S/'ip'/name/'synth'/(name+'.v') for name in sorted(leaves));files.append(S/'synth/ps_ai.v')
    inputs=files+list((S/'ipshared').rglob('*.vh'))+list((S/'ip/ps_ai_xbar_4').glob('*.xci'))
    manifest=[]
    for p in inputs:
        relative=p.relative_to(S);reference=BASE/relative
        assert reference.is_file() and sha(reference)==sha(p),f'Generated dependency changed: {relative}'
        manifest.append({'path':str(p),'relative_to_bd':relative.as_posix(),'sha256':sha(p),'reference_equal':True})
        if p.suffix in ('.v','.vh'):
            dst=W/p.name
            if dst.exists():assert sha(dst)==sha(p)
            else:shutil.copyfile(p,dst)
        else:shutil.copyfile(p,E/p.name)
    dump(E/'sources.json',manifest)
    tb=tb_path.read_text();shutil.copyfile(tb_path,E/'source-testbench.sv')
    clock_reset={name for _,_,name in ports if name.endswith(('ACLK','ARESETN'))}
    continuously_driven={'S00_AXI_rready','S01_AXI_rready','S00_AXI_bready','S01_AXI_bready',
        'M00_AXI_arready','M00_AXI_awready','M00_AXI_wready'}
    # Outputs are DUT-owned. READY inputs are continuously assigned by the TB;
    # all other payload/VALID inputs are driven procedurally.
    for marker in ('// GENERATED_DECLARATIONS','// GENERATED_CONNECTIONS','// GENERATED_CLOCK_RESET','// GENERATED_INPUT_INITIALIZATION'):assert tb.count(marker)==1,marker
    tb=tb.replace('// GENERATED_DECLARATIONS','\n'.join(('wire' if direction=='output' or name in clock_reset|continuously_driven else 'reg')+' '+width+' '+name+';' for direction,width,name in ports))
    tb=tb.replace('// GENERATED_CONNECTIONS','ps_ai_axi_interconnect_3_0 dut(\n'+',\n'.join('.'+name+'('+name+')' for _,_,name in ports)+'\n);')
    tb=tb.replace('// GENERATED_CLOCK_RESET','\n'.join('assign '+name+' = '+('clk' if name.endswith('ACLK') else 'rstn')+';' for name in sorted(clock_reset)))
    tb=tb.replace('// GENERATED_INPUT_INITIALIZATION','\n'.join(name+"='0;" for direction,_,name in ports if direction=='input' and name not in clock_reset|continuously_driven))
    (W/'tb.sv').write_text(tb,encoding='ascii');shutil.copyfile(W/'tb.sv',E/'expanded-testbench.sv')
    (W/'run.tcl').write_text('run all\nquit\n')
    dump(E/'dependency-roles.json',{'reachable_modules':sorted(seen),'wrappers':sorted(leaves),'ports':ports})
    steps=[]
    try:
        for stage,args in (
            ('compile',[str(V/'xvlog.bat'),*[p.name for p in files]]),
            ('compile-tb',[str(V/'xvlog.bat'),'--sv','tb.sv']),
            ('elaborate',[str(V/'xelab.bat'),'tb_generated_axi3_stream','--timescale','1ns/1ps','-L','unisims_ver','-L','secureip','--snapshot','generated_axi_stream']),
            ('simulate',[str(V/'xsim.bat'),'generated_axi_stream','--tclbatch','run.tcl'])):run(stage,args,steps)
        output=(E/'simulate.stdout.txt').read_text(errors='replace')
        passed='GENERATED_AXI3_STREAM_PASS' in output and 'Fatal:' not in output
        dump(E/'result.json',{'passed':passed,'board':False,'full_system':False,'actual_generated_model':True})
        if not passed:raise RuntimeError('Simulation did not meet explicit pass marker')
    finally:
        for p in W.iterdir():
            if p.is_file() and p.suffix in ('.csv','.txt','.log','.jou','.tcl'):shutil.copyfile(p,E/p.name)
    print((E/'simulate.stdout.txt').read_text(errors='replace')[-2200:],flush=True)

if __name__=='__main__':main()

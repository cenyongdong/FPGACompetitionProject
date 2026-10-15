"""Bounded original-RTL behavior tests and local bit identity comparison.

No FPGA synthesis/implementation, IP regeneration, bit download, SDK or board use.
XSim is a behavioral simulator only; this is not Procise or silicon signoff.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess,time,sys,re,difflib

R=Path(__file__).resolve().parents[2]
REV=sys.argv[1] if len(sys.argv)>1 else 'r1'
assert REV in ('r1','r2','r3','r4','r5','r6')
E=R/('tools/pose-v1/evidence/hdmi-contract-sim-20261015-'+REV)
W=R/('.local/hdmi-contract-sim-20261015-'+REV)
V=Path('D:/Xilinx/Vivado/2019.1/bin')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
    (E/'before').mkdir()
    for n in ('ARCHITECTURE-DISCUSSION-20261015.md','Done.md','DIFFICULTIES.md','PROJECT-PROGRESS.md','REFERENCES.md'):
        shutil.copyfile(R/n,E/'before'/n)
    original=R/'Docs/26嵌赛开发/fpai_demo_fpga/rtl/display'
    sources={}
    for n in ('color_bar.v','video_define.v','frame_fifo_read.v','video_rect_read_data.v','timing_gen_xy.v','aq_axi_master.v'):
        shutil.copyfile(original/n,W/n)
        sources[n]={'path':str(original/n),'sha256':sha(original/n)}
        if n=='aq_axi_master.v':
            # XSim rejects the reference's duplicated ANSI-port wire declarations.
            # Remove only those declarations from the simulation copy; keep all
            # expressions, state machines and original project source untouched.
            before=(W/n).read_text(encoding='utf-8')
            pattern=r'(?m)^[ \t]*\(\* keep = "true" \*\)wire M_AXI_(?:AWREADY|WREADY|ARREADY|AWVALID|WVALID|ARVALID|BVALID|BREADY|RREADY|RVALID);[ \t]*\n'
            after,count=re.subn(pattern,'',before)
            assert count==10,'Unexpected reference syntax; stop'
            (W/n).write_text(after,encoding='utf-8',newline='\n')
            sources[n]['simulation_copy_sha256']=sha(W/n)
            sources[n]['syntax_only_adapter_removed_duplicate_port_wires']=count
            (E/'aq-simulation-only-syntax.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='original',tofile='simulation-copy')),encoding='utf-8')
    shutil.copyfile(Path(__file__).with_name('tb_hdmi_contract.sv'),W/'tb_hdmi_contract.sv')
    sources['tb_hdmi_contract.sv']={'path':str(Path(__file__).with_name('tb_hdmi_contract.sv')),'sha256':sha(W/'tb_hdmi_contract.sv')}
    shutil.copyfile(Path(__file__).with_name('tb_axi_read_backpressure.sv'),W/'tb_axi_read_backpressure.sv')
    sources['tb_axi_read_backpressure.sv']={'path':str(Path(__file__).with_name('tb_axi_read_backpressure.sv')),'sha256':sha(W/'tb_axi_read_backpressure.sv')}
    (E/'source-manifest.json').write_text(json.dumps(sources,indent=2)+'\n',encoding='utf-8')
    # Existing project BIT files versus exact user-selected download artifact.
    selected=Path('D:/Dowload from Chrome/嵌赛资料/Icraft/参考实现/位流/悟净LITE版_BOOT_25122301_单路PLIN+pHDMI(外置detpost)/悟净LITE版_BOOT_25122301_单路PLIN+pHDMI(外置detpost)')
    items=[]
    for p in sorted((R/'Docs/26嵌赛开发/BIT').rglob('*')):
        if p.is_file():
            base=selected/p.name
            items.append({'path':str(p),'sha256':sha(p),'matches_selected_same_name':base.is_file() and sha(p)==sha(base)})
    (E/'bit-comparison.json').write_text(json.dumps(items,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (W/'run.tcl').write_text('run all\nquit\n',encoding='ascii')
    steps=[]
    try:
        for name,args in (
            ('compile-rtl',[str(V/'xvlog.bat'),'color_bar.v','frame_fifo_read.v','video_rect_read_data.v','timing_gen_xy.v','aq_axi_master.v']),
            ('compile-testbench',[str(V/'xvlog.bat'),'--sv','tb_axi_read_backpressure.sv','tb_hdmi_contract.sv']),
            ('elaborate',[str(V/'xelab.bat'),'tb_hdmi_contract','--timescale','1ns/1ps','--debug','typical','--snapshot','hdmi_contract']),
            ('simulate',[str(V/'xsim.bat'),'hdmi_contract','--tclbatch','run.tcl'])):
            started=time.monotonic()
            p=subprocess.run(args,cwd=W,capture_output=True,timeout=120)
            (E/(name+'.stdout.txt')).write_bytes(p.stdout)
            (E/(name+'.stderr.txt')).write_bytes(p.stderr)
            steps.append({'stage':name,'argv':args,'exit':p.returncode,'seconds':time.monotonic()-started,'timeout_seconds':120})
            (E/'execution.json').write_text(json.dumps(steps,indent=2)+'\n',encoding='utf-8')
            if p.returncode:raise RuntimeError(name+' failed; stop without automatic retry')
            print(name,'exit',p.returncode,flush=True)
        output=(E/'simulate.stdout.txt').read_text(errors='replace')
        assert 'HDMI_CONTRACT_TEST_PASS' in output and 'AXI_EXISTING_BUG_REPRODUCED' in output and 'Fatal:' not in output
        for n in ('control.vcd','xvlog.log','xelab.log','xsim.log'):
            if (W/n).is_file():shutil.copyfile(W/n,E/n)
        result={'behavioral_checks_passed':True,'original_project_RTL_modified':False,
            'simulation_copy_syntax_adapter':'aq_axi_master only: removed ten duplicate ANSI-port wire declarations; no logic changes',
            'checks':['full 1080p frame read completes at zero occupancy','consumer stop can stall with no frame completion','resuming consumption permits completion','VS gate creates new request','200MHz versus nominal pixel frame cadence'],
            'original_AXI_backpressure_bug_reproduced':True,'DUT_accepted_as_correct':False,
            'silicon_test':False,'Procise_signoff':False,'BOOT_changed':False}
        (E/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(output[-1800:])
    finally:
        for p in W.glob('*.log'):
            if not (E/p.name).exists():shutil.copyfile(p,E/p.name)
if __name__=='__main__':main()

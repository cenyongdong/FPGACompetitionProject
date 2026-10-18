"""Check the unchanged 256B default and new 512B decode on the isolated RTL."""
from pathlib import Path
import hashlib,json,shutil,subprocess,time
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r3/sim-read-router-r2'
W=R/'.local/hdmi-live-20261017-r3/sim-read-router-r2'
V=Path('D:/vivado18.3/Vivado/2018.3/bin')
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not E.exists() and not W.exists()
    assert json.loads((E.parent/'read-candidate-preparation/review.json').read_text())['passed']
    E.mkdir();W.mkdir();shutil.copyfile(Path(__file__),E/'actual-driver.py')
    sources=[R/'.local/hdmi-live-20261017-r3/reference/rtl/utils/mna_itf.sv',
        R/'.local/hdmi-live-20261017-r3/reference/rtl/hdmi_candidate/hdmi_cam_router.sv',
        R/'FPGA/hdmi_candidate/sim/tb_hdmi_integration.sv']
    dump(E/'scope.json',{'platform':'Windows XSim2018.3','working_directory':str(W),'board':False,'each_stage_budget_seconds':90,
        'pass':'Both default256B and explicit512B decode pass read/write and response/endpoint backpressure checks',
        'stop':'Tool/scoreboard/watchdog/identity failure, no automatic failed load retry'})
    dump(E/'sources.json',[{'path':str(p),'sha256':sha(p)} for p in sources])
    for p in sources[:2]:shutil.copyfile(p,W/p.name);shutil.copyfile(p,E/p.name)
    baseline=sources[2].read_text().split('module tb_hdmi_board_phy;')[0]
    assert baseline.count('module tb_hdmi_router;')==1 and baseline.rstrip().endswith('endmodule')
    wide=baseline.replace('tb_hdmi_router','tb_ai_read_router').replace('hdmi_cam_router dut(',
        "hdmi_cam_router #(.HDMI_BASE(32'h400b0400),.DECODE_LSB(9)) dut(")
    begin=wide.index("  read_one(32'h40080000,0);")
    end=wide.index('  $display("HDMI_ROUTER_PASS',begin)
    cases="""  read_one(32'h400b0000,0);read_one(32'h400b0100,0);
  read_one(32'h400b03fc,0);read_one(32'h400b0400,1);
  read_one(32'h400b04fc,1);read_one(32'h400b0500,1);
  read_one(32'h400b05dc,1);read_one(32'h400b05fc,1);
  read_one(32'h400b0600,0);read_one(32'h410b0400,0);
  write_one(32'h400b03fc,0);write_one(32'h400b0400,1);
  write_one(32'h400b0500,1);write_one(32'h400b05dc,1);
  write_one(32'h400b05fc,1);write_one(32'h400b0600,0);
"""
    wide=wide[:begin]+cases+wide[end:]
    wide=wide.replace('HDMI_ROUTER_PASS reads=6 writes=4','AI_READ_ROUTER_PASS reads=10 writes=6')
    (W/'tb.sv').write_text(baseline+'\n'+wide,encoding='ascii');shutil.copyfile(W/'tb.sv',E/'expanded-testbench.sv')
    (W/'run.tcl').write_text('run all\nquit\n',encoding='ascii')
    steps=[]
    def run(name,args):
        started=time.monotonic();timeout=False
        with (E/(name+'.stdout.txt')).open('wb') as out,(E/(name+'.stderr.txt')).open('wb') as err:
            p=subprocess.Popen(args,cwd=W,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            try:p.wait(timeout=90)
            except subprocess.TimeoutExpired:
                timeout=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
                (E/(name+'.cleanup.txt')).write_bytes(k.stdout+k.stderr)
                try:p.wait(timeout=15)
                except subprocess.TimeoutExpired:pass
        row={'stage':name,'exit':p.poll(),'seconds':time.monotonic()-started,'timeout':timeout,'budget_seconds':90}
        steps.append(row);dump(E/'execution.json',steps);print(json.dumps(row),flush=True)
        assert p.poll()==0 and not timeout,'Dependent verification stopped'
    try:
        run('compile',[str(V/'xvlog.bat'),'--sv','mna_itf.sv','hdmi_cam_router.sv','tb.sv'])
        for top,marker in [('tb_hdmi_router','HDMI_ROUTER_PASS'),('tb_ai_read_router','AI_READ_ROUTER_PASS')]:
            run(top+'-elaborate',[str(V/'xelab.bat'),top,'--timescale','1ns/1ps','--mt','2','--snapshot',top])
            run(top+'-simulate',[str(V/'xsim.bat'),top,'--tclbatch','run.tcl'])
            output=(E/(top+'-simulate.stdout.txt')).read_text(errors='replace')
            assert marker in output and 'Fatal:' not in output
        dump(E/'result.json',{'passed':True,'default256B':True,'explicit512B':True,'HDL_route_only':True,'board':False})
    except BaseException as ex:
        dump(E/'failure.json',{'type':type(ex).__name__,'message':str(ex)});raise
    finally:
        for p in W.iterdir():
            if p.is_file() and p.suffix in ('.log','.jou','.tcl','.txt'):shutil.copyfile(p,E/p.name)
if __name__=='__main__':main()

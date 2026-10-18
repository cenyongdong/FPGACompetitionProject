"""Bounded standalone simulation of the passive read observer; no board access."""
from pathlib import Path
import hashlib,json,shutil,subprocess,time

R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r3/sim-ai-read-monitor-r1'
W=R/'.local/hdmi-live-20261017-r3/sim-ai-read-monitor-r1'
V=Path('D:/vivado18.3/Vivado/2018.3/bin')

def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not E.exists() and not W.exists(),'Fresh evidence and workspace required'
    assert json.loads((E.parent/'toolchain-identity.json').read_text())['passed']
    sources=[R/'.local/hdmi-live-20261017-r3/reference/rtl/utils/mna_itf.sv',
             R/'FPGA/hdmi_candidate/diagnostics/ai_read_monitor.sv',
             R/'FPGA/hdmi_candidate/sim/tb_ai_read_monitor.sv']
    assert all(p.is_file() for p in sources)
    E.mkdir();W.mkdir()
    dump(E/'scope.json',{'platform':'Windows XSim 2018.3','work':str(W),'board_access':False,
        'stage_budget_seconds':90,'pass':'Explicit positive and expected stopped-clock markers, no fatal errors',
        'stop':'Tool failure, watchdog failure, timeout or missing coverage; preserve evidence before diagnosis'})
    dump(E/'sources.json',[{'path':str(p),'sha256':sha(p)} for p in sources])
    for p in sources:shutil.copyfile(p,W/p.name);shutil.copyfile(p,E/p.name)
    (W/'run.tcl').write_text('run all\nquit\n',encoding='ascii')
    stages=[('compile',[str(V/'xvlog.bat'),'--sv',*[p.name for p in sources]]),
            ('elaborate',[str(V/'xelab.bat'),'tb_ai_read_monitor','--timescale','1ns/1ps','--snapshot','ai_read_monitor_unit']),
            ('simulate',[str(V/'xsim.bat'),'ai_read_monitor_unit','--tclbatch','run.tcl'])]
    results=[]
    try:
        for name,args in stages:
            begin=time.monotonic();timeout=False
            with (E/(name+'.stdout.txt')).open('wb') as out,(E/(name+'.stderr.txt')).open('wb') as err:
                p=subprocess.Popen(args,cwd=W,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
                dump(E/'owned-process.json',{'pid':p.pid,'stage':name,'args':args,'budget_seconds':90})
                try:p.wait(timeout=90)
                except subprocess.TimeoutExpired:
                    timeout=True
                    k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
                    (E/(name+'.cleanup.txt')).write_bytes(k.stdout+k.stderr)
                    try:p.wait(timeout=15)
                    except subprocess.TimeoutExpired:pass
            row={'stage':name,'exit':p.poll(),'seconds':time.monotonic()-begin,'timeout':timeout,'budget_seconds':90}
            results.append(row);dump(E/'execution.json',results);print(json.dumps(row),flush=True)
            assert p.poll()==0 and not timeout,'Stage failed; dependent operations stopped'
        output=(E/'simulate.stdout.txt').read_text(errors='replace')
        passed=all(m in output for m in ('AI_READ_MONITOR_PASS','AI_READ_MONITOR_EXPECTED_TIMEOUT')) and 'Fatal:' not in output
        dump(E/'result.json',{'passed':passed,'standalone_observer_only':True,'board':False,'whole_system':False})
        assert passed,'Explicit simulation pass markers required'
        print(output[-2600:],flush=True)
    except BaseException as ex:
        dump(E/'failure.json',{'type':type(ex).__name__,'message':str(ex),'dependent_operations_stopped':True})
        raise
    finally:
        for p in W.iterdir():
            if p.is_file() and p.suffix in ('.log','.jou','.tcl','.csv','.txt'):shutil.copyfile(p,E/p.name)

if __name__=='__main__':main()

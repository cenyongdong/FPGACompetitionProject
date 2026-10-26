"""Local RTL simulation and OOC resource measurement; never installs a bitstream."""
from pathlib import Path
import argparse, json, random, subprocess, sys, time

ROOT=Path(__file__).resolve().parents[2]
SRC=Path(__file__).resolve().parent
V=Path('D:/vivado18.3/Vivado/2018.3/bin')

def vectors(dst):
    rng=random.Random(2901)
    arrays=[[-65535,65535,0,-3,12,32768,-32768,100],
            [rng.randrange(-65535,65536) for _ in range(129)],
            [-65535]*2048,
            [round(48000*__import__('math').sin(i*.151)+10000*__import__('math').sin(i*.093)) for i in range(1500)]]
    lags=[7,64,1,501];configs=[]
    for c,(x,last) in enumerate(zip(arrays,lags)):
        configs.extend([len(x),last])
        (dst/f'input{c}.hex').write_text(''.join(f'{v&0xffffffff:08x}\n' for v in x))
        sums=[sum(x[i]*x[i-k] for i in range(k,len(x))) for k in range(last+1)]
        (dst/f'expected{c}.hex').write_text(''.join(f'{v&((1<<48)-1):012x}\n' for v in sums))
    (dst/'cases.hex').write_text(''.join(f'{v:08x}\n' for v in configs))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['simulate','bridge','synthesize'])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    results=[]
    def run(name,cmd):
        started=time.time()
        with (out/(name+'.log')).open('w') as log:
            process=subprocess.Popen(list(map(str,cmd)),cwd=out,stdout=log,stderr=subprocess.STDOUT)
            (out/'process.json').write_text(json.dumps(dict(pid=process.pid,started=started,command=list(map(str,cmd)),automatic_kill=False)))
            code=process.wait()
        results.append(dict(stage=name,exit=code,seconds=time.time()-started))
        (out/'results.json').write_text(json.dumps(results,indent=2))
        print(name,code,str(out),flush=True)
        if code:raise SystemExit(code)
    if args.mode in ('simulate','bridge'):
        vectors(out);(out/'run.tcl').write_text('run all\nquit\n')
        sources=[SRC/'rtl/vitals_acf_csr.sv',SRC/'sim/tb_vitals_acf.sv'];top='tb_vitals_acf';marker='VITALS_ACF_PASS'
        if args.mode=='bridge':
            baseline=ROOT/'.local/hdmi-boot-witness-20261019-r23/reference/rtl'
            sources=[baseline/'utils/mna_itf.sv',baseline/'hdmi_candidate/hdmi_cam_router.sv',SRC/'rtl/vitals_acf_csr.sv',SRC/'rtl/vitals_acf_bridge.sv',SRC/'sim/tb_vitals_bridge.sv'];top='tb_vitals_bridge';marker='VITALS_BRIDGE_PASS'
        run('compile',[V/'xvlog.bat','-sv',*sources])
        run('elaborate',[V/'xelab.bat',top,'-s','vitals_sim','-timescale','1ns/1ps','-mt','2'])
        run('simulate',[V/'xsim.bat','vitals_sim','-tclbatch','run.tcl'])
        log=(out/'simulate.log').read_text(errors='replace')
        if marker not in log or 'Fatal:' in log:raise SystemExit(1)
        print(log[-1200:])
    else:
        (out/'synth.tcl').write_text(f'''set_param general.maxThreads 2
read_verilog -sv {{{(SRC/'rtl/vitals_acf_csr.sv').as_posix()}}}
synth_design -top vitals_acf_csr -part xc7z030ffg676-2 -mode out_of_context
create_clock -name GP -period 20 [get_ports clk]
report_utilization -file utilization.rpt
report_timing_summary -file timing.rpt -report_unconstrained
write_checkpoint -force vitals-acf.dcp
exit
''')
        run('synthesis',[V/'vivado.bat','-mode','batch','-source','synth.tcl','-log','vivado.log','-nojournal'])
    return 0
if __name__=='__main__':sys.exit(main())

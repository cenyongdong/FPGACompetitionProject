"""Independent bounded router and true 2018.3 MMCM/TMDS/CSR simulations."""
from pathlib import Path
import os,sys,json,shutil,hashlib,subprocess,time
R=Path(__file__).resolve().parents[3];NAME='hdmi-integration-20261016-r1'
mode=sys.argv[1];assert mode in ('router','phy')
revision=sys.argv[2] if len(sys.argv)>2 else 'r1'
assert revision in ('r1','r2','r3')
suffix='' if revision=='r1' else '-'+revision
E=R/'tools/pose-v1/evidence'/NAME/('sim-'+mode+suffix);W=R/'.local'/NAME/('sim-'+mode+suffix)
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
F=R/'.local'/NAME/'reference';B=Path('D:/vivado18.3/Vivado/2018.3/bin')
sources=[F/'rtl/utils/mna_itf.sv',R/'FPGA/hdmi_candidate/sim/tb_hdmi_integration.sv']
sources+=sorted((F/'rtl/hdmi_candidate').glob('*'))
sources+=[F/'rtl/display/uihdmitx.v',F/'rtl/display/oserdese2_10to1.v',F/'rtl/display/oserdese3_10to1.v']
sources+=[Path('D:/vivado18.3/Vivado/2018.3/data/verilog/src/glbl.v')]
for p in sources:shutil.copyfile(p,W/p.name)
vhdl=F/'rtl/display/TMDSEncoder.vhd';shutil.copyfile(vhdl,W/vhdl.name)
(E/'sources.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[vhdl]},indent=2)+'\n')
top='tb_hdmi_router' if mode=='router' else 'tb_hdmi_board_phy'
(W/'run.tcl').write_text('run all\nquit\n')
env=os.environ.copy();env['XILINX_VIVADO']='D:/vivado18.3/Vivado/2018.3'
for key in list(env):
 if key.startswith('RDI_'):env.pop(key)
steps=[]
for stage,args in [('vhdl',[str(B/'xvhdl.bat'),vhdl.name]),
 ('compile_verilog',[str(B/'xvlog.bat'),*[p.name for p in sources if p.suffix=='.v']]),
 ('compile_sv',[str(B/'xvlog.bat'),'--sv',*[p.name for p in sources if p.suffix=='.sv']]),
 ('elaborate',[str(B/'xelab.bat'),top,'glbl','--timescale','1ns/1ps','-L','unisims_ver','-L','secureip','--snapshot',top]),
 ('simulate',[str(B/'xsim.bat'),top,'--tclbatch','run.tcl'])]:
 t=time.monotonic();p=subprocess.Popen(args,cwd=W,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
 timed=False
 try:out,err=p.communicate(timeout=90)
 except subprocess.TimeoutExpired:
  timed=True;kill=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=20)
  (E/(stage+'.cleanup.txt')).write_bytes(kill.stdout+kill.stderr);out,err=p.communicate(timeout=20)
 (E/(stage+'.stdout.txt')).write_bytes(out);(E/(stage+'.stderr.txt')).write_bytes(err)
 steps.append({'stage':stage,'exit':p.returncode,'seconds':time.monotonic()-t,'budget':90,'timeout':timed})
 (E/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(json.dumps(steps[-1]),flush=True)
 if p.returncode or timed:
  print(out.decode(errors='replace')[-4000:].encode('ascii',errors='backslashreplace').decode('ascii'));raise SystemExit('Simulation stopped; preserve evidence')
text=(E/'simulate.stdout.txt').read_text(errors='replace');marker='HDMI_ROUTER_PASS' if mode=='router' else 'HDMI_BOARD_PHY_PASS'
passed=marker in text and 'Fatal:' not in text
(E/'result.json').write_text(json.dumps({'passed':passed,'real_board':False,'tool':'Vivado2018.3 XSim','top':top},indent=2)+'\n')
shutil.copyfile(Path(__file__),E/Path(__file__).name)
print(text[-2000:].encode('ascii',errors='backslashreplace').decode('ascii'),flush=True)
if not passed:raise SystemExit('Simulation assertions did not pass')

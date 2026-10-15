"""One fresh mixed-language UNISIM regression; 90s per stage, no device I/O."""
from pathlib import Path
import hashlib,json,shutil,subprocess,time,sys
R=Path(__file__).resolve().parents[3];C=R/'FPGA/hdmi_candidate'
REV=sys.argv[1] if len(sys.argv)>1 else 'r1'
assert REV in ('r1','r2','r3','r4')
LITE=REV=='r4'
TOP='tb_tmds_lite' if LITE else 'tb_tmds_clock'
E=R/('tools/pose-v1/evidence/hdmi-tmds-literal-20261015-'+REV)
W=R/('.local/hdmi-tmds-literal-20261015-'+REV)
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
S=R/'Docs/26嵌赛开发/fpai_demo_fpga/rtl/display'
sources={}
for p in (C/'rtl/display/uihdmitx.v',C/'sim/tb_tmds_clock.sv',S/'oserdese2_10to1.v',S/'oserdese3_10to1.v',S/'TMDSEncoder.vhd',Path('D:/Xilinx/Vivado/2019.1/data/verilog/src/glbl.v')):
 shutil.copyfile(p,W/p.name);sources[p.name]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
old=(S/'uihdmitx.v').read_bytes();assert old.count(b'module uihdmitx#')==1
(W/'uihdmitx_legacy.v').write_bytes(old.replace(b'module uihdmitx#',b'module uihdmitx_legacy#'))
sources['uihdmitx_legacy.v']={'path':str(S/'uihdmitx.v'),'original_sha256':hashlib.sha256(old).hexdigest(),
 'simulated_sha256':hashlib.sha256((W/'uihdmitx_legacy.v').read_bytes()).hexdigest(),'change':'module name only; logic unchanged'}
(E/'source-manifest.json').write_text(json.dumps(sources,indent=2)+'\n')
(W/'run.tcl').write_text('open_vcd tmds_clock.vcd\nlog_vcd /'+TOP+'/*\nrun all\nclose_vcd\nquit\n')
V=Path('D:/Xilinx/Vivado/2019.1/bin');steps=[]
stages=[('vhdl',[str(V/'xvhdl.bat'),'TMDSEncoder.vhd']),
 ('verilog',[str(V/'xvlog.bat'),'uihdmitx.v','uihdmitx_legacy.v','oserdese2_10to1.v','oserdese3_10to1.v','glbl.v']),
 ('testbench',[str(V/'xvlog.bat'),'--sv','tb_tmds_clock.sv']),
 ('elaborate',[str(V/'xelab.bat'),TOP,'glbl','-L','unisims_ver','-L','secureip','--timescale','1ps/1ps','--debug','typical','--snapshot','tmds_clock']),
 ('simulate',[str(V/'xsim.bat'),'tmds_clock','--tclbatch','run.tcl'])]
for name,args in stages:
 t=time.monotonic();timeout=False
 p=subprocess.Popen(args,cwd=W,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
 try:out,err=p.communicate(timeout=90)
 except subprocess.TimeoutExpired:
  timeout=True;kill=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  (E/(name+'.cleanup.txt')).write_bytes(kill.stdout+kill.stderr);out,err=p.communicate(timeout=15)
 (E/(name+'.stdout.txt')).write_bytes(out);(E/(name+'.stderr.txt')).write_bytes(err)
 steps.append({'stage':name,'exit':p.returncode,'timed_out':timeout,'seconds':time.monotonic()-t,'budget':90})
 (E/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 print(name,'exit',p.returncode,flush=True)
 if timeout or p.returncode:break
raw=(E/'simulate.stdout.txt').read_text(errors='replace') if (E/'simulate.stdout.txt').exists() else ''
marker='TMDS_LITE_LITERAL_AND_WAVEFORM_PASS' if LITE else 'TMDS_LITERAL_AND_WAVEFORM_PASS'
passed=len(steps)==5 and all(s['exit']==0 and not s['timed_out'] for s in steps) and marker in raw and 'Fatal:' not in raw
(E/'result.json').write_text(json.dumps({'passed':passed,'native_Procise_phy_model':False,'silicon_validation':False,
 'source_serializer_wrappers_and_UNISIM_used':True,'model_pixel_frequency_MHz':100,'automatic_retry':False,
 'profile':'Lite 7FAMILY only; same exact edge gate' if LITE else 'both-family exploratory exact-edge gate'},indent=2)+'\n')
shutil.copytree(W,E/'simulation-copy',ignore=shutil.ignore_patterns('xsim.dir','*.wdb','*.pb'))
print(raw[-2300:])
if not passed:raise SystemExit('TMDS literal gate failed; preserve and stop without retry')

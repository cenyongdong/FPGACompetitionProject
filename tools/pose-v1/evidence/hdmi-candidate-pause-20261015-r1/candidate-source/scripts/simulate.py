from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[3]
REV=sys.argv[1] if len(sys.argv)>1 else 'r1'
assert REV in ('r1','r2','r3','r4')
E=R/('tools/pose-v1/evidence/hdmi-candidate-sim-20261015-'+REV)
W=R/('.local/hdmi-candidate-sim-20261015-'+REV)
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
S=R/'FPGA/hdmi_candidate'
rtl=['hdmi_axi_read.v','hdmi_command_mailbox.v','hdmi_scan_control.v','hdmi_candidate_core.v','hdmi_register_bank.v','hdmi_candidate_register_core.v']
tb=['tb_axi_read.sv','tb_scan_control.sv','tb_fullframe.sv','tb_register_bank.sv','tb_candidate.sv']
manifest={}
for sub,names in (('rtl',rtl),('sim',tb)):
 for n in names:
  p=S/sub/n;shutil.copyfile(p,W/n);manifest[n]=hashlib.sha256(p.read_bytes()).hexdigest()
(E/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(W/'run.tcl').write_text('run all\nquit\n',encoding='ascii')
V=Path('D:/Xilinx/Vivado/2019.1/bin');steps=[]
for name,args in (
 ('compile',[str(V/'xvlog.bat'),'--sv',*rtl,*tb]),
 ('elaborate',[str(V/'xelab.bat'),'tb_candidate','--timescale','1ns/1ps','--debug','typical','--snapshot','candidate']),
 ('simulate',[str(V/'xsim.bat'),'candidate','--tclbatch','run.tcl'])):
 t=time.monotonic();p=subprocess.run(args,cwd=W,capture_output=True,timeout=90)
 (E/(name+'.stdout.txt')).write_bytes(p.stdout);(E/(name+'.stderr.txt')).write_bytes(p.stderr)
 steps.append({'stage':name,'exit':p.returncode,'seconds':time.monotonic()-t,'budget':90})
 (E/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 if p.returncode:raise SystemExit(name+' failed; stop')
 print(name,'exit',p.returncode,flush=True)
out=(E/'simulate.stdout.txt').read_text(errors='replace')
print(out[-2500:])
if 'HDMI_CANDIDATE_TEST_PASS' not in out or 'Fatal:' in out:raise SystemExit('Behavior gate failed; preserve result')
(E/'result.json').write_text(json.dumps({'passed':True,'silicon_test':False,'clock_PLL_model_tested':False,'full_system_integration':False},indent=2)+'\n')
shutil.copytree(W,E/'simulation-copy',ignore=shutil.ignore_patterns('xsim.dir','*.pb','*.wdb'))

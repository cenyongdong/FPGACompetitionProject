from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[3]
REV=sys.argv[1] if len(sys.argv)>1 else 'r1'
assert REV in ('r1','r2','r3','r4','r5','r6','r7','r8')
GROUP=sys.argv[2] if len(sys.argv)>2 else 'all'
assert GROUP in ('all','core','pixel')
E=R/('tools/pose-v1/evidence/hdmi-candidate-sim-20261015-'+REV)
W=R/('.local/hdmi-candidate-sim-20261015-'+REV)
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
S=R/'FPGA/hdmi_candidate'
rtl=['hdmi_axi_read.v','hdmi_command_mailbox.v','hdmi_scan_control.v','hdmi_candidate_core.v','hdmi_register_bank.v','hdmi_candidate_register_core.v','hdmi_stream_fifo.v','hdmi_pixel_scan.v','hdmi_scanout.v']
tb=['tb_axi_read.sv','tb_scan_control.sv','tb_fullframe.sv','tb_register_bank.sv','tb_stream_fifo.sv','tb_scanout.sv','tb_candidate.sv']
manifest={}
for sub,names in (('rtl',rtl),('sim',tb)):
 for n in names:
  p=S/sub/n;shutil.copyfile(p,W/n);manifest[n]=hashlib.sha256(p.read_bytes()).hexdigest()
(E/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(W/'run.tcl').write_text('run all\nquit\n',encoding='ascii')
V=Path('D:/Xilinx/Vivado/2019.1/bin');steps=[]
for name,args in (
 ('compile',[str(V/'xvlog.bat'),'--sv',*rtl,*tb]),
 ('elaborate',[str(V/'xelab.bat'),{'all':'tb_candidate','core':'tb_core_suite','pixel':'tb_pixel_suite'}[GROUP],'--timescale','1ns/1ps','--debug','typical','--snapshot','candidate']),
 ('simulate',[str(V/'xsim.bat'),'candidate','--tclbatch','run.tcl'])):
 t=time.monotonic();timed_out=False
 p=subprocess.Popen(args,cwd=W,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
 try:out,err=p.communicate(timeout=90)
 except subprocess.TimeoutExpired:
  timed_out=True
  cleanup=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  (E/(name+'.cleanup.stdout.txt')).write_bytes(cleanup.stdout)
  (E/(name+'.cleanup.stderr.txt')).write_bytes(cleanup.stderr)
  out,err=p.communicate(timeout=15)
 (E/(name+'.stdout.txt')).write_bytes(out);(E/(name+'.stderr.txt')).write_bytes(err)
 steps.append({'stage':name,'exit':p.returncode,'seconds':time.monotonic()-t,'budget':90,'timed_out':timed_out,'group':GROUP})
 (E/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 if timed_out or p.returncode:
  shutil.copytree(W,E/'simulation-copy',ignore=shutil.ignore_patterns('xsim.dir','*.pb','*.wdb'))
  (E/'result.json').write_text(json.dumps({'passed':False,'failed_stage':name,'timed_out':timed_out,'group':GROUP},indent=2)+'\n')
  raise SystemExit(name+' failed; stop without retry')
 print(name,'exit',p.returncode,flush=True)
out=(E/'simulate.stdout.txt').read_text(errors='replace')
print(out[-2500:])
shutil.copytree(W,E/'simulation-copy',ignore=shutil.ignore_patterns('xsim.dir','*.pb','*.wdb'))
passed='HDMI_CANDIDATE_TEST_PASS' in out and 'Fatal:' not in out
(E/'result.json').write_text(json.dumps({'passed':passed,'group':GROUP,'silicon_test':False,'clock_PLL_model_tested':False,'full_system_integration':False},indent=2)+'\n')
if not passed:raise SystemExit('Behavior gate failed; preserve result without retry')

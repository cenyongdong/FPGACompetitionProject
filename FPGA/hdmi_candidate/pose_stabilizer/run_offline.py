"""Local xsim/OOC-only workflow; no board, BOOT, implementation, or bitstream commands."""
from pathlib import Path
import subprocess,json,sys,time,shutil
ROOT=Path(__file__).resolve().parents[3];SRC=Path(__file__).resolve().parent
V=Path('D:/vivado18.3/Vivado/2018.3/bin')
W=ROOT/'.local/pose-postprocess-offline'/('rtl-'+time.strftime('%Y%m%d-%H%M%S'));W.mkdir(parents=True)
steps=[]
def run(stage,args,cwd=W):
 with (cwd/(stage+'.log')).open('w') as f:
  p=subprocess.Popen(args,cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
  (W/'process.json').write_text(json.dumps(dict(pid=p.pid,stage=stage,command=list(map(str,args)),automatic_kill=False)))
  code=p.wait()
 steps.append(dict(stage=stage,native_exit=code));(W/'results.json').write_text(json.dumps(steps,indent=2));print(stage,code,str(W),flush=True)
 if code:print((cwd/(stage+'.log')).read_text(errors='replace')[-5000:]);raise SystemExit(code)
mode=sys.argv[1] if len(sys.argv)>1 else 'filter'
if mode=='geometry':
 run('vectors-build',['g++','-O2','-std=c++17','-I'+str(ROOT/'software/core/pose'),str(ROOT/'software/pose180_pipeline/resident/geometry_vectors.cpp'),'-o',str(W/'geometry_vectors.exe')])
 run('vectors',[str(W/'geometry_vectors.exe'),str(W)])
 (W/'run.tcl').write_text('run all\nquit\n')
 run('compile',[str(V/'xvlog.bat'),'-sv',str(SRC/'rtl/pose_geometry.sv'),str(SRC/'sim/tb_pose_geometry.sv')])
 run('elaborate',[str(V/'xelab.bat'),'tb_pose_geometry','-s','geometry_sim','-timescale','1ns/1ps','-mt','2'])
 run('simulate',[str(V/'xsim.bat'),'geometry_sim','-tclbatch','run.tcl'])
 text=(W/'simulate.log').read_text(errors='replace');print(text[-1800:]);sys.exit(0 if 'GEOMETRY_PASS' in text else 1)
elif mode=='filter':
 for name in ('input.hex','expected.hex','params.hex'):shutil.copyfile(ROOT/'.local/pose-postprocess-offline'/name,W/name)
 (W/'run.tcl').write_text('run all\nquit\n')
 run('compile',[str(V/'xvlog.bat'),'-sv',str(SRC/'rtl/pose_geometry.sv'),str(SRC/'rtl/pose_filter_lane.sv'),str(SRC/'rtl/pose_filter.sv'),str(SRC/'rtl/pose_filter_csr.sv'),str(SRC/'sim/tb_pose_filter.sv')])
 run('elaborate',[str(V/'xelab.bat'),'tb_pose_filter','-s','filter_sim','-timescale','1ns/1ps','-mt','2'])
 run('simulate',[str(V/'xsim.bat'),'filter_sim','-tclbatch','run.tcl'])
 text=(W/'simulate.log').read_text(errors='replace');print(text[-1800:]);sys.exit(0 if 'FILTER_PASS' in text else 1)
elif mode=='guard':
 (W/'run.tcl').write_text('run all\nquit\n')
 run('compile',[str(V/'xvlog.bat'),'-sv',str(SRC/'rtl/startup_guard.sv'),str(SRC/'rtl/startup_guard_csr.sv'),str(ROOT/'FPGA/hdmi_candidate/diagnostics/deferred_consume_r45/sources/hp2_startup_drain.sv'),str(SRC/'sim/tb_startup_guard.sv')])
 run('elaborate',[str(V/'xelab.bat'),'tb_startup_guard','-s','guard_sim','-timescale','1ns/1ps','-mt','2'])
 run('simulate',[str(V/'xsim.bat'),'guard_sim','-tclbatch','run.tcl'])
 text=(W/'simulate.log').read_text(errors='replace');print(text[-1800:]);sys.exit(0 if 'GUARD_PASS' in text else 1)
elif mode in ('guard-faults','filter-csr','drain-bounds','guard-csr'):
 top={'guard-faults':'tb_guard_faults','filter-csr':'tb_filter_csr','drain-bounds':'tb_startup_drain','guard-csr':'tb_guard_csr'}[mode]
 sources=([SRC/'rtl/startup_guard.sv',SRC/'sim/tb_guard_faults.sv'] if mode=='guard-faults' else
          [SRC/'rtl/startup_guard_csr.sv',SRC/'sim/tb_guard_csr.sv'] if mode=='guard-csr' else
          [ROOT/'FPGA/hdmi_candidate/diagnostics/deferred_consume_r45/sources/hp2_startup_drain.sv',ROOT/'FPGA/hdmi_candidate/diagnostics/deferred_consume_r45/tb_bounds.sv'] if mode=='drain-bounds' else
          [SRC/'rtl'/n for n in ('pose_geometry.sv','pose_filter_lane.sv','pose_filter.sv','pose_filter_csr.sv')]+[SRC/'sim/tb_filter_csr.sv'])
 (W/'run.tcl').write_text('run all\nquit\n')
 run('compile',[str(V/'xvlog.bat'),'-sv',*map(str,sources)])
 run('elaborate',[str(V/'xelab.bat'),top,'-s','extra_sim','-timescale','1ns/1ps','-mt','2'])
 run('simulate',[str(V/'xsim.bat'),'extra_sim','-tclbatch','run.tcl'])
 text=(W/'simulate.log').read_text(errors='replace');print(text[-2200:])
 if 'FATAL' in text or '$fatal' in text or 'PASS' not in text:raise SystemExit(1)
elif mode=='synthesis':
 for lanes in (1,4):
  d=W/('lanes'+str(lanes));d.mkdir()
  src=' '.join('{'+str(SRC/'rtl'/name).replace('\\','/')+'}' for name in ['pose_geometry.sv','pose_filter_lane.sv','pose_filter.sv','pose_filter_csr.sv'])
  script=f"""set_param general.maxThreads 2
read_verilog -sv [list {src}]
synth_design -top pose_filter_csr -part xc7z030ffg676-2 -mode out_of_context -generic LANES={lanes}
create_clock -period 10 [get_ports clk]
report_utilization -file utilization.rpt
report_timing_summary -file timing.rpt -report_unconstrained
write_checkpoint -force filter.dcp
exit
"""
  (d/'synth.tcl').write_text(script)
  run('synthesis',[str(V/'vivado.bat'),'-mode','batch','-source','synth.tcl','-log','vivado.log','-nojournal'],d)
elif mode=='overlay-parse':
 subprocess.run([sys.executable,str(SRC/'prepare_overlay.py')],check=True)
 ref=ROOT/'.local/hdmi-boot-witness-20261019-r23/reference/rtl'
 run('compile',[str(V/'xvlog.bat'),'-sv',str(ref/'utils/mna_itf.sv'),str(ref/'hdmi_candidate/hdmi_cam_router.sv'),
  *map(str,sorted((SRC/'rtl').glob('*.sv'))),str(ROOT/'.local/pose-postprocess-offline/overlay/ps_ai_peripheral.sv')])
elif mode=='guard-synthesis':
 (W/'synth.tcl').write_text(f'''set_param general.maxThreads 2
read_verilog -sv [glob {{{SRC.as_posix()}/rtl/startup_guard*.sv}}]
synth_design -top startup_guard_block -part xc7z030ffg676-2 -mode out_of_context -generic COVERAGE_COMPLETE=1
create_clock -name HP -period 5 [get_ports hp_clk]
create_clock -name GP -period 20 [get_ports csr_clk]
report_utilization -file utilization.rpt
report_timing_summary -file timing.rpt -report_unconstrained
write_checkpoint -force guard.dcp
exit
''')
 run('synthesis',[str(V/'vivado.bat'),'-mode','batch','-source','synth.tcl','-log','vivado.log','-nojournal'])
else:raise SystemExit('Unknown offline mode')

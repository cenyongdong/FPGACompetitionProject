"""Explore project-local vendor primitive declarations without database replacement.
RTL elaboration metadata only: not a synthesized/implemented PS hardware gate.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-jfm-ps-elaboration-20261015-r1'
W=R/'.local/hdmi-jfm-ps-elaboration-20261015-r1'
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
old=R/'.local/hdmi-native-ps-20261015-r1'
files=list(old.glob('*.v'));assert len(files)==7
lib=R/'Docs/26嵌赛开发/JFM_Kits/JFM_Kits/ip_patch/030ai/unisim_comp.v'
sources={}
for src in files+[lib]:
 shutil.copyfile(src,W/src.name)
 sources[src.name]={'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
(E/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
script='''
if {[catch {
 create_project -in_memory -part xc7z030ffg676-2
 read_verilog -library fmsh030ai unisim_comp.v
 read_verilog [list SOURCES]
 puts "LOCAL_PS_RTL_ELABORATION_BEGIN"
 synth_design -rtl -top ps_ai_processing_system7_0_0 -part xc7z030ffg676-2
 set cells [get_cells -hierarchical -filter {REF_NAME == PS7}]
 puts "LOCAL_PS7_CELL_COUNT [llength $cells]"
 if {[llength $cells]!=1} {error "Expected one real PS7 declaration binding"}
 set f [open PINFILE w]
 foreach pin [get_pins -of_objects $cells] {puts $f "$pin|[get_property DIRECTION $pin]"}
 close $f
 report_property $cells
 close_design
 close_project
 puts "LOCAL_PS_RTL_ELABORATION_METADATA_COMPLETE"
} result]} {puts "LOCAL_PS_RTL_ELABORATION_FAIL $result";exit 1}
exit
'''.replace('SOURCES',' '.join(p.name for p in files)).replace('PINFILE','{'+(E/'PS7-pins.txt').as_posix()+'}')
(W/'elaborate.tcl').write_text(script,encoding='ascii');shutil.copyfile(W/'elaborate.tcl',E/'elaborate.tcl')
env=os.environ.copy();env['PROCESSOR_ARCHITECTURE']='AMD64'
args=['D:/Xilinx/Vivado/2019.1/bin/vivado.bat','-mode','batch','-nojournal','-log',str(E/'vivado.log'),'-source',str(W/'elaborate.tcl')]
t=time.monotonic();timeout=False
with (E/'stdout.txt').open('wb') as out,(E/'stderr.txt').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=p.wait(timeout=60)
 except subprocess.TimeoutExpired:
  timeout=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  (E/'cleanup.txt').write_bytes(k.stdout+k.stderr);code=p.wait(timeout=15)
result={'exit':code,'seconds':time.monotonic()-t,'timeout':timeout,'budget':60,
 'project_local_vendor_declaration':True,'RTL_metadata_only':True,
 'global_database_write':False,'replace_invoked':False,'version_guard_bypassed':False,
 'PS_or_AI_Mate_modified':False,'hardware_synthesis_or_timing_signoff':False}
(E/'execution.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
print((E/'stdout.txt').read_text(errors='replace')[-4500:],flush=True)
if code or timeout:raise SystemExit('Project-local PS metadata probe failed; preserve and stop')

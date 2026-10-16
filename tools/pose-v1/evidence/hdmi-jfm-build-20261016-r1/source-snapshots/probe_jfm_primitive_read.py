"""Project-local parser test on the vendor 030AI primitive declaration.
Does not call replace/reset, install models, change global libraries, generate
hardware, or use a black box as implementation acceptance.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
R=Path(__file__).resolve().parents[3]
W=R/'.local/hdmi-jfm-primitive-20261015-r1'
E=R/'tools/pose-v1/evidence/hdmi-jfm-primitive-20261015-r1'
W.mkdir(exist_ok=False);E.mkdir(exist_ok=False)
source=R/'Docs/26嵌赛开发/JFM_Kits/JFM_Kits/ip_patch/030ai/unisim_comp.v'
shutil.copyfile(source,W/'unisim_comp.v')
script='''
if {[catch {
 create_project -in_memory -part xc7z030ffg676-2
 puts "LOCAL_030AI_DECLARATION_READ_BEGIN"
 read_verilog -library fmsh030ai unisim_comp.v
 puts "LOCAL_030AI_DECLARATION_READ_COMPLETE"
 synth_design -rtl -top PS7 -part xc7z030ffg676-2
 set f [open PORTFILE w]
 foreach port [get_ports] {puts $f "$port|[get_property DIRECTION $port]"}
 close $f
 close_design
 close_project
 puts "LOCAL_030AI_DECLARATION_PORTS_READ_COMPLETE"
} result]} {puts "LOCAL_030AI_DECLARATION_READ_FAIL $result";exit 1}
exit
'''.replace('PORTFILE','{'+(E/'PS7-ports.txt').as_posix()+'}')
(W/'read.tcl').write_text(script,encoding='ascii');shutil.copyfile(W/'read.tcl',E/'read.tcl')
env=os.environ.copy();env['PROCESSOR_ARCHITECTURE']='AMD64'
args=['D:/Xilinx/Vivado/2019.1/bin/vivado.bat','-mode','batch','-nojournal','-log',str(E/'vivado.log'),'-source',str(W/'read.tcl')]
t=time.monotonic();timeout=False
with (E/'stdout.txt').open('wb') as out,(E/'stderr.txt').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=p.wait(timeout=60)
 except subprocess.TimeoutExpired:
  timeout=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  (E/'cleanup.txt').write_bytes(k.stdout+k.stderr);code=p.wait(timeout=15)
result={'exit':code,'seconds':time.monotonic()-t,'timeout':timeout,'budget':60,
 'purpose':'project-local primitive declaration parser/port metadata probe only',
 'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'PS_custom_IP_changed':False,'replace_invoked':False,'version_guard_bypassed':False,
 'global_database_write':False,'hardware_synthesis_or_timing_signoff':False}
(E/'execution.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
print((E/'stdout.txt').read_text(errors='replace')[-4000:],flush=True)
if code or timeout:raise SystemExit('Primitive metadata probe failed; preserve and stop')

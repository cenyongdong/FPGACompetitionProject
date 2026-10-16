"""Actual offline 30TAI ICAP postprocess of one copied factory reference bit."""
from pathlib import Path
import hashlib,json,shutil,subprocess,os,time
R=Path(__file__).resolve().parents[3];B=R/'tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1';ROOT=R/'.local/hdmi-jfm-build-20261016-r1'
E=B/'factory-bit-icap';W=ROOT/'factory-bit-icap';E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'Docs/26嵌赛开发/BOOT_Gen/ai7030_edif_top.bit';inp=W/'factory-input.bit';out=W/'factory-input_disable_icap.bit'
expected='1405d7f1cb992d8f9c78e7b4bbe756faa96eeecb2ff4bdd0d253e92b191e2575'
assert sha(source)==expected;shutil.copyfile(source,inp);assert sha(inp)==expected
tcl='''
if {[catch {
 set_device JFMQL30TAI676H
 increment_bit_cfg_v3 {INPUT} {OUTPUT} -disable_icap
 puts "FACTORY_BIT_ICAP_COMMAND_RETURNED"
} result]} {puts "FACTORY_BIT_ICAP_FAILED $result";exit 1}
exit
'''.replace('INPUT',inp.as_posix()).replace('OUTPUT',out.as_posix())
(W/'patch.tcl').write_text(tcl,encoding='ascii');shutil.copyfile(W/'patch.tcl',E/'patch.tcl')
root='C:/FudanMicro/Procise';env=os.environ.copy();env.update(APP_DIR=root,ICTIME_HOME=root,FMSH_DB=root+'/db',TCL_LIBRARY=root+'/tcl8.4');env['PATH']=root+'/dll;'+env['PATH']
start=time.monotonic();timeout=False
with (E/'stdout.txt').open('wb') as stdout,(E/'stderr.txt').open('wb') as stderr:
 p=subprocess.Popen([root+'/bin/procise.exe','patch.tcl'],cwd=W,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  timeout=True;clean=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=20);(E/'cleanup.txt').write_bytes(clean.stdout+clean.stderr)
  try:code=p.wait(timeout=20)
  except subprocess.TimeoutExpired:code=None
result={'exit':code,'seconds':time.monotonic()-start,'budget':180,'timeout':timeout,'target':'JFMQL30TAI676H','input_SHA':sha(inp),
 'input_unchanged':sha(inp)==sha(source)==expected,'output_exists':out.is_file(),'factory_reference_only':True,'BOOT_or_board_operation':False}
if out.is_file():
 result['output_SHA']=sha(out);result['output_bytes']=out.stat().st_size;shutil.copyfile(out,E/out.name)
(E/'execution.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
print((E/'stdout.txt').read_text(encoding='utf-8',errors='replace')[-1800:].encode('ascii',errors='backslashreplace').decode('ascii'),flush=True)
assert code==0 and not timeout and result['input_unchanged'] and result['output_exists'],result
assert out.stat().st_size>0

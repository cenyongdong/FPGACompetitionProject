"""Native synthesis gate on the actual newly generated AXI3 subsystem.
No system modifications, place/route, bitstream or board operation.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[3]
P=R/'tools/pose-v1/evidence/hdmi-generated-axi-20261015-r2'
assert json.loads((P/'result.json').read_text())['passed']
profile=sys.argv[1] if len(sys.argv)>1 else 'axi'
assert profile in ('axi','ps')
S=R/'.local/hdmi-generated-axi-20261015-r2'
E=R/('tools/pose-v1/evidence/hdmi-native-'+profile+'-20261015-r1')
W=R/('.local/hdmi-native-'+profile+'-20261015-r1')
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
manifest=json.loads((P/'sources.json').read_text())
top='ps_ai_axi_interconnect_3_0'
if profile=='ps':
    B=R/'.local/hdmi-ip-generation-20261015-r3/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai'
    sources=[B/'ip/ps_ai_processing_system7_0_0/synth/ps_ai_processing_system7_0_0.v',
             B/'ip/ps_ai_processing_system7_0_0/hdl/verilog/processing_system7_v5_5_processing_system7.v']
    sources+=list((B/'ipshared/8fd3/hdl/verilog').glob('*.v'))
    manifest={p.name:{'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources}
    top='ps_ai_processing_system7_0_0'
files=[]
for name,item in manifest.items():
    src=Path(item['source']) if profile=='ps' else S/name
    assert hashlib.sha256(src.read_bytes()).hexdigest()==item['sha256']
    shutil.copyfile(src,W/name)
    if src.suffix=='.v':files.append(name)
(E/'sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
script='''
if {[catch {
create_project -name generated_axi -device JFMQL30TAI676H
add_design_file -file FILES
set_top -top TOP
save_project
load_design -stage_elaborate -no_hier
launch_run -stage synthesis
} result]} {puts "NATIVE_AXI_FAIL $result";exit 1}
puts "NATIVE_AXI_SYNTHESIS_RETURNED"
exit
'''.replace('FILES',' '.join(files)).replace('TOP',top)
(W/'build.tcl').write_text(script,encoding='ascii')
root='C:/FudanMicro/Procise';env=os.environ.copy()
env.update(APP_DIR=root,TCL_LIBRARY=root+'/tcl8.4',ICTIME_HOME=root,FMSH_DB=root+'/db')
env['PATH']=root+'/dll;'+env['PATH']
start=time.monotonic();timeout=False
with (E/'stdout.txt').open('wb') as out,(E/'stderr.txt').open('wb') as err:
    p=subprocess.Popen([root+'/bin/procise.exe','build.tcl'],cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    try:code=p.wait(timeout=180)
    except subprocess.TimeoutExpired:
        timeout=True
        k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
        (E/'cleanup.txt').write_bytes(k.stdout+k.stderr);code=p.wait(timeout=15)
result={'exit':code,'seconds':time.monotonic()-start,'timeout':timeout,'budget':180,
        'profile':profile,'device':'JFMQL30TAI676H','stage':'synthesis','full_system':False,'timing_signoff':False,'board_operation':False}
(E/'execution.json').write_text(json.dumps(result,indent=2)+'\n')
shutil.copytree(W,E/'returned-project')
print(json.dumps(result),flush=True)
print((E/'stdout.txt').read_text(errors='replace')[-4500:],flush=True)
if code or timeout:raise SystemExit('Native AXI gate failed; preserve and stop')

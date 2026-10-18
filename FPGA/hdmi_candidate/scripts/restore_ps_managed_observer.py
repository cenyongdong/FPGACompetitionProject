"""Keep the observed PS top in its original managed BD dependency boundary."""
from pathlib import Path
import hashlib,importlib.util,json,re,shutil
R=Path(__file__).resolve().parents[3];W=R/'.local/hdmi-live-20261017-r3'
E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r3';P=W/'reference'
out=E/'managed-PS-observer-r2';out.mkdir(exist_ok=False)
def sha(b):return hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('exporter',Path(__file__).with_name('prepare_ps_read_taps.py'))
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
p=P/x.PS_REL;raw=p.read_bytes();assert sha(raw)==x.EXPECTED[x.PS_REL]
original=raw.decode('ascii');a,b,_,_=x.module_span(original,'ps_ai')
observed=(P/'rtl/hdmi_candidate/ps_ai_read_observed.v').read_bytes().decode('ascii')
oa,ob,_,_=x.module_span(observed,'ps_ai_read_observed')
top=observed[oa:ob];assert top.count('module ps_ai_read_observed')==1
top=top.replace('module ps_ai_read_observed','module ps_ai',1)
new=(original[:a]+top+original[b:]).encode('ascii')
assert new[:a]+raw[a:b]+new[a+len(top.encode('ascii')):]==raw
assert new.count(b'\x60timescale')==raw.count(b'\x60timescale')==1
wrap=P/'rtl/ps_ai_wrapper.sv';wb=wrap.read_bytes()
assert wb.count(b'ps_ai_read_observed ps_ai_i(')==1
wa=wb.replace(b'ps_ai_read_observed ps_ai_i(',b'ps_ai ps_ai_i(')
for name,data in [('ps_ai.v.before',raw),('ps_ai.v.after',new),('ps_ai_wrapper.sv.before',wb),('ps_ai_wrapper.sv.after',wa)]:
 (out/name).write_bytes(data)
xpr=P/'fpai_demo_vivado.xpr';shutil.copyfile(xpr,out/'fpai_demo_vivado.xpr.before')
p.write_bytes(new);wrap.write_bytes(wa)
result={'passed':True,'scope':'isolated passive output ports; preserve original managed BD identity',
 'changes':{x.PS_REL:{'before':sha(raw),'after':sha(new)},'rtl/ps_ai_wrapper.sv':{'before':sha(wb),'after':sha(wa)}},
 'original_top_span':[a,b],'new_top_span':[a,a+len(top.encode('ascii'))],
 'full_original_byte_exact_reconstruction':True,'other_12_original_modules_byte_identical':True,
 'original_timescale_unchanged':True,'BD_XCI_or_OOC_content_changed':False,
 'previous_failed_synthesis':'../read-v3-synthesis/execution.json',
 'reason':'unused renamed PS top removed managed BD and eleven PS leaf IPs from compile dependencies'}
(out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
shutil.copyfile(Path(__file__),out/'actual-driver.py')
spec=importlib.util.spec_from_file_location('eda_support',R/'.local/hdmi-live-20261017-r1/eda_support.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.E=E;m.W=W
body=r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
foreach tail {ps_ai_read_observed.v ps_ai_original_submodules.v} {
 set path [file normalize "@@REF@@/rtl/hdmi_candidate/$tail"]
 set object [get_files -quiet $path]
 if {[llength $object]!=1} {error "Previous global source not unique $tail"}
 remove_files $object
}
update_compile_order -fileset sources_1
set files [get_files -compile_order sources -used_in synthesis]
set f [open {@@OUT@@/source-order.txt} w]
foreach file $files {puts $f $file}
close $f
foreach tail {ps_ai_read_observed.v ps_ai_original_submodules.v} {
 foreach file $files {if {[file tail $file] eq $tail} {error "Removed source remains active $tail"}}
}
set bd [get_files -quiet {@@REF@@/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd}]
if {[llength $bd]!=1} {error "Original managed BD absent"}
set f [open {@@OUT@@/OOC-state.txt} w]
foreach run [get_runs -filter {IS_SYNTHESIS && NAME != synth_1 && NAME !~ synth_monitor* && NAME !~ synth_read*}] {
 puts $f "$run|[get_property STATUS $run]|[get_property NEEDS_REFRESH $run]"
 if {![string match {*Complete*} [get_property STATUS $run]] || [get_property NEEDS_REFRESH $run]} {error "Protected OOC stale $run"}
}
close $f
check_syntax -fileset sources_1
close_project
puts "MANAGED_PS_READ_SETUP_COMPLETE_NO_BOARD"
'''
stage=m.stage('read-v3r2-setup','if {[catch {\n'+body+'\n} result]} {puts "MANAGED_READ_SETUP_FAILED $result";puts $::errorInfo;exit 1}\nexit\n',ceiling=540,run_names=[])
assert p.read_bytes()==new and wrap.read_bytes()==wa,'Managed output regenerated; preserve and stop'
shutil.copyfile(xpr,stage/'fpai_demo_vivado.xpr')
m.dump(stage/'xpr-after-setup.json',{'sha256':sha(xpr.read_bytes()),'path':str(xpr),'managed_source_review':str(out/'review.json'),
 'managed_source_review_sha256':sha((out/'review.json').read_bytes()),'PS_output_SHA256':sha(new)})


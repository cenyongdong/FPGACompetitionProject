"""Register exact original generated PS submodules in the new global source set."""
from pathlib import Path
import hashlib,importlib.util,json,re,shutil
R=Path(__file__).resolve().parents[3]
W=R/'.local/hdmi-live-20261017-r3';E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r3'
P=W/'reference';out=E/'read-submodule-source';out.mkdir(exist_ok=False)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
exporter=load('read_export',Path(__file__).with_name('prepare_ps_read_taps.py'))
source=P/exporter.PS_REL;raw=source.read_bytes()
assert digest(raw)==exporter.EXPECTED[exporter.PS_REL]
text=raw.decode('ascii');start,end,_,_=exporter.module_span(text,'ps_ai')
submodules=(text[:start]+text[end:]).encode('ascii')
assert submodules[:start]+raw[start:end]+submodules[start:]==raw
original_names=re.findall(r'^\s*module\s+(\w+)',text,re.M)
new_names=re.findall(r'^\s*module\s+(\w+)',submodules.decode('ascii'),re.M)
assert new_names==[n for n in original_names if n!='ps_ai'] and len(new_names)==12
target=P/'rtl/hdmi_candidate/ps_ai_original_submodules.v'
assert not target.exists()
target.write_bytes(submodules);(out/target.name).write_bytes(submodules)
(out/'removed-original-top.txt').write_bytes(raw[start:end])
result={'passed':True,'original_generated_path':str(source),'original_sha256':digest(raw),'submodules_sha256':digest(submodules),
 'removed_top_span':[start,end],'byte_exact_reconstruction':True,'modules':new_names,'new_source':str(target),
 'original_generated_PS_BD_XCI_changed':False,'reason':'managed BD source absent from global synthesis compile order after explicit observed top'}
(out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
shutil.copyfile(Path(__file__),out/'actual-driver.py')
m=load('read_eda_support',R/'.local/hdmi-live-20261017-r1/eda_support.py');m.W=W;m.E=E
tcl=r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
add_files -norecurse {@@REF@@/rtl/hdmi_candidate/ps_ai_original_submodules.v}
update_compile_order -fileset sources_1
set files [get_files -compile_order sources -used_in synthesis]
set f [open {@@OUT@@/source-order.txt} w]
foreach file $files {puts $f $file}
close $f
foreach tail {ps_ai_read_observed.v ps_ai_original_submodules.v ai_read_monitor.sv} {
 set matches {}
 foreach file $files {if {[file tail $file] eq $tail} {lappend matches $file}}
 if {[llength $matches]!=1} {error "Global PS read source absent/duplicate $tail"}
}
set f [open {@@OUT@@/OOC-state.txt} w]
foreach run [get_runs -filter {IS_SYNTHESIS && NAME != synth_1 && NAME !~ synth_monitor* && NAME !~ synth_read*}] {
 puts $f "$run|[get_property STATUS $run]|[get_property NEEDS_REFRESH $run]"
 if {![string match {*Complete*} [get_property STATUS $run]] || [get_property NEEDS_REFRESH $run]} {error "Protected OOC stale $run"}
}
close $f
check_syntax -fileset sources_1
close_project
puts "READ_GLOBAL_SUBMODULE_SETUP_COMPLETE_NO_BOARD"
'''
stage=m.stage('read-v3-setup-submodules','if {[catch {\n'+tcl+'\n} result]} {puts "READ_SETUP_FAILED $result";puts $::errorInfo;exit 1}\nexit\n',ceiling=540,run_names=[])
xpr=P/'fpai_demo_vivado.xpr';shutil.copyfile(xpr,stage/xpr.name)
m.dump(stage/'xpr-after-setup.json',{'sha256':digest(xpr.read_bytes()),'path':str(xpr),
 'additional_source_review':str(out/'review.json'),'additional_source_review_sha256':digest((out/'review.json').read_bytes()),
 'clock_review_sha256':digest((P/'constrs_1/ai_read_clock_review.tcl').read_bytes())})


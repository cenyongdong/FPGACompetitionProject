"""Actual frozen custom PS wrapper gate after the authorized original 030ai patch."""
import vivado2018_support as s
import json,sys
R=s.R;E=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2';W=R/'.local/hdmi-vivado2018-20261016-r2'
s.E=E;s.W=W
mode=sys.argv[1];assert mode in ('rtl','synth')
assert json.loads((E/'patch-review.json').read_text(encoding='utf-8'))['all_nine_equal_vendor_patch']
old=json.loads((R/'tools/pose-v1/evidence/hdmi-native-ps-20261015-r1/sources.json').read_text(encoding='utf-8'))
sources=[R/'.local/hdmi-native-ps-20261015-r1'/name for name in old]
assert len(sources)==7
for source in sources:assert s.sha(source)==old[source.name]['sha256']
commands='''
 set cells [get_cells -hierarchical -filter {REF_NAME == PS7}]
 if {[llength $cells]!=1} {error "Expected one actual PS7 primitive"}
 puts "ACTUAL_PS7_PRIMITIVE $cells"
 report_property $cells
 set f [open {@@OUT@@/actual-PS7-pins.txt} w]
 foreach pin [get_pins -of_objects $cells] {puts $f "$pin|[get_property DIRECTION $pin]"}
 close $f
 set lib [get_lib_cells PS7]
 report_property $lib
 set f [open {@@OUT@@/library-PS7-pins.txt} w]
 foreach pin [get_lib_pins -of_objects $lib] {puts $f "$pin|[get_property DIRECTION $pin]"}
 close $f
'''
if mode=='synth':
 commands+='''
 report_utilization -file {@@OUT@@/utilization.rpt}
 write_edif -force {@@OUT@@/actual_ps.edf}
 write_checkpoint -force {@@OUT@@/actual_ps.dcp}
'''
tcl='''
if {[catch {
 if {[version -short] ne "2018.3"} {error "Wrong Vivado version"}
 create_project -in_memory -part xc7z030ffg676-2
 read_verilog [list @@FILES@@]
 synth_design @@RTL@@ -top ps_ai_processing_system7_0_0 -part xc7z030ffg676-2
 @@COMMANDS@@
 puts "ACTUAL_EXTENDED_PS_GATE_COMPLETE"
 close_design
 close_project
} result]} {puts "ACTUAL_EXTENDED_PS_GATE_FAILED $result";exit 1}
exit
'''.replace('@@FILES@@',' '.join(p.name for p in sources)).replace('@@RTL@@','-rtl' if mode=='rtl' else '').replace('@@COMMANDS@@',commands)
out,work=s.stage('actual-ps-'+mode,tcl,budget=180,inputs=sources)
from review_vivado2018_ps_contract import review
result=review(R,E,mode)
print(json.dumps({'actual_PS_mode':mode,'PS7_library_pins':result['actual_and_runtime_pins'],'gate_pass':True}),flush=True)

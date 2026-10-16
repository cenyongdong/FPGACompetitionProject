"""Verify user-installed 2018.3 and snapshot protected inputs without patching it."""
from vivado2018_support import *
old=json.loads((R/'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/replacement-review.json').read_text(encoding='utf-8'))
targets=[]
for pair in old['replacement_pairs']:
 rel=Path(pair['installed_target']['path']).relative_to(Path('D:/Xilinx/Vivado/2019.1'))
 p=INSTALLED/rel
 assert p.is_file(),str(p)
 targets.append({'relative':rel.as_posix(),'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p),
                 'patch_source':pair['patch']['path'],'patch_sha256':pair['patch']['sha256']})
dump(E/'installed-targets-before.json',targets)
dump(E/'installed-launcher-identity.json',{'path':str(INSTALLED/'bin/vivado.bat'),
 'sha256':sha(INSTALLED/'bin/vivado.bat'),'user_reported_installed':True})
script='''
if {[catch {
 puts "INSTALLED_VERSION [version -short]"
 puts "INSTALLED_ROOT $::env(XILINX_VIVADO)"
 if {[version -short] ne "2018.3"} {error "Unexpected installed Vivado version"}
 set f [open anchor.v w]
 puts $f {module metadata_anchor(input a, output y); assign y=a; endmodule}
 close $f
 create_project -in_memory -part xc7z030ffg676-2
 read_verilog anchor.v
 synth_design -rtl -top metadata_anchor -part xc7z030ffg676-2
 set cells [get_lib_cells -quiet *PS7*]
 if {[llength $cells]!=1} {error "Expected one PS7 library cell"}
 report_property $cells
 set f [open {@@OUT@@/builtin-PS7-pins.txt} w]
 foreach pin [get_lib_pins -of_objects $cells] {puts $f "$pin|[get_property DIRECTION $pin]"}
 close $f
 close_design
 close_project
 puts "INSTALLED_PREFLIGHT_COMPLETE"
} result]} {puts "INSTALLED_PREFLIGHT_FAIL $result";exit 1}
exit
'''
stage('installed-preflight',script)
for item in targets:assert sha(Path(item['path']))==item['sha256'],item['path']
dump(E/'installation-preflight-review.json',{'actual_version':'2018.3','actual_library_query_succeeded':True,
 'nine_installation_database_targets_unchanged':True,'installation_operation_by_agent':False,
 'installed_root':str(INSTALLED),'full_PS_or_HDMI_pass':False})

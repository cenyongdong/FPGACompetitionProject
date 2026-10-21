"""Native physical checks and existing factory bit hook, isolated from baseline."""
from prepare_ps_release_candidate import R,REF,W,E,S,wrap


def main():
    reports=E/'qualified-r8';reports.mkdir(exist_ok=True)
    old=(R/'tools/pose-v1/evidence/hdmi-hp2-ready-20261020-r24/final.tcl').read_text()
    old=old.replace((REF/'fpai_demo_vivado.runs/impl_hp2ready_r24/ai7030_edif_top_routed.dcp').as_posix(),(W/'routed-r8.dcp').as_posix())
    old=old.replace((R/'tools/pose-v1/evidence/hdmi-hp2-ready-20261020-r24').as_posix(),reports.as_posix())
    old=old.replace('# The implementation hook already installed the CDC constraints.',
        '# The implementation installed the factory clock bindings and all CDC bounds; validate without reapplying.')
    extra=r'''
set r {^U0_ps_ai_peripheral/ai_read_path_monitor/release_history/}
set s [get_cells -hier -regexp [format {%ssource_snapshot_reg\[[0-9]+\]$} $r]]
set d [get_cells -hier -regexp [format {%scsr_source_snapshot_reg\[[0-9]+\]$} $r]]
if {![llength $s] || [llength $s]!=[llength $d]} {error "New source/capture bus missing"}
set p [get_timing_paths -from [get_pins -of_objects $s -filter {REF_PIN_NAME == C}] -to [get_pins -of_objects $d -filter {REF_PIN_NAME == D}] -max_paths 1]
puts $f "NEW_BUS\t[llength $s]\t[get_property REQUIREMENT $p]\t[get_property SLACK $p]"
if {![llength $p] || abs([get_property REQUIREMENT $p]-10)>0.001 || [get_property SLACK $p]<0} {set pass 0}
set m {}
foreach c [get_cells -hier -regexp [format {%s(levels_meta_reg\[[0-9]+\]|beat_meta_reg)$} $r]] {
 if {![regexp {levels_meta_reg\[7\]$} [get_property NAME $c]]} {lappend m [get_pins -of_objects $c -filter {REF_PIN_NAME == D}]}
}
if {[llength $m]<16} {set pass 0}
foreach pin $m {
 set p [get_timing_paths -to $pin -max_paths 1]
 if {![llength $p]} {error "Missing final first-stage path: $pin"}
 puts $f "NEW_META\t[get_property ENDPOINT_PIN $p]\t[get_property REQUIREMENT $p]\t[get_property SLACK $p]"
 if {abs([get_property REQUIREMENT $p]-5)>0.001 || [get_property SLACK $p]<0} {set pass 0}
}
set ps [get_cells -hier -filter {REF_NAME == PS7}]
set pin [get_pins -of_objects $ps -filter {REF_PIN_NAME == SAXIHP2ARESETN}]
set fanout [filter [all_fanout -flat -endpoints_only -from $pin] {NAME =~ *ai_read_path_monitor/release_history/*}]
puts $f "PSRESET\t$pin\t[llength $fanout]"
if {[llength $pin]!=1 || ![llength $fanout]} {set pass 0}
foreach clock {clk_fpga_0 clk_out1_clk_wiz_0 clk_pll_i} period {20 10 5} {
 set c [get_clocks $clock]
 puts $f "CLOCK\t$clock\t[get_property PERIOD $c]"
 if {[llength $c]!=1 || abs([get_property PERIOD $c]-$period)>0.001} {set pass 0}
}
set raw_D {}
foreach c [get_cells -hier -regexp {^U0_ps_ai_peripheral/ai_read_path_monitor/release_history/first_r_levels_reg\[[0-9]+\]$}] {
 if {![regexp {first_r_levels_reg\[7\]$} [get_property NAME $c]]} {lappend raw_D [get_pins -of_objects $c -filter {REF_PIN_NAME == D}]}
}
if {[llength $raw_D]<16} {error "Raw first-event capture missing"}
foreach pin $raw_D {
 set p [get_timing_paths -to $pin -max_paths 1]
 puts $f "NEW_RAW\t$pin\t[get_property REQUIREMENT $p]\t[get_property SLACK $p]"
 if {[get_property REQUIREMENT $p] eq "" || abs([get_property REQUIREMENT $p]-5)>0.001 || [get_property SLACK $p]<0} {set pass 0}
}
'''
    old=old.replace('puts $f "BOOT_BUS\t','puts $f "OLD_BUS\t').replace('puts $f "GP\t','puts $f "OLD_META\t')
    old=old.replace('close $f\nreport_timing',extra+'\nclose $f\nreport_timing',1)
    old=old.replace('if {!$pass} {error',
        'write_checkpoint -force {'+(W/'qualified-routed.dcp').as_posix()+'}\nif {!$pass} {error',1)
    (E/'final.tcl').write_text(old)
    bit=(R/'tools/pose-v1/evidence/hdmi-hp2-ready-20261020-r24/bit.tcl').read_text()
    a=bit.index('set native $ref/');b=bit.index('\nfile mkdir',a)
    # Vendor callbacks use ../../ip_patch and the standard <project>.runs/run
    # convention for their output files. Keep that layout inside this workdir.
    native=W/'fpai_demo_vivado.runs/impl_ps_release_r26'
    bit=bit[:a]+'set native {'+native.as_posix()+'}\nfile mkdir {'+(W/'ip_patch').as_posix()+'}'+bit[b:]
    bit=bit.replace('set ::boot_allowed_launcher [file normalize $ref/call_procise_disable_icap.bat]',
                    'set ::boot_allowed_launcher [file normalize {'+(W/'call_procise_disable_icap.bat').as_posix()+'}]')
    bit=bit.replace('open_checkpoint $ref/fpai_demo_vivado.runs/impl_hp2ready_r24/ai7030_edif_top_routed.dcp','open_checkpoint {'+(W/'qualified-routed.dcp').as_posix()+'}')
    bit=bit.replace((R/'tools/pose-v1/evidence/hdmi-hp2-ready-20261020-r24').as_posix(),E.as_posix())
    for name in ('write_bitstream_pre.tcl','write_bitstream_post.tcl'):
        t=(REF/'ip_patch/process_control'/name).read_text().replace('[file join [pwd] "../.."]','{'+REF.as_posix()+'}')
        t=t.replace('set prj_path [get_prj_path]','set prj_path {'+(REF/'fpai_demo_vivado.xpr').as_posix()+'}')
        (S/name).write_text(t)
        bit=bit.replace('source $ref/ip_patch/process_control/'+name,'source {'+(S/name).as_posix()+'}')
    (E/'bit-r2.tcl').write_text(bit)
    print('Prepared native final checks and bit stage; BOOT remains offline only.')


if __name__=='__main__':main()

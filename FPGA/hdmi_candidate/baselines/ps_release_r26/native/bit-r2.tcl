if {[catch {

set ref {D:/FPGACompetitionProject/.local/hdmi-boot-witness-20261019-r23/reference}
set native {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/fpai_demo_vivado.runs/impl_ps_release_r26}
file mkdir {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/ip_patch}
file mkdir $native
cd $native
open_checkpoint {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/qualified-routed.dcp}
set_param general.maxThreads 2
source $ref/ip_patch/project_execution_guard.tcl
set ::env(JFM_PATH) $ref
set ::boot_allowed_xpr [file normalize $ref/fpai_demo_vivado.xpr]
set ::boot_allowed_launcher [file normalize {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/call_procise_disable_icap.bat}]
rename open_project boot_original_open_project
proc open_project args {
 if {[llength $args]!=1 || [file normalize [lindex $args 0]] ne $::boot_allowed_xpr} {error "Bit hook selected an unexpected project: $args"}
 return [uplevel 1 [linsert $args 0 boot_original_open_project]]
}
rename exec boot_original_exec
proc exec args {
 if {[llength $args]==3 && [string equal -nocase [lindex $args 0] cmd] && [lindex $args 1] eq "/c" && [file normalize [lindex $args 2]] eq $::boot_allowed_launcher} {
  set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/factory-ICAP-deferred.txt} w];puts $f $args;close $f
  puts "BOOT_WITNESS_FACTORY_ICAP_DEFERRED_TO_EXPLICIT_INPUT_STAGE"
  return ""
 }
 return [uplevel 1 [linsert $args 0 boot_original_exec]]
}
# Constraints are already in the final routed DCP. Do not reapply the large
# factory exception collections to an unchanged physical checkpoint.
set root {^U0_ps_ai_peripheral/ai_read_path_monitor/boot_history[./]witness/}
set boot_source [get_cells -hier -regexp [format {%ssource_snapshot_reg\[[0-9]+\]$} $root]]
set boot_capture_all [get_cells -hier -regexp [format {%scsr_snapshot_reg\[[0-9]+\]$} $root]]
set boot_capture {}
foreach c $boot_capture_all {regexp {\[([0-9]+)\]$} [get_property NAME $c] unused index;if {$index<384} {lappend boot_capture $c}}
if {[llength $boot_source]!=374 || [llength $boot_capture]!=374} {error "Missing physical held bus bits"}
set boot_source_C [get_pins -of_objects $boot_source -filter {REF_PIN_NAME == C}]
set boot_capture_D [get_pins -of_objects $boot_capture -filter {REF_PIN_NAME == D}]
set boot_meta [get_cells -hier -regexp [format {%sflags_meta_reg\[[0-9]+\]$} $root]]
set boot_meta_D [get_pins -of_objects $boot_meta -filter {REF_PIN_NAME == D}]
if {[llength $boot_meta_D]!=5} {error "Missing GP first-stage flags"}
foreach mode {max min} {
 set p [get_timing_paths -delay_type $mode -max_paths 1]
 if {![llength $p] || [get_property SLACK $p]<0} {error "Physical setup/hold prerequisite failed"}
}
foreach p [get_timing_paths -to $boot_meta_D -max_paths 5 -nworst 1] {
 if {[get_property REQUIREMENT $p] eq "" || abs([get_property REQUIREMENT $p]-5)>0.001 || [get_property SLACK $p]<0} {error "GP flag CDC prerequisite failed"}
}
set p [get_timing_paths -from $boot_source_C -to $boot_capture_D -max_paths 1]
if {[get_property REQUIREMENT $p] eq "" || abs([get_property REQUIREMENT $p]-10)>0.001 || [get_property SLACK $p]<0} {error "Boot held bus CDC prerequisite failed"}
report_route_status -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/route-status-final.rpt}
set expected_design [current_design]
set expected_project [current_project]
set root {^U0_ps_ai_peripheral/ai_read_path_monitor/boot_history[./]witness/}
set witness [get_cells -quiet -hier -regexp [format {%s.*} $root]]
if {[llength $witness]<500} {error "New boot witness missing in physical checkpoint"}
source {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/sources/write_bitstream_pre.tcl}
if {[current_design] ne $expected_design || [current_project] ne $expected_project || [get_property PART [current_project]] ne "xc7z030ffg676-2"} {error "Bit pre-hook replaced the routed context"}
if {[file exists ai7030_edif_top.bit]} {error "Preserve existing bit output"}
write_bitstream ai7030_edif_top.bit
source {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/sources/write_bitstream_post.tcl}
if {![file exists ai7030_edif_top.bit] || [file size ai7030_edif_top.bit]<5000000} {error "Native bit missing/incomplete"}
puts "BOOT_WITNESS_RAW_BIT_COMPLETE_NO_BOARD_OPERATION"

} result]} {puts "BOOT_WITNESS_BIT_FAILED $result";puts $::errorInfo;exit 1}
exit

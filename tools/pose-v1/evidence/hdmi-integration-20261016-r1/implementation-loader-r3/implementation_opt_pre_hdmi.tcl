
source [file join [file dirname [info script]] implementation_opt_pre.tcl]
if {[info exists ::hdmi_cdc_constraints_applied]} {error "HDMI constraints applied before dedicated hook"}
source [file normalize [file join [file dirname [info script]] ../../constrs_1/hdmi_cdc.tcl]]
set hdmi_source [hdmi_cdc_cells {scanout/core/core/mailbox/payload_hold_reg\[[0-9]+\]} 1]
set hdmi_response [hdmi_cdc_cells {scanout/core/core/mailbox/response_hold_reg\[[0-9]+\]} 1]
set hdmi_capture [hdmi_cdc_cells {scanout/core/core/mailbox/source_response_reg\[[0-9]+\]} 1]
set hdmi_mem_clock [get_clocks -of_objects [hdmi_cdc_pins [lindex $hdmi_response 0] C]]
set hdmi_memory_regs [filter [all_registers -clock $hdmi_mem_clock] {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
foreach hdmi_item [list [list command $hdmi_source $hdmi_memory_regs 5.000] [list response $hdmi_response $hdmi_capture 10.000]] {
 lassign $hdmi_item hdmi_name hdmi_src hdmi_dst hdmi_expected
 set hdmi_paths [get_timing_paths -from [hdmi_cdc_pins $hdmi_src C] -to [hdmi_cdc_pins $hdmi_dst D] -max_paths 1]
 if {![llength $hdmi_paths]} {error "HDMI_IMPL_MAILBOX_BOUND_ABSENT $hdmi_name"}
 set hdmi_req [get_property REQUIREMENT [lindex $hdmi_paths 0]]
 if {abs($hdmi_req-$hdmi_expected)>0.001} {error "HDMI_IMPL_MAILBOX_BOUND_WRONG $hdmi_name $hdmi_req"}
 puts "HDMI_IMPL_MAILBOX_BOUND_ACTIVE $hdmi_name $hdmi_req"
}
puts "HDMI_IMPL_PROCEDURAL_CONSTRAINT_HOOK_APPLIED"

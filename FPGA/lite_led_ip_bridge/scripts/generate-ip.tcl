# Reproduction recipe for the approved actual Vivado 2019.1 IP generation.
# Run in Vivado Tcl with: source this_file.tcl
# For reproduction, set bridge_root to a NEW ASCII directory before sourcing.
if {![info exists bridge_root]} {
    set bridge_root {D:/FPGACompetitionProject/FPGA/lite_led_ip_bridge}
}
if {[file exists [file join $bridge_root ip led_state_concat led_state_concat.xci]]} {
    error {Existing approved IP is preserved; set bridge_root to a new directory.}
}
file mkdir [file join $bridge_root ip]
create_project lite_led_ip_frontend [file join $bridge_root vivado] -part xc7z030ffg676-2
set def [get_ipdefs -all -quiet xilinx.com:ip:xlconcat:2.1]
if {[llength $def] != 1 || [get_property CORE_REVISION $def] != 3} {
    error {Expected xlconcat 2.1 revision 3}
}
create_ip -name xlconcat -vendor xilinx.com -library ip -version 2.1 -module_name led_state_concat -dir [file join $bridge_root ip]
set_property -dict [list CONFIG.NUM_PORTS {4} CONFIG.IN0_WIDTH {1} CONFIG.IN1_WIDTH {1} CONFIG.IN2_WIDTH {1} CONFIG.IN3_WIDTH {1}] [get_ips led_state_concat]
# For this IPI-only IP the property is read-only and already 0; do not set it.
if {[get_property GENERATE_SYNTH_CHECKPOINT [get_files led_state_concat.xci]] != 0} {
    error {Unexpected synthesis checkpoint generation}
}
generate_target {simulation synthesis instantiation_template} [get_ips led_state_concat]
puts "SYNTHESIS_FILES=[get_files -compile_order sources -used_in synthesis -of_objects [get_files led_state_concat.xci]]"
puts IP_GENERATION_COMPLETED

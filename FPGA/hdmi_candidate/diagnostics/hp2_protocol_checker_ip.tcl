# Native 2018.3 IP; an observational AXI3 checker, no interface conversion.
if {[catch {
set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
# argv[1] selects the monitor capacity; it does not change bus issuing limits.
set capacity 16
if {[llength $argv]>1} {set capacity [lindex $argv 1]}
file mkdir $out
create_project -in_memory -part xc7z030ffg676-2
set_property target_language Verilog [current_project]
create_ip -name axi_protocol_checker -vendor xilinx.com -library ip -version 2.0 \
 -module_name hp2_native_protocol_checker -dir $out
set ip [get_ips hp2_native_protocol_checker]
set_property -dict [list \
 CONFIG.PROTOCOL AXI3 CONFIG.ADDR_WIDTH 32 CONFIG.DATA_WIDTH 64 CONFIG.ID_WIDTH 6 \
 CONFIG.READ_WRITE_MODE READ_WRITE CONFIG.MAX_RD_BURSTS $capacity CONFIG.MAX_WR_BURSTS $capacity \
 CONFIG.MAX_BURST_LENGTH 16 CONFIG.LIGHT_WEIGHT 0 CONFIG.PC_MASTER_SIDE 0 \
 CONFIG.HAS_SYSTEM_RESET 1 CONFIG.ENABLE_CONTROL 0 CONFIG.ENABLE_MARK_DEBUG 0 \
 CONFIG.MAX_AW_WAITS 0 CONFIG.MAX_AR_WAITS 0 CONFIG.MAX_W_WAITS 0 \
 CONFIG.MAX_R_WAITS 0 CONFIG.MAX_B_WAITS 0 \
 CONFIG.MAX_CONTINUOUS_RTRANSFERS_WAITS 0 CONFIG.MAX_CONTINUOUS_WTRANSFERS_WAITS 0 \
 CONFIG.MAX_WLAST_TO_AWVALID_WAITS 0 CONFIG.MAX_WRITE_TO_BVALID_WAITS 0 \
 CONFIG.AWUSER_WIDTH 0 CONFIG.ARUSER_WIDTH 0 CONFIG.WUSER_WIDTH 0 \
 CONFIG.RUSER_WIDTH 0 CONFIG.BUSER_WIDTH 0 CONFIG.MESSAGE_LEVEL 0] $ip
generate_target all $ip
report_property $ip -file [file join $out hp2-protocol-ip-properties.rpt]
puts "HP2_PROTOCOL_IP_GENERATED [get_property IP_FILE $ip]"
} result]} {puts $result;puts $::errorInfo;exit 1}
exit

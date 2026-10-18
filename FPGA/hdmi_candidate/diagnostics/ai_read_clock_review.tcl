# Read-only actual DCP clock review. Paths are bound to the successful
# read-clock-discovery-r1 dump, not to optimized-away HDL boundary ports.
# Caller supplies a NEW ::ai_read_clock_report path. No design/constraint edits.
if {![info exists ::ai_read_clock_report]} {error "AI_READ_CLOCK_REPORT_PATH_REQUIRED"}
if {[file exists $::ai_read_clock_report]} {error "AI_READ_CLOCK_REPORT_ALREADY_EXISTS"}
namespace eval ::ai_read_clock_review {
 variable fd
 variable source_clock
 variable csr_clock
 variable clock_cache [dict create]
 proc record {line} {variable fd; puts $fd $line}
 proc clock_for_pin {pin} {
  variable clock_cache
  if {[dict exists $clock_cache $pin]} {return [dict get $clock_cache $pin]}
  set clocks [get_clocks -quiet -of_objects $pin]
  if {[llength $clocks]!=1} {error "AI_READ_CLOCK_PIN_NOT_CLOCKED_ONCE $pin clocks=$clocks"}
  set result [list [get_property NAME $clocks] [get_property PERIOD $clocks]]
  dict set clock_cache $pin $result
  return $result
 }
 proc fd_prefix {prefix} {
  return [get_cells -quiet -hier -filter "NAME =~ $prefix/* && REF_NAME =~ FD*"]
 }
 proc fd_regex {pattern} {
  # Vivado -regexp also changes the filter matcher; FD* would not mean a
  # glob prefix here. Exact register-name regex selects; owner type is below.
  return [get_cells -quiet -hier -regexp $pattern]
 }
 proc ff_group {label cells minimum expected_period expected_clock} {
  variable fd
  if {[llength $cells]<$minimum} {error "AI_READ_CLOCK_GROUP_MISSING $label cells=[llength $cells] minimum=$minimum"}
  set pins [get_pins -quiet -of_objects $cells -filter {REF_PIN_NAME == C}]
  if {[llength $pins]!=[llength $cells]} {error "AI_READ_CLOCK_GROUP_C_PIN_MISSING $label cells=[llength $cells] pins=[llength $pins]"}
  set names [get_property NAME $pins]
  if {[llength [lsort -unique $names]]!=[llength $pins]} {error "AI_READ_CLOCK_GROUP_DUPLICATE_PIN $label"}
  record "GROUP|$label|kind=FF_C|cells=[llength $cells]|pins=[llength $pins]"
  set group_clock $expected_clock
  foreach pin $pins {
   lassign [clock_for_pin $pin] actual_clock period
   if {abs($period-$expected_period)>0.001} {error "AI_READ_CLOCK_PERIOD_WRONG $label pin=$pin period=$period"}
   if {$group_clock eq ""} {set group_clock $actual_clock}
   if {$actual_clock ne $group_clock} {error "AI_READ_CLOCK_OBJECT_DIFFERENT $label pin=$pin actual=$actual_clock expected=$group_clock"}
   set owner [get_cells -quiet -of_objects $pin]
   if {[llength $owner]!=1} {error "AI_READ_CLOCK_PIN_OWNER_NOT_UNIQUE $pin"}
   if {![string match FD* [get_property REF_NAME $owner]]} {error "AI_READ_CLOCK_PIN_OWNER_NOT_FF $pin owner=$owner"}
   record "CLOCK_PIN|$label|pin=[get_property NAME $pin]|ref=[get_property REF_NAME $owner]|clock=$actual_clock|period_ns=$period"
  }
  record "COVERAGE|$label|enumerated_cells=[llength $cells]|queried_pins=[llength $pins]|unique_pins=[llength $pins]|clocked_pins=[llength $pins]|unclocked_pins=0|multi_clock_pins=0|wrong_clock_pins=0"
  record "CLOCK|$label|pins=[llength $pins]|clock=$group_clock|period_ns=$expected_period"
  flush $fd
  return $group_clock
 }
 proc ps7_group {prefix} {
  variable source_clock
  set cells [get_cells -quiet -hier -filter "REF_NAME == PS7 && NAME =~ $prefix/*"]
  if {[llength $cells]!=1} {error "AI_READ_CLOCK_PS7_PRIMITIVE_NOT_UNIQUE count=[llength $cells]"}
  set pins [get_pins -quiet -of_objects $cells -filter {REF_PIN_NAME == SAXIHP2ACLK}]
  if {[llength $pins]!=1} {error "AI_READ_CLOCK_PS7_SAXIHP2ACLK_MISSING"}
  lassign [clock_for_pin $pins] actual_clock period
  if {$actual_clock ne $source_clock || abs($period-5.000)>0.001} {error "AI_READ_CLOCK_PS7_CLOCK_OBJECT_OR_PERIOD_WRONG $actual_clock $period"}
  record "GROUP|PS7_SAXIHP2ACLK|kind=PS7|cells=1|pins=1"
  record "CLOCK_PIN|PS7_SAXIHP2ACLK|pin=[get_property NAME $pins]|ref=PS7|clock=$actual_clock|period_ns=$period"
  record "COVERAGE|PS7_SAXIHP2ACLK|enumerated_cells=1|queried_pins=1|unique_pins=1|clocked_pins=1|unclocked_pins=0|multi_clock_pins=0|wrong_clock_pins=0"
  record "CLOCK|PS7_SAXIHP2ACLK|pins=1|clock=$actual_clock|period_ns=$period"
  return $pins
 }
 proc reset_detail {label pins} {
  # Keep distinct reset chain evidence, without asserting reset equivalence.
  set nets [get_nets -quiet -segments -of_objects $pins]
  set drivers [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}]
  record "RESET_DETAIL|$label|pins=$pins|nets=$nets|drivers=$drivers|not_equivalence_checked"
 }
 proc run {} {
  variable source_clock
  variable csr_clock
  set base U0_ps_ai_peripheral
  set mon $base/ai_read_path_monitor
  set ps $base/ps_ai_wrapper_u0/ps_ai_i
  set hc $base/ZGolo/u_AI_Mate_top/U0_ddr2hp_itcn
  # Collect whole actual sequential groups, then inspect every member C pin.
  set source [fd_regex {^U0_ps_ai_peripheral/ai_read_path_monitor/source_snapshot_reg\[[0-9]+\]$}]
  set capture [fd_regex {^U0_ps_ai_peripheral/ai_read_path_monitor/csr_snapshot_reg\[[0-9]+\]$}]
  set live [get_cells -quiet -hier -filter "NAME =~ $mon/live_words_reg* && REF_NAME =~ FD*"]
  set controls [fd_regex {^U0_ps_ai_peripheral/ai_read_path_monitor/(source_release_reg.*|arm_request_sync_reg.*|freeze_request_sync_reg.*|arm_ack_toggle_reg.*|freeze_ack_toggle_reg.*|source_active_reg.*)$}]
  set groups {}
  for {set lane 0} {$lane<4} {incr lane} {
   lappend groups [list HC${lane}_mna_converter [fd_prefix $hc/U${lane}_mna_to_axi_burst]]
   lappend groups [list HC${lane}_narrow_to_wide [fd_prefix $hc/U${lane}_n2w_bwc_r]]
  }
  lappend groups [list HC_round_robin [fd_prefix $hc/U0_dmux4]]
  lappend groups [list HC1_internal_join [fd_prefix $base/ZGolo/u_AI_Mate_top/u_axi_2to1]]
  foreach name {s00 s01 m00} {
   lappend groups [list HP2_${name}_coupler [fd_prefix $ps/axi_interconnect_4/${name}_couplers]]
  }
  lappend groups [list HP2_crossbar [fd_prefix $ps/axi_interconnect_4/xbar]]
  set reset_cells [fd_prefix $ps/proc_sys_reset_1]
  lappend groups [list HP2_reset_controller $reset_cells]
  lappend groups [list HDMI_AXI_reader [fd_prefix $base/hdmi_display/scanout/core/core/reader]]
  set source_clock [ff_group source_snapshot $source 1024 5.000 ""]
  set csr_clock [ff_group csr_snapshot $capture 1024 10.000 ""]
  if {$source_clock eq $csr_clock} {error "AI_READ_CLOCK_CSR_SOURCE_NOT_DISTINCT"}
  ff_group live_counter_registers $live 1024 5.000 $source_clock
  ff_group monitor_source_control $controls 10 5.000 $source_clock
  foreach item $groups {lassign $item label cells; ff_group $label $cells 1 5.000 $source_clock}
  set ps7_clock_pin [ps7_group $ps/processing_system7_0]
  # Actual MIG UI clock net is in the discovery's full source/PS7 net segments.
  # Check shared connectivity as additional provenance, not frequency equality.
  set source_pin [lindex [get_pins -quiet -of_objects $source -filter {REF_PIN_NAME == C}] 0]
  set source_nets [get_nets -quiet -segments -of_objects $source_pin]
  set ps7_nets [get_nets -quiet -segments -of_objects $ps7_clock_pin]
  set mig_net $base/mig_ddr3_u0/u_mig_7series_0_mig/u_ddr3_infrastructure/CLK
  if {[llength [get_nets -quiet $mig_net]]!=1} {error "AI_READ_CLOCK_MIG_UI_NET_MISSING"}
  set source_names [lsort -unique [get_property NAME $source_nets]]
  set ps7_names [lsort -unique [get_property NAME $ps7_nets]]
  if {$source_names ne $ps7_names || [lsearch -exact $source_names $mig_net]<0} {error "AI_READ_CLOCK_SOURCE_PS7_MIG_NET_SEGMENTS_DIFFER"}
  foreach net $source_names {record "SOURCE_NET_SEGMENT|net=$net"}
  record "SOURCE_NET_SHARED|source_snapshot_C=$source_pin|PS7_HP2_C=$ps7_clock_pin|same_segment_count=[llength $source_names]|MIG_UI_net=$mig_net"
  foreach {label pattern} [list observer_source_release $mon/source_release_reg* observer_csr_release $mon/csr_release_reg*] {
   set cells [get_cells -quiet -hier -filter "NAME =~ $pattern && REF_NAME =~ FD*"]
   reset_detail $label [get_pins -quiet -of_objects $cells -filter {REF_PIN_NAME == CLR}]
  }
  reset_detail HP2_controller_register_reset_inputs [get_pins -quiet -of_objects $reset_cells -filter {REF_PIN_NAME == CLR || REF_PIN_NAME == PRE || REF_PIN_NAME == R || REF_PIN_NAME == S}]
  record "RESET_CHAIN_NOTE|HC hp0_clk_rst, PS proc_sys_reset_1 peripheral_aresetn and observer release chains are distinct; no reset-equivalence assertion"
  record "EXCLUDED_CONSTANT_PORTS|internal ddr2hp_itcn.S0..3_AXI_HP_ACLK are not used as clock evidence"
  record "OPTIMIZED_PORTS_NOTE|monitor source_clk/exported_HP2_clk and HDL ACLK hierarchy ports are replaced by complete actual FF C groups plus unique real PS7 SAXIHP2ACLK; missing actual groups still fail"
  record "AI_READ_CLOCK_REVIEW_PASS|same_source_clock=$source_clock|source_period=5.000|csr_clock=$csr_clock|csr_period=10.000|every_group_pin_clock_checked|no_constraints_or_design_mutations"
 }
}
set ::ai_read_clock_review::fd [open $::ai_read_clock_report {WRONLY CREAT EXCL}]
if {[catch {::ai_read_clock_review::run} ai_read_clock_error ai_read_clock_options]} {
 ::ai_read_clock_review::record "AI_READ_CLOCK_REVIEW_FAILED|$ai_read_clock_error"
 close $::ai_read_clock_review::fd
 return -options $ai_read_clock_options $ai_read_clock_error
}
close $::ai_read_clock_review::fd
puts "AI_READ_CLOCK_REVIEW_PASS report=$::ai_read_clock_report"

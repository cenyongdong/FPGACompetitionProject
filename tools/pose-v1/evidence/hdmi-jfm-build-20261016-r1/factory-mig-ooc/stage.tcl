
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 create_ip_run [get_ips mig_7series_0]
 set r [get_runs mig_7series_0_synth_1]
 if {[get_property STEPS.SYNTH_DESIGN.TCL.PRE $r] ne ""} {error "Unexpected IP pre-hook"}
 launch_runs $r -jobs 1
 wait_on_run $r
 puts "ACTUAL_MIG_STATUS [get_property STATUS $r]"
 if {![string match {*Complete*} [get_property STATUS $r]]} {error "MIG OOC did not complete"}
 close_project
 puts "FACTORY_MIG_PREREQUISITE_COMPLETE"
} result]} {puts "FACTORY_MIG_FAILED $result";puts $::errorInfo;exit 1}
exit

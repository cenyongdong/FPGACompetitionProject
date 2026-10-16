
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 set ip [get_ips mig_7series_0]
 if {[get_property IS_LOCKED $ip]} {error "MIG unexpectedly locked"}
 generate_target synthesis $ip
 create_ip_run $ip
 set run [get_runs mig_7series_0_synth_1]
 if {[get_property STEPS.SYNTH_DESIGN.TCL.PRE $run] ne ""} {error "Unexpected IP synthesis pre-hook; do not execute"}
 launch_runs $run -jobs 1
 wait_on_run $run
 puts "MIG_RUN_STATUS [get_property STATUS $run]"
 puts "MIG_RUN_PROGRESS [get_property PROGRESS $run]"
 if {![string match {*Complete*} [get_property STATUS $run]]} {error "MIG OOC synthesis did not complete"}
 set d [get_property DIRECTORY $run]
 set files [glob -nocomplain $d/*.dcp]
 if {[llength $files]!=1} {error "Expected one actual MIG OOC checkpoint"}
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/mig-ooc/checkpoint-path.txt} w];puts $f [lindex $files 0];close $f
 close_project
 puts "MIG_SAME_CONFIGURATION_OOC_COMPLETE"
} result]} {puts "MIG_OOC_FAILED $result";exit 1}
exit

if {[catch {
set_param general.maxThreads 2
open_checkpoint {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/opt-r8.dcp}
read_checkpoint -incremental {D:/FPGACompetitionProject/.local/hdmi-boot-witness-20261019-r23/reference/fpai_demo_vivado.runs/impl_hp2ready_r24/ai7030_edif_top_routed.dcp}
place_design -directive ExtraNetDelay_high
write_checkpoint -force {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/placed-r8.dcp}
phys_opt_design -directive AggressiveExplore
write_checkpoint -force {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/physopt-r8.dcp}
route_design -directive NoTimingRelaxation
source {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/sources/implementation_route_post.tcl}
write_checkpoint -force {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/routed-r8.dcp}

} result]} {puts $result;puts $::errorInfo;exit 1}
exit

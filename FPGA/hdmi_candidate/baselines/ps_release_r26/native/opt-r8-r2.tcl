if {[catch {
set_param general.maxThreads 2
open_checkpoint {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/linked-r8.dcp}
source {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/sources/pre-opt.tcl}
opt_design
source {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/sources/implementation_opt_post.tcl}
write_checkpoint -force {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/opt-r8.dcp}

} result]} {puts $result;puts $::errorInfo;exit 1}
exit

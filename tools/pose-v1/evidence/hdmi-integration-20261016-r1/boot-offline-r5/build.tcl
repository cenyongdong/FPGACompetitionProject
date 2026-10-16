if {[catch {
 create_boot_image {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/boot-offline-r5/candidate.bif} {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/boot-offline-r5/BOOT-hdmi-r5.bin} -fmql
 puts "HDMI_OFFLINE_BOOT_COMMAND_RETURNED"
} result]} {puts "HDMI_OFFLINE_BOOT_FAILED $result";exit 1}
exit

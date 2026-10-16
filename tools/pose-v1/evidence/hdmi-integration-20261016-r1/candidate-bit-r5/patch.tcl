
if {[catch {
 set_device JFMQL30TAI676H
 increment_bit_cfg_v3 {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/candidate-bit-r5/hdmi-integrated-r5.bit} {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/candidate-bit-r5/hdmi-integrated-r5_disable_icap.bit} -disable_icap
 puts "HDMI_PROCISE_ICAP_RETURNED"
} result]} {puts "HDMI_ICAP_FAILED $result";exit 1}
exit

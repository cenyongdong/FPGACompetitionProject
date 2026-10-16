
if {[catch {
 set_device JFMQL30TAI676H
 increment_bit_cfg_v3 {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/factory-bit-icap/factory-input.bit} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/factory-bit-icap/factory-input_disable_icap.bit} -disable_icap
 puts "FACTORY_BIT_ICAP_COMMAND_RETURNED"
} result]} {puts "FACTORY_BIT_ICAP_FAILED $result";exit 1}
exit

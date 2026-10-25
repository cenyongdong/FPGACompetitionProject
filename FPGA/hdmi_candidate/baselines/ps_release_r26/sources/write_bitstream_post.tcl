set ::env(JFM_PATH) {D:/FPGACompetitionProject/.local/hdmi-boot-witness-20261019-r23/reference}
set run_tcl_path [file join $::env(JFM_PATH) "ip_patch" "run.tcl"]
source $run_tcl_path
post_write_bitstream_patch -xfft_modify FALSE -change_speed FALSE -disable_icap TRUE -device 0

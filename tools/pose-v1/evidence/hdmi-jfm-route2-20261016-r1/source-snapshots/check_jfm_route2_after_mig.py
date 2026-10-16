"""Recheck original factory prerequisites after same-configuration MIG OOC.
No hook registration, IP generation, implementation, bit patch or install writes.
"""
import vivado2018_support as s
import shutil
R=s.R; E=R/'tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1'; W=R/'.local/hdmi-jfm-route2-20261016-r1'
s.E=E;s.W=W;ref=W/'reference'
tcl=r'''
if {[catch {
 open_project {REFROOT/fpai_demo_vivado.xpr}
 package require md5
 rename exec audit_exec
 proc exec args {error "NO_EXTERNAL_EXEC_ALLOWED"}
 foreach cmd {set_property upgrade_ip upgrade_bd_cells generate_target synth_design launch_runs write_bitstream} {
  if {[llength [info commands $cmd]]} {rename $cmd audit_$cmd;proc $cmd args {error "READ_ONLY_PRECHECK"}}
 }
 source {REFROOT/ip_patch/all_src_files.tcl}
 set status [catch {pre_patch_check} result]
 set f [open {@@OUT@@/precheck.txt} w]
 puts $f "PRECHECK_STATUS $status";puts $f "PRECHECK_RESULT $result";close $f
 if {$status} {error $result}
 close_project
 puts "FACTORY_PRECHECK_AFTER_MIG_PASS"
} result]} {puts "FACTORY_PRECHECK_FAILED $result";exit 1}
exit
'''.replace('REFROOT',ref.as_posix())
out,work=s.stage('precheck-after-mig',tcl,budget=180,env_extra={'JFM_PATH':str(ref)})
run=ref/'fpai_demo_vivado.runs/mig_7series_0_synth_1'
dest=E/'mig-ooc/run-products';dest.mkdir(exist_ok=False)
for p in run.iterdir():
 if p.is_file() and p.suffix.lower() in {'.log','.rpt','.vds','.tcl','.sh','.bat','.xml'}:
  shutil.copyfile(p,dest/p.name)
s.dump(out/'review.json',{'original_pre_patch_check_pass':True,'same_configuration_MIG_OOC_only':True,
 'all_IPs_synthesized':False,'top_implementation_or_bit_patch_executed':False})

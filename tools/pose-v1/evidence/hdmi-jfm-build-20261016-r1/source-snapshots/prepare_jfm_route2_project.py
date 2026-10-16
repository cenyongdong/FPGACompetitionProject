"""Restore exact original 2018.3 inputs in an isolated project, query only.
No hooks, IP revision upgrades, global library changes or bitstream generation.
"""
import vivado2018_support as s
import json,shutil
R=s.R;E=R/'tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1';W=R/'.local/hdmi-jfm-route2-20261016-r1';s.E=E;s.W=W
source=R/'Docs/26嵌赛开发/fpai_demo_fpga';ref=W/'reference'
identity=json.loads((R/'tools/pose-v1/evidence/hdmi-system-20261015-r1/original-manifest.json').read_text(encoding='utf-8'))
for n,h in identity.items():assert s.sha(source/n)==h,n
shutil.copytree(source,ref)
for n,h in identity.items():assert s.sha(ref/n)==h,n
s.dump(E/'restored-reference-identity.json',{'files':len(identity),'all_match':True,'original_manifest':'../hdmi-system-20261015-r1/original-manifest.json','directory':str(ref),'IP_upgraded':False})
tcl='''
if {[catch {
 open_project {REF/fpai_demo_vivado.xpr}
 set_property ip_repo_paths [list {REF/PS_AI IP}] [current_project]
 set_property ip_cache_permissions {} [current_project]
 update_ip_catalog
 report_ip_status -file {@@OUT@@/IP-status.rpt}
 set f [open {@@OUT@@/IP-properties.txt} w]
 foreach ip [get_ips -all] {
  puts $f "IP $ip"
  foreach p {IPDEF IS_LOCKED IP_FILE GENERATE_SYNTH_CHECKPOINT CORE_REVISION} {
   if {[lsearch -exact [list_property $ip] $p]>=0} {puts $f "$p|[get_property $p $ip]"}
  }
 }
 close $f
 puts "ORIGINAL_2018_IP_COUNT [llength [get_ips -all]]"
 puts "ORIGINAL_2018_IP_LOCKED [get_ips -all -filter {IS_LOCKED == 1}]"
 close_project
 puts "ORIGINAL_PROJECT_STATUS_COMPLETE"
} result]} {puts "ORIGINAL_PROJECT_STATUS_FAILED $result";exit 1}
exit
'''.replace('REF',ref.as_posix())
s.stage('project-status',tcl,budget=180)

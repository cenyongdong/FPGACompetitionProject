"""Explicitly authorized in-place original 030ai patch with exact write allowlist."""
import vivado2018_support as s
from pathlib import Path
import json
R=s.R;E=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2';W=R/'.local/hdmi-vivado2018-20261016-r2'
s.E=E;s.W=W
backup=json.loads((E/'backup-manifest.json').read_text(encoding='utf-8'))
for item in backup['targets']:
 p=s.INSTALLED/item['relative']
 if 'sha256' in item:
  assert s.sha(p)==item['sha256'] and s.sha(E/'backup'/item['relative'])==item['sha256']
 elif not item['exists']:assert not p.exists()
allowed=[(s.INSTALLED/i['relative']).as_posix() for i in backup['targets'] if not i['is_directory']]
local=W/'kit/ip_patch'
old=json.loads((R/'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/replacement-review.json').read_text(encoding='utf-8'))
for pair in old['replacement_pairs']:assert s.sha(local/'030ai'/Path(pair['patch']['path']).name)==pair['patch']['sha256']
tcl='''
package require md5
set audit_log [open {@@OUT@@/mutations.txt} w]
set audit_allowed [list ALLOWED]
set audit_local {LOCALROOT}
rename file audit_orig_file
proc audit_key p {return [string tolower [audit_orig_file normalize $p]]}
proc file {sub args} {
 if {$sub eq "copy"} {
  set src [lindex $args end-1];set dst [lindex $args end]
  if {[lsearch -exact $::audit_allowed [audit_key $dst]]<0} {error "WRITE_GUARD target $dst"}
  if {[string first [audit_key $::audit_local] [audit_key $src]]!=0} {error "WRITE_GUARD source $src"}
  puts $::audit_log [list COPY $src $dst];flush $::audit_log
 } elseif {$sub eq "delete"} {
  if {[llength $args]!=2 || [lindex $args 0] ne "-force" || [audit_key [lindex $args 1]] ne [audit_key {ROOT/data/parts/xilinx/zynq/devint/zynq.rtd.bak}]} {error "WRITE_GUARD delete $args"}
  puts $::audit_log [list DELETE [lindex $args 1]];flush $::audit_log
 } elseif {[lsearch -exact {rename mkdir attributes mtime atime link} $sub]>=0} {error "WRITE_GUARD file $sub $args"}
 return [eval [linsert $args 0 audit_orig_file $sub]]
}
rename open audit_orig_open
proc open {path args} {
 set mode r
 if {[llength $args]>0} {set mode [lindex $args 0]}
 if {$mode ne "r" && $mode ne "rb"} {error "WRITE_GUARD direct open $path $mode"}
 return [eval [linsert $args 0 audit_orig_open $path]]
}
foreach cmd {exec load create_project open_project set_property set_param} {
 if {[llength [info commands $cmd]]} {rename $cmd audit_original_$cmd;proc $cmd args {error "WRITE_GUARD external or configuration command"}}
}
if {[catch {
 source {LOCALROOT/all_src_files.tcl}
 if {[version -short] ne "2018.3"} {error "Wrong Vivado version"}
 if {[audit_key [get_vvd_path]] ne [audit_key {ROOT}]} {error "Wrong tool installation root"}
 if {![file exists {ROOT/data/parts/xilinx/common/unisim.btl}]} {error "Require actual 2018.3 reset branch"}
 puts "ACTUAL_PATCH_ROOT [get_vvd_path]"
 replace_7z030ai_file 0
 puts "INPLACE_ORIGINAL_030AI_PATCH_COMPLETE"
} result]} {puts "INPLACE_PATCH_FAILED $result";puts $audit_log "FAILED $result";close $audit_log;exit 1}
close $audit_log
exit
'''.replace('ALLOWED',' '.join('{'+p.lower()+'}' for p in allowed)).replace('LOCALROOT',local.as_posix()).replace('ROOT',s.INSTALLED.as_posix())
s.stage('inplace-patch',tcl,budget=180,env_extra={'JFM_PATH':str(local.parent)})
after=[]
for pair in old['replacement_pairs']:
 rel=Path(pair['installed_target']['path']).relative_to(Path('D:/Xilinx/Vivado/2019.1'))
 p=s.INSTALLED/rel;h=s.sha(p)
 after.append({'relative':rel.as_posix(),'actual_sha256':h,'patch_sha256':pair['patch']['sha256'],'equal':h==pair['patch']['sha256']})
 assert h==pair['patch']['sha256'],str(p)
diff=[]
for item in backup['targets']:
 p=s.INSTALLED/item['relative']
 if 'sha256' in item:
  h=s.sha(p)
  if h!=item['sha256']:diff.append({'relative':item['relative'],'before':item['sha256'],'after':h})
s.dump(E/'patch-review.json',{'all_nine_equal_vendor_patch':True,'targets':after,
 'changed_backed_up_files':diff,'backup_files':34,'backup_bytes':backup['bytes_copied'],
 'full_tool_copy':False,'inplace':True,'version_check_preserved':True,'speed':0,
 'PS_Procise_or_HDMI_pass':False})
print(json.dumps({'nine_targets_match':True,'changed_files':len(diff),'backup_bytes':backup['bytes_copied']}),flush=True)

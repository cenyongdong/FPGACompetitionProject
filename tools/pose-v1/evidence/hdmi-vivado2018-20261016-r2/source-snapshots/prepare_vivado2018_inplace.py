"""Back up exact potential file targets, then inspect original vendor procedures.
No installation writes, patch execution or full tool copy in this preparation.
"""
import vivado2018_support as s
from pathlib import Path
import json,shutil
R=s.R;E=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2';W=R/'.local/hdmi-vivado2018-20261016-r2'
s.E=E;s.W=W
root=s.INSTALLED
prior=json.loads((R/'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/replacement-review.json').read_text(encoding='utf-8'))
paths=set(prior['reset_helper_target_paths_static'])
paths.update(Path(p['installed_target']['path']).relative_to(Path('D:/Xilinx/Vivado/2019.1')).as_posix() for p in prior['replacement_pairs'])
backup=E/'backup';backup.mkdir(exist_ok=False);entries=[]
for rel in sorted(paths):
 src=root/rel
 item={'relative':rel,'exists':src.exists(),'is_directory':src.is_dir()}
 if src.is_file():
  dst=backup/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
  item.update(bytes=src.stat().st_size,sha256=s.sha(src),backup_sha256=s.sha(dst))
  assert item['sha256']==item['backup_sha256']
 entries.append(item)
s.dump(E/'backup-manifest.json',{'root':str(root),'targets':entries,'full_tool_copy':False,
 'directory_entries_not_recursively_copied':'2018.3 branch only copies listed files; 2022.1 directory deletion branch is unreachable',
 'bytes_copied':sum(x.get('bytes',0) for x in entries)})
kit=R/'Docs/26嵌赛开发/JFM_Kits/JFM_Kits/ip_patch'
local=W/'kit/ip_patch';local.mkdir(parents=True,exist_ok=False)
for n in ('all_src_files.tcl','ip_patch.cfg','ip_patch_version.log'):
 shutil.copyfile(kit/n,local/n);assert s.sha(kit/n)==s.sha(local/n)
for n in ('030ai','database_ori/2018.3'):
 shutil.copytree(kit/n,local/n)
source=local/'all_src_files.tcl'
tcl='''
package require md5
set f [open {@@OUT@@/procedures.txt} w]
rename open audit_orig_open
proc open {path args} {
 set mode r
 if {[llength $args]>0} {set mode [lindex $args 0]}
 if {$mode ne "r" && $mode ne "rb"} {error "READ_ONLY_OPEN $path $mode"}
 return [eval [linsert $args 0 audit_orig_open $path]]
}
rename file audit_orig_file
proc file {sub args} {
 if {[lsearch -exact {copy delete rename mkdir attributes mtime atime link} $sub]>=0} {error "READ_ONLY_FILE $sub $args"}
 return [eval [linsert $args 0 audit_orig_file $sub]]
}
foreach cmd {exec load create_project open_project set_property set_param} {
 if {[llength [info commands $cmd]]} {rename $cmd audit_original_$cmd;proc $cmd args {error "READ_ONLY_COMMAND"}}
}
if {[catch {
 source {SOURCE}
 foreach name {get_vvd_path check_current_platform reset_database_to_default replace_7z030ai_file} {
  puts $f "PROCEDURE $name"
  if {[llength [info procs $name]]} {puts $f [info body $name]}
 }
 puts "PROCEDURE_METADATA_COMPLETE"
} result]} {puts $f "FAILED $result";close $f;exit 1}
close $f
exit
'''.replace('SOURCE',source.as_posix())
s.stage('vendor-procedures',tcl,budget=180,env_extra={'JFM_PATH':str(local.parent)})
print(json.dumps({'backed_up_files':sum('sha256' in x for x in entries),'bytes':sum(x.get('bytes',0) for x in entries),'full_tool_copy':False}),flush=True)

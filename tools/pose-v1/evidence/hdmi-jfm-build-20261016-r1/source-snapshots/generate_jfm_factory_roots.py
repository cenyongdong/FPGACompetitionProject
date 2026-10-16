"""Generate original root XCI/BD via their owners after nested-IP API diagnosis."""
import jfm_build_support as s
import xml.etree.ElementTree as ET,json
root=s.R/'Docs/26嵌赛开发/fpai_demo_fpga';ref=s.W/'reference'
files=[]
for f in ET.parse(root/'fpai_demo_vivado.xpr').findall('.//FileSet[@Name="sources_1"]/File'):
 p=f.attrib['Path'].replace('$PPRDIR',ref.as_posix()).replace('$PSRCDIR',(ref/'fpai_demo_vivado.srcs').as_posix())
 if p.endswith(('.xci','.bd')):files.append(p)
assert files and sum(p.endswith('.bd') for p in files)==1
s.dump(s.E/'generation-owner-list.json',files)
tcl=r'''
if {[catch {
 open_project {@@REF@@/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 foreach name [list @@FILES@@] {
  set owner [get_files -all -quiet $name]
  if {[llength $owner]!=1} {error "Expected exact root owner $name"}
  puts "GENERATE_ORIGINAL_ROOT_OWNER $name"
  generate_target all $owner
 }
 close_project
 puts "ORIGINAL_ROOT_OWNED_GENERATION_COMPLETE"
} result]} {puts "ROOT_GENERATION_FAILED $result";puts $::errorInfo;exit 1}
exit
'''.replace('@@FILES@@',' '.join('{'+p+'}' for p in files))
s.stage('generate-root-owners',tcl)

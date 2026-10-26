"""Prepare the existing factory bit-generation route for the new checkpoint."""
from pathlib import Path
from prepare import ROOT, WORK, EVIDENCE, OLD, OLD_E, remap, put

text = remap((OLD_E / 'bit.tcl').read_text()).replace('impl_deferred_consume_r45', 'impl_probe_free_r1')
begin = text.index('# Constraints are already')
end = text.index('source {', text.index('set witness ', begin))
text = text[:begin] + '''# Physical qualification is recorded separately; preserve the routed context.
foreach mode {max min} {
 set path [get_timing_paths -delay_type $mode -max_paths 1]
 if {![llength $path] || [get_property SLACK $path]<0} {error "Physical setup/hold failed"}
}
set expected_design [current_design]
set expected_project [current_project]
''' + text[end:]
put(EVIDENCE / 'bit.tcl', text)
for name in ('call_procise_disable_icap.bat', 'procise_run_disable_icap.tcl'):
    text = remap((OLD / name).read_text()).replace('impl_deferred_consume_r45', 'impl_probe_free_r1')
    put(WORK / name, text)
print('Prepared factory bit hooks and explicit Procise ICAP packaging inputs')

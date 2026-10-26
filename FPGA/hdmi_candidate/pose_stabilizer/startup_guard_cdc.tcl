# New crossings only. No false paths, clock groups, DRC waivers, or period changes.
# Apply after integration; check all objects exist before accepting constraints.
proc pose_cut {from_glob to_glob max_ns skew_ns} {
 set src [get_cells -hier -regexp $from_glob]
 set dst [get_cells -hier -regexp $to_glob]
 if {![llength $src] || ![llength $dst]} {error "Missing pose guard CDC endpoints: $from_glob -> $to_glob"}
 set_max_delay -datapath_only $max_ns -from $src -to $dst
 set_bus_skew $skew_ns -from $src -to $dst
}
pose_cut {.*lean_guard/csr/request_reg} {.*lean_guard/csr/rq_reg\[0\]} 5 5
pose_cut {.*lean_guard/csr/ack_reg} {.*lean_guard/csr/ak_reg\[0\]} 20 20
pose_cut {.*lean_guard/csr/held_command_reg.*} {.*lean_guard/guard/.*} 5 5
pose_cut {.*lean_guard/csr/held_snapshot_reg.*} {.*lean_guard/csr/snapshot_reg.*} 20 20

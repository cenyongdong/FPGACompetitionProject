# Bundled commands/replies are held until a two-stage toggle ACK. Add explicit
# data bounds without cutting clocks or making a false path.
set dcroot {^U0_ps_ai_peripheral/deferred_control/}
set dcmeta [get_cells -hier -regexp [format {%s(request_sync|ack_sync)_reg\[0\]$} $dcroot]]
if {[llength $dcmeta]!=2} {error "Deferred control toggle CDC missing"}
set dcends [get_pins -of_objects $dcmeta -filter {REF_PIN_NAME == D}]
set_max_delay -datapath_only 5.000 -from [all_fanin -flat -startpoints_only -to $dcends] -to $dcends
set dcreply [get_cells -hier -regexp [format {%scsr_(status|pc|cycle|arm_cycle|flags)_reg\[[0-9]+\]$} $dcroot]]
set dcsrc [get_cells -hier -regexp [format {%sheld_(status|pc|cycle|arm_cycle|flags)_reg\[[0-9]+\]$} $dcroot]]
if {![llength $dcreply] || ![llength $dcsrc]} {error "Deferred control held reply missing"}
set_max_delay -datapath_only 10.000 -from [get_pins -of_objects $dcsrc -filter {REF_PIN_NAME == C}] -to [get_pins -of_objects $dcreply -filter {REF_PIN_NAME == D}]
set dccmd [get_cells -hier -regexp [format {%sheld_command_reg\[[0-9]+\]$} $dcroot]]
set dcfeed [all_fanout -flat -endpoints_only -from [get_pins -of_objects $dccmd -filter {REF_PIN_NAME == Q}]]
set dcfeed [filter $dcfeed {REF_PIN_NAME == D || REF_PIN_NAME == CE}]
if {![llength $dccmd] || ![llength $dcfeed]} {error "Deferred command bundle missing"}
set_max_delay -datapath_only 5.000 -from [get_pins -of_objects $dccmd -filter {REF_PIN_NAME == C}] -to $dcfeed
puts "DEFERRED_CDC toggle=[llength $dcmeta] reply=[llength $dcreply] command=[llength $dcfeed]"

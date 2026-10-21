"""Adapt the already approved native r24 implementation, using isolated inputs."""
from prepare_ps_release_candidate import R,REF,W,E,S,wrap
import argparse
from pathlib import Path


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--attempt',type=int,default=2);cli.add_argument('--from-linked',action='store_true')
    cli.add_argument('--synthesis',type=Path,default=W/'synth-r2.dcp')
    cli.add_argument('--reference',type=Path,default=REF/'fpai_demo_vivado.runs/impl_hp2ready_r24/ai7030_edif_top_routed.dcp')
    args=cli.parse_args()
    hooks=REF/'ip_patch/process_control'
    for name in ('implementation_opt_pre.tcl','implementation_opt_post.tcl','implementation_route_post.tcl'):
        t=(hooks/name).read_text().replace('[file join [pwd] "../.."]','{'+REF.as_posix()+'}')
        t=t.replace('set prj_path [get_prj_path]','set prj_path {'+(REF/'fpai_demo_vivado.xpr').as_posix()+'}')
        (S/name).write_text(t)
    t=(REF/'constrs_1/ai_boot_witness_cdc.tcl').read_text()
    t=t.replace('NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/boot_history*witness/*}',
                'NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/boot_history*witness/* && NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/release_history/*}')
    (S/'ai_boot_witness_cdc.tcl').write_text(t)
    pre=f'source {{{(S/"implementation_opt_pre.tcl").as_posix()}}}\n'
    for name in ('hdmi_cdc.tcl','ai_monitor_cdc.tcl','ai_read_monitor_cdc.tcl'):
        pre+='source {'+(REF/'constrs_1'/name).as_posix()+'}\n'
    pre+='source {'+(S/'ai_boot_witness_cdc.tcl').as_posix()+'}\n'
    pre+='source {'+(R/'FPGA/hdmi_candidate/constraints/ps_release_cdc.tcl').as_posix()+'}\n'
    pre+='source {'+(R/'FPGA/hdmi_candidate/constraints/ps_release_raw_flags_cdc.tcl').as_posix()+'}\n'
    (S/'pre-opt.tcl').write_text(pre)
    native=(REF/'fpai_demo_vivado.runs/impl_hp2ready_r24/ai7030_edif_top.tcl').read_text()
    a=native.index('  create_project -in_memory');b=native.index('  write_hwdef',a)
    setup=native[a:b]
    setup=setup.replace((REF/'fpai_demo_vivado.runs/synth_hp2ready_r24/ai7030_edif_top.dcp').as_posix(),args.synthesis.resolve().as_posix())
    bd=REF/'fpai_demo_vivado.srcs/sources_1/bd/ps_ai'
    ips=[x for x in sorted((bd/'ip').glob('*/*.xci')) if x.parent.name!='ps_ai_processing_system7_0_0']
    setup=setup.replace('  add_files '+(bd/'ps_ai.bd').as_posix(),
                        '\n'.join('  read_ip -quiet {'+p.as_posix()+'}' for p in ips))
    setup+='read_checkpoint -cell U0_ps_ai_peripheral/ps_ai_wrapper_u0/ps_ai_i/processing_system7_0 {'+(W/'ps-export.dcp').as_posix()+'}\n'
    # The generated PS XDC still uses the old PS7_i/FCLKCLK hierarchy, which
    # does not resolve in this adapted wrapper. Bind the same original 50MHz
    # root clock to its actual primitive pin; do not change any clock rate.
    setup+='write_checkpoint -force {'+(W/'linked-unclocked.dcp').as_posix()+'}\n'
    setup+=r'''set ps_primitive [get_cells -hier -filter {REF_NAME == PS7}]
if {[llength $ps_primitive]!=1} {error "Adapted PS7 primitive missing"}
set fclk [get_pins -of_objects $ps_primitive -filter {REF_PIN_NAME == "FCLKCLK[0]"}]
puts "PS_RELEASE_FCLK_BIND primitive=$ps_primitive pin=$fclk"
if {[llength $fclk]!=1} {error "Real PS FCLKCLK0 output is not unique"}
if {![llength [get_clocks -quiet clk_fpga_0]]} {create_clock -name clk_fpga_0 -period 20.000 $fclk}
if {abs([get_property PERIOD [get_clocks clk_fpga_0]]-20)>0.001} {error "Original PS frequency changed"}
set_input_jitter [get_clocks clk_fpga_0] 0.600
'''
    setup+='source {'+(R/'FPGA/hdmi_candidate/constraints/ps_release_factory_clocks.tcl').as_posix()+'}\n'
    setup+='report_clocks -file {'+(E/'linked-clocks.rpt').as_posix()+'}\n'
    setup+='write_checkpoint -force {'+(W/'linked.dcp').as_posix()+'}\n'
    if args.from_linked:setup='open_checkpoint {'+(W/'linked.dcp').as_posix()+'}\n'
    body=setup+'source {'+(S/'pre-opt.tcl').as_posix()+'}\nopt_design\n'
    body+='source {'+(S/'implementation_opt_post.tcl').as_posix()+'}\n'
    body+='write_checkpoint -force {'+(W/'opt.dcp').as_posix()+'}\n'
    body+='read_checkpoint -incremental {'+args.reference.resolve().as_posix()+'}\n'
    body+='place_design -directive ExtraNetDelay_high\nwrite_checkpoint -force {'+(W/'placed.dcp').as_posix()+'}\n'
    body+='phys_opt_design -directive AggressiveExplore\nwrite_checkpoint -force {'+(W/'physopt.dcp').as_posix()+'}\n'
    body+='route_design -directive NoTimingRelaxation\nsource {'+(S/'implementation_route_post.tcl').as_posix()+'}\n'
    body+='write_checkpoint -force {'+(W/'routed.dcp').as_posix()+'}\n'
    for command,name in [('report_timing_summary -report_unconstrained -max_paths 10','timing-final'),
                          ('report_route_status','route-status-final'),('report_drc','drc-final'),
                          ('report_bus_skew','bus-skew-final'),('report_utilization -hierarchical','utilization-final'),
                          ('report_clock_interaction','clock-interaction-final')]:
        body+=command+' -file {'+(E/(name+'.rpt')).as_posix()+'}\n'
    (E/('route-r'+str(args.attempt)+'.tcl')).write_text(wrap(body))
    print('Prepared isolated implementation with unchanged directives and narrower legacy cut.')


if __name__=='__main__':main()

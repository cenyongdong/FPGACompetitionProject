"""Add a passive BRAM cycle recorder to the qualified isolated r28 topology."""
from pathlib import Path
import argparse,hashlib,json,re
from prepare_s01_isolation import block

R=Path(__file__).resolve().parents[3]
B=R/'FPGA/hdmi_candidate/baselines/ps_release_r26/sources'


def once(t,old,new):
    if t.count(old)!=1:raise ValueError('Insertion point is not unique: '+old[:90])
    return t.replace(old,new,1)


def recover_constraints(assets):
    w=assets/'.local/hdmi-hp2-cycletrace-20261022-r30'
    e=assets/'tools/pose-v1/evidence/hdmi-hp2-cycletrace-20261022-r30'
    s=w/'sources';new=w/'sources-r2';new.mkdir()
    def protect(t):
        for op,join in [('!~','&&'),('=~','||')]:
            old='NAME '+op+' U0_ps_ai_peripheral/ai_read_path_monitor/*'
            t=t.replace(old,old+' '+join+' NAME '+op+' U0_ps_ai_peripheral/hp2_cycle_recorder/*')
        old='NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/release_history/*}'
        return t.replace(old,old[:-1]+' && NAME !~ U0_ps_ai_peripheral/hp2_cycle_recorder/*}')
    for name in ('hdmi_cdc.tcl','ai_read_monitor_cdc.tcl','ps_release_cdc.tcl','ps_release_raw_flags_cdc.tcl'):
        (new/name).write_text(protect((s/name).read_text()))
    for name,path in [('ai_boot_witness_cdc.tcl',B/'ai_boot_witness_cdc.tcl'),
                      ('ps_release_factory_clocks.tcl',R/'FPGA/hdmi_candidate/constraints/ps_release_factory_clocks.tcl')]:
        (new/name).write_text(protect(path.read_text()))
    t=(s/'pre-opt.tcl').read_text().replace(s.as_posix(),new.as_posix())
    t=t.replace((B/'ai_boot_witness_cdc.tcl').as_posix(),(new/'ai_boot_witness_cdc.tcl').as_posix())
    (new/'pre-opt.tcl').write_text(t)
    old=(e/'opt.tcl').read_text()
    start=old.index('set ps_primitive ');end=old.index('set x U0_ps_ai_peripheral/ps_ai_wrapper_u0/ps_ai_i/axi_interconnect_4')
    t=old[start:end]
    t=t.replace((R/'FPGA/hdmi_candidate/constraints/ps_release_factory_clocks.tcl').as_posix(),(new/'ps_release_factory_clocks.tcl').as_posix())
    t=t.replace('linked-r8.dcp','linked-r2.dcp').replace('linked-clocks.rpt','linked-clocks-r2.rpt')
    t+='source {'+(new/'pre-opt.tcl').as_posix()+'}\nopt_design\n'
    t+='source {'+(B/'implementation_opt_post.tcl').as_posix()+'}\n'
    t+='write_checkpoint -force {'+(w/'opt-r2.dcp').as_posix()+'}\n'
    t='open_checkpoint {'+(w/'linked-unclocked-r8.dcp').as_posix()+'}\n'+t
    (e/'opt-r2.tcl').write_text('if {[catch {\nset_param general.maxThreads 2\n'+t+'\n} result]} {puts $result;puts $::errorInfo;exit 1}\nexit\n')
    route=(e/'route.tcl').read_text().replace('opt-r8.dcp','opt-r2.dcp')
    (e/'route.tcl').write_text(route)
    overlay=json.loads((e/'source-overlay.json').read_text())
    overlay['additional_constraint_sources']=[str(new/name) for name in
        ('hdmi_cdc.tcl','ai_read_monitor_cdc.tcl','ps_release_cdc.tcl','ps_release_raw_flags_cdc.tcl',
         'ai_boot_witness_cdc.tcl','ps_release_factory_clocks.tcl','pre-opt.tcl')]
    overlay['constraint_recovery']='Reuse identical linked-unclocked checkpoint. Exclude new trace from old aggregate launch/capture cuts before adding unchanged 5/10ns bounds; no per-pin reset_path expansion.'
    (e/'source-overlay.json').write_text(json.dumps(overlay,indent=2)+'\n')
    state=json.loads((e/'state.json').read_text())
    state.update(status='offline_constraint_recovery',active_native_stage='opt-r2',
        prior_opt_exit_preserved=True,reused_synthesis=True,reused_linked_checkpoint=True)
    (e/'state.json').write_text(json.dumps(state,indent=2)+'\n')
    print(json.dumps(dict(prepared=True,stage='opt-r2',RTL_unchanged=True,CDC_bounds_ns=[5,10])))


def main():
    p=argparse.ArgumentParser();p.add_argument('--asset-root',type=Path,required=True)
    p.add_argument('--recover-constraints',action='store_true');a=p.parse_args()
    if a.recover_constraints:return recover_constraints(a.asset_root.resolve())
    assets=a.asset_root.resolve();old=assets/'.local/hdmi-s01-isolation-20261022-r28'
    oe=assets/'tools/pose-v1/evidence/hdmi-s01-isolation-20261022-r28'
    w=old.with_name('hdmi-hp2-cycletrace-20261022-r30');e=oe.with_name('hdmi-hp2-cycletrace-20261022-r30');s=w/'sources'
    if list(e.glob('*-process.json')):raise RuntimeError('Native build already started')
    s.mkdir();(e/'qualified-r8').mkdir()
    q=json.loads((oe/'qualification.json').read_text())
    for path in (old/'sources/ps_ai_peripheral.sv',B/'ps_ai.v',B/'ps_ai_wrapper.sv'):
        if hashlib.sha256(path.read_bytes()).hexdigest()!=q['source_sha256'][str(path)]:
            raise RuntimeError('Qualified baseline changed: '+str(path))
    t=(B/'ps_ai.v').read_text()
    t=once(t,'    diagnostic_ps_awaddr);','    diagnostic_ps_awaddr,\n    diagnostic_hp2_rdata);')
    t=once(t,'  output [127:0] diagnostic_hp2_read;','  output [127:0] diagnostic_hp2_read;\n  output [63:0] diagnostic_hp2_rdata;')
    t=once(t,'  assign diagnostic_hp2_read[31:0]',
           '  assign diagnostic_hp2_rdata = axi_interconnect_4_M00_AXI_RDATA;\n  assign diagnostic_hp2_read[31:0]')
    (s/'ps_ai.v').write_text(t)
    t=(B/'ps_ai_wrapper.sv').read_text()
    t=once(t,'    output [127:0] diagnostic_hp2_read,','    output [127:0] diagnostic_hp2_read,\n    output [63:0] diagnostic_hp2_rdata,')
    t=once(t,'  .diagnostic_hp2_read(diagnostic_hp2_read),','  .diagnostic_hp2_read(diagnostic_hp2_read),\n  .diagnostic_hp2_rdata(diagnostic_hp2_rdata),')
    (s/'ps_ai_wrapper.sv').write_text(t)
    original=(old/'sources/ps_ai_peripheral.sv').read_text();t=original
    t=once(t,'wire [127:0] diagnostic_hp2_read;', 'wire [127:0] diagnostic_hp2_read;\nwire [63:0] diagnostic_hp2_rdata;')
    t=once(t,'.diagnostic_hp2_read(diagnostic_hp2_read),','.diagnostic_hp2_read(diagnostic_hp2_read),\n    .diagnostic_hp2_rdata(diagnostic_hp2_rdata),')
    t=once(t,'.upstream(cam.slave),\n .camera(read_diag_passthrough.master)',
           '.upstream(cycletrace_passthrough.slave),\n .camera(read_diag_passthrough.master)')
    addition='''mna_gp_ww_itf cycletrace_passthrough(),cycletrace_csr();
hdmi_cam_router #(.HDMI_BASE(32'h400b8000),.DECODE_LSB(15)) cycletrace_router(
 .clk(gp_clk),.resetn(~gp_clk_rst),.upstream(cam.slave),
 .camera(cycletrace_passthrough.master),.hdmi(cycletrace_csr.master));
hp2_cycle_trace hp2_cycle_recorder(
 .source_clk(diagnostic_hp2_clk),.csr_clk(gp_clk),.csr_resetn(~gp_clk_rst),
 .ps_read(diagnostic_hp2_read),.s01_read(ai_read_channels[512+:128]),.hc2_read(ai_read_channels[256+:128]),
 .ps_rdata(diagnostic_hp2_rdata),.s01_rdata(S_AXI_HP2_RDATA),.hc2_rdata(S2_AXI_HP_HC_RDATA),
 .flags({7'd0,pl_rst_n,diagnostic_hp2_resetn,hp_clk_rst,ddr_ui_rst,ddr3_init_done,
     soft_rst,sys_rst_n,diagnostic_ps_write[4],diagnostic_ps_write[2],diagnostic_ps_write[0],
     S_AXI_HP2_BVALID,S_AXI_HP2_WVALID,S_AXI_HP2_AWVALID,S_AXI_HP2_RVALID,S_AXI_HP2_ARVALID,
     diagnostic_hp2_read[62],diagnostic_hp2_read[60],1'b0,ddr3_init_done,ddr_ui_rst,
     FCLK_RESET0_N,hp_clk_rst,gp_clk_rst,diagnostic_hp2_resetn,diagnostic_ps_resetn}),
 .csr(cycletrace_csr.slave));
'''
    t=once(t,'// Six-boundary passive',addition+'\n// Six-boundary passive')
    # All functional AI instance pins are byte-identical; PS wrapper differs by
    # the new observational RDATA output only. The 27 zero inputs stay intact.
    if block(t,'AI_Mate ZGolo(','\nendmodule')[2]!=block(original,'AI_Mate ZGolo(','\nendmodule')[2]:raise RuntimeError('AI instance changed')
    new_ps=block(t,'ps_ai_wrapper ps_ai_wrapper_u0 (','AI_Mate ZGolo(')[2].replace('    .diagnostic_hp2_rdata(diagnostic_hp2_rdata),\n','')
    if new_ps!=block(original,'ps_ai_wrapper ps_ai_wrapper_u0 (','AI_Mate ZGolo(')[2]:raise RuntimeError('Functional PS wiring changed')
    (s/'ps_ai_peripheral.sv').write_text(t)
    def remap(t):
        t=t.replace(old.as_posix(),w.as_posix()).replace(oe.as_posix(),e.as_posix())
        t=re.sub(r'D:/FPGACompetitionProject/FPGA/hdmi_candidate',lambda _: (R/'FPGA/hdmi_candidate').as_posix(),t,flags=re.I)
        for name in ('ps_ai.v','ps_ai_wrapper.sv'):
            t=t.replace((B/name).as_posix(),(s/name).as_posix())
        return t
    for name in ('hdmi_cdc.tcl','ai_read_monitor_cdc.tcl','ps_release_cdc.tcl','ps_release_raw_flags_cdc.tcl','pre-opt.tcl'):
        t=remap((old/'sources'/name).read_text())
        if name=='ps_release_cdc.tcl':
            t=once(t,'[string match U0_ps_ai_peripheral/ai_read_path_monitor/release_history/* [get_property NAME $p]] &&',
                   '([string match U0_ps_ai_peripheral/ai_read_path_monitor/release_history/* [get_property NAME $p]] || [string match U0_ps_ai_peripheral/hp2_cycle_recorder/* [get_property NAME $p]]) &&')
        if name=='pre-opt.tcl':t+='\nsource {'+(R/'FPGA/hdmi_candidate/constraints/hp2_cycle_trace_cdc.tcl').as_posix()+'}\n'
        (s/name).write_text(t)
    t=remap((oe/'synthesis.tcl').read_text())
    t=once(t,'read_verilog -library xil_defaultlib -sv {','read_verilog -library xil_defaultlib -sv {\n  '+(R/'FPGA/hdmi_candidate/diagnostics/hp2_cycle_trace.sv').as_posix())
    (e/'synthesis.tcl').write_text(t)
    (e/'opt.tcl').write_text(remap((oe/'opt.tcl').read_text()))
    t=remap((oe/'route.tcl').read_text())
    t=re.sub(r'read_checkpoint -incremental \{[^}]+\}','read_checkpoint -incremental {'+(old/'qualified-routed.dcp').as_posix()+'}',t)
    (e/'route.tcl').write_text(t)
    t=remap((oe/'final.tcl').read_text())
    t=once(t,'close $f\nreport_timing -through $ready',
           'close $f\nset trace_validation_file {'+(e/'qualified-r8/hp2-cycletrace-native-facts.tsv').as_posix()+'}\nsource {'+(R/'FPGA/hdmi_candidate/constraints/hp2_cycle_trace_validate.tcl').as_posix()+'}\nreport_timing -through $ready')
    (e/'final.tcl').write_text(t)
    t=remap((oe/'bit-r3.tcl').read_text()).replace('impl_s01_isolation_r28','impl_hp2_cycletrace_r30')
    (e/'bit.tcl').write_text(t)
    overlay=json.loads((oe/'source-overlay.json').read_text())
    overlay['replacements']={k:remap(v.replace('\\','/')) for k,v in overlay['replacements'].items()}
    overlay['additional_sources']=[str(R/'FPGA/hdmi_candidate/diagnostics/hp2_cycle_trace.sv')]
    overlay['scope']='Passive cycle recorder only; S01 zero sources and AI four HC/functional PS wiring unchanged'
    (e/'source-overlay.json').write_text(json.dumps(overlay,indent=2)+'\n')
    (e/'state.json').write_text(json.dumps(dict(status='source_prepared_not_built',package_id='hp2-cycletrace-r30',
        user_authorization='2026-10-22 user asks to run on board and capture waveforms; board and UART restored.',
        caps=dict(candidate_starts=1,original_fallbacks=1,SDK_Open=0,DMA=False,inference=False,HDMI_START=False,physical_key=0),
        actual_candidate_starts=0,actual_original_fallbacks=0,background_tasks=[],AI_four_HC_unchanged=True,
        sample_bits=512,bank_depth=128,banks=2,pretrigger=32,csr_base='0x400b8000',
        next='Directed simulation and actual physical qualification before any BOOT mutation.'),indent=2)+'\n')
    print(json.dumps(dict(prepared=True,work=str(w),evidence=str(e),AI_four_HC_unchanged=True)))


if __name__=='__main__':main()

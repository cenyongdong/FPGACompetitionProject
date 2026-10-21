"""Isolated r26 overlays; reuse unchanged native IP products and r24 commands."""
from pathlib import Path
import json
import re
import shutil

R=Path(__file__).resolve().parents[3]
REF=R/'.local/hdmi-boot-witness-20261019-r23/reference'
W=R/'.local/hdmi-ps-release-20261020-r26'
E=R/'tools/pose-v1/evidence/hdmi-ps-release-20261020-r26'
S=W/'sources'


def once(t,a,b):
    if t.count(a)!=1: raise ValueError('Hardware insertion not unique: '+a[:100])
    return t.replace(a,b,1)


def wrap(t):
    return 'if {[catch {\nset_param general.maxThreads 2\n'+t+'\n} result]} {puts $result;puts $::errorInfo;exit 1}\nexit\n'


def main():
    S.mkdir(parents=True,exist_ok=True)
    replacements={}
    def save(p,t):
        q=S/p.name;q.write_text(t);replacements[str(p)]=str(q);return q
    bd=REF/'fpai_demo_vivado.srcs/sources_1/bd/ps_ai'
    p=bd/'synth/ps_ai.v';t=p.read_text()
    t=once(t,'    hp2_domain_ready);','    hp2_domain_ready,\n    diagnostic_ps_resetn,\n    diagnostic_ps_write,\n    diagnostic_ps_awaddr);')
    t=once(t,'  input hp2_domain_ready;','  input hp2_domain_ready;\n  output diagnostic_ps_resetn;\n  output [5:0] diagnostic_ps_write;\n  output [31:0] diagnostic_ps_awaddr;')
    t=once(t,'        .S_AXI_HP2_ACLK(', '        .S_AXI_HP2_ARESETN(diagnostic_ps_resetn),\n        .S_AXI_HP2_ACLK(')
    t=once(t,'  assign diagnostic_hp2_clk = hp_axi_aclk_1;', '''  assign diagnostic_ps_write = {axi_interconnect_4_M00_AXI_BREADY,
    axi_interconnect_4_M00_AXI_BVALID,axi_interconnect_4_M00_AXI_WREADY,
    axi_interconnect_4_M00_AXI_WVALID,axi_interconnect_4_M00_AXI_AWREADY,
    axi_interconnect_4_M00_AXI_AWVALID};
  assign diagnostic_ps_awaddr = axi_interconnect_4_M00_AXI_AWADDR;
  assign diagnostic_hp2_clk = hp_axi_aclk_1;''')
    save(p,t)
    p=R/'.local/hdmi-hp2-ready-20261020-r24/sources/ps_ai_wrapper.sv';t=p.read_text()
    t=once(t,'    input hp2_domain_ready\n);','    input hp2_domain_ready,\n    output diagnostic_ps_resetn,\n    output [5:0] diagnostic_ps_write,\n    output [31:0] diagnostic_ps_awaddr\n);')
    t=once(t,'  .hp2_domain_ready(hp2_domain_ready)', '  .diagnostic_ps_resetn(diagnostic_ps_resetn),\n  .diagnostic_ps_write(diagnostic_ps_write),\n  .diagnostic_ps_awaddr(diagnostic_ps_awaddr),\n  .hp2_domain_ready(hp2_domain_ready)')
    save(p,t)
    p=R/'.local/hdmi-hp2-ready-20261020-r24/sources/ps_ai_peripheral.sv';t=p.read_text()
    t=once(t,'  wire [767:0] ai_read_channels;', '  wire [767:0] ai_read_channels;\n  wire diagnostic_ps_resetn;\n  wire [5:0] diagnostic_ps_write;\n  wire [31:0] diagnostic_ps_awaddr;')
    t=once(t,".HDMI_BASE(32'h400b0400),.DECODE_LSB(9)",".HDMI_BASE(32'h400b0400),.DECODE_LSB(10)")
    t=once(t,' .witness_gp_reset(gp_clk_rst),', ''' .witness_gp_reset(gp_clk_rst),
 .release_levels({soft_rst,sys_rst_n,diagnostic_ps_write[4],diagnostic_ps_write[2],diagnostic_ps_write[0],
     S_AXI_HP2_BVALID,S_AXI_HP2_WVALID,S_AXI_HP2_AWVALID,
     S_AXI_HP2_RVALID,S_AXI_HP2_ARVALID,diagnostic_hp2_read[62],diagnostic_hp2_read[60],
     1'b0,ddr3_init_done,ddr_ui_rst,FCLK_RESET0_N,hp_clk_rst,gp_clk_rst,
     diagnostic_hp2_resetn,diagnostic_ps_resetn}),
 .release_legacy_write({S_AXI_HP2_BREADY,S_AXI_HP2_BVALID,S_AXI_HP2_WREADY,S_AXI_HP2_WVALID,S_AXI_HP2_AWREADY,S_AXI_HP2_AWVALID}),
 .release_ps_write(diagnostic_ps_write),.release_ps_awaddr(diagnostic_ps_awaddr),''')
    t=once(t,'    .hp2_domain_ready(ddr3_init_done & ~ddr_ui_rst),', '''    .diagnostic_ps_resetn(diagnostic_ps_resetn),
    .diagnostic_ps_write(diagnostic_ps_write),
    .diagnostic_ps_awaddr(diagnostic_ps_awaddr),
    .hp2_domain_ready(ddr3_init_done & ~ddr_ui_rst),''')
    save(p,t)
    p=REF/'rtl/hdmi_candidate/ai_read_monitor.sv';t=p.read_text()
    t=once(t,'    input wire witness_gp_reset,','    input wire witness_gp_reset,\n    input wire [19:0] release_levels,\n    input wire [5:0] release_legacy_write,release_ps_write,\n    input wire [31:0] release_ps_awaddr,')
    # Keep the old 512-byte monitor and all old commands; the outer router now
    # reserves 0x400..0x7ff. New 0x600 aperture accepts no control commands.
    t=t.replace('csr.', 'legacy_csr.')
    t=once(t,'    assign legacy_csr.awwready=', '''    mna_gp_ww_itf legacy_csr();
    mna_gp_ww_itf release_csr();
    hdmi_cam_router #(.HDMI_BASE(32'h400b0600),.DECODE_LSB(9)) release_router(
      .clk(csr_clk),.resetn(csr_resetn),.upstream(csr),
      .camera(legacy_csr),.hdmi(release_csr));
    ps_release_witness release_history(
      .source_clk(source_clk),.csr_clk(csr_clk),.csr_resetn(csr_resetn),
      .source_freeze(source_resetn && arm_request_sync[1]==arm_ack_toggle && freeze_request_sync[1]!=freeze_ack_toggle),
      .csr_freeze(busy && pending_freeze && freeze_ack_sync[1]==freeze_request_toggle),
      .levels(release_levels),.ps_read(channels[640+:128]),.hdmi_read(channels[512+:128]),
      .legacy_write(release_legacy_write),.ps_write(release_ps_write),
      .ps_awaddr(release_ps_awaddr),.csr(release_csr));
    assign legacy_csr.awwready=''' )
    save(p,t)
    ps=bd/'ip/ps_ai_processing_system7_0_0'
    p=ps/'synth/ps_ai_processing_system7_0_0.v';t=p.read_text()
    t=once(t,'  S_AXI_HP2_RVALID,','  S_AXI_HP2_ARESETN,\n  S_AXI_HP2_RVALID,')
    t=once(t,'output wire S_AXI_HP2_RVALID;','output wire S_AXI_HP2_ARESETN;\noutput wire S_AXI_HP2_RVALID;')
    t=once(t,'    .S_AXI_HP2_RVALID(S_AXI_HP2_RVALID),','    .S_AXI_HP2_ARESETN(S_AXI_HP2_ARESETN),\n    .S_AXI_HP2_RVALID(S_AXI_HP2_RVALID),')
    new_ps=save(p,t)
    hdl=ps/'hdl/verilog/processing_system7_v5_5_processing_system7.v'
    atc=bd/'ipshared/8fd3/hdl/verilog/processing_system7_v5_5_atc.v'
    ooc='create_project -in_memory -part xc7z030ffg676-2\nset_property default_lib xil_defaultlib [current_project]\n'
    ooc+='read_verilog {'+' '.join(p.as_posix() for p in (new_ps,hdl,atc))+'}\n'
    ooc+=f'read_xdc {{{ps.as_posix()}/ps_ai_processing_system7_0_0.xdc}}\n'
    ooc+='synth_design -top ps_ai_processing_system7_0_0 -part xc7z030ffg676-2 -mode out_of_context\n'
    ooc+=f'write_checkpoint -force {{{W.as_posix()}/ps-ooc.dcp}}\nwrite_verilog -force -mode synth_stub {{{S.as_posix()}/ps_release_stub.v}}\n'
    (E/'ps-ooc.tcl').write_text(wrap(ooc))
    bdips=[p for p in sorted((bd/'ip').glob('*/*.xci')) if p.parent!=ps]
    load_bd='\n'.join('read_ip -quiet {'+p.as_posix()+'}' for p in bdips)+'\n'
    syn=(REF/'fpai_demo_vivado.runs/synth_hp2ready_r24/ai7030_edif_top.tcl').read_text()
    # Native source library/hook settings retained. No source/BD writes.
    a=syn.index('set src_rc [catch {');b=syn.index('read_verilog -library',a)
    syn=syn[:a]+syn[b:]
    a=syn.index('add_files '+bd.as_posix()+'/ps_ai.bd');b=syn.index('read_ip -quiet ',a)
    syn=syn[:a]+load_bd+'read_verilog {'+(S/'ps_ai.v').as_posix()+' '+(S/'ps_release_stub.v').as_posix()+'}\n'+syn[b:]
    for a,b in replacements.items():
        syn=syn.replace(Path(a).as_posix(),Path(b).as_posix())
    syn=syn.replace('read_verilog -library xil_defaultlib -sv {','read_verilog -library xil_defaultlib -sv {\n  '+(R/'FPGA/hdmi_candidate/diagnostics/ps_release_witness.sv').as_posix(),1)
    syn=syn.replace('read_xdc dont_touch.xdc','read_xdc {'+(REF/'fpai_demo_vivado.runs/synth_hp2ready_r24/dont_touch.xdc').as_posix()+'}')
    syn=syn.replace('[get_files dont_touch.xdc]','[get_files {'+(REF/'fpai_demo_vivado.runs/synth_hp2ready_r24/dont_touch.xdc').as_posix()+'}]')
    syn=syn.replace('write_checkpoint -force -noxdef ai7030_edif_top.dcp','write_checkpoint -force -noxdef {'+(W/'synth.dcp').as_posix()+'}')
    (E/'synthesis.tcl').write_text(wrap(syn))
    (E/'source-overlay.json').write_text(json.dumps({'replacements':replacements,'scope':'passive PS release/write recorder; unchanged r24 functional datapath',
        'unchanged_IP_count':len(bdips),'PS_OOC_rebuilt':True,'original_project_modified':False},indent=2))
    print(json.dumps({'overlays':len(replacements),'unchanged_BD_IPs':len(bdips),'work':str(W)}))


if __name__=='__main__':main()

"""Generate an isolated, deliberately non-deployable r45 derivative. No EDA/board access."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
BASE=ROOT/'FPGA/hdmi_candidate/diagnostics/deferred_consume_r45/sources'
OUT=ROOT/'.local/pose-postprocess-offline/overlay';OUT.mkdir(parents=True,exist_ok=True)
text=(BASE/'ps_ai_peripheral.sv').read_text()
begin=text.index('// r37: S01 HDMI');end=text.index("hdmi_cam_router #(.HDMI_BASE(32'h400b0000)) hdmi_router",begin)
old=text[begin:end]
# Retain original native checker and active consumer statements verbatim.
native=old[old.index('hp2_protocol_observer hp2_protocol_observer('):old.index('mna_gp_ww_itf protocol_passthrough')]
drain=old[old.index('// r38: bounded S01'):]
insert='''// Offline compact overlay. Coverage qualification is deliberately false.
mna_gp_ww_itf lean_csr(),filter_csr(),lean_pass();
wire drain_arm,drain_checker_rearm,lean_admitted;
wire [159:0] diagnostic_pc_status;
wire diagnostic_pc_asserted,diagnostic_pc_system_resetn,diagnostic_pc_ready,diagnostic_pc_seen_reset;
hdmi_cam_router #(.HDMI_BASE(32'h400b0800)) lean_router(
 .clk(gp_clk),.resetn(~gp_clk_rst),.upstream(cam.slave),.camera(lean_pass.master),.hdmi(lean_csr.master));
hdmi_cam_router #(.HDMI_BASE(32'h400b1000),.DECODE_LSB(12)) filter_router(
 .clk(gp_clk),.resetn(~gp_clk_rst),.upstream(lean_pass.slave),.camera(diag_passthrough.master),.hdmi(filter_csr.master));
wire [127:0] lean_s01={55'd0,S_AXI_HP2_RLAST,S_AXI_HP2_RRESP,{1'b0,S_AXI_HP2_RID},S_AXI_HP2_RREADY,S_AXI_HP2_RVALID,62'd0};
startup_guard_block #(.COVERAGE_COMPLETE(0)) lean_guard(
 .hp_clk(diagnostic_hp2_clk),.csr_clk(gp_clk),.csr_resetn(~gp_clk_rst),
 .ps_resetn(diagnostic_ps_resetn),.pl_resetn(diagnostic_hp2_resetn),.hp_reset(hp_clk_rst),
 .ps_read(diagnostic_hp2_read),.s01_read(lean_s01),
 .any_request(drain_request_activity|diagnostic_hp2_read[60]),
 .any_write(diagnostic_hp2_write[60]|diagnostic_hp2_write[141]|diagnostic_hp2_write[151]|S_AXI_HP2_BVALID|
 S0_AXI_HP_HC_WVALID|S1_AXI_HP_HC_WVALID|S2_AXI_HP_HC_WVALID|S3_AXI_HP_HC_WVALID|
 S0_AXI_HP_HC_BVALID|S1_AXI_HP_HC_BVALID|S2_AXI_HP_HC_BVALID|S3_AXI_HP_HC_BVALID),
 .hc_return(S0_AXI_HP_HC_RVALID|S1_AXI_HP_HC_RVALID|S2_AXI_HP_HC_RVALID|S3_AXI_HP_HC_RVALID),
 .reader_ready(hdmi_reader_rready),.native_status(diagnostic_pc_status),.native_ready(diagnostic_pc_ready),.native_seen_reset(diagnostic_pc_seen_reset),
 .drain_status(startup_drain_status),.arm(drain_arm),.checker_rearm(drain_checker_rearm),.admitted(lean_admitted),
 .wr_valid(lean_csr.awwvalid),.wr_addr(lean_csr.awwaddr[7:0]),.wr_data(lean_csr.awwdata),.wr_ready(lean_csr.awwready),
 .rd_valid(lean_csr.arvalid),.rd_addr(lean_csr.araddr[7:0]),.rd_ready(lean_csr.arready),.rsp_valid(lean_csr.rvalid),.rsp_data(lean_csr.rdata),.rsp_ready(lean_csr.rready));
`ifndef POSE_FILTER_LANES
 `define POSE_FILTER_LANES 1
`endif
pose_filter_csr #(.LANES(`POSE_FILTER_LANES)) presentation_filter(
 .clk(gp_clk),.resetn(~gp_clk_rst),.wr_valid(filter_csr.awwvalid),.wr_addr(filter_csr.awwaddr[11:0]),.wr_data(filter_csr.awwdata),.wr_ready(filter_csr.awwready),
 .rd_valid(filter_csr.arvalid),.rd_addr(filter_csr.araddr[11:0]),.rd_ready(filter_csr.arready),.rsp_valid(filter_csr.rvalid),.rsp_data(filter_csr.rdata),.rsp_ready(filter_csr.rready));
'''+native
# Place original declarations before any compact observer port references.
insert=insert.replace('wire drain_arm,drain_checker_rearm,lean_admitted;\n','wire drain_arm,drain_checker_rearm,lean_admitted;\n'+drain)
text=text[:begin]+insert+text[end:]
(OUT/'ps_ai_peripheral.sv').write_text(text)
manifest=dict(profile='pose-stabilizer-offline-v1',deployable=False,coverage_complete=False,
 baseline=str(BASE),overlay=str(OUT/'ps_ai_peripheral.sv'),unchanged=['ps_ai.v','ps_ai_wrapper.sv','hp2_startup_drain.sv'],
 retain=['hp2_protocol_observer','hp2_native_protocol_checker','startup_drain','HDMI_RREADY | startup_drain_ready'],
 remove=['hp2_cycle_recorder','hp2_protocol_recorder','ai_read_path_monitor','ai_path_monitor','deferred_control'],
 rtl=[str(p) for p in sorted((HERE/'rtl').glob('*.sv'))],
 router=str(ROOT/'.local/hdmi-boot-witness-20261019-r23/reference/rtl/hdmi_candidate/hdmi_cam_router.sv'),
 removed_constraints=['hp2_cycle_trace_cdc.tcl','ai_read_monitor_cdc.tcl','ai_boot_witness_cdc.tcl','deferred_control_cdc.tcl','deferred_control_validate.tcl'],
 pending='Native checker retained; source-domain coverage/clock mapping and new CDC constraints require integration qualification. No opt/place/route/bit scripts generated.')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));print(OUT)

// Standalone compact guard + immutable CSR snapshot. No AXI master/functional reset.
module startup_guard_block #(parameter COVERAGE_COMPLETE=0)(
 input wire hp_clk,csr_clk,csr_resetn,ps_resetn,pl_resetn,hp_reset,
 input wire [127:0] ps_read,s01_read,input wire any_request,any_write,hc_return,reader_ready,
 input wire [159:0] native_status,input wire native_ready,native_seen_reset,
 input wire [31:0] drain_status,output wire arm,checker_rearm,admitted,
 input wire wr_valid,input wire [7:0] wr_addr,input wire [31:0] wr_data,output wire wr_ready,
 input wire rd_valid,input wire [7:0] rd_addr,output wire rd_ready,
 output wire rsp_valid,output wire [31:0] rsp_data,input wire rsp_ready
);
 reg config_resetn=0;always @(posedge hp_clk)config_resetn<=1;
 wire cv;wire [2:0] command,state;wire [31:0] faults,ps_count,s_count,identity,resets,aps,ass,plast,slast;
 wire [63:0] cycle,first_cycle,arm_cycle;wire [159:0] history;
 wire [1023:0] bundle={96'd0,32'h00000001,32'(COVERAGE_COMPLETE),native_status,history,drain_status,slast,plast,ass,aps,resets,identity,arm_cycle,first_cycle,cycle,s_count,ps_count,faults,29'd0,state};
 startup_guard guard(.clk(hp_clk),.config_resetn(config_resetn),.ps_resetn(ps_resetn),.pl_resetn(pl_resetn),.hp_reset(hp_reset),
 .any_request(any_request),.any_write(any_write),.hc_return(hc_return),.reader_ready(reader_ready),
 .ps_valid(ps_read[62]),.ps_ready(ps_read[63]),.ps_last(ps_read[72]),.ps_id(ps_read[69:64]),.ps_resp(ps_read[71:70]),
 .s_valid(s01_read[62]),.s_ready(s01_read[63]),.s_last(s01_read[72]),.s_id(s01_read[68:64]),.s_resp(s01_read[71:70]),
 .native_ready(native_ready),.native_seen_reset(native_seen_reset),.coverage_complete(COVERAGE_COMPLETE!=0),.native_status(native_status),
 .drain_status(drain_status),.command_valid(cv),.command(command),.arm(arm),.checker_rearm(checker_rearm),.admitted(admitted),
 .state(state),.faults(faults),.ps_count(ps_count),.s_count(s_count),.cycle(cycle),.first_valid_cycle(first_cycle),.arm_cycle(arm_cycle),.native_history(history),
 .first_identity(identity),.reset_evidence(resets),.arm_ps_count(aps),.arm_s_count(ass),.ps_last_position(plast),.s_last_position(slast));
 startup_guard_csr csr(.hp_clk(hp_clk),.csr_clk(csr_clk),.csr_resetn(csr_resetn),.status_bundle(bundle),.command_valid(cv),.command(command),
 .wr_valid(wr_valid),.wr_addr(wr_addr),.wr_data(wr_data),.wr_ready(wr_ready),.rd_valid(rd_valid),.rd_addr(rd_addr),.rd_ready(rd_ready),.rsp_valid(rsp_valid),.rsp_data(rsp_data),.rsp_ready(rsp_ready));
endmodule

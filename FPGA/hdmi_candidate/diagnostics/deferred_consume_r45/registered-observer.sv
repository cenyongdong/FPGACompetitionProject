// Passive monitor of the actual PS-facing AXI3 connection. No functional
// handshake or reset outputs. The checker starts independently of GP/MIG.
module hp2_protocol_observer(
 input wire clk,ps_resetn,diagnostic_rearm,
 input wire [127:0] ps_read,
 input wire [63:0] ps_rdata,
 input wire [152:0] ps_write,
 output wire [159:0] pc_status,
 output wire pc_asserted,system_resetn,checker_ready,
 output reg seen_reset_low=0
);
 reg [5:0] startup_count=0;
 always @(posedge clk)begin
  if(diagnostic_rearm)startup_count<=0;
  else if(!(&startup_count))startup_count<=startup_count+1'b1;
  if(checker_ready && !ps_resetn)seen_reset_low<=1;
 end
 assign system_resetn=startup_count[5];
 // The native IP resynchronizes system_resetn internally for three clocks.
 // This conservative coverage flag is not used to gate any bus/checker input.
 assign checker_ready=startup_count>=6'd40;
 // Delay the complete monitored AXI bundle and its reset by one HP edge.
 // Functional wiring and the raw waveform capture remain upstream of this.
 reg [127:0] sampled_read=0;
 reg [63:0] sampled_rdata=0;
 reg [152:0] sampled_write=0;
 reg sampled_resetn=0;
 always @(posedge clk)begin
  sampled_read<=ps_read;sampled_rdata<=ps_rdata;
  sampled_write<=ps_write;sampled_resetn<=ps_resetn;
 end
 hp2_native_protocol_checker native_checker(
  .aclk(clk),.aresetn(sampled_resetn),.system_resetn(system_resetn),
  .pc_status(pc_status),.pc_asserted(pc_asserted),
  .pc_axi_araddr(sampled_read[31:0]),.pc_axi_arid(sampled_read[37:32]),
  .pc_axi_arlen(sampled_read[41:38]),.pc_axi_arsize(sampled_read[44:42]),
  .pc_axi_arburst(sampled_read[46:45]),.pc_axi_arlock(sampled_read[48:47]),
  .pc_axi_arcache(sampled_read[52:49]),.pc_axi_arprot(sampled_read[55:53]),
  .pc_axi_arqos(sampled_read[59:56]),.pc_axi_arvalid(sampled_read[60]),.pc_axi_arready(sampled_read[61]),
  .pc_axi_rvalid(sampled_read[62]),.pc_axi_rready(sampled_read[63]),
  .pc_axi_rid(sampled_read[69:64]),.pc_axi_rresp(sampled_read[71:70]),.pc_axi_rlast(sampled_read[72]),
  .pc_axi_rdata(sampled_rdata),
  .pc_axi_awaddr(sampled_write[31:0]),.pc_axi_awid(sampled_write[37:32]),
  .pc_axi_awlen(sampled_write[41:38]),.pc_axi_awsize(sampled_write[44:42]),
  .pc_axi_awburst(sampled_write[46:45]),.pc_axi_awlock(sampled_write[48:47]),
  .pc_axi_awcache(sampled_write[52:49]),.pc_axi_awprot(sampled_write[55:53]),
  .pc_axi_awqos(sampled_write[59:56]),.pc_axi_awvalid(sampled_write[60]),.pc_axi_awready(sampled_write[61]),
  .pc_axi_wdata(sampled_write[125:62]),.pc_axi_wid(sampled_write[131:126]),
  .pc_axi_wstrb(sampled_write[139:132]),.pc_axi_wlast(sampled_write[140]),
  .pc_axi_wvalid(sampled_write[141]),.pc_axi_wready(sampled_write[142]),
  .pc_axi_bid(sampled_write[148:143]),.pc_axi_bresp(sampled_write[150:149]),
  .pc_axi_bvalid(sampled_write[151]),.pc_axi_bready(sampled_write[152]));
endmodule

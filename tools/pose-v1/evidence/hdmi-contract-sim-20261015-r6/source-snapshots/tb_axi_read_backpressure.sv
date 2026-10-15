`timescale 1ns/1ps
// Reproduce, rather than accept, the original AXI master's missing handshake
// qualification. A legal slave holds RVALID/RLAST/data until RREADY is high.
module axi_read_backpressure_case(output reg done=0);
  reg clk=0,resetn=0,start=0,full=0,rvalid=0,rlast=0;
  always #2.5 clk=~clk;
  wire arvalid,rready,ready,fifo_we,read_done;
  wire [7:0] arlen;
  integer accepted=0;
  aq_axi_master dut(
    .ARESETN(resetn),.ACLK(clk),
    .M_AXI_AWREADY(1'b0),.M_AXI_WREADY(1'b0),.M_AXI_BID(1'b0),
    .M_AXI_BRESP(2'b0),.M_AXI_BUSER(1'b0),.M_AXI_BVALID(1'b0),
    .M_AXI_ARVALID(arvalid),.M_AXI_ARLEN(arlen),.M_AXI_ARREADY(1'b1),
    .M_AXI_RID(1'b0),.M_AXI_RDATA(64'h0123456789abcdef),.M_AXI_RRESP(2'b0),
    .M_AXI_RLAST(rlast),.M_AXI_RUSER(1'b0),.M_AXI_RVALID(rvalid),.M_AXI_RREADY(rready),
    .MASTER_RST(1'b0),.WR_START(1'b0),.WR_ADRS(32'b0),.WR_LEN(32'b0),
    .WR_FIFO_EMPTY(1'b1),.WR_FIFO_AEMPTY(1'b1),.WR_FIFO_DATA(64'b0),
    .RD_START(start),.RD_ADRS(32'h30100000),.RD_LEN(32'd8),.RD_READY(ready),
    .RD_FIFO_WE(fifo_we),.RD_FIFO_FULL(full),.RD_FIFO_AFULL(1'b0),.RD_DONE(read_done));
  always @(posedge clk) if(resetn && rvalid && rready) accepted=accepted+1;

  task initiate;
    begin
      wait(ready===1'b1);
      @(negedge clk); start=1;
      @(negedge clk); start=0;
      wait(arvalid===1'b1);
      if(arlen!==0) $fatal(1,"Expected one-beat request");
      @(negedge clk); // next rising edge accepts address
      @(negedge clk);
    end
  endtask

  initial begin
    repeat(8) @(negedge clk); resetn=1;
    initiate();
    rvalid=1; rlast=1;
    @(negedge clk);
    if(!read_done || accepted!=1) $fatal(1,"AXI positive control failed");
    rvalid=0; rlast=0;
    $display("AXI_CONTROL no_backpressure accepted=1 completed=1");
    repeat(6) @(negedge clk);
    initiate();
    // Full FIFO holds RREADY low. Slave keeps this last beat unchanged.
    full=1; rvalid=1; rlast=1;
    #0.1;
    if(rready!==0) $fatal(1,"Expected AXI backpressure");
    if(fifo_we!==1) $fatal(1,"Original unqualified FIFO write defect not reproduced");
    @(negedge clk);
    if(accepted!=1) $fatal(1,"Backpressured data unexpectedly accepted");
    if(!read_done) $fatal(1,"Original early-completion defect not reproduced");
    $display("AXI_EXISTING_BUG_REPRODUCED rvalid=1 rlast=1 rready=0 fifo_we=1 accepted_this_request=0 RD_DONE=1");
    // End this isolated simulation by reset, not by an invented drain contract.
    resetn=0; rvalid=0; rlast=0;
    done=1;
  end
  initial begin #10000; if(!done) $fatal(1,"AXI reproduction watchdog"); end
endmodule

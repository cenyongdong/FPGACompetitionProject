`timescale 1ns/1ps
// Actual HP2 fabric plus real, reset HDMI mailbox/control/reader.
// In the first three cases HDMI never STARTs and holds RREADY low.
module tb_hp2_orphan;
  reg clk=0, rstn=0;
  always #2.5 clk=~clk;
  wire  ACLK;
wire  ARESETN;
wire  M00_ACLK;
wire  M00_ARESETN;
wire [31:0] M00_AXI_araddr;
wire [1:0] M00_AXI_arburst;
wire [3:0] M00_AXI_arcache;
wire [5:0] M00_AXI_arid;
wire [3:0] M00_AXI_arlen;
wire [1:0] M00_AXI_arlock;
wire [2:0] M00_AXI_arprot;
wire [3:0] M00_AXI_arqos;
wire  M00_AXI_arready;
wire [2:0] M00_AXI_arsize;
wire  M00_AXI_arvalid;
wire [31:0] M00_AXI_awaddr;
wire [1:0] M00_AXI_awburst;
wire [3:0] M00_AXI_awcache;
wire [5:0] M00_AXI_awid;
wire [3:0] M00_AXI_awlen;
wire [1:0] M00_AXI_awlock;
wire [2:0] M00_AXI_awprot;
wire [3:0] M00_AXI_awqos;
wire  M00_AXI_awready;
wire [2:0] M00_AXI_awsize;
wire  M00_AXI_awvalid;
wire [5:0] M00_AXI_bid;
wire  M00_AXI_bready;
wire [1:0] M00_AXI_bresp;
wire  M00_AXI_bvalid;
wire [63:0] M00_AXI_rdata;
wire [5:0] M00_AXI_rid;
wire  M00_AXI_rlast;
wire  M00_AXI_rready;
wire [1:0] M00_AXI_rresp;
wire  M00_AXI_rvalid;
wire [63:0] M00_AXI_wdata;
wire [5:0] M00_AXI_wid;
wire  M00_AXI_wlast;
wire  M00_AXI_wready;
wire [7:0] M00_AXI_wstrb;
wire  M00_AXI_wvalid;
wire  S00_ACLK;
wire  S00_ARESETN;
wire [31:0] S00_AXI_araddr;
wire [1:0] S00_AXI_arburst;
wire [3:0] S00_AXI_arcache;
wire [4:0] S00_AXI_arid;
wire [3:0] S00_AXI_arlen;
wire [1:0] S00_AXI_arlock;
wire [2:0] S00_AXI_arprot;
wire [3:0] S00_AXI_arqos;
wire  S00_AXI_arready;
wire [2:0] S00_AXI_arsize;
wire  S00_AXI_arvalid;
wire [31:0] S00_AXI_awaddr;
wire [1:0] S00_AXI_awburst;
wire [3:0] S00_AXI_awcache;
wire [4:0] S00_AXI_awid;
wire [3:0] S00_AXI_awlen;
wire [1:0] S00_AXI_awlock;
wire [2:0] S00_AXI_awprot;
wire [3:0] S00_AXI_awqos;
wire  S00_AXI_awready;
wire [2:0] S00_AXI_awsize;
wire  S00_AXI_awvalid;
wire [4:0] S00_AXI_bid;
wire  S00_AXI_bready;
wire [1:0] S00_AXI_bresp;
wire  S00_AXI_bvalid;
wire [63:0] S00_AXI_rdata;
wire [4:0] S00_AXI_rid;
wire  S00_AXI_rlast;
wire  S00_AXI_rready;
wire [1:0] S00_AXI_rresp;
wire  S00_AXI_rvalid;
wire [63:0] S00_AXI_wdata;
wire [4:0] S00_AXI_wid;
wire  S00_AXI_wlast;
wire  S00_AXI_wready;
wire [7:0] S00_AXI_wstrb;
wire  S00_AXI_wvalid;
wire  S01_ACLK;
wire  S01_ARESETN;
wire [31:0] S01_AXI_araddr;
wire [1:0] S01_AXI_arburst;
wire [3:0] S01_AXI_arcache;
wire [4:0] S01_AXI_arid;
wire [3:0] S01_AXI_arlen;
wire [1:0] S01_AXI_arlock;
wire [2:0] S01_AXI_arprot;
wire [3:0] S01_AXI_arqos;
wire  S01_AXI_arready;
wire [2:0] S01_AXI_arsize;
wire  S01_AXI_arvalid;
wire [31:0] S01_AXI_awaddr;
wire [1:0] S01_AXI_awburst;
wire [3:0] S01_AXI_awcache;
wire [4:0] S01_AXI_awid;
wire [3:0] S01_AXI_awlen;
wire [1:0] S01_AXI_awlock;
wire [2:0] S01_AXI_awprot;
wire [3:0] S01_AXI_awqos;
wire  S01_AXI_awready;
wire [2:0] S01_AXI_awsize;
wire  S01_AXI_awvalid;
wire [4:0] S01_AXI_bid;
wire  S01_AXI_bready;
wire [1:0] S01_AXI_bresp;
wire  S01_AXI_bvalid;
wire [63:0] S01_AXI_rdata;
wire [4:0] S01_AXI_rid;
wire  S01_AXI_rlast;
wire  S01_AXI_rready;
wire [1:0] S01_AXI_rresp;
wire  S01_AXI_rvalid;
wire [63:0] S01_AXI_wdata;
wire [4:0] S01_AXI_wid;
wire  S01_AXI_wlast;
wire  S01_AXI_wready;
wire [7:0] S01_AXI_wstrb;
wire  S01_AXI_wvalid;
  ps_ai_axi_interconnect_3_0 fabric(.ACLK(ACLK),.ARESETN(ARESETN),.M00_ACLK(M00_ACLK),.M00_ARESETN(M00_ARESETN),.M00_AXI_araddr(M00_AXI_araddr),.M00_AXI_arburst(M00_AXI_arburst),.M00_AXI_arcache(M00_AXI_arcache),.M00_AXI_arid(M00_AXI_arid),.M00_AXI_arlen(M00_AXI_arlen),.M00_AXI_arlock(M00_AXI_arlock),.M00_AXI_arprot(M00_AXI_arprot),.M00_AXI_arqos(M00_AXI_arqos),.M00_AXI_arready(M00_AXI_arready),.M00_AXI_arsize(M00_AXI_arsize),.M00_AXI_arvalid(M00_AXI_arvalid),.M00_AXI_awaddr(M00_AXI_awaddr),.M00_AXI_awburst(M00_AXI_awburst),.M00_AXI_awcache(M00_AXI_awcache),.M00_AXI_awid(M00_AXI_awid),.M00_AXI_awlen(M00_AXI_awlen),.M00_AXI_awlock(M00_AXI_awlock),.M00_AXI_awprot(M00_AXI_awprot),.M00_AXI_awqos(M00_AXI_awqos),.M00_AXI_awready(M00_AXI_awready),.M00_AXI_awsize(M00_AXI_awsize),.M00_AXI_awvalid(M00_AXI_awvalid),.M00_AXI_bid(M00_AXI_bid),.M00_AXI_bready(M00_AXI_bready),.M00_AXI_bresp(M00_AXI_bresp),.M00_AXI_bvalid(M00_AXI_bvalid),.M00_AXI_rdata(M00_AXI_rdata),.M00_AXI_rid(M00_AXI_rid),.M00_AXI_rlast(M00_AXI_rlast),.M00_AXI_rready(M00_AXI_rready),.M00_AXI_rresp(M00_AXI_rresp),.M00_AXI_rvalid(M00_AXI_rvalid),.M00_AXI_wdata(M00_AXI_wdata),.M00_AXI_wid(M00_AXI_wid),.M00_AXI_wlast(M00_AXI_wlast),.M00_AXI_wready(M00_AXI_wready),.M00_AXI_wstrb(M00_AXI_wstrb),.M00_AXI_wvalid(M00_AXI_wvalid),.S00_ACLK(S00_ACLK),.S00_ARESETN(S00_ARESETN),.S00_AXI_araddr(S00_AXI_araddr),.S00_AXI_arburst(S00_AXI_arburst),.S00_AXI_arcache(S00_AXI_arcache),.S00_AXI_arid(S00_AXI_arid),.S00_AXI_arlen(S00_AXI_arlen),.S00_AXI_arlock(S00_AXI_arlock),.S00_AXI_arprot(S00_AXI_arprot),.S00_AXI_arqos(S00_AXI_arqos),.S00_AXI_arready(S00_AXI_arready),.S00_AXI_arsize(S00_AXI_arsize),.S00_AXI_arvalid(S00_AXI_arvalid),.S00_AXI_awaddr(S00_AXI_awaddr),.S00_AXI_awburst(S00_AXI_awburst),.S00_AXI_awcache(S00_AXI_awcache),.S00_AXI_awid(S00_AXI_awid),.S00_AXI_awlen(S00_AXI_awlen),.S00_AXI_awlock(S00_AXI_awlock),.S00_AXI_awprot(S00_AXI_awprot),.S00_AXI_awqos(S00_AXI_awqos),.S00_AXI_awready(S00_AXI_awready),.S00_AXI_awsize(S00_AXI_awsize),.S00_AXI_awvalid(S00_AXI_awvalid),.S00_AXI_bid(S00_AXI_bid),.S00_AXI_bready(S00_AXI_bready),.S00_AXI_bresp(S00_AXI_bresp),.S00_AXI_bvalid(S00_AXI_bvalid),.S00_AXI_rdata(S00_AXI_rdata),.S00_AXI_rid(S00_AXI_rid),.S00_AXI_rlast(S00_AXI_rlast),.S00_AXI_rready(S00_AXI_rready),.S00_AXI_rresp(S00_AXI_rresp),.S00_AXI_rvalid(S00_AXI_rvalid),.S00_AXI_wdata(S00_AXI_wdata),.S00_AXI_wid(S00_AXI_wid),.S00_AXI_wlast(S00_AXI_wlast),.S00_AXI_wready(S00_AXI_wready),.S00_AXI_wstrb(S00_AXI_wstrb),.S00_AXI_wvalid(S00_AXI_wvalid),.S01_ACLK(S01_ACLK),.S01_ARESETN(S01_ARESETN),.S01_AXI_araddr(S01_AXI_araddr),.S01_AXI_arburst(S01_AXI_arburst),.S01_AXI_arcache(S01_AXI_arcache),.S01_AXI_arid(S01_AXI_arid),.S01_AXI_arlen(S01_AXI_arlen),.S01_AXI_arlock(S01_AXI_arlock),.S01_AXI_arprot(S01_AXI_arprot),.S01_AXI_arqos(S01_AXI_arqos),.S01_AXI_arready(S01_AXI_arready),.S01_AXI_arsize(S01_AXI_arsize),.S01_AXI_arvalid(S01_AXI_arvalid),.S01_AXI_awaddr(S01_AXI_awaddr),.S01_AXI_awburst(S01_AXI_awburst),.S01_AXI_awcache(S01_AXI_awcache),.S01_AXI_awid(S01_AXI_awid),.S01_AXI_awlen(S01_AXI_awlen),.S01_AXI_awlock(S01_AXI_awlock),.S01_AXI_awprot(S01_AXI_awprot),.S01_AXI_awqos(S01_AXI_awqos),.S01_AXI_awready(S01_AXI_awready),.S01_AXI_awsize(S01_AXI_awsize),.S01_AXI_awvalid(S01_AXI_awvalid),.S01_AXI_bid(S01_AXI_bid),.S01_AXI_bready(S01_AXI_bready),.S01_AXI_bresp(S01_AXI_bresp),.S01_AXI_bvalid(S01_AXI_bvalid),.S01_AXI_rdata(S01_AXI_rdata),.S01_AXI_rid(S01_AXI_rid),.S01_AXI_rlast(S01_AXI_rlast),.S01_AXI_rready(S01_AXI_rready),.S01_AXI_rresp(S01_AXI_rresp),.S01_AXI_rvalid(S01_AXI_rvalid),.S01_AXI_wdata(S01_AXI_wdata),.S01_AXI_wid(S01_AXI_wid),.S01_AXI_wlast(S01_AXI_wlast),.S01_AXI_wready(S01_AXI_wready),.S01_AXI_wstrb(S01_AXI_wstrb),.S01_AXI_wvalid(S01_AXI_wvalid));
  assign ACLK = clk;
assign ARESETN = rstn;
assign M00_ACLK = clk;
assign M00_ARESETN = rstn;
assign M00_AXI_awready = '0;
assign M00_AXI_bid = '0;
assign M00_AXI_bresp = '0;
assign M00_AXI_bvalid = '0;
assign M00_AXI_wready = '0;
assign S00_ACLK = clk;
assign S00_ARESETN = rstn;
assign S00_AXI_arcache = '0;
assign S00_AXI_arlock = '0;
assign S00_AXI_arprot = '0;
assign S00_AXI_arqos = '0;
assign S00_AXI_awaddr = '0;
assign S00_AXI_awburst = '0;
assign S00_AXI_awcache = '0;
assign S00_AXI_awid = '0;
assign S00_AXI_awlen = '0;
assign S00_AXI_awlock = '0;
assign S00_AXI_awprot = '0;
assign S00_AXI_awqos = '0;
assign S00_AXI_awsize = '0;
assign S00_AXI_awvalid = '0;
assign S00_AXI_bready = '0;
assign S00_AXI_wdata = '0;
assign S00_AXI_wid = '0;
assign S00_AXI_wlast = '0;
assign S00_AXI_wstrb = '0;
assign S00_AXI_wvalid = '0;
assign S01_ACLK = clk;
assign S01_ARESETN = rstn;
assign S01_AXI_arcache = '0;
assign S01_AXI_arid = '0;
assign S01_AXI_arlock = '0;
assign S01_AXI_arprot = '0;
assign S01_AXI_arqos = '0;
assign S01_AXI_awaddr = '0;
assign S01_AXI_awburst = '0;
assign S01_AXI_awcache = '0;
assign S01_AXI_awid = '0;
assign S01_AXI_awlen = '0;
assign S01_AXI_awlock = '0;
assign S01_AXI_awprot = '0;
assign S01_AXI_awqos = '0;
assign S01_AXI_awsize = '0;
assign S01_AXI_awvalid = '0;
assign S01_AXI_bready = '0;
assign S01_AXI_wdata = '0;
assign S01_AXI_wid = '0;
assign S01_AXI_wlast = '0;
assign S01_AXI_wstrb = '0;
assign S01_AXI_wvalid = '0;
  reg [31:0] ai_addr=0;
  reg [4:0] ai_id=0;
  reg ai_valid=0,ai_ready=0;
  assign S00_AXI_araddr=ai_addr;
  assign S00_AXI_arid=ai_id;
  assign S00_AXI_arlen=4'd7;
  assign S00_AXI_arsize=3'd3;
  assign S00_AXI_arburst=2'b01;
  assign S00_AXI_arvalid=ai_valid;
  assign S00_AXI_rready=ai_ready;

  reg [71:0] hdmi_command=0;
  reg hdmi_command_valid=0,frame_toggle=0;
  wire hdmi_command_ready,hdmi_response_valid;
  wire [159:0] hdmi_response;
  wire hdmi_idle,hdmi_running,hdmi_push,hdmi_rready;
  reg manual_arm=0;wire discard_ready;wire [31:0] discard_status;
  hp2_startup_drain drain(.clk(clk),.arm(manual_arm),.ps_resetn(rstn),.pl_resetn(rstn),.hp_reset(!rstn),
   .any_request(S00_AXI_arvalid || S01_AXI_arvalid),.reader_ready(hdmi_rready),
   .rvalid(S01_AXI_rvalid),.rid(S01_AXI_rid),.rresp(S01_AXI_rresp),.rlast(S01_AXI_rlast),
   .drain_ready(discard_ready),.status(discard_status));
  assign S01_AXI_rready=hdmi_rready || discard_ready;
  wire [63:0] hdmi_data;
  wire [7:0] hdmi_len;
  hdmi_candidate_core #(.FRAME_WORDS(64),.DMA_BASE(32'h10000000),.DMA_LIMIT(32'h40000000)) hdmi(
    .csr_clk(clk),.csr_resetn(rstn),.command_valid(hdmi_command_valid),.command_ready(hdmi_command_ready),
    .command(hdmi_command),.response_valid(hdmi_response_valid),.response(hdmi_response),
    .mem_clk(clk),.mem_resetn(rstn),.clock_locked(1'b1),.pixel_frame_toggle(frame_toggle),.sink_fault(1'b0),
    .fifo_ready(1'b1),.fifo_push(hdmi_push),.fifo_data(hdmi_data),
    .araddr(S01_AXI_araddr),.arlen(hdmi_len),.arsize(S01_AXI_arsize),.arburst(S01_AXI_arburst),
    .arvalid(S01_AXI_arvalid),.arready(S01_AXI_arready),
    .rdata(S01_AXI_rdata),.rresp(S01_AXI_rresp),.rlast(S01_AXI_rlast),.rvalid(S01_AXI_rvalid),.rready(hdmi_rready),
    .safe_idle(hdmi_idle),.display_running(hdmi_running));
  assign S01_AXI_arlen=hdmi_len[3:0];


  // Stimulus is an injected boundary fault, not a model of the real PS macro.
  reg injected_valid=0;
  assign M00_AXI_arready=1'b1;
  assign M00_AXI_rvalid=injected_valid;
  assign M00_AXI_rid=6'h20;
  assign M00_AXI_rdata=64'd0;
  assign M00_AXI_rresp=2'd0;
  
  integer cycle=0, ps_count=0, s01_count=0, ar_count=0, phase=0;
  integer ps_first=-1,ps_last=-1,s01_first=-1,stalls=0;
  assign M00_AXI_rlast=ps_count==15;
  always @(posedge clk) if(rstn) begin
    cycle=cycle+1;
    if(M00_AXI_arvalid || S00_AXI_arvalid || S01_AXI_arvalid) ar_count=ar_count+1;
    if(S00_AXI_rvalid) $fatal(1,"Orphan RID20 reached S00");
    if(S01_AXI_rvalid && (S01_AXI_rid!==0 || S01_AXI_rdata!==0))
      $fatal(1,"S01 orphan return mapping differs");
    if(hdmi_push || hdmi_running || !hdmi_idle || hdmi_rready)
      $fatal(1,"Real HDMI core started/consumed without START");
    if(M00_AXI_rvalid && M00_AXI_rready) begin
      if(ps_first<0)ps_first=cycle;ps_last=cycle;ps_count=ps_count+1;
      $display("PS_ACCEPT phase=%0d cycle=%0d count=%0d",phase,cycle,ps_count);
    end
    if(M00_AXI_rvalid && !M00_AXI_rready)stalls=stalls+1;
    if(S01_AXI_rvalid && s01_first<0)s01_first=cycle;
    if(S01_AXI_rvalid && S01_AXI_rready)s01_count=s01_count+1;
    if(cycle<20)$display("TRACE phase=%0d cycle=%0d PS_RV=%b PS_RR=%b S01_RV=%b S01_RR=%b HDMI_RR=%b",
      phase,cycle,M00_AXI_rvalid,M00_AXI_rready,S01_AXI_rvalid,S01_AXI_rready,hdmi_rready);
  end
  task automatic reset_case(input integer p);
    begin
      @(negedge clk);rstn=0;injected_valid=0;phase=p;
      repeat(60)@(negedge clk); // includes initial vendor GSR interval
      cycle=0;ps_count=0;s01_count=0;ar_count=0;ps_first=-1;ps_last=-1;s01_first=-1;stalls=0;
      injected_valid=1; // fault exists before PL interconnect reset release
      repeat(12)@(negedge clk);rstn=1;
    end
  endtask
  integer test=0;
  initial begin
    if($test$plusargs("continuous"))test=1;
    else if($test$plusargs("late"))test=2;
    else test=0;
    reset_case(test);
    repeat(1200)begin
      @(negedge clk);
      if(cycle==299 && (ps_count!=6 || s01_count!=0 || discard_ready || discard_status!=0))
        $fatal(1,"Prefill did not hold PS6/S010 before controlled ARM");
      manual_arm=cycle==300;
      if(test!=1 && ps_count>=16)injected_valid=0;
      if(test==2 && cycle>=600)injected_valid=1;
    end
    if(ar_count!=0 || hdmi_push || hdmi_running || !hdmi_idle || hdmi_rready)
      $fatal(1,"Business path disturbed");
    if(test==0 && (ps_count!=16 || s01_count!=16 || discard_status[2:0]!=2))
      $fatal(1,"Finite return not drained");
    if(test==1 && (ps_count!=262 || s01_count!=256 || discard_status[2:0]!=3 || M00_AXI_rready!==0))
      $fatal(1,"Continuous bound wrong PS=%0d S01=%0d state=%0d",ps_count,s01_count,discard_status[2:0]);
    if(test==2 && (ps_count!=22 || s01_count!=16 || !discard_status[31] || discard_ready))
      $fatal(1,"Late return was silently consumed");
    $display("DEFERRED_DRAIN_FABRIC_PASS case=%0d PS=%0d S01=%0d status=%08x no_AR no_FIFO_push",test,ps_count,s01_count,discard_status);
    $finish;
  end
  initial begin #20000;$fatal(1,"Bounded simulation watchdog");end
endmodule

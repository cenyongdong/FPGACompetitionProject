`timescale 1ns/1ps
module tb_generated_axi3;
  reg clk=0, rstn=0;
  always #5 clk=~clk;
  integer cycles=0, source=0, test_id=0, completed_read=0, completed_write=0;
  reg [31:0] test_addr;
  reg [63:0] test_data;
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
reg [5:0] M00_AXI_bid;
wire  M00_AXI_bready;
reg [1:0] M00_AXI_bresp;
reg  M00_AXI_bvalid;
reg [63:0] M00_AXI_rdata;
reg [5:0] M00_AXI_rid;
reg  M00_AXI_rlast;
wire  M00_AXI_rready;
reg [1:0] M00_AXI_rresp;
reg  M00_AXI_rvalid;
wire [63:0] M00_AXI_wdata;
wire [5:0] M00_AXI_wid;
wire  M00_AXI_wlast;
wire  M00_AXI_wready;
wire [7:0] M00_AXI_wstrb;
wire  M00_AXI_wvalid;
wire  S00_ACLK;
wire  S00_ARESETN;
reg [31:0] S00_AXI_araddr;
reg [1:0] S00_AXI_arburst;
reg [3:0] S00_AXI_arcache;
reg [4:0] S00_AXI_arid;
reg [3:0] S00_AXI_arlen;
reg [1:0] S00_AXI_arlock;
reg [2:0] S00_AXI_arprot;
reg [3:0] S00_AXI_arqos;
wire  S00_AXI_arready;
reg [2:0] S00_AXI_arsize;
reg  S00_AXI_arvalid;
reg [31:0] S00_AXI_awaddr;
reg [1:0] S00_AXI_awburst;
reg [3:0] S00_AXI_awcache;
reg [4:0] S00_AXI_awid;
reg [3:0] S00_AXI_awlen;
reg [1:0] S00_AXI_awlock;
reg [2:0] S00_AXI_awprot;
reg [3:0] S00_AXI_awqos;
wire  S00_AXI_awready;
reg [2:0] S00_AXI_awsize;
reg  S00_AXI_awvalid;
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
reg [63:0] S00_AXI_wdata;
reg [4:0] S00_AXI_wid;
reg  S00_AXI_wlast;
wire  S00_AXI_wready;
reg [7:0] S00_AXI_wstrb;
reg  S00_AXI_wvalid;
wire  S01_ACLK;
wire  S01_ARESETN;
reg [31:0] S01_AXI_araddr;
reg [1:0] S01_AXI_arburst;
reg [3:0] S01_AXI_arcache;
reg [4:0] S01_AXI_arid;
reg [3:0] S01_AXI_arlen;
reg [1:0] S01_AXI_arlock;
reg [2:0] S01_AXI_arprot;
reg [3:0] S01_AXI_arqos;
wire  S01_AXI_arready;
reg [2:0] S01_AXI_arsize;
reg  S01_AXI_arvalid;
reg [31:0] S01_AXI_awaddr;
reg [1:0] S01_AXI_awburst;
reg [3:0] S01_AXI_awcache;
reg [4:0] S01_AXI_awid;
reg [3:0] S01_AXI_awlen;
reg [1:0] S01_AXI_awlock;
reg [2:0] S01_AXI_awprot;
reg [3:0] S01_AXI_awqos;
wire  S01_AXI_awready;
reg [2:0] S01_AXI_awsize;
reg  S01_AXI_awvalid;
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
reg [63:0] S01_AXI_wdata;
reg [4:0] S01_AXI_wid;
reg  S01_AXI_wlast;
wire  S01_AXI_wready;
reg [7:0] S01_AXI_wstrb;
reg  S01_AXI_wvalid;
  ps_ai_axi_interconnect_3_0 dut(
.ACLK(ACLK),
.ARESETN(ARESETN),
.M00_ACLK(M00_ACLK),
.M00_ARESETN(M00_ARESETN),
.M00_AXI_araddr(M00_AXI_araddr),
.M00_AXI_arburst(M00_AXI_arburst),
.M00_AXI_arcache(M00_AXI_arcache),
.M00_AXI_arid(M00_AXI_arid),
.M00_AXI_arlen(M00_AXI_arlen),
.M00_AXI_arlock(M00_AXI_arlock),
.M00_AXI_arprot(M00_AXI_arprot),
.M00_AXI_arqos(M00_AXI_arqos),
.M00_AXI_arready(M00_AXI_arready),
.M00_AXI_arsize(M00_AXI_arsize),
.M00_AXI_arvalid(M00_AXI_arvalid),
.M00_AXI_awaddr(M00_AXI_awaddr),
.M00_AXI_awburst(M00_AXI_awburst),
.M00_AXI_awcache(M00_AXI_awcache),
.M00_AXI_awid(M00_AXI_awid),
.M00_AXI_awlen(M00_AXI_awlen),
.M00_AXI_awlock(M00_AXI_awlock),
.M00_AXI_awprot(M00_AXI_awprot),
.M00_AXI_awqos(M00_AXI_awqos),
.M00_AXI_awready(M00_AXI_awready),
.M00_AXI_awsize(M00_AXI_awsize),
.M00_AXI_awvalid(M00_AXI_awvalid),
.M00_AXI_bid(M00_AXI_bid),
.M00_AXI_bready(M00_AXI_bready),
.M00_AXI_bresp(M00_AXI_bresp),
.M00_AXI_bvalid(M00_AXI_bvalid),
.M00_AXI_rdata(M00_AXI_rdata),
.M00_AXI_rid(M00_AXI_rid),
.M00_AXI_rlast(M00_AXI_rlast),
.M00_AXI_rready(M00_AXI_rready),
.M00_AXI_rresp(M00_AXI_rresp),
.M00_AXI_rvalid(M00_AXI_rvalid),
.M00_AXI_wdata(M00_AXI_wdata),
.M00_AXI_wid(M00_AXI_wid),
.M00_AXI_wlast(M00_AXI_wlast),
.M00_AXI_wready(M00_AXI_wready),
.M00_AXI_wstrb(M00_AXI_wstrb),
.M00_AXI_wvalid(M00_AXI_wvalid),
.S00_ACLK(S00_ACLK),
.S00_ARESETN(S00_ARESETN),
.S00_AXI_araddr(S00_AXI_araddr),
.S00_AXI_arburst(S00_AXI_arburst),
.S00_AXI_arcache(S00_AXI_arcache),
.S00_AXI_arid(S00_AXI_arid),
.S00_AXI_arlen(S00_AXI_arlen),
.S00_AXI_arlock(S00_AXI_arlock),
.S00_AXI_arprot(S00_AXI_arprot),
.S00_AXI_arqos(S00_AXI_arqos),
.S00_AXI_arready(S00_AXI_arready),
.S00_AXI_arsize(S00_AXI_arsize),
.S00_AXI_arvalid(S00_AXI_arvalid),
.S00_AXI_awaddr(S00_AXI_awaddr),
.S00_AXI_awburst(S00_AXI_awburst),
.S00_AXI_awcache(S00_AXI_awcache),
.S00_AXI_awid(S00_AXI_awid),
.S00_AXI_awlen(S00_AXI_awlen),
.S00_AXI_awlock(S00_AXI_awlock),
.S00_AXI_awprot(S00_AXI_awprot),
.S00_AXI_awqos(S00_AXI_awqos),
.S00_AXI_awready(S00_AXI_awready),
.S00_AXI_awsize(S00_AXI_awsize),
.S00_AXI_awvalid(S00_AXI_awvalid),
.S00_AXI_bid(S00_AXI_bid),
.S00_AXI_bready(S00_AXI_bready),
.S00_AXI_bresp(S00_AXI_bresp),
.S00_AXI_bvalid(S00_AXI_bvalid),
.S00_AXI_rdata(S00_AXI_rdata),
.S00_AXI_rid(S00_AXI_rid),
.S00_AXI_rlast(S00_AXI_rlast),
.S00_AXI_rready(S00_AXI_rready),
.S00_AXI_rresp(S00_AXI_rresp),
.S00_AXI_rvalid(S00_AXI_rvalid),
.S00_AXI_wdata(S00_AXI_wdata),
.S00_AXI_wid(S00_AXI_wid),
.S00_AXI_wlast(S00_AXI_wlast),
.S00_AXI_wready(S00_AXI_wready),
.S00_AXI_wstrb(S00_AXI_wstrb),
.S00_AXI_wvalid(S00_AXI_wvalid),
.S01_ACLK(S01_ACLK),
.S01_ARESETN(S01_ARESETN),
.S01_AXI_araddr(S01_AXI_araddr),
.S01_AXI_arburst(S01_AXI_arburst),
.S01_AXI_arcache(S01_AXI_arcache),
.S01_AXI_arid(S01_AXI_arid),
.S01_AXI_arlen(S01_AXI_arlen),
.S01_AXI_arlock(S01_AXI_arlock),
.S01_AXI_arprot(S01_AXI_arprot),
.S01_AXI_arqos(S01_AXI_arqos),
.S01_AXI_arready(S01_AXI_arready),
.S01_AXI_arsize(S01_AXI_arsize),
.S01_AXI_arvalid(S01_AXI_arvalid),
.S01_AXI_awaddr(S01_AXI_awaddr),
.S01_AXI_awburst(S01_AXI_awburst),
.S01_AXI_awcache(S01_AXI_awcache),
.S01_AXI_awid(S01_AXI_awid),
.S01_AXI_awlen(S01_AXI_awlen),
.S01_AXI_awlock(S01_AXI_awlock),
.S01_AXI_awprot(S01_AXI_awprot),
.S01_AXI_awqos(S01_AXI_awqos),
.S01_AXI_awready(S01_AXI_awready),
.S01_AXI_awsize(S01_AXI_awsize),
.S01_AXI_awvalid(S01_AXI_awvalid),
.S01_AXI_bid(S01_AXI_bid),
.S01_AXI_bready(S01_AXI_bready),
.S01_AXI_bresp(S01_AXI_bresp),
.S01_AXI_bvalid(S01_AXI_bvalid),
.S01_AXI_rdata(S01_AXI_rdata),
.S01_AXI_rid(S01_AXI_rid),
.S01_AXI_rlast(S01_AXI_rlast),
.S01_AXI_rready(S01_AXI_rready),
.S01_AXI_rresp(S01_AXI_rresp),
.S01_AXI_rvalid(S01_AXI_rvalid),
.S01_AXI_wdata(S01_AXI_wdata),
.S01_AXI_wid(S01_AXI_wid),
.S01_AXI_wlast(S01_AXI_wlast),
.S01_AXI_wready(S01_AXI_wready),
.S01_AXI_wstrb(S01_AXI_wstrb),
.S01_AXI_wvalid(S01_AXI_wvalid)
);
  assign ACLK = clk;
assign ARESETN = rstn;
assign M00_ACLK = clk;
assign M00_ARESETN = rstn;
assign S00_ACLK = clk;
assign S00_ARESETN = rstn;
assign S01_ACLK = clk;
assign S01_ARESETN = rstn;
  always @(posedge clk) begin
    cycles <= cycles+1;
    if (cycles>100000) $fatal(1,"Generated AXI contract watchdog");
  end
  assign S00_AXI_rready = cycles%5!=0;
  assign S01_AXI_rready = cycles%4!=0;
  assign S00_AXI_bready = cycles%4!=0;
  assign S01_AXI_bready = cycles%5!=0;
  reg read_active=0, write_active=0;
  reg [5:0] returned_rid=0, returned_bid=0;
  integer read_beat=0, write_beat=0;
  assign M00_AXI_arready = !read_active && cycles%3!=0;
  assign M00_AXI_awready = !write_active && !M00_AXI_bvalid && cycles%3!=0;
  assign M00_AXI_wready = write_active && cycles%4!=0;
  always @(posedge clk) begin
    if (!rstn) begin
      read_active<=0; write_active<=0;
      M00_AXI_rvalid<=0; M00_AXI_bvalid<=0;
      M00_AXI_rid<=0; M00_AXI_rdata<=0; M00_AXI_rresp<=0; M00_AXI_rlast<=0;
      M00_AXI_bid<=0; M00_AXI_bresp<=0;
    end else begin
      if(M00_AXI_arvalid && M00_AXI_arready) begin
        if(M00_AXI_arid !== (test_id | (source<<5)) || M00_AXI_araddr !== test_addr ||
           M00_AXI_arlen!==15 || M00_AXI_arsize!==3 || M00_AXI_arburst!==1)
          $fatal(1,"AR route/fields source=%0d id=%0d actual=%0d",source,test_id,M00_AXI_arid);
        read_active<=1; returned_rid<=M00_AXI_arid; read_beat<=0;
      end
      if(M00_AXI_rvalid && M00_AXI_rready) begin
        M00_AXI_rvalid<=0;
        if(read_beat==15) read_active<=0;
        else read_beat<=read_beat+1;
      end
      if(read_active && !M00_AXI_rvalid && cycles%3!=1) begin
        M00_AXI_rvalid<=1; M00_AXI_rid<=returned_rid;
        M00_AXI_rdata<=test_data+read_beat; M00_AXI_rresp<=0;
        M00_AXI_rlast<=read_beat==15;
      end
      if(M00_AXI_awvalid && M00_AXI_awready) begin
        if(M00_AXI_awid !== (test_id | (source<<5)) || M00_AXI_awaddr !== test_addr ||
           M00_AXI_awlen!==15 || M00_AXI_awsize!==3 || M00_AXI_awburst!==1)
          $fatal(1,"AW route/fields source=%0d id=%0d actual=%0d",source,test_id,M00_AXI_awid);
        write_active<=1; returned_bid<=M00_AXI_awid; write_beat<=0;
      end
      if(M00_AXI_wvalid && M00_AXI_wready) begin
        if(M00_AXI_wid !== returned_bid || M00_AXI_wdata !== test_data+write_beat ||
           M00_AXI_wstrb!==8'hff || M00_AXI_wlast !== (write_beat==15))
          $fatal(1,"W data/ID/last source=%0d id=%0d beat=%0d",source,test_id,write_beat);
        write_beat<=write_beat+1;
        if(write_beat==15) begin
          write_active<=0; M00_AXI_bvalid<=1; M00_AXI_bid<=returned_bid; M00_AXI_bresp<=0;
        end
      end
      if(M00_AXI_bvalid && M00_AXI_bready) M00_AXI_bvalid<=0;
    end
  end
  task automatic read_transaction(input integer src,input integer id);
    integer beat;
    begin
      source=src; test_id=id; test_addr=32'h10000+src*4096+id*128;
      test_data=64'h1234000000000000+test_addr;
      @(negedge clk);
      if(src==0) begin
        S00_AXI_araddr=test_addr; S00_AXI_arid=id; S00_AXI_arlen=15;
        S00_AXI_arsize=3; S00_AXI_arburst=1; S00_AXI_arvalid=1;
        do @(posedge clk); while(!S00_AXI_arready);
        @(negedge clk); S00_AXI_arvalid=0;
      end else begin
        S01_AXI_araddr=test_addr; S01_AXI_arid=id; S01_AXI_arlen=15;
        S01_AXI_arsize=3; S01_AXI_arburst=1; S01_AXI_arvalid=1;
        do @(posedge clk); while(!S01_AXI_arready);
        @(negedge clk); S01_AXI_arvalid=0;
      end
      beat=0;
      while(beat<16) begin
        @(posedge clk);
        if(src==0 && S01_AXI_rvalid || src==1 && S00_AXI_rvalid) $fatal(1,"Read returned to wrong source");
        if(src==0 && S00_AXI_rvalid && S00_AXI_rready) begin
          if(S00_AXI_rid!==id[4:0] || S00_AXI_rdata!==test_data+beat ||
             S00_AXI_rresp!==0 || S00_AXI_rlast!==(beat==15)) $fatal(1,"S00 read result mismatch");
          beat=beat+1;
        end
        if(src==1 && S01_AXI_rvalid && S01_AXI_rready) begin
          if(S01_AXI_rid!==id[4:0] || S01_AXI_rdata!==test_data+beat ||
             S01_AXI_rresp!==0 || S01_AXI_rlast!==(beat==15)) $fatal(1,"S01 read result mismatch");
          beat=beat+1;
        end
      end
      @(negedge clk); completed_read=completed_read+1;
    end
  endtask
  task automatic write_transaction(input integer src,input integer id);
    integer beat;
    begin
      source=src; test_id=id; test_addr=32'h20000+src*4096+id*128;
      test_data=64'h9876000000000000+test_addr;
      @(negedge clk);
      if(src==0) begin
        S00_AXI_awaddr=test_addr; S00_AXI_awid=id; S00_AXI_awlen=15;
        S00_AXI_awsize=3; S00_AXI_awburst=1; S00_AXI_awvalid=1;
        do @(posedge clk); while(!S00_AXI_awready);
        @(negedge clk); S00_AXI_awvalid=0;
      end else begin
        S01_AXI_awaddr=test_addr; S01_AXI_awid=id; S01_AXI_awlen=15;
        S01_AXI_awsize=3; S01_AXI_awburst=1; S01_AXI_awvalid=1;
        do @(posedge clk); while(!S01_AXI_awready);
        @(negedge clk); S01_AXI_awvalid=0;
      end
      for(beat=0;beat<16;beat=beat+1) begin
        @(negedge clk);
        if(src==0) begin
          S00_AXI_wid=id; S00_AXI_wdata=test_data+beat;
          S00_AXI_wstrb=8'hff; S00_AXI_wlast=beat==15; S00_AXI_wvalid=1;
          do @(posedge clk); while(!S00_AXI_wready);
          @(negedge clk); S00_AXI_wvalid=0;
        end else begin
          S01_AXI_wid=id; S01_AXI_wdata=test_data+beat;
          S01_AXI_wstrb=8'hff; S01_AXI_wlast=beat==15; S01_AXI_wvalid=1;
          do @(posedge clk); while(!S01_AXI_wready);
          @(negedge clk); S01_AXI_wvalid=0;
        end
      end
      if(src==0) begin
        do @(posedge clk); while(!(S00_AXI_bvalid && S00_AXI_bready));
        if(S00_AXI_bid!==id[4:0] || S00_AXI_bresp!==0 || S01_AXI_bvalid) $fatal(1,"S00 B route mismatch");
      end else begin
        do @(posedge clk); while(!(S01_AXI_bvalid && S01_AXI_bready));
        if(S01_AXI_bid!==id[4:0] || S01_AXI_bresp!==0 || S00_AXI_bvalid) $fatal(1,"S01 B route mismatch");
      end
      @(negedge clk); completed_write=completed_write+1;
    end
  endtask
  integer s,i;
  initial begin
    S00_AXI_araddr='0;
S00_AXI_arburst='0;
S00_AXI_arcache='0;
S00_AXI_arid='0;
S00_AXI_arlen='0;
S00_AXI_arlock='0;
S00_AXI_arprot='0;
S00_AXI_arqos='0;
S00_AXI_arsize='0;
S00_AXI_arvalid='0;
S00_AXI_awaddr='0;
S00_AXI_awburst='0;
S00_AXI_awcache='0;
S00_AXI_awid='0;
S00_AXI_awlen='0;
S00_AXI_awlock='0;
S00_AXI_awprot='0;
S00_AXI_awqos='0;
S00_AXI_awsize='0;
S00_AXI_awvalid='0;
S00_AXI_wdata='0;
S00_AXI_wid='0;
S00_AXI_wlast='0;
S00_AXI_wstrb='0;
S00_AXI_wvalid='0;
S01_AXI_araddr='0;
S01_AXI_arburst='0;
S01_AXI_arcache='0;
S01_AXI_arid='0;
S01_AXI_arlen='0;
S01_AXI_arlock='0;
S01_AXI_arprot='0;
S01_AXI_arqos='0;
S01_AXI_arsize='0;
S01_AXI_arvalid='0;
S01_AXI_awaddr='0;
S01_AXI_awburst='0;
S01_AXI_awcache='0;
S01_AXI_awid='0;
S01_AXI_awlen='0;
S01_AXI_awlock='0;
S01_AXI_awprot='0;
S01_AXI_awqos='0;
S01_AXI_awsize='0;
S01_AXI_awvalid='0;
S01_AXI_wdata='0;
S01_AXI_wid='0;
S01_AXI_wlast='0;
S01_AXI_wstrb='0;
S01_AXI_wvalid='0;
    repeat(16) @(negedge clk);
    rstn=1;
    repeat(16) @(negedge clk);
    for(s=0;s<2;s=s+1) for(i=0;i<32;i=i+1) begin
      read_transaction(s,i);
      write_transaction(s,i);
    end
    if(completed_read!=64 || completed_write!=64) $fatal(1,"Incomplete contract test");
    $display("GENERATED_AXI3_CONTRACT_PASS read_bursts=64 write_bursts=64 read_beats=1024 write_beats=1024 IDs=0..31 sources=2 outstanding=1");
    $finish;
  end
endmodule

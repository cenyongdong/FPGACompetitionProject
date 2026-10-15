`timescale 1ns/1ps
module tb_generated_axi3;
  reg clk=0, rstn=0;
  always #5 clk=~clk;
  integer cycles=0, source=0, test_id=0, completed_read=0, completed_write=0;
  reg [31:0] test_addr;
  reg [63:0] test_data;
  // GENERATED_DECLARATIONS
  // GENERATED_CONNECTIONS
  // GENERATED_CLOCK_RESET
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
    // GENERATED_INPUT_INITIALIZATION
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

`timescale 1ns/1ps
// Actual HP2 fabric plus real, reset HDMI mailbox/control/reader.
// In the first three cases HDMI never STARTs and holds RREADY low.
module tb_hp2_idle;
  reg clk=0, rstn=0;
  always #2.5 clk=~clk;
  // PORTS
  // DUT
  // INPUTS
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
  wire hdmi_idle,hdmi_running,hdmi_push;
  wire [63:0] hdmi_data;
  wire [7:0] hdmi_len;
  hdmi_candidate_core #(.FRAME_WORDS(64),.DMA_BASE(32'h10000000),.DMA_LIMIT(32'h40000000)) hdmi(
    .csr_clk(clk),.csr_resetn(rstn),.command_valid(hdmi_command_valid),.command_ready(hdmi_command_ready),
    .command(hdmi_command),.response_valid(hdmi_response_valid),.response(hdmi_response),
    .mem_clk(clk),.mem_resetn(rstn),.clock_locked(1'b1),.pixel_frame_toggle(frame_toggle),.sink_fault(1'b0),
    .fifo_ready(1'b1),.fifo_push(hdmi_push),.fifo_data(hdmi_data),
    .araddr(S01_AXI_araddr),.arlen(hdmi_len),.arsize(S01_AXI_arsize),.arburst(S01_AXI_arburst),
    .arvalid(S01_AXI_arvalid),.arready(S01_AXI_arready),
    .rdata(S01_AXI_rdata),.rresp(S01_AXI_rresp),.rlast(S01_AXI_rlast),.rvalid(S01_AXI_rvalid),.rready(S01_AXI_rready),
    .safe_idle(hdmi_idle),.display_running(hdmi_running));
  assign S01_AXI_arlen=hdmi_len[3:0];

  reg memory_arready=0,memory_rvalid=0,memory_rlast=0;
  reg [5:0] memory_rid=0;
  reg [63:0] memory_rdata=0;
  assign M00_AXI_arready=memory_arready;
  assign M00_AXI_rvalid=memory_rvalid;
  assign M00_AXI_rid=memory_rid;
  assign M00_AXI_rdata=memory_rdata;
  assign M00_AXI_rresp=2'b00;
  assign M00_AXI_rlast=memory_rlast;

  integer cycles=0,case_id=0,submitted=0,completed=0,ai_beats=0,hdmi_beats=0;
  integer downstream_ar=0,downstream_beats=0,hdmi_ar=0,peak=0;
  integer head=0,tail=0,count=0,beat=0;
  integer no_start_cycles=0,stalled_ar=0,stalled_r=0;
  reg consumed=0,allow_hdmi=0;
  reg [31:0] queue_addr[0:127];
  reg [5:0] queue_id[0:127];
  integer queue_len[0:127];
  reg [31:0] submitted_addr[0:63];
  reg [4:0] submitted_id[0:63];

  function automatic [63:0] data_for(input [31:0] addr,input integer b);
    data_for=64'h51a7000000000000+addr+b*8;
  endfunction

  // All master input changes occur off the sampling edge.
  always @(negedge clk) begin
    if(!rstn) begin
      memory_arready=0;memory_rvalid=0;memory_rlast=0;memory_rid=0;memory_rdata=0;ai_ready=0;
    end else begin
      ai_ready=cycles%80>=40;
      memory_arready=count<8 && cycles%3!=0;
      if(!memory_rvalid || consumed) begin
        if(count>0 && cycles%4!=0) begin
          memory_rvalid=1;memory_rid=queue_id[head];memory_rdata=data_for(queue_addr[head],beat);
          memory_rlast=(beat==queue_len[head]-1);
        end else begin memory_rvalid=0;memory_rlast=0;end
      end
    end
  end

  always @(posedge clk) begin
    if(!rstn) begin
      cycles=0;submitted=0;completed=0;ai_beats=0;hdmi_beats=0;
      downstream_ar=0;downstream_beats=0;hdmi_ar=0;peak=0;
      head=0;tail=0;count=0;beat=0;consumed=0;
      no_start_cycles=0;stalled_ar=0;stalled_r=0;
    end else begin
      cycles=cycles+1;
      if(cycles>20000)$fatal(1,"HP2 idle test watchdog case=%0d done=%0d",case_id,completed);
      if(!allow_hdmi) begin
        no_start_cycles=no_start_cycles+1;
        if(S01_AXI_arvalid!==1'b0)$fatal(1,"HDMI ghost ARVALID before START");
        if(S01_AXI_rready!==1'b0)$fatal(1,"HDMI IDLE RREADY expected 0");
        // Reject even a stalled response; do not count only accepted R beats.
        if(S01_AXI_rvalid!==1'b0)$fatal(1,"AI response leaked to idle HDMI");
      end
      if(S00_AXI_arvalid && !S00_AXI_arready)stalled_ar=stalled_ar+1;
      if(M00_AXI_rvalid && !M00_AXI_rready)stalled_r=stalled_r+1;
      if(S00_AXI_arvalid && S00_AXI_arready) begin
        if(submitted>=64)$fatal(1,"Extra S00 request");
        submitted_addr[submitted]=S00_AXI_araddr;submitted_id[submitted]=S00_AXI_arid;
        submitted=submitted+1;
      end
      if(S01_AXI_arvalid && S01_AXI_arready) begin
        if(!allow_hdmi)$fatal(1,"S01 request without START");
        if(S01_AXI_arid!==0 || S01_AXI_araddr!==(32'h20000000+hdmi_ar*128) || S01_AXI_arlen!==15)
          $fatal(1,"Unexpected real HDMI burst");
        hdmi_ar=hdmi_ar+1;
      end
      if(M00_AXI_arvalid && M00_AXI_arready) begin
        if(count>=8 || tail>=128)$fatal(1,"Memory model queue overflow");
        if(M00_AXI_araddr>=32'h20000000) begin
          if(!allow_hdmi || M00_AXI_arid!==6'd32)$fatal(1,"S01 source bit / ID mapping wrong");
        end else if(M00_AXI_arid[5]!==0)$fatal(1,"S00 source bit set unexpectedly");
        queue_addr[tail]=M00_AXI_araddr;queue_id[tail]=M00_AXI_arid;queue_len[tail]=M00_AXI_arlen+1;
        tail=tail+1;count=count+1;downstream_ar=downstream_ar+1;
        if(count>peak)peak=count;
      end
      consumed=M00_AXI_rvalid && M00_AXI_rready;
      if(consumed) begin
        downstream_beats=downstream_beats+1;
        if(beat==queue_len[head]-1)begin head=head+1;count=count-1;beat=0;end
        else beat=beat+1;
      end
      if(S00_AXI_rvalid && S00_AXI_rready) begin
        if(completed>=submitted || S00_AXI_rid!==submitted_id[completed] ||
           S00_AXI_rdata!==data_for(submitted_addr[completed],ai_beats%8) ||
           S00_AXI_rresp!==0 || S00_AXI_rlast!==(ai_beats%8==7))
          $fatal(1,"S00 RID/data/RESP/LAST mismatch case=%0d submitted=%0d burst=%0d beat=%0d rid=%h resp=%h last=%b data=%h",case_id,submitted,completed,ai_beats,S00_AXI_rid,S00_AXI_rresp,S00_AXI_rlast,S00_AXI_rdata);
        ai_beats=ai_beats+1;
        if(S00_AXI_rlast)completed=completed+1;
      end
      if(S01_AXI_rvalid && S01_AXI_rready) begin
        if(!allow_hdmi || S01_AXI_rid!==0 || S01_AXI_rresp!==0 ||
           S01_AXI_rdata!==(64'h51a7000020000000+hdmi_beats*8) ||
           S01_AXI_rlast!==(hdmi_beats%16==15))$fatal(1,"S01 return mapping/data mismatch");
        hdmi_beats=hdmi_beats+1;
      end
    end
  end

`ifdef TRACE_HP2
  always @(negedge clk) if(rstn && case_id==0 && cycles<20) begin
    #0.001;
    $display("HP2_RESET_TRACE t=%t cycles=%0d reset=%b p0=%b p1=%b S00AR=%b M00AR=%b M00RV=%b S00RV=%b S01RV=%b s00_inner_RV=%b s00_inner_ready=%b",
      $time,cycles,rstn,fabric.s00_couplers.s00_regslice.inst.p_0_in,fabric.s00_couplers.s00_regslice.inst.p_1_in,
      S00_AXI_arvalid,M00_AXI_arvalid,M00_AXI_rvalid,S00_AXI_rvalid,S01_AXI_rvalid,
      fabric.s00_couplers.s00_regslice.inst.m_axi_rvalid,fabric.s00_couplers.s00_regslice.inst.m_axi_rready);
    $display("HP2_AR_TRACE s00_buffer=%b s01_buffer=%b crossbar_out=%b source00=%b source01=%b",
      fabric.s00_couplers_to_xbar_ARVALID,fabric.s01_couplers_to_xbar_ARVALID,fabric.xbar_to_m00_couplers_ARVALID,S00_AXI_arvalid,S01_AXI_arvalid);
  end
`endif

  // The settled RTL reset assertion is checked independently of clock edges.
  always @(negedge rstn) begin
    #0.001;
    if(S01_AXI_arvalid!==1'b0)$fatal(1,"HDMI ARVALID not low after asynchronous reset assertion");
  end

  task automatic reset_case(input integer n);
    begin
      #1.25;rstn=0;ai_valid=0;hdmi_command_valid=0;frame_toggle=0;allow_hdmi=0;case_id=n;
      repeat(12)@(negedge clk);
      #0.75;rstn=1;
      repeat(40)@(negedge clk);
    end
  endtask

  task automatic send_ai;
    integer n;
    begin
      for(n=0;n<64;n=n+1) begin
        @(negedge clk);ai_valid=1;ai_addr=32'h10000000+n*128;
`ifdef PHYSICAL_HP2
        // The real AI bridge hard-wires ARID=0; the routed netlist has legally
        // optimized its unused ID bits. Test that actual contract here.
        ai_id=0;
`else
        case(case_id)
          0:ai_id=0;
          1:ai_id=n%32;
          2:ai_id=31;
          default:ai_id=n%2;
        endcase
`endif
        do @(posedge clk);while(S00_AXI_arready!==1'b1);
      end
      @(negedge clk);ai_valid=0;
    end
  endtask

  task automatic start_hdmi;
    begin
      repeat(12)@(negedge clk);
      allow_hdmi=1;hdmi_command={4'd1,4'd0,32'd1,32'h20000000};hdmi_command_valid=1;
      do @(posedge clk);while(hdmi_command_ready!==1'b1);
      @(negedge clk);hdmi_command_valid=0;
      wait(hdmi_response_valid===1'b1);
      repeat(6)@(negedge clk);frame_toggle=1;
    end
  endtask

  integer test;
  initial begin
    for(test=0;test<4;test=test+1) begin
      reset_case(test);
      if(test==3)fork send_ai();start_hdmi();join
      else send_ai();
      wait(completed==64 && (test!=3 || hdmi_beats==64));
      repeat(40)@(negedge clk);
      if(count!=0 || submitted!=64 || ai_beats!=512 || downstream_beats!=512+(test==3?64:0) ||
         hdmi_ar!=(test==3?4:0) || peak<2 || stalled_r==0)$fatal(1,"Coverage/conservation failure case=%0d peak=%0d Rstall=%0d",test,peak,stalled_r);
      $display("HP2_IDLE_CASE_PASS case=%0d AI_AR=%0d AI_R=%0d HDMI_AR=%0d HDMI_R=%0d downstream_R=%0d peak=%0d idle_cycles=%0d ARstall=%0d Rstall=%0d",test,submitted,ai_beats,hdmi_ar,hdmi_beats,downstream_beats,peak,no_start_cycles,stalled_ar,stalled_r);
    end
    $display("HP2_IDLE_PASS AI_bursts=256 AI_beats=2048 HDMI_bursts=4 HDMI_beats=64 no_START_cases=3 reset_cases=4");
    $finish;
  end
endmodule

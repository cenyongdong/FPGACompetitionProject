`timescale 1ns/1ps
// Original reference RTL only. Memory and FIFO occupancy are explicit stimuli;
// no encrypted IP, silicon clock primitive, DDR controller or TMDS PHY is modeled.
module frame_period_case #(parameter integer ID=0, parameter real HALF_NS=2.5)
 (output reg done=0);
  reg clk=0, rst=1;
  wire hs,vs,de;
  wire [7:0] r,g,b;
  integer edges=0;
  integer active=0;
  real started;
  color_bar dut(clk,rst,hs,vs,de,r,g,b);
  always #(HALF_NS) clk=~clk;
  initial begin repeat(8) @(negedge clk); rst=0; end
  always @(posedge clk) if(!rst && edges==1 && de) active=active+1;
  always @(posedge vs) if(!rst) begin
    edges=edges+1;
    if(edges==1) begin started=$realtime; active=0; end
    if(edges==2) begin
      if(active!=1920*1080) $fatal(1,"CASE %0d active pixels %0d",ID,active);
      if(($realtime-started)<2475000*2*HALF_NS-0.1 ||
         ($realtime-started)>2475000*2*HALF_NS+0.1)
        $fatal(1,"CASE %0d period mismatch",ID);
      $display("FRAME_CASE id=%0d period_ns=%0.3f refresh_hz=%0.6f active=%0d",ID,
        $realtime-started,1.0e9/($realtime-started),active);
      done=1;
    end
  end
endmodule

module tb_hdmi_contract;
  reg clk=0,rst=1,request=0;
  always #2.5 clk=~clk;
  wire burst_req,ack,finished,clear_fifo;
  wire [9:0] burst_len;
  wire [26:0] burst_addr;
  reg [15:0] occupancy=0;
  reg data_valid=0,burst_finish=0;
  integer bursts=0;
  reg memory_busy=0;
  wire fast_done,nominal_done,axi_done;
  axi_read_backpressure_case axi_case(axi_done);
  frame_period_case #(.ID(200),.HALF_NS(2.5)) fast(fast_done);
  // 1ps simulator resolution: 6.734ns is an approximation to 148.5MHz.
  frame_period_case #(.ID(148),.HALF_NS(3.367)) nominal(nominal_done);

  frame_fifo_read #(.MEM_DATA_BITS(64),.ADDR_BITS(27),.BUSRT_BITS(10),
    .FIFO_DEPTH(32768),.BURST_SIZE(16)) reader(
    .rst(rst),.mem_clk(clk),.rd_burst_req(burst_req),.rd_burst_len(burst_len),
    .rd_burst_addr(burst_addr),.rd_burst_data_valid(data_valid),
    .rd_burst_finish(burst_finish),.read_req(request),.read_req_ack(ack),
    .read_finish(finished),.read_addr_0(27'h6020000),.read_addr_1(27'h6020000),
    .read_addr_2(27'h6020000),.read_addr_3(27'h6020000),.read_addr_index(2'b0),
    .read_len(27'd518400),.fifo_aclr(clear_fifo),.wrusedw(occupancy));

  // Transaction-level memory responder: acknowledge a requested burst once.
  // Payload data and full FIFO IP are outside this control-path test.
  always @(negedge clk) begin
    data_valid=0; burst_finish=0;
    if(rst) begin memory_busy=0; bursts=0; end
    else if(burst_req && !memory_busy) begin
      if(burst_len!=16) $fatal(1,"Unexpected burst size");
      memory_busy=1; data_valid=1; burst_finish=1; bursts=bursts+1;
    end else if(!burst_req) memory_busy=0;
  end

  reg raw_vs=0,display_enable=1;
  wire gated_req;
  video_rect_read_data #(.DATA_WIDTH(16)) request_generator(
    .video_clk(clk),.rst(rst),.video_left_offset(12'd0),.video_top_offset(12'd0),
    .video_width(12'd1920),.video_height(12'd1080),.read_req(gated_req),
    .read_req_ack(1'b0),.read_en(),.read_data(16'b0),.timing_hs(1'b0),
    .timing_vs(raw_vs & display_enable),.timing_de(1'b0),.timing_data(16'b0),
    .hs(),.vs(),.de(),.vout_data());

  task start_frame;
    begin
      @(negedge clk); request=1;
      wait(ack===1'b1);
      @(negedge clk); request=0;
      wait(ack===1'b0);
    end
  endtask

  integer before_bursts;
  initial begin
    $dumpfile("control.vcd");
    $dumpvars(0,reader);
    repeat(8) @(negedge clk); rst=0;
    start_frame();
    wait(finished===1'b1);
    if(bursts!=32400) $fatal(1,"Positive control: expected 32400 bursts, got %0d",bursts);
    $display("CONTROL normal_full_frame_completed bursts=%0d words=518400",bursts);
    repeat(8) @(negedge clk);

    // Stop consumption after at least one accepted burst, while frame remains.
    before_bursts=bursts;
    start_frame();
    wait(bursts>before_bursts);
    @(negedge clk); occupancy=16'd32752;
    repeat(16) @(negedge clk);
    before_bursts=bursts;
    repeat(4096) begin
      @(negedge clk);
      if(finished) $fatal(1,"Unexpected completion under sustained FIFO backpressure");
    end
    if(bursts!=before_bursts || reader.state!=2)
      $fatal(1,"Reader did not remain in S_CHECK_FIFO");
    $display("CONTROL stopped_consumer_stalls cycles=4096 state=%0d read_finish=0",reader.state);
    occupancy=0;
    wait(finished===1'b1);
    $display("CONTROL resumed_consumer_completes");

    // The top-level display gate changes a high VS into a falling edge.
    @(negedge clk); raw_vs=1;
    repeat(10) @(negedge clk);
    if(gated_req) $fatal(1,"Unexpected request before VS falling edge");
    display_enable=0;
    repeat(10) @(negedge clk);
    if(!gated_req) $fatal(1,"Display gate did not cause falling-edge read request");
    $display("CONTROL disabling_during_vs_high_creates_read_request");
    $dumpoff;
    wait(fast_done && nominal_done && axi_done);
    $display("HDMI_CONTRACT_TEST_PASS");
    $finish;
  end
  initial begin #40000000; $fatal(1,"40ms simulation watchdog"); end
endmodule

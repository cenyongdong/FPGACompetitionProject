`timescale 1ns/1ps
module full_frame_tests(output reg complete=0);
 reg csr_clk=0,clk=0,resetn=0,valid=0,frame_toggle=0;
 reg [71:0] command=0;wire ready,response_valid,idle;wire [159:0] response;
 wire push,arvalid,rready;wire [31:0] addr;wire [7:0] len;wire [63:0] data;
 reg active=0;reg [31:0] address=0;reg [7:0] index=0,last=0;
 reg [15:0] random_state=16'hade1;
 integer requests=0,accepted=0,pushes=0;
 wire fifo_ready=random_state[0] || random_state[2];
 always #7 csr_clk=~csr_clk;
 always #2.5 clk=~clk;
 hdmi_candidate_core #(.DMA_BASE(32'h30100000),.DMA_LIMIT(32'h38100000)) dut(
  .csr_clk(csr_clk),.csr_resetn(resetn),.command_valid(valid),.command_ready(ready),.command(command),
  .response_valid(response_valid),.response(response),.mem_clk(clk),.mem_resetn(resetn),
  .clock_locked(1'b1),.pixel_frame_toggle(frame_toggle),.fifo_ready(fifo_ready),.fifo_push(push),.fifo_data(data),
  .araddr(addr),.arlen(len),.arsize(),.arburst(),.arvalid(arvalid),.arready(!active),
  .rdata({32'd0,address}+index*8),.rresp(2'b00),.rlast(index==last),.rvalid(active),.rready(rready),.safe_idle(idle));
 always @(negedge clk) random_state={random_state[14:0],random_state[15]^random_state[13]^random_state[12]^random_state[10]};
 always @(posedge clk) if(resetn) begin
   if(arvalid && !active) begin
     if(addr!==32'h30100000+requests*128 || len!=15) $fatal(1,"Full-frame address sequence changed");
     if(({1'b0,addr[11:0]}+128)>4096) $fatal(1,"Burst crosses 4KiB");
     address<=addr;index<=0;last<=len;active<=1;requests=requests+1;
   end
   if(active && rready) begin
     accepted=accepted+1;
     if(index==last) active<=0;else index<=index+1'b1;
   end
   if(push) begin
     if(!fifo_ready || !active || !rready || data!==(64'h30100000+pushes*8)) $fatal(1,"Full-frame data changed under backpressure");
     pushes=pushes+1;
   end
 end
 initial begin
   repeat(8) @(negedge clk);resetn=1;repeat(8) @(negedge clk);
   @(negedge csr_clk);wait(ready);command={4'd1,4'd0,32'd123,32'h30100000};valid=1;
   @(negedge csr_clk);valid=0;wait(response_valid);
   @(negedge clk);frame_toggle=1;
   wait(requests>0);wait(!dut.control.frame_active && !dut.reader.busy);
   if(requests!=32400 || accepted!=518400 || pushes!=518400 || dut.control.faults!=0)
      $fatal(1,"Full-frame transfer count failed");
   $display("CANDIDATE_FULL_FRAME_PASS bursts=32400 words=518400 bytes=4147200 deterministic_backpressure=1");
   complete=1;
 end
 initial begin #20000000; if(!complete) $fatal(1,"Full-frame watchdog");end
endmodule

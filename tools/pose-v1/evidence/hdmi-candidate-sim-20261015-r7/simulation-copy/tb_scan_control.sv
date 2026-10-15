`timescale 1ns/1ps
module scan_control_tests(output reg complete=0);
 reg csr_clk=0,mem_clk=0,resetn=0,locked=1,frame_toggle=0;
 reg cmd_valid=0;reg [71:0] cmd=0;wire cmd_ready,resp_valid;wire [159:0] resp;
 reg fifo_ready=1,allow_ar=1;reg [1:0] slave_resp=0;
 wire push,arvalid,rready,idle;wire [63:0] data;wire [31:0] araddr;wire [7:0] arlen;
 wire [2:0] arsize;wire [1:0] arburst;
 reg active=0;reg [31:0] slave_addr=0;reg [7:0] slave_len=0,slave_index=0;
 integer requests=0,accepted=0,pushes=0,cases=0;
 reg [159:0] snapshot;
 always #7 csr_clk=~csr_clk;
 always #2.5 mem_clk=~mem_clk;
 hdmi_candidate_core #(.FRAME_WORDS(32),.DMA_BASE(32'h10000000),.DMA_LIMIT(32'h11000000)) dut(
   .csr_clk(csr_clk),.csr_resetn(resetn),.command_valid(cmd_valid),.command_ready(cmd_ready),.command(cmd),
   .response_valid(resp_valid),.response(resp),.mem_clk(mem_clk),.mem_resetn(resetn),
   .clock_locked(locked),.pixel_frame_toggle(frame_toggle),.sink_fault(1'b0),.fifo_ready(fifo_ready),.fifo_push(push),.fifo_data(data),
   .araddr(araddr),.arlen(arlen),.arsize(arsize),.arburst(arburst),.arvalid(arvalid),.arready(allow_ar&&!active),
   .rdata({32'd0,slave_addr}+slave_index*8),.rresp(slave_resp),.rlast(slave_index==slave_len),
   .rvalid(active),.rready(rready),.safe_idle(idle));
 always @(posedge mem_clk) begin
   if(!resetn) begin active<=0;slave_index<=0;requests=0;accepted=0;pushes=0;end
   else begin
     if(arvalid && allow_ar && !active) begin
       if(arsize!=3 || arburst!=1 || araddr[6:0]!=0 || arlen!=15) $fatal(1,"Bad candidate AXI request");
       active<=1;slave_addr<=araddr;slave_len<=arlen;slave_index<=0;requests=requests+1;
     end
     if(active && rready) begin
       accepted=accepted+1;
       if(slave_index==slave_len) active<=0;else slave_index<=slave_index+1'b1;
     end
     if(push) begin
       pushes=pushes+1;
       if(!active || !rready || !fifo_ready) $fatal(1,"Core FIFO write not accepted");
     end
     if(idle && (active || arvalid)) $fatal(1,"safe_idle while AXI owns memory");
   end
 end
 task command(input [3:0] op,input [31:0] id,input [31:0] addr);
 begin
   @(negedge csr_clk);wait(cmd_ready);cmd={op,4'b0,id,addr};cmd_valid=1;
   @(negedge csr_clk);cmd_valid=0;
   wait(resp_valid);@(negedge csr_clk);snapshot=resp;
 end endtask
 task frame;
 begin @(negedge mem_clk);frame_toggle=~frame_toggle;repeat(8) @(negedge mem_clk);end
 endtask
 task poll_idle(input [31:0] expected_id);
 begin
   wait(idle);repeat(5) @(negedge mem_clk);command(0,0,0);
   if(!snapshot[0] || snapshot[63:32]!=expected_id) $fatal(1,"Stop acknowledgement missing");
 end endtask
 task finish_frame;
 begin wait(!dut.control.frame_active && !dut.reader.busy);repeat(6) @(negedge mem_clk);end
 endtask
 initial begin
   repeat(8) @(negedge mem_clk);resetn=1;repeat(8) @(negedge mem_clk);
   command(0,0,0);if(!snapshot[0]) $fatal(1,"Default must be stopped");
   command(1,11,32'h10000000);if(snapshot[31]) $fatal(1,"Valid start rejected");
   command(0,0,0);if(snapshot[127:96]!=0) $fatal(1,"Queued start adopted without boundary");
   frame();finish_frame();command(0,0,0);
   if(snapshot[127:96]!=11 || snapshot[95:64]!=32'h10000000 || requests!=2 || pushes!=32) $fatal(1,"First frame mismatch");cases=cases+1;
   command(2,22,32'h10001000);command(0,0,0);
   if(snapshot[127:96]!=11 || !snapshot[4]) $fatal(1,"Flip adopted before boundary");
   command(2,99,32'h10002000);if(!snapshot[31]) $fatal(1,"Pending flip overwritten");
   frame();finish_frame();command(0,0,0);
   if(snapshot[127:96]!=22 || snapshot[95:64]!=32'h10001000 || requests!=4) $fatal(1,"Boundary flip failed");cases=cases+1;

   allow_ar=0;frame();wait(arvalid);command(3,77,0);
   repeat(8) begin @(negedge mem_clk);if(!arvalid || idle || araddr!=32'h10001000) $fatal(1,"Stop withdrew address or falsely idled");end
   fifo_ready=0;allow_ar=1;poll_idle(77);cases=cases+1;
   frame();repeat(20) @(negedge mem_clk);if(arvalid || active) $fatal(1,"New frame after stop");
   command(1,33,32'h10000001);if(!snapshot[31]) $fatal(1,"Unaligned start accepted");
   command(1,33,32'h10ffff80);if(!snapshot[31]) $fatal(1,"Out-of-window frame accepted");cases=cases+1;

   fifo_ready=1;command(1,33,32'h10002000);frame();wait(active);
   slave_resp=2;wait(idle);slave_resp=0;
   command(0,0,0);if(!snapshot[129]) $fatal(1,"AXI fault not propagated");
   command(4,0,0);command(0,0,0);if(snapshot[159:128]!=0) $fatal(1,"Error clear did not release both modules");cases=cases+1;

   fifo_ready=0;command(1,44,32'h10003000);frame();wait(active);locked=0;
   wait(idle);command(0,0,0);if(!snapshot[128]) $fatal(1,"Lost lock not reported");
   locked=1;repeat(8) @(negedge mem_clk);command(4,0,0);cases=cases+1;

   command(1,55,32'h10004000);frame();wait(active);frame();
   wait(idle);command(0,0,0);if(!snapshot[130]) $fatal(1,"Frame overrun did not stop safely");cases=cases+1;
   $display("CANDIDATE_CONTROL_PASS cases=%0d csr_period_ns=14 mem_period_ns=5",cases);complete=1;
 end
 initial begin #1000000; if(!complete) $fatal(1,"Control test watchdog");end
endmodule

`timescale 1ns/1ps
module axi_read_tests(output reg complete=0);
 reg clk=0,resetn=0,valid=0,stop=0,clear_error=0,fifo_ready=1,arready=0,rvalid=0,rlast=0;
 reg [31:0] address=0;reg [7:0] beats=0;reg [63:0] rdata=0;reg [1:0] rresp=0;
 wire reqready,busy,done,error,push,arvalid,rready;wire [63:0] fifo_data;wire [31:0] araddr;wire [7:0] arlen;
 wire [2:0] arsize;wire [1:0] arburst;
 integer accepted=0,pushed=0,cases=0;
 always #2.5 clk=~clk;
 hdmi_axi_read dut(clk,resetn,valid,reqready,address,beats,stop,clear_error,busy,done,error,
   push,fifo_data,fifo_ready,araddr,arlen,arsize,arburst,arvalid,arready,rdata,rresp,rlast,rvalid,rready);
 always @(posedge clk) if(resetn) begin
   if(rvalid && rready) accepted=accepted+1;
   if(push) begin
     pushed=pushed+1;
     if(!(rvalid&&rready) || stop || rresp!=0) $fatal(1,"AXI push without usable handshake");
   end
 end
 task clean;
 begin
   @(negedge clk);resetn=0;valid=0;stop=0;clear_error=0;fifo_ready=1;arready=0;rvalid=0;rlast=0;rresp=0;
   repeat(3) @(negedge clk);resetn=1;accepted=0;pushed=0;
 end endtask
 task issue(input [31:0] a,input [7:0] n);
 begin
   @(negedge clk);address=a;beats=n;valid=1;
   wait(reqready);@(negedge clk);valid=0;
 end endtask
 task accept_address;
 begin
   wait(arvalid);@(negedge clk);arready=1;@(negedge clk);arready=0;
 end endtask
 task beat(input bit last,input [1:0] resp);
 begin
   @(negedge clk);rvalid=1;rlast=last;rresp=resp;rdata=rdata+1;
   wait(rready);@(negedge clk);rvalid=0;rlast=0;rresp=0;
 end endtask
 initial begin
   clean();issue(32'h10000000,16);accept_address();
   for(integer i=0;i<16;i=i+1) beat(i==15,0);
   if(!done || error || accepted!=16 || pushed!=16) $fatal(1,"Normal AXI read failed");
   cases=cases+1;

   clean();issue(32'h10000040,1);wait(arvalid);
   @(negedge clk);stop=1;
   repeat(8) begin @(negedge clk);if(!arvalid || araddr!=32'h10000040 || !busy || done) $fatal(1,"AR withdrawn by stop");end
   fifo_ready=0;accept_address();beat(1,0);
   if(!done || busy || accepted!=1 || pushed!=0) $fatal(1,"Stop at AR did not safely drain");
   cases=cases+1;

   clean();issue(32'h10000080,1);accept_address();
   @(negedge clk);fifo_ready=0;rvalid=1;rlast=1;
   repeat(8) begin @(negedge clk);if(rready || push || done || !busy) $fatal(1,"Unaccepted last beat completed");end
   stop=1;@(negedge clk);
   if(!done || busy || accepted!=1 || pushed!=0) $fatal(1,"Full-FIFO stop drain failed");
   rvalid=0;rlast=0;cases=cases+1;

   clean();issue(32'h10000100,4);accept_address();beat(0,0);beat(1,0);
   if(!done || !error || accepted!=2) $fatal(1,"Early RLAST not detected");cases=cases+1;
   clean();issue(32'h10000180,2);accept_address();beat(0,0);beat(0,0);
   if(!error || !busy || done) $fatal(1,"Missing RLAST falsely released ownership");
   fifo_ready=0;beat(1,0);
   if(!done || busy || accepted!=3 || pushed!=2) $fatal(1,"Malformed burst not drained");cases=cases+1;
   clean();issue(32'h10000200,1);accept_address();beat(1,2);
   if(!done || !error || pushed!=0) $fatal(1,"RRESP error not quarantined");cases=cases+1;

   clean();issue(32'h10000ff8,2);repeat(4) @(negedge clk);
   if(!error || arvalid || busy) $fatal(1,"4KiB crossing accepted");cases=cases+1;
   clear_error=1;@(negedge clk);clear_error=0;
   if(error) $fatal(1,"Idle error clear failed");
   issue(32'h10000001,1);repeat(4) @(negedge clk);
   if(!error || arvalid || busy) $fatal(1,"Misaligned address accepted");cases=cases+1;
   clean();issue(32'h10000000,0);repeat(4) @(negedge clk);
   if(!error || arvalid) $fatal(1,"Zero length accepted");cases=cases+1;
   clean();issue(32'h10000000,17);repeat(4) @(negedge clk);
   if(!error || arvalid) $fatal(1,"Oversized burst accepted");cases=cases+1;
   $display("CANDIDATE_AXI_PASS cases=%0d",cases);complete=1;
 end
 initial begin #100000; if(!complete) $fatal(1,"AXI test watchdog");end
endmodule

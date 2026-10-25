`timescale 1ns/1ps
module deferred_case #(parameter integer N=0)(output reg finished=0);
 reg hp=0,gp=0;always #2.5 hp=~hp;always #5 gp=~gp;
 reg resetn=0,ps=0,pl=0,hpr=1,request=0,reader=0,rv=0,inject_late=0;
 reg [4:0] id=0;reg [1:0] resp=0;
 wire ready,arm,rearm;wire [31:0] status;
 integer accepted=0,arms=0,clears=0;
 wire last=accepted==15;
 mna_gp_ww_itf csr();
 hp2_startup_drain d(.clk(hp),.ps_resetn(ps),.pl_resetn(pl),.hp_reset(hpr),.arm(arm),
  .any_request(request),.reader_ready(reader),.rvalid(rv),.rid(id),.rresp(resp),
  .rlast(last),.drain_ready(ready),.status(status));
 hp2_deferred_control c(.source_clk(hp),.csr_clk(gp),.csr_resetn(resetn),
  .ps_resetn(ps),.pl_resetn(pl),.hp_reset(hpr),.any_request(request),.reader_ready(reader),
  .rvalid(rv),.rid(id),.rresp(resp),.drain_status(status),.pc_status(160'h0c00000000000000),
  .pc_ready(1'b1),.pc_system_resetn(1'b1),.arm(arm),.checker_rearm(rearm),.csr(csr));
 always @(posedge hp)begin
  if(rv&&ready)accepted<=accepted+1;
  if(arm)arms<=arms+1;
  if(rearm)clears<=clears+1;
  if(ready && (request || reader || !ps || !pl || hpr || (rv&&id!=0)))$fatal(1,"unsafe ready");
 end
 always @(negedge hp)if(accepted==16 && !inject_late)rv=0;
 task write(input [31:0] cmd);
  begin @(negedge gp);csr.awwaddr=32'h400b0800;csr.awwdata=cmd;csr.awwvalid=1;
   @(negedge gp);csr.awwvalid=0;end
 endtask
 task settled;
  begin repeat(15)@(negedge gp);if(c.busy)$fatal(1,"missing toggle ACK");end
 endtask
 initial begin
  csr.awwvalid=0;csr.awwaddr=0;csr.awwdata=0;csr.arvalid=0;csr.araddr=0;csr.rready=1;
  repeat(5)@(negedge gp);resetn=1;ps=1;pl=1;hpr=0;rv=1;
  // A genuine deferred consumer must preserve backpressure far beyond 64 quiet cycles.
  repeat(500)@(negedge hp);
  if(accepted!=0 || ready || status!=0)$fatal(1,"consumed before software permission N%0d",N);
  case(N)
   0:begin
    write(32'h534e4150);settled();
    if(c.csr_status!=0 || c.csr_flags[1:0]!=0)$fatal(1,"before evidence changed");
    write(32'h434f4e53);settled();repeat(120)@(negedge hp);
    write(32'h534e4150);settled();
    if(accepted!=16 || arms!=1 || status[2:0]!=2 || !status[25] || c.csr_status!=status || c.csr_flags[7])$fatal(1,"finite drain/SNAPSHOT failed");
    write(32'h43484b52);settled();write(32'h534e4150);settled();
    if(clears!=1 || !c.csr_flags[1])$fatal(1,"post-quiet checker rearm not acknowledged");
    write(32'h434f4e53);settled();
    inject_late=1;rv=1;repeat(100)@(negedge hp);
    if(arms!=1 || accepted!=16 || !c.command_error || !status[31])$fatal(1,"second arm or late consumption");
   end
   1:begin id=1;write(32'h434f4e53);settled();write(32'h534e4150);settled();
    if(arms || accepted || !c.csr_flags[7])$fatal(1,"bad ID enabled");end
   2:begin request=1;repeat(4)@(negedge hp);request=0;write(32'h434f4e53);settled();
    if(arms || accepted || status[2:0]!=5)$fatal(1,"request prior to arm not latched");end
   3:begin rv=0;write(32'h434f4e53);settled();write(32'h534e4150);settled();
    if(arms || accepted || !c.csr_flags[7])$fatal(1,"absent target enabled");end
   4:begin write(32'h43484b52);settled();
    if(clears || !c.command_error)$fatal(1,"checker reset before drain");end
   5:begin write(32'h434f4e53);settled();repeat(120)@(negedge hp);
    resetn=0;repeat(5)@(negedge gp);resetn=1;repeat(15)@(negedge gp);
    write(32'h434f4e53);settled();
    if(arms!=1 || accepted!=16)$fatal(1,"CSR reset rearmed consumer");end
   6:begin resp=2;write(32'h434f4e53);settled();write(32'h534e4150);settled();
    if(arms || accepted || !c.csr_flags[7])$fatal(1,"non-OKAY enabled");end
  endcase
  if(ready)$fatal(1,"test left consumer active");
  $display("DEFERRED_CASE_PASS N=%0d accepted=%0d arm=%0d checker_rearm=%0d",N,accepted,arms,clears);
  finished=1;
 end
endmodule
module tb_deferred_control;
 wire [6:0] done;
 genvar i;generate for(i=0;i<7;i=i+1)begin:g deferred_case #(.N(i)) c(done[i]);end endgenerate
 initial begin wait(&done);$display("DEFERRED_CONTROL_PASS");$finish;end
 initial begin #30000;$fatal(1,"watchdog");end
endmodule

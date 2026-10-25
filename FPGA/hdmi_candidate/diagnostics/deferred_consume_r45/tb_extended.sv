`timescale 1ns/1ps
module trace_case(output reg finished=0);
 reg hp=0,gp=0;always #2.5 hp=~hp;always #5 gp=~gp;
 reg arm=0,rv=0;integer n=0;wire ready;wire [31:0] status;
 wire [127:0] pins={55'd0,(n==15),2'd0,6'd0,ready,rv,2'd0,60'd0};
 wire [31:0] flags={status[2:0],27'd0,2'b11};
 mna_gp_ww_itf csr();
 hp2_startup_drain d(.clk(hp),.ps_resetn(1'b1),.pl_resetn(1'b1),.hp_reset(1'b0),.arm(arm),
 .any_request(1'b0),.reader_ready(1'b0),.rvalid(rv),.rid(5'd0),.rresp(2'd0),.rlast(n==15),.drain_ready(ready),.status(status));
 hp2_cycle_trace t(.source_clk(hp),.csr_clk(gp),.csr_resetn(1'b1),
 .ps_read(pins),.s01_read(pins),.hc2_read(128'd0),.ps_rdata(64'd0),.s01_rdata(64'd0),.hc2_rdata(64'd0),.flags(flags),.csr(csr));
 always @(posedge hp)if(rv&&ready)n<=n+1;
 always @(negedge hp)if(n==16)rv=0;
 reg [31:0] wordvalue;reg [511:0] row;integer lane;
 task read(input [31:0] addr,output [31:0] value);
 begin
  @(negedge gp);csr.araddr=addr;csr.arvalid=1;
  do @(posedge gp);while(!csr.arready);
  @(negedge gp);csr.arvalid=0;
  wait(csr.rvalid);value=csr.rdata;@(negedge gp);
 end
 endtask
 initial begin
  csr.awwvalid=0;csr.awwaddr=0;csr.awwdata=0;csr.arvalid=0;csr.araddr=0;csr.rready=1;
  repeat(40)@(negedge hp);rv=1;
  repeat(300)@(negedge hp);
  if(n!=0 || !t.published0 || t.published1)$fatal(1,"startup capture or deferred bank corrupt");
  arm=1;@(negedge hp);arm=0;repeat(180)@(negedge hp);
  if(n!=16 || !t.published1 || t.csr_count1!=128 || t.csr_index1!=32 || t.csr_cycle1<=t.csr_cycle0)$fatal(1,"controlled trace descriptor");
  read(32'h400b8004,wordvalue);if(wordvalue!=32'h02028010)$fatal(1,"format ABI");
  for(lane=0;lane<16;lane=lane+1)begin
   read(32'h400bb000+32*64+lane*4,wordvalue);row[32*lane+:32]=wordvalue;
  end
  if(row[506:504]!=1 || row[63:0]!=t.csr_cycle1)$fatal(1,"BRAM lane/trigger not actual RUN");
  $display("CONTROLLED_TRACE_PASS firstR=%0d consume=%0d",t.csr_cycle0,t.csr_cycle1);finished=1;
 end
endmodule

module checker_case(output reg finished=0);
 reg clk=0;always #2.5 clk=~clk;
 reg ps=0,rearm=0;reg [127:0] rd=0;
 wire [159:0] status;wire asserted,systemn,ready,seen;
 hp2_protocol_observer d(.clk(clk),.ps_resetn(ps),.diagnostic_rearm(rearm),.ps_read(rd),.ps_rdata(64'd0),.ps_write(153'd0),
 .pc_status(status),.pc_asserted(asserted),.system_resetn(systemn),.checker_ready(ready),.seen_reset_low(seen));
 initial begin
  repeat(60)@(negedge clk);ps=1;
  rd[62]=1;rd[69:64]=6'h20;repeat(15)@(negedge clk);
  if(!status[58] || !status[59] || !seen)$fatal(1,"native anomaly not captured");
  rd[62]=0;repeat(10)@(negedge clk);rearm=1;@(negedge clk);rearm=0;
  repeat(80)@(negedge clk);
  if(status!=0 || !ready || !systemn || !ps || !seen)$fatal(1,"diagnostic checker failed fresh epoch");
  // A valid single-beat read after diagnostic rearm must remain clean.
  rd=0;rd[44:42]=3;rd[46:45]=1;rd[60]=1;rd[61]=1;@(negedge clk);rd[60]=0;
  repeat(3)@(negedge clk);rd[62]=1;rd[63]=1;rd[72]=1;@(negedge clk);rd[62]=0;
  repeat(15)@(negedge clk);if(status!=0)$fatal(1,"valid read failed in new epoch");
  // The same native rule must be detectable again, rather than hidden by old sticky status.
  rd[62]=1;rd[69:64]=6'h20;repeat(15)@(negedge clk);
  if(!status[58] || !status[59])$fatal(1,"fresh native fault hidden");
  $display("NATIVE_CHECKER_REARM_PASS");finished=1;
 end
endmodule
module tb_extended;
 wire [6:0] a;wire [8:0] b;wire trace_done,checker_done;
 genvar i;generate for(i=0;i<7;i=i+1)begin:g deferred_case #(.N(i)) c(a[i]);end
 for(i=0;i<9;i=i+1)begin:h drain_case #(.N(i)) c(b[i]);end endgenerate
 trace_case tr(trace_done);checker_case pc(checker_done);
 initial begin wait((&a)&&(&b)&&trace_done&&checker_done);$display("DEFERRED_EXTENDED_PASS");$finish;end
 initial begin #50000;$fatal(1,"extended watchdog");end
endmodule

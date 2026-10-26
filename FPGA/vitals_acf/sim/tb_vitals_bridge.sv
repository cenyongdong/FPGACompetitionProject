`timescale 1ns/1ps
module tb_vitals_bridge;
 reg clk=0;always #10 clk=~clk;reg resetn=0;
 mna_gp_ww_itf host(),legacy();
 vitals_acf_bridge dut(clk,resetn,host.slave,legacy.master);
 reg old_valid=0;reg[31:0] old_data;integer old_writes=0;
 assign legacy.arready=!old_valid;
 assign legacy.rvalid=old_valid;assign legacy.rdata=old_data;assign legacy.awwready=1;
 always @(posedge clk)begin
  if(!resetn)begin old_valid<=0;old_data<=0;old_writes<=0;end
  else begin
   if(legacy.arvalid&&legacy.arready)begin old_valid<=1;old_data<=legacy.araddr^32'h12345678;end
   if(legacy.rvalid&&legacy.rready)old_valid<=0;
   if(legacy.awwvalid&&legacy.awwready)old_writes<=old_writes+1;
  end
 end
 task rd(input[31:0] addr,input[31:0] expect_data);integer n;reg[31:0] held;begin
  @(negedge clk);host.araddr=addr;host.arvalid=1;host.rready=0;n=0;
  while(!host.arready)begin @(negedge clk);n=n+1;if(n>20)$fatal(1,"Address timeout");end
  @(negedge clk);host.arvalid=0;n=0;
  while(!host.rvalid)begin @(negedge clk);n=n+1;if(n>20)$fatal(1,"Read timeout");end
  held=host.rdata;if(held!==expect_data)$fatal(1,"Wrong target addr=%h data=%h",addr,held);
  repeat(4)begin @(negedge clk);if(!host.rvalid||host.rdata!==held)$fatal(1,"Unstable held response");end
  host.rready=1;@(negedge clk);@(negedge clk);
 end endtask
 task wr(input[31:0] addr,input[31:0] value);begin
  @(negedge clk);host.awwaddr=addr;host.awwdata=value;host.awwvalid=1;
  if(!host.awwready)$fatal(1,"Write not ready");@(negedge clk);host.awwvalid=0;
 end endtask
 initial begin
  host.arvalid=0;host.araddr=0;host.rready=0;host.awwvalid=0;host.awwaddr=0;host.awwdata=0;
  repeat(5)@(negedge clk);resetn=1;
  rd(32'h400b2000,32'h56414301);
  rd(32'h400b0000,32'h523f5678);rd(32'h400b0800,32'h523f5e78);
  rd(32'h400b1000,32'h523f4678);rd(32'h400b2100,32'h523f7778);
  wr(32'h400b0008,12);wr(32'h400b2008,2);wr(32'h400b200c,2);
  wr(32'h400b2010,1);wr(32'h400b2014,7);wr(32'h400b2020,3);wr(32'h400b2020,-2);wr(32'h400b2008,1);
  repeat(40)@(negedge clk);rd(32'h400b2004,2);rd(32'h400b2018,7);
  rd(32'h400b202c,13);wr(32'h400b2028,1);rd(32'h400b202c,32'hfffffffa);rd(32'h400b2030,32'hffffffff);
  if(old_writes!=1)$fatal(1,"ACF write reached old chain");
  $display("VITALS_BRIDGE_PASS");$finish;
 end
 initial begin #100000;$fatal(1,"Test deadline");end
endmodule

`timescale 1ns/1ps
module trace_test_case #(parameter integer FIRST_R=50,FIRST_PL=83,CASE_ID=0)(output reg passed=0);
 reg source_clk=0,csr_clk=0,resetn=0;
 always #2.5 source_clk=~source_clk;
 always #5 csr_clk=~csr_clk;
 reg [127:0] ps=0,s01=0,hc2=0;
 reg [63:0] pd=0,sd=0,hd=0;
 reg [31:0] flags=0;
 integer cycle=0;
 reg [511:0] expected[0:1023];
 mna_gp_ww_itf cpu(),legacy(),trace_csr();
 hdmi_cam_router #(.HDMI_BASE(32'h400b8000),.DECODE_LSB(15)) route(
  .clk(csr_clk),.resetn(resetn),.upstream(cpu.slave),.camera(legacy.master),.hdmi(trace_csr.master));
 hp2_cycle_trace dut(.source_clk(source_clk),.csr_clk(csr_clk),.csr_resetn(resetn),
  .ps_read(ps),.s01_read(s01),.hc2_read(hc2),.ps_rdata(pd),.s01_rdata(sd),.hc2_rdata(hd),.flags(flags),.csr(trace_csr.slave));
 reg lrvalid=0;reg [31:0] lrdata=0;
 assign legacy.arready=!lrvalid || legacy.rready;
 assign legacy.rvalid=lrvalid;assign legacy.rdata=lrdata;assign legacy.awwready=1;
 always @(posedge csr_clk)begin
  if(!resetn)lrvalid<=0;
  else begin
   if(lrvalid && legacy.rready)lrvalid<=0;
   if(legacy.arvalid && legacy.arready)begin lrvalid<=1;lrdata<=legacy.araddr^32'ha5a50000;end
  end
 end
 task drive(input integer n);
  begin
   ps=0;s01=0;hc2=0;
   ps[31:0]=32'h10000000+n;ps[59:32]=28'h1234567;
   ps[60]=0;ps[61]=1;ps[62]=(FIRST_R>=0 && n>=FIRST_R && n<FIRST_R+20);ps[63]=n%2;
   ps[69:64]=32;ps[71:70]=n%4;ps[72]=n%3==0;
   s01[31:0]=32'h20000000+n;s01[72:32]=41'h1abc1234567;
   hc2[31:0]=32'h30000000+n;hc2[72:32]=41'h123c456789a;
   pd=64'haabbccdd00000000^n;sd=64'h1122334400000000^n;hd=64'h5566778800000000^n;
   flags=32'h12345601;flags[1]=(n>=FIRST_PL);
  end
 endtask
 initial drive(0);
 always @(negedge source_clk)drive(cycle);
 always @(posedge source_clk)begin
  if(cycle<1024)expected[cycle]={5'd0,flags,hd,sd,pd,hc2[72:0],s01[72:0],ps[72:0],32'd0,cycle[31:0]};
  cycle=cycle+1;
 end
 task read32(input [31:0] address,output [31:0] value);
  integer limit;reg accepted;
  begin
   @(negedge csr_clk);cpu.araddr=address;cpu.arvalid=1;cpu.rready=0;
   accepted=0;limit=0;
   while(!accepted)begin @(posedge csr_clk);accepted=cpu.arready;limit=limit+1;if(limit>50)$fatal(1,"AR timeout case%0d",CASE_ID);end
   @(negedge csr_clk);cpu.arvalid=0;
   limit=0;
   while(!cpu.rvalid)begin @(negedge csr_clk);limit=limit+1;if(limit>50)$fatal(1,"R timeout case%0d",CASE_ID);end
   value=cpu.rdata;
   repeat(2)begin @(negedge csr_clk);if(!cpu.rvalid || cpu.rdata!==value)$fatal(1,"R backpressure unstable");end
   cpu.rready=1;@(posedge csr_clk);@(negedge csr_clk);cpu.rready=0;
  end
 endtask
 integer bank,i,lane,waits,count,trig,index,expected_count,expected_index;
 reg [31:0] value,status;
 reg [63:0] trigger_cycle;
 reg [511:0] row;
 initial begin
  cpu.araddr=0;cpu.arvalid=0;cpu.rready=0;cpu.awwaddr=0;cpu.awwdata=0;cpu.awwvalid=0;
  #12;@(negedge csr_clk);resetn=1;
  read32(32'h400b9000,value);if(value!==32'hbad00002)$fatal(1,"Unpublished RAM was exposed");
  read32(32'h400b0004,value);if(value!==(32'h400b0004^32'ha5a50000))$fatal(1,"Legacy route changed");
  read32(32'h400b8000,value);if(value!==32'h48505401)$fatal(1,"Trace ABI");
  read32(32'h400b8004,value);if(value!==32'h01028010)$fatal(1,"Trace format");
  waits=0;status=0;
  while((status & (FIRST_R<0?12:15))!=(FIRST_R<0?12:15))begin
   read32(32'h400b8008,status);waits=waits+1;if(waits>100)$fatal(1,"Capture timeout %0d",CASE_ID);
  end
  if(FIRST_R<0 && (status&3)!=0)$fatal(1,"Quiet PS falsely triggered");
  for(bank=0;bank<2;bank=bank+1)begin
   if(bank==0 && FIRST_R<0)begin
    read32(32'h400b9000,value);if(value!==32'hbad00002)$fatal(1,"Pending bank readable");
   end else begin
    trig=bank==0?FIRST_R:FIRST_PL;expected_index=trig<32?trig:32;expected_count=expected_index+96;
    read32(32'h400b8010+bank*32,value);count=value;if(count!=expected_count)$fatal(1,"Count %0d expected %0d",count,expected_count);
    read32(32'h400b8018+bank*32,value);index=value;if(index!=expected_index)$fatal(1,"Trigger index");
    read32(32'h400b8020+bank*32,value);trigger_cycle[31:0]=value;
    read32(32'h400b8024+bank*32,value);trigger_cycle[63:32]=value;
    if(trigger_cycle!=trig)$fatal(1,"Trigger cycle %0d expected %0d",trigger_cycle,trig);
    for(i=0;i<count;i=i+1)begin
     for(lane=0;lane<16;lane=lane+1)begin
      read32(32'h400b9000+bank*8192+i*64+lane*4,value);row[lane*32+:32]=value;
     end
     if(row!==expected[trig-expected_index+i])$fatal(1,"Sample mismatch case%0d bank%0d row%0d cycle%0d",CASE_ID,bank,i,row[63:0]);
    end
    if(count<128)begin
     read32(32'h400b9000+bank*8192+count*64,value);if(value!==32'hbad00003)$fatal(1,"Unwritten tail exposed");
    end
   end
  end
  // Ignored control writes cannot clear captures or affect the datapath.
  @(negedge csr_clk);cpu.awwaddr=32'h400b8000;cpu.awwdata=32'hffffffff;cpu.awwvalid=1;
  @(negedge csr_clk);cpu.awwvalid=0;
  read32(32'h400b8008,value);if(value!==status)$fatal(1,"Ignored write changed capture");
  read32(32'h400bb000,value);if(value!==expected[(FIRST_PL<32?0:FIRST_PL-32)][31:0])$fatal(1,"Frozen capture changed");
  read32(32'h400b8001,value);if(value!==32'hbad00001)$fatal(1,"Unaligned read accepted");
  $display("CYCLE_TRACE_CASE_PASS id=%0d firstR=%0d firstPL=%0d",CASE_ID,FIRST_R,FIRST_PL);passed=1;
 end
endmodule

module tb_hp2_cycle_trace;
 wire a,b,c;
 trace_test_case #(.CASE_ID(0)) normal(a);
 trace_test_case #(.FIRST_R(0),.FIRST_PL(0),.CASE_ID(1)) initial_high(b);
 trace_test_case #(.FIRST_R(-1),.FIRST_PL(83),.CASE_ID(2)) no_return(c);
 initial begin wait(a && b && c);$display("HP2_CYCLE_TRACE_PASS");$finish;end
 initial begin #5000000;$fatal(1,"Cycle trace watchdog");end
endmodule

`timescale 1ns/1ps
module protocol_case #(parameter integer CASE_ID=0)(output reg passed=0);
 reg clk=0,csr_clk=0,csr_resetn=0;
 always #2.5 clk=~clk;
 always #5 csr_clk=~csr_clk;
 reg ps_resetn=(CASE_ID==7);
 reg [127:0] ps=0;
 reg [63:0] data=0;
 reg [152:0] wr=0;
 wire [159:0] status;
 wire asserted,sysresetn,ready,seen;
 wire [31:0] flags={3'd0,asserted,seen,ready,sysresetn,24'd0,ps_resetn};
 hp2_protocol_observer monitor(.clk(clk),.ps_resetn(ps_resetn),.ps_read(ps),.ps_rdata(data),
  .ps_write(wr),.pc_status(status),.pc_asserted(asserted),.system_resetn(sysresetn),
  .checker_ready(ready),.seen_reset_low(seen));
 mna_gp_ww_itf cpu();
 hp2_protocol_trace trace(.source_clk(clk),.csr_clk(csr_clk),.csr_resetn(csr_resetn),
  .ps_read(ps),.ps_rdata(data),.ps_write(wr),.pc_status(status),.flags(flags),.csr(cpu.slave));
 reg [575:0] expected[0:4095];
 integer cycle=0;
 always @(posedge clk)begin
  if(cycle<4096)expected[cycle]={30'd0,status,flags,wr,data,ps[72:0],32'd0,cycle[31:0]};
  cycle=cycle+1;
 end
 task ticks(input integer n);begin repeat(n)@(negedge clk);end endtask
 task request(input [5:0] id,input [3:0] len);
  begin ps[37:32]=id;ps[41:38]=len;ps[60]=1;ps[61]=1;ticks(1);ps[60]=0;ticks(4);end
 endtask
 task read32(input [13:0] address,output [31:0] value);
  integer limit;reg accepted;
  begin
   @(negedge csr_clk);cpu.araddr=32'h400b4000+address;cpu.arvalid=1;cpu.rready=0;
   accepted=0;limit=0;
   while(!accepted)begin @(posedge csr_clk);accepted=cpu.arready;limit=limit+1;if(limit>50)$fatal(1,"AR timeout case%0d",CASE_ID);end
   @(negedge csr_clk);cpu.arvalid=0;limit=0;
   while(!cpu.rvalid)begin @(negedge csr_clk);limit=limit+1;if(limit>50)$fatal(1,"R timeout case%0d",CASE_ID);end
   value=cpu.rdata;
   repeat(2)begin @(negedge csr_clk);if(!cpu.rvalid || cpu.rdata!==value)$fatal(1,"CSR backpressure case%0d",CASE_ID);end
   cpu.rready=1;@(posedge csr_clk);@(negedge csr_clk);cpu.rready=0;
  end
 endtask
 integer wanted,i,lane,count,index,capture_fd;
 reg [31:0] value,header;
 reg [63:0] trigger_cycle;
 reg [159:0] first;
 reg [575:0] row;
 initial begin
  cpu.araddr=0;cpu.arvalid=0;cpu.rready=0;cpu.awwaddr=0;cpu.awwdata=0;cpu.awwvalid=0;
  ps[44:42]=3;ps[46:45]=1;wr[44:42]=3;wr[46:45]=1;
  if(CASE_ID==7)begin ps[62]=1;ps[69:64]=32;end
  ticks(80);
  if(CASE_ID!=7)begin
   ticks(24);ps_resetn=1;ticks(20);
   if(status!==0)$fatal(1,"Reset baseline case%0d status=%h",CASE_ID,status);
  end
  wanted=-1;
  case(CASE_ID)
   0,4:begin
    request(7,1);ps[69:64]=7;ps[62]=1;ps[63]=0;data=64'hf0123456789abcde;
    ticks(100);if(status!==0)$fatal(1,"Legal backpressure was reported case%0d %h",CASE_ID,status);
    ps[63]=1;ticks(1);ps[72]=1;ticks(1);ps[62]=0;ps[63]=0;ps[72]=0;
    if(CASE_ID==0)begin
     wr[37:32]=9;wr[60]=1;wr[61]=1;ticks(1);wr[60]=0;ticks(4);
     wr[125:62]=64'hfedcba9876543210;wr[131:126]=9;wr[139:132]=8'hff;
     wr[140]=1;wr[141]=1;wr[142]=1;ticks(1);wr[141]=0;wr[140]=0;ticks(4);
     wr[148:143]=9;wr[151]=1;wr[152]=1;ticks(1);wr[151]=0;
    end
   end
   1:begin ps[62]=1;ps[69:64]=32;wanted=59;end
   2:begin ps_resetn=0;ticks(24);ps_resetn=1;ps[62]=1;ps[69:64]=32;wanted=61;end
   3:begin request(7,3);ps[69:64]=7;ps[62]=1;ps[63]=1;ps[72]=1;wanted=58;ticks(1);ps[62]=0;end
   5:begin request(7,0);ps[69:64]=7;ps[62]=1;ps[72]=1;data=1;ticks(12);data=2;wanted=62;end
   6:begin wr[37:32]=9;wr[60]=1;wr[61]=1;ticks(1);wr[60]=0;ticks(4);wr[148:143]=9;wr[151]=1;wanted=32;end
   7:wanted=59;
   8:begin
    // Real M00 permits eight outstanding bursts; IDs on the two branches
    // differ in bit5. Legal responses may return in reverse ID order.
    for(i=0;i<8;i=i+1)request((i%2)*32+i/2,0);
    for(i=7;i>=0;i=i-1)begin
     ps[69:64]=(i%2)*32+i/2;ps[62]=1;ps[63]=1;ps[72]=1;
     data=64'hfedcba9876543200+i;ticks(1);ps[62]=0;ticks(2);
    end
   end
   9:begin request(32,0);ps[69:64]=0;ps[62]=1;ps[72]=1;wanted=59;end
  endcase
  ticks(170);
  if(wanted>=0 && !status[wanted])$fatal(1,"Expected check%0d case%0d actual=%h",wanted,CASE_ID,status);
  if(wanted<0 && status!==0)$fatal(1,"Normal traffic failed case%0d actual=%h",CASE_ID,status);
  if(CASE_ID==7 && seen)$fatal(1,"Unobserved reset was claimed");
  @(negedge csr_clk);csr_resetn=1;
  read32(0,value);if(value!==32'h48505002)$fatal(1,"ABI");
  read32(4,value);if(value!==32'h02018012)$fatal(1,"format");
  read32(8,header);
  if(wanted<0)begin
   if(header[1:0]!=0)$fatal(1,"False capture");
   read32(14'h1000,value);if(value!==32'hbad00002)$fatal(1,"Pending RAM exposed");
  end else begin
   if(header[1:0]!=3)$fatal(1,"No published trace case%0d",CASE_ID);
   read32(14'h10,value);count=value;read32(14'h18,value);index=value;
   read32(14'h20,value);trigger_cycle[31:0]=value;
   read32(14'h24,value);trigger_cycle[63:32]=value;
   if(count!=128 || index!=32)$fatal(1,"Unexpected capture geometry %d %d",count,index);
   for(lane=0;lane<5;lane=lane+1)begin read32(14'h30+4*lane,value);first[32*lane+:32]=value;end
   if(first!==expected[trigger_cycle][545:386] || first==0)$fatal(1,"First status mismatch");
   if(CASE_ID==3)begin
    capture_fd=$fopen("native-protocol-case3.json","w");
    $fwrite(capture_fd,"{\"abi\":%0d,\"format\":%0d,\"boot_id\":\"SIMULATION_NOT_BOARD\",\"status\":%0d,\"capture\":{\"count\":%0d,\"trigger_index\":%0d,\"trigger_cycle\":%0d,\"first_status\":%0d,\"samples\":[",32'h48505001,32'h01018012,header,count,index,trigger_cycle,first);
   end
   for(i=0;i<count;i=i+1)begin
    if(CASE_ID==3)$fwrite(capture_fd,"%s[",i==0?"":",");
    for(lane=0;lane<18;lane=lane+1)begin
     read32(lane<16 ? 14'h1000+i*64+lane*4 : 14'h3000+i*8+(lane-16)*4,value);
     row[32*lane+:32]=value;
     if(CASE_ID==3)$fwrite(capture_fd,"%s%0d",lane==0?"":",",value);
    end
    if(CASE_ID==3)$fwrite(capture_fd,"]");
    if(row!==expected[trigger_cycle-index+i])$fatal(1,"Full raw word mismatch case%0d row%0d",CASE_ID,i);
   end
   if(CASE_ID==3)begin $fwrite(capture_fd,"]}}\n");$fclose(capture_fd);end
   // Native status clears on functional reset; frozen evidence must survive.
   @(negedge clk);ps_resetn=0;ps[62]=0;wr[151]=0;ticks(24);
   if(status!==0)$fatal(1,"Native reset failed to clear");
   @(negedge csr_clk);csr_resetn=0;repeat(3)@(negedge csr_clk);csr_resetn=1;
   cpu.awwvalid=1;cpu.awwaddr=32'h400b4000;cpu.awwdata=32'hffffffff;
   repeat(3)@(negedge csr_clk);cpu.awwvalid=0;
   read32(14'h30,value);if(value!==first[31:0])$fatal(1,"Frozen evidence changed after resets/write");
  end
  $display("HP2_PROTOCOL_CASE_PASS case=%0d expected_check=%0d",CASE_ID,wanted);passed=1;
 end
endmodule

module tb_hp2_protocol_ids;
 wire [1:0] passed;
 protocol_case #(.CASE_ID(8)) correct_ids(.passed(passed[0]));
 protocol_case #(.CASE_ID(9)) wrong_high_id(.passed(passed[1]));
 initial begin wait(&passed);$display("HP2_PROTOCOL_IDS_PASS eight_outstanding_and_bit5");$finish;end
 initial begin #5000000;$fatal(1,"ID simulation timeout %b",passed);end
endmodule

module tb_hp2_protocol;
 wire [7:0] passed;
 genvar i;
 generate for(i=0;i<8;i=i+1)begin:cases
  protocol_case #(.CASE_ID(i)) test_case(.passed(passed[i]));
 end endgenerate
 initial begin wait(&passed);$display("HP2_PROTOCOL_PASS native_checker_full_bus_raw_capture");$finish;end
 initial begin #5000000;$fatal(1,"Protocol simulation timeout %b",passed);end
endmodule

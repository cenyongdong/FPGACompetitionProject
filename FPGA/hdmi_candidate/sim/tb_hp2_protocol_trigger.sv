`timescale 1ns/1ps
module trigger_case #(parameter integer CASE_ID=0)(output reg passed=0);
 reg clk=0,gp=0,resetn=0;always #2.5 clk=~clk;always #5 gp=~gp;
 reg [159:0] status=0;wire [31:0] flags=0;
 mna_gp_ww_itf cpu();
 hp2_protocol_trace trace(.source_clk(clk),.csr_clk(gp),.csr_resetn(resetn),
 .ps_read(128'd0),.ps_rdata(64'd0),.ps_write(153'd0),.pc_status(status),.flags(flags),.csr(cpu.slave));
 task ticks(input integer n);begin repeat(n)@(negedge clk);end endtask
 task read32(input [13:0] address,output [31:0] value);
  integer limit;reg accepted;
  begin
   @(negedge gp);cpu.araddr=32'h400b4000+address;cpu.arvalid=1;cpu.rready=0;
   accepted=0;limit=0;
   while(!accepted)begin @(posedge gp);accepted=cpu.arready;limit=limit+1;if(limit>50)$fatal(1,"AR timeout");end
   @(negedge gp);cpu.arvalid=0;limit=0;
   while(!cpu.rvalid)begin @(negedge gp);limit=limit+1;if(limit>50)$fatal(1,"R timeout");end
   value=cpu.rdata;repeat(2)begin @(negedge gp);if(!cpu.rvalid||cpu.rdata!==value)$fatal(1,"CSR changed under stall");end
   cpu.rready=1;@(posedge gp);@(negedge gp);cpu.rready=0;
  end
 endtask
 reg [159:0] recommendation,first,mask,witness;reg [63:0] first_cycle,witness_cycle;
 reg [575:0] row;reg [31:0] value,header;integer lane,index,count;
 initial begin
  cpu.araddr=0;cpu.arvalid=0;cpu.rready=0;cpu.awwaddr=0;cpu.awwdata=0;cpu.awwvalid=0;
  recommendation=0;
  if(CASE_ID==2)recommendation[67]=1;
  else begin recommendation[92]=1;recommendation[93]=1;recommendation[95]=1;end
  ticks(80);status=recommendation;ticks(180);
  if(CASE_ID==1)status[59]=1;
  if(CASE_ID==2)status[62]=1;
  if(CASE_ID==3)status[159]=1;
  ticks(180);@(negedge gp);resetn=1;
  read32(0,value);if(value!==32'h48505002)$fatal(1,"ABI");
  read32(4,value);if(value!==32'h02018012)$fatal(1,"format");
  read32(8,header);read32(14'h6c,value);if(value!==1)$fatal(1,"First indication missing");
  for(lane=0;lane<5;lane=lane+1)begin
   read32(14'h50+lane*4,value);witness[32*lane+:32]=value;
   read32(14'h70+lane*4,value);mask[32*lane+:32]=value;
  end
  read32(14'h64,value);witness_cycle[31:0]=value;read32(14'h68,value);witness_cycle[63:32]=value;
  if(witness!==recommendation || witness_cycle!==64'd80)$fatal(1,"First indication was overwritten case%0d cycle%0d",CASE_ID,witness_cycle);
  if(|(recommendation&mask))$fatal(1,"Recommendation entered error trigger");
  if(CASE_ID==0)begin
   if(header[1:0]!==0)$fatal(1,"Recommendation consumed error window");
  end else begin
   if(header[1:0]!==3)$fatal(1,"Hard error window missing");
   read32(14'h10,value);count=value;read32(14'h18,value);index=value;
   if(count!=128||index!=32)$fatal(1,"Capture geometry");
   for(lane=0;lane<5;lane=lane+1)begin read32(14'h30+lane*4,value);first[32*lane+:32]=value;end
   read32(14'h20,value);first_cycle[31:0]=value;read32(14'h24,value);first_cycle[63:32]=value;
   if(first!==status || first_cycle!==64'd260)$fatal(1,"Error trigger replaced by recommendation case%0d cycle%0d",CASE_ID,first_cycle);
   for(lane=0;lane<18;lane=lane+1)begin
    read32(lane<16?14'h1000+index*64+lane*4:14'h3000+index*8+(lane-16)*4,value);row[32*lane+:32]=value;
   end
   if(row[545:386]!==status || row[63:0]!==first_cycle)$fatal(1,"Full raw error status lost");
  end
  // GP reset must not erase either autonomous source witness.
  status=0;@(negedge gp);resetn=0;repeat(4)@(negedge gp);resetn=1;
  // Source evidence survives GP reset, while the CSR copy must republish.
  // Poll the documented publication bit before reading the frozen fields.
  read32(14'h6c,value);index=0;
  while(value!==1)begin
   index=index+1;if(index>16)$fatal(1,"Witness did not republish after GP reset");
   read32(14'h6c,value);
  end
  for(lane=0;lane<5;lane=lane+1)begin read32(14'h50+lane*4,value);witness[32*lane+:32]=value;end
  read32(14'h64,value);witness_cycle[31:0]=value;read32(14'h68,value);witness_cycle[63:32]=value;
  if(witness!==recommendation || witness_cycle!==64'd80)$fatal(1,"Source witness changed after GP reset");
  $display("HP2_PROTOCOL_REPUBLICATION_PASS case%0d polls%0d",CASE_ID,index);
  $display("HP2_PROTOCOL_TRIGGER_CASE_PASS %0d",CASE_ID);passed=1;
 end
endmodule
module tb_hp2_protocol_trigger;
 wire [3:0] passed;genvar i;
 generate for(i=0;i<4;i=i+1)begin:cases trigger_case #(.CASE_ID(i)) t(.passed(passed[i]));end endgenerate
 initial begin wait(&passed);$display("HP2_PROTOCOL_TRIGGER_PASS");$finish;end
 initial begin #5000000;$fatal(1,"Trigger simulation timeout");end
endmodule

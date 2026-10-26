`timescale 1ns/1ps
module tb_vitals_acf;
 reg clk=0;always #10 clk=~clk;
 reg resetn=0,wr_valid=0,rd_valid=0,rsp_ready=1;
 reg [7:0] wr_addr=0,rd_addr=0;reg [31:0] wr_data=0;
 wire wr_ready,rd_ready,rsp_valid;wire [31:0] rsp_data;
 vitals_acf_csr dut(.*);
 reg [31:0] config_words[0:7];reg [31:0] inputs[0:2047];reg [47:0] expected[0:511];
 reg [31:0] a,b;reg [47:0] actual;integer c,n,last,i,k,elapsed;string file_name;
 task write_word(input [7:0] addr,input [31:0] data);begin
  @(negedge clk);wr_addr=addr;wr_data=data;wr_valid=1;
  @(negedge clk);wr_valid=0;
 end endtask
 task read_word(input [7:0] addr,output [31:0] value);integer wait_cycles;begin
  @(negedge clk);rd_addr=addr;rd_valid=1;wait_cycles=0;
  while(!rd_ready)begin @(negedge clk);wait_cycles=wait_cycles+1;if(wait_cycles>20)$fatal(1,"CSR not ready");end
  @(negedge clk);rd_valid=0;wait_cycles=0;
  while(!rsp_valid)begin @(negedge clk);wait_cycles=wait_cycles+1;if(wait_cycles>20)$fatal(1,"CSR response timeout");end
  value=rsp_data;@(negedge clk);
 end endtask
 task check_fault;begin read_word(4,a);if(!(a&32'h100))$fatal(1,"Missing fault");end endtask
 initial begin
  repeat(5)@(negedge clk);resetn=1;read_word(0,a);if(a!==32'h56414301)$fatal(1,"ABI");
  $readmemh("cases.hex",config_words);
  for(c=0;c<4;c=c+1)begin
   n=config_words[2*c];last=config_words[2*c+1];
   file_name=$sformatf("input%0d.hex",c);$readmemh(file_name,inputs,0,n-1);
   file_name=$sformatf("expected%0d.hex",c);$readmemh(file_name,expected,0,last);
   write_word(8,2);write_word(12,n);write_word(16,last);write_word(20,c+1);
   for(i=0;i<n;i=i+1)write_word(32,inputs[i]);
   read_word(36,a);if(a!==n)$fatal(1,"Load count");write_word(8,1);
   elapsed=0;while(!dut.done)begin @(negedge clk);elapsed=elapsed+1;if(elapsed>4000000)$fatal(1,"Kernel hang");end
   read_word(4,a);if(a!==2)$fatal(1,"Completion status");read_word(24,a);if(a!==c+1)$fatal(1,"Result identity");
   read_word(28,a);$display("CASE %0d n=%0d lag=%0d cycles=%0d",c,n,last,a);
   for(k=0;k<=last;k=k+1)begin
    write_word(40,k);read_word(44,a);read_word(48,b);actual={b[15:0],a};
    if(actual!==expected[k])$fatal(1,"Dot mismatch case=%0d lag=%0d got=%h expected=%h",c,k,actual,expected[k]);
    if(b[31:16]!=={16{b[15]}})$fatal(1,"Missing sign extension");
   end
  end
  // Partial input, oversized configuration, and invalid 18-bit values reject.
  write_word(8,2);write_word(12,3);write_word(16,1);write_word(20,11);write_word(32,1);write_word(8,1);check_fault();
  write_word(8,2);write_word(12,2049);check_fault();
  write_word(8,2);write_word(12,3);write_word(16,512);check_fault();
  write_word(8,2);write_word(12,3);write_word(32,65536);check_fault();
  // A busy write faults the current batch; local reset cancels compute only.
  write_word(8,2);write_word(12,32);write_word(16,30);write_word(20,12);
  for(i=0;i<32;i=i+1)write_word(32,i);write_word(8,1);write_word(8,1);check_fault();
  write_word(8,2);repeat(120)@(negedge clk);read_word(4,a);if(a!==0)$fatal(1,"Reset replayed batch");read_word(24,a);if(a!==0)$fatal(1,"Late completion");
  // Hold an accepted response while a new CSR command is received.
  rsp_ready=0;@(negedge clk);rd_valid=1;rd_addr=0;@(negedge clk);rd_valid=0;
  wait(rsp_valid);a=rsp_data;write_word(12,4);repeat(10)begin @(negedge clk);if(!rsp_valid||rsp_data!==a||rd_ready)$fatal(1,"Read backpressure");end
  rsp_ready=1;@(negedge clk);
  $display("VITALS_ACF_PASS");$finish;
 end
 initial begin #200000000;$fatal(1,"Simulation deadline");end
endmodule

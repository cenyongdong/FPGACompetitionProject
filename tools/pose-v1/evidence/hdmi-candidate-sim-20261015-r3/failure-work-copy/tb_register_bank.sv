`timescale 1ns/1ps
module register_bank_tests(output reg complete=0);
 reg clk=0,resetn=0,write_valid=0,command_ready=0,response_valid=0;
 reg [7:0] offset=0,read_offset=0;reg [31:0] data=0;reg [3:0] strobe=15;
 reg [159:0] response=0;
 wire write_ready,command_valid;wire [71:0] command;wire [31:0] read_data;
 always #7 clk=~clk;
 hdmi_register_bank dut(clk,resetn,write_valid,write_ready,offset,data,strobe,read_offset,read_data,
  command_valid,command_ready,command,response_valid,response);
 task write(input [7:0] a,input [31:0] v,input [3:0] s);
 begin @(negedge clk);wait(write_ready);offset=a;data=v;strobe=s;write_valid=1;
  @(negedge clk);write_valid=0;
 end endtask
 initial begin
  repeat(4) @(negedge clk);resetn=1;#1;
  if(read_data!=32'h48444d01) $fatal(1,"CSR ABI marker missing");
  write(4,32'h12340000,12);write(4,32'h00005678,3);write(8,32'hdeadbeef,15);
  write(12,2,15);
  repeat(8) begin @(negedge clk);
    if(!command_valid || write_ready || command!={4'd2,4'd0,32'hdeadbeef,32'h12345678}) $fatal(1,"CSR payload changed before acceptance");
  end
  command_ready=1;@(negedge clk);if(command_valid || !write_ready) $fatal(1,"CSR queue did not retire");
  response=160'h0000001100000022000000330000004400000055;response_valid=1;
  @(negedge clk);response_valid=0;read_offset=16;#1;if(read_data!=32'h55) $fatal(1,"CSR snapshot status mismatch");
  read_offset=28;#1;if(read_data!=32'h22) $fatal(1,"CSR snapshot ID mismatch");
  read_offset=40;#1;if(read_data!=1) $fatal(1,"CSR response generation mismatch");
  write(12,2,1);read_offset=44;#1;if(!read_data[2] || command_valid) $fatal(1,"Partial command executed");
  write(44,1,1);#1;if(read_data[2]) $fatal(1,"CSR error clear failed");
  $display("CANDIDATE_CSR_PASS byte_strobes=1 stable_mailbox=1 atomic_snapshot=1 rejected_partial_command=1");complete=1;
 end
 initial begin #100000; if(!complete) $fatal(1,"CSR test watchdog");end
endmodule

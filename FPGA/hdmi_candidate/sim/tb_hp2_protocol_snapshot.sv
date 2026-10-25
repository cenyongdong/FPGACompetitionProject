`timescale 1ns/1ps
module pipeline_pulse_case(output reg passed=0);
 reg clk=0,gp=0;always #2.5 clk=~clk;always #5 gp=~gp;
 reg [159:0] status=0;mna_gp_ww_itf cpu();
 hp2_protocol_trace dut(.source_clk(clk),.csr_clk(gp),.csr_resetn(1'b0),
 .ps_read(128'd0),.ps_rdata(64'd0),.ps_write(153'd0),.pc_status(status),.flags(32'd0),.csr(cpu.slave));
 initial begin
  cpu.arvalid=0;cpu.rready=0;cpu.awwvalid=0;
  repeat(80)@(negedge clk);status[95]=1;
  @(negedge clk);status=160'd1<<59;
  @(negedge clk);status=0;
  repeat(12)@(negedge clk);
  if(!dut.any_seen || dut.any_pc_status!==(160'd1<<95) || dut.any_cycle!==64'd80)
   $fatal(1,"Single-cycle first indication/data/cycle misaligned");
  $display("HP2_PIPELINE_SINGLE_CYCLE_PASS");passed=1;
 end
endmodule
module tb_pipeline_with_pulse;
 wire [4:0] passed;genvar i;
 generate for(i=0;i<4;i=i+1)begin:cases trigger_case #(.CASE_ID(i)) t(.passed(passed[i]));end endgenerate
 pipeline_pulse_case pulse(.passed(passed[4]));
 initial begin wait(&passed);$display("HP2_PIPELINE_ALL_PASS");$finish;end
 initial begin #5000000;$fatal(1,"Pipeline test timeout");end
endmodule

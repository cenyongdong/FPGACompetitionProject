`timescale 1ns/1ps
module tb_candidate;
 wire axi_done,control_done;
 axi_read_tests a(axi_done);
 scan_control_tests c(control_done);
 initial begin
   wait(axi_done && control_done);
   $display("HDMI_CANDIDATE_TEST_PASS");$finish;
 end
endmodule

`timescale 1ns/1ps
module tb_candidate;
 wire axi_done,control_done,full_done,csr_done;
 axi_read_tests a(axi_done);
 scan_control_tests c(control_done);
 full_frame_tests f(full_done);
 register_bank_tests r(csr_done);
 initial begin
   wait(axi_done && control_done && full_done && csr_done);
   $display("HDMI_CANDIDATE_TEST_PASS");$finish;
 end
endmodule

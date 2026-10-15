`timescale 1ns/1ps
module tb_candidate;
 wire axi_done,control_done,full_done,offset_done,page_done,csr_done,fifo_done,scanout_done;
 axi_read_tests a(axi_done);
 scan_control_tests c(control_done);
 full_frame_tests f(full_done);
 full_frame_tests #(.OFFSET(64)) f_offset(offset_done);
 full_frame_tests #(.OFFSET(4032)) f_page(page_done);
 register_bank_tests r(csr_done);
 stream_fifo_tests s(fifo_done);
 scanout_tests v(scanout_done);
 initial begin
   wait(axi_done && control_done && full_done && offset_done && page_done && csr_done && fifo_done && scanout_done);
   $display("HDMI_CANDIDATE_TEST_PASS");$finish;
 end
endmodule

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

// Separate elaboration roots prevent completed unit benches from generating
// millions of irrelevant clock events during the full-raster observation.
module tb_core_suite;
 wire a,c,f,o,p,r;
 axi_read_tests t0(a);scan_control_tests t1(c);full_frame_tests t2(f);
 full_frame_tests #(.OFFSET(64)) t3(o);full_frame_tests #(.OFFSET(4032)) t4(p);
 register_bank_tests t5(r);
 initial begin wait(a&&c&&f&&o&&p&&r);$display("HDMI_CANDIDATE_TEST_PASS group=core");$finish;end
endmodule
module tb_pixel_suite;
 wire f,s;
 stream_fifo_tests t0(f);scanout_tests t1(s);
 initial begin wait(f&&s);$display("HDMI_CANDIDATE_TEST_PASS group=pixel");$finish;end
endmodule

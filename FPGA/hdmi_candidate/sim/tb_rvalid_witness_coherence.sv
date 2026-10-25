`timescale 1ns/1ps
// Exercise the shipped r45 passive samplers together, with no functional AXI.
// Fault cases are deliberately injected hypotheses, not proof of board cause.
module rvalid_coherence_case #(parameter integer KIND=0)(output reg passed=0);
 reg hp=0,gp=0,resetn=0,freeze=0;
 always #2.5 hp=~hp;
 always #5 gp=~gp;
 reg [127:0] ps=0,delayed_ps=0;
 always @(posedge hp)delayed_ps<=ps;
 wire [127:0] trace_ps=KIND==2?delayed_ps:ps;
 mna_gp_ww_itf witness_csr(),trace_csr();
 ps_release_witness witness(.source_clk(hp),.csr_clk(gp),.csr_resetn(resetn),
  .source_freeze(freeze),.csr_freeze(1'b0),.levels(20'h209),
  .ps_read(ps),.hdmi_read(128'd0),.legacy_write(6'd0),.ps_write(6'd0),
  .ps_awaddr(32'd0),.csr(witness_csr));
 hp2_cycle_trace trace(.source_clk(hp),.csr_clk(gp),.csr_resetn(resetn),
  .ps_read(trace_ps),.s01_read(128'd0),.hc2_read(128'd0),
  .ps_rdata(64'h1234),.s01_rdata(64'd0),.hc2_rdata(64'd0),
  .flags(32'd0),.csr(trace_csr));
 reg [63:0] first_native,first_snapshot;
 integer physical_index;
 initial begin
  witness_csr.araddr=0;witness_csr.arvalid=0;witness_csr.rready=1;
  witness_csr.awwaddr=0;witness_csr.awwdata=0;witness_csr.awwvalid=0;
  trace_csr.araddr=0;trace_csr.arvalid=0;trace_csr.rready=1;
  trace_csr.awwaddr=0;trace_csr.awwdata=0;trace_csr.awwvalid=0;
  repeat(4)@(negedge hp);resetn=1;
  if(KIND==1)witness.hp_cycles=trace.hp_cycle-1; // Independent origin fault.
  if(KIND==3)begin
   witness.hp_cycles=64'hfffffff0;trace.hp_cycle=64'hfffffff0;
  end
  repeat(64)@(negedge hp);
  ps[62]=1;ps[69:64]=32;
  repeat(120)@(negedge hp);
  freeze=1;@(negedge hp);freeze=0;
  first_snapshot=witness.source_snapshot[14*32+:64];
  first_native=trace.cycle0;
  if(!trace.source_status[1] || trace.count0!=128 || trace.index0!=32)
   $fatal(1,"Incomplete native trace kind=%0d",KIND);
  physical_index=(trace.start0+32)%128;
  if(trace.first_return.samples[physical_index][63:0]!==first_native ||
     !trace.first_return.samples[physical_index][126] ||
     trace.first_return.samples[(physical_index+127)%128][126])
   $fatal(1,"Native trigger row mismatch kind=%0d",KIND);
  if(first_native-first_snapshot!=(KIND==1 || KIND==2 ? 1 : 0))
   $fatal(1,"Unexpected sampler relation kind=%0d snapshot=%0d trace=%0d",KIND,first_snapshot,first_native);
  if(KIND==3 && first_snapshot<64'h100000000)$fatal(1,"High timestamp bits lost");
  $display("COHERENCE_CASE kind=%0d snapshot=%0d trace=%0d delta=%0d",KIND,first_snapshot,first_native,first_native-first_snapshot);
  passed=1;
 end
endmodule

module tb_rvalid_witness_coherence;
 wire [3:0] passed;
 for(genvar i=0;i<4;i=i+1)begin:cases
  rvalid_coherence_case #(.KIND(i)) test_case(.passed(passed[i]));
 end
 initial begin wait(&passed);$display("RVALID_WITNESS_COHERENCE_PASS cases=4");$finish;end
 initial begin #20000;$fatal(1,"Simulation watchdog");end
endmodule

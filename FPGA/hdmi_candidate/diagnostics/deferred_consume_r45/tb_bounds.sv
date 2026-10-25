`timescale 1ns/1ps
module drain_case #(parameter integer N=0)(output reg finished=0);
 reg clk=0;always #2.5 clk=~clk;
 reg ps=0,pl=0,hp=1,request=0,reader=0,rv=0,last=0;
 reg [4:0] id=0;reg [1:0] resp=0;
 wire ready;wire [31:0] status;
 hp2_startup_drain d(.clk(clk),.arm(1'b1),.ps_resetn(ps),.pl_resetn(pl),.hp_reset(hp),
  .any_request(request),.reader_ready(reader),.rvalid(rv),.rid(id),.rresp(resp),
  .rlast(last),.drain_ready(ready),.status(status));
 integer tick=0,accepted=0;
 always @(posedge clk)begin
  if(rv&&ready)accepted=accepted+1;
  if(accepted>256)$fatal(1,"discard beat bound");
  if(ready && (!ps || !pl || hp || request || reader || (rv&&id!=0)))
   $fatal(1,"unsafe discard condition case %0d",N);
 end
 initial begin
  repeat(30)@(negedge clk);
  ps=1;pl=1;hp=0;
  for(tick=0;tick<5000;tick=tick+1)begin
   // Each instance runs once from FPGA initialization, no test-only reset.
   case(N)
    0: rv=0;
    1: begin rv=tick>=2&&tick<14;last=tick==13;end
    2: rv=1;
    3: rv=(tick%32)==0;
    4: begin rv=1;request=tick>=7;end
    5: begin rv=1;id=1;end
    6: begin rv=1;if(tick==7)ps=0;if(tick==20)ps=1;end
    7: rv=tick>=100;
    8: begin rv=1;reader=tick>=7;end
   endcase
   @(negedge clk);
  end
  if(status[11:3]!=accepted)$fatal(1,"count differs from handshakes");
  case(N)
   0: if(status[2:0]!=2||accepted!=0)$fatal(1,"quiet no fault");
   1: if(status[2:0]!=2||accepted!=12||!status[25])$fatal(1,"finite return");
   2: if(status[2:0]!=3||accepted!=256)$fatal(1,"continuous beat bound");
   3: if(status[2:0]!=4||status[24:12]!=4096)$fatal(1,"sparse time bound");
   4,6,8: if(status[2:0]!=5||accepted!=6)$fatal(1,"abort case %0d count=%0d",N,accepted);
   5: if(status[2:0]!=5||accepted!=0||!status[27])$fatal(1,"wrong ID abort");
   7: if(status[2:0]!=2||accepted!=0||!status[31])$fatal(1,"late return not consumed");
  endcase
  if(ready)$fatal(1,"terminal ready remains high");
  $display("DRAIN_CASE_PASS case=%0d status=%08x accepted=%0d",N,status,accepted);
  finished=1;
 end
endmodule
module tb_startup_drain;
 wire [8:0] finished;
 genvar i;generate for(i=0;i<9;i=i+1)begin:g
  drain_case #(.N(i)) c(finished[i]);
 end endgenerate
 initial begin wait(&finished);$display("BOUNDED_DRAIN_UNIT_PASS");$finish;end
 initial begin #30000;$fatal(1,"unit simulation watchdog");end
endmodule

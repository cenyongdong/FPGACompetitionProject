module tb_pose_filter;
 reg clk=0;always #10 clk=~clk;
 reg resetn=0,write=0,commit=0;reg [6:0] wi=0,ri=0;reg [31:0] value=0,seq=0;
 reg [2:0] init_mask,update_mask;reg signed [31:0] inv,ad,k,fc,beta;
 wire [31:0] out1,out4,seq1,seq4,cycles1,cycles4;wire busy1,busy4;wire [3:0] error1,error4;
 pose_filter #(.LANES(1)) one(.clk(clk),.resetn(resetn),.input_write(write),.input_index(wi),.input_value(value),.commit(commit),.frame_sequence(seq),.init_mask(init_mask),.update_mask(update_mask),.inverse_dt(inv),.derivative_alpha(ad),.k(k),.min_cutoff(fc),.beta(beta),.output_index(ri),.output_value(out1),.busy(busy1),.completed_sequence(seq1),.cycles(cycles1),.error(error1));
 pose_filter #(.LANES(4)) four(.clk(clk),.resetn(resetn),.input_write(write),.input_index(wi),.input_value(value),.commit(commit),.frame_sequence(seq),.init_mask(init_mask),.update_mask(update_mask),.inverse_dt(inv),.derivative_alpha(ad),.k(k),.min_cutoff(fc),.beta(beta),.output_index(ri),.output_value(out4),.busy(busy4),.completed_sequence(seq4),.cycles(cycles4),.error(error4));
 reg [31:0] inputs[0:5039],expected[0:5039],params[0:279];integer f,i,waited,max1=0,max4=0;
 task tick;begin @(posedge clk);#1;end endtask
 initial begin
  $readmemh("input.hex",inputs);$readmemh("expected.hex",expected);$readmemh("params.hex",params);
  repeat(3)tick;resetn=1;tick;
  // Incomplete input must reject without starting either lane set.
  seq=1;commit=1;tick;commit=0;tick;
  if(busy1||busy4||!error1[1]||!error4[1])$fatal(1,"incomplete input admitted");
  resetn=0;tick;resetn=1;tick;
  for(f=0;f<40;f=f+1)begin
   inv=params[f*7];ad=params[f*7+1];k=params[f*7+2];fc=params[f*7+3];beta=params[f*7+4];init_mask=params[f*7+5];update_mask=params[f*7+6];
   for(i=0;i<126;i=i+1)begin write=1;wi=i;value=inputs[f*126+i];tick;end
   write=0;ri=0;repeat(3)tick;seq=f+1;commit=1;tick;commit=0;waited=0;
   while(seq1!=seq||seq4!=seq)begin tick;waited=waited+1;if(waited>50000)$fatal(1,"filter timeout");
    if(f>0&&seq1!=seq&&out1!==expected[(f-1)*126])$fatal(1,"partial one-lane publication");
    if(f>0&&seq4!=seq&&out4!==expected[(f-1)*126])$fatal(1,"partial four-lane publication");end
   if(error1||error4)$fatal(1,"unexpected filter error");
   if(f>=24&&f<=26)$display("PERSON_MASK_CYCLES mask=%0d lanes1=%0d lanes4=%0d",update_mask,cycles1,cycles4);
   if(cycles1>max1)max1=cycles1;if(cycles4>max4)max4=cycles4;
   for(i=0;i<126;i=i+1)begin ri=i;repeat(3)tick;
    if(out1!==expected[f*126+i]||out4!==expected[f*126+i])$fatal(1,"mismatch frame=%0d index=%0d one=%h four=%h expected=%h",f,i,out1,out4,expected[f*126+i]);end
  end
  if(max4*2>max1||max1>=50000)$fatal(1,"cycle budget");
  $display("FILTER_PASS frames=40 coordinates=126 cycles1=%0d cycles4=%0d",max1,max4);$finish;
 end
endmodule

module tb_pose_geometry;
 reg clk=0;always #5 clk=~clk;
 reg resetn=0,write=0,clear=0,start=0;
 reg [6:0] index;reg [31:0] value,seq;reg [2:0] mask;reg [3:0] mi;
 wire [31:0] mv,completed,cycles;wire busy;wire [3:0] error;wire [2:0] duplicates;
 pose_geometry d(.clk(clk),.resetn(resetn),.input_write(write),.clear_written(clear),.input_index(index),.input_value(value),
 .start(start),.valid_mask(mask),.frame_sequence(seq),.moment_index(mi),.moment_value(mv),.busy(busy),.error(error),.completed(completed),.cycles(cycles),.duplicate_mask(duplicates));
 reg [31:0] inputs[0:5039],expected[0:679];integer f,i,total,maxcycles=0;reg [31:0] old;
 task tick;begin @(posedge clk);#1;end endtask
 initial begin
  $readmemh("geometry_input.hex",inputs);$readmemh("geometry_expected.hex",expected);
  tick;resetn=1;tick;
  for(f=0;f<40;f=f+1)begin
   mask=expected[f*17];seq=f+1;
   for(i=0;i<126;i=i+1)if(mask[i/42])begin index=i;value=inputs[f*126+i];write=1;tick;end
   write=0;mi=0;#1;old=mv;start=1;tick;start=0;
   while(busy)begin if(mv!=old)$fatal(1,"partial geometry publication");tick;end
   if(error||completed!=f+1||duplicates!=expected[f*17+1])$fatal(1,"geometry result f=%0d mask=%0h/%0h error=%0h",f,duplicates,expected[f*17+1],error);
   for(i=0;i<15;i=i+1)begin mi=i;#1;if(mv!=expected[f*17+2+i])$fatal(1,"moment f=%0d i=%0d got=%h expected=%h",f,i,mv,expected[f*17+2+i]);end
   if(cycles>maxcycles)maxcycles=cycles;
  end
  // Missing current input must be refused, and local reset clears the latch.
  seq=41;start=1;tick;start=0;tick;if(!error[1]||busy)$fatal(1,"incomplete geometry accepted");
  resetn=0;tick;resetn=1;tick;mask=1;seq=1;
  for(i=0;i<42;i=i+1)begin index=i;value=i==0?1048577:0;write=1;tick;end
  write=0;start=1;tick;start=0;while(busy)tick;
  if(!error[2]||completed!=0)$fatal(1,"range failure published");
  $display("GEOMETRY_PASS frames=40 max_cycles=%0d immutable missing range reset",maxcycles);$finish;
 end
 initial begin #2000000;$fatal(1,"geometry timeout");end
endmodule

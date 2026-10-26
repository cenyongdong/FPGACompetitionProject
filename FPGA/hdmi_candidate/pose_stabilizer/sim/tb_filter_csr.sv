module tb_filter_csr;
 reg clk=0;always #10 clk=~clk;
 reg resetn=0,wv=0,rv=0,ready=1;reg [11:0] wa=0,ra=0;reg [31:0] wd=0;
 wire wr,rr,valid;wire [31:0] data;integer cycles=0,i,begin_io,end_io;reg [31:0] got;
 pose_filter_csr #(.LANES(4)) d(.clk(clk),.resetn(resetn),.wr_valid(wv),.wr_addr(wa),.wr_data(wd),.wr_ready(wr),.rd_valid(rv),.rd_addr(ra),.rd_ready(rr),.rsp_valid(valid),.rsp_data(data),.rsp_ready(ready));
 task tick;begin @(posedge clk);#1;cycles=cycles+1;end endtask
 task write(input [11:0] a,input [31:0] v);begin wa=a;wd=v;wv=1;tick;wv=0;end endtask
 task read(input [11:0] a);begin ra=a;rv=1;while(!rr)tick;tick;rv=0;while(!valid)tick;got=data;tick;end endtask
 initial begin
  repeat(2)tick;resetn=1;tick;read(0);if(got!=32'h504f5301)$fatal(1,"ABI");
  begin_io=cycles;
  write('h20,978149);write('h24,19399);write('h28,27589);write('h2c,65536);write('h30,32768);write('h1c,7);write('h34,7);
  for(i=0;i<126;i=i+1)write('h400+i*4,i*65536);
  write('hc,1);write(8,1);end_io=cycles;
  got=0;while(got!=1)read('h10);
  for(i=0;i<126;i=i+1)begin read('h800+i*4);if(got!=i*65536)$fatal(1,"CSR index/initialization %0d",i);end
  // Held response cannot change while the consumer is stalled.
  ready=0;ra='h18;rv=1;tick;rv=0;while(!valid)tick;repeat(12)begin tick;if(!valid||data!=4)$fatal(1,"response not held");end ready=1;tick;
  write('h1c,0);for(i=0;i<126;i=i+1)write('h400+i*4,65536);write('hc,2);write(8,1);tick;write(8,1);tick;
  read(4);if(!(got&16))$fatal(1,"busy duplicate not rejected");
  // A busy core reset is local and terminates publication; next frame reinitializes.
  write(8,2);repeat(4)tick;read('h10);if(got!=0)$fatal(1,"reset completed sequence");read(4);if(got!=0)$fatal(1,"reset did not clear busy/error");
  $display("CSR_PASS input_commit_cycles=%0d output_read_cycles=%0d backpressure busy reset",end_io-begin_io,126*5);$finish;
 end
 initial begin #1000000;$fatal(1,"CSR timeout");end
endmodule

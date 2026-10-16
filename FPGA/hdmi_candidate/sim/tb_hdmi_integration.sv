`timescale 1ns/1ps
module tb_hdmi_router;
 reg clk=0,resetn=0;always #5 clk=~clk;
 mna_gp_ww_itf up();mna_gp_ww_itf cam();mna_gp_ww_itf hdmi();
 hdmi_cam_router dut(clk,resetn,up.slave,cam.master,hdmi.master);
 reg cam_allow=1,hdmi_allow=1;reg crv=0,hrv=0;reg[31:0] crd,hrd;
 integer cw=0,hw=0;
 assign cam.arready=cam_allow && !crv;assign hdmi.arready=hdmi_allow && !hrv;
 assign cam.rvalid=crv;assign hdmi.rvalid=hrv;assign cam.rdata=crd;assign hdmi.rdata=hrd;
 assign cam.awwready=cam_allow;assign hdmi.awwready=hdmi_allow;
 always @(posedge clk) begin
  if(cam.arvalid&&cam.arready)begin crv<=1;crd<=cam.araddr^32'h12345678;end
  else if(cam.rready)crv<=0;
  if(hdmi.arvalid&&hdmi.arready)begin hrv<=1;hrd<=hdmi.araddr^32'h87654321;end
  else if(hdmi.rready)hrv<=0;
  if(cam.awwvalid&&cam.awwready)cw<=cw+1;
  if(hdmi.awwvalid&&hdmi.awwready)hw<=hw+1;
 end
 task automatic read_one(input[31:0]addr,input bit is_hdmi);
  reg[31:0]expected;begin
   expected=addr^(is_hdmi?32'h87654321:32'h12345678);
   @(negedge clk);up.araddr=addr;up.arvalid=1;up.rready=0;
   do @(posedge clk);while(!up.arready);
   @(negedge clk);up.arvalid=0;
   wait(up.rvalid);repeat(5)begin @(negedge clk);if(!up.rvalid||up.rdata!==expected||up.arready)$fatal(1,"Read ownership/backpressure");end
   up.rready=1;@(posedge clk);@(negedge clk);up.rready=0;
  end
 endtask
 task automatic write_one(input[31:0]addr,input bit is_hdmi);
  integer oldcw,oldhw;begin
   oldcw=cw;oldhw=hw;
   @(negedge clk);up.awwaddr=addr;up.awwdata=32'h1234abcd;up.awwvalid=1;
   if(is_hdmi)hdmi_allow=0;else cam_allow=0;
   repeat(4)begin @(negedge clk);if(up.awwready)$fatal(1,"Write backpressure");end
   if(is_hdmi)hdmi_allow=1;else cam_allow=1;
   @(posedge clk);@(negedge clk);up.awwvalid=0;
   if(cw!=oldcw+!is_hdmi||hw!=oldhw+is_hdmi)$fatal(1,"Write duplicated or misrouted");
  end
 endtask
 initial begin
  up.araddr=0;up.arvalid=0;up.rready=0;up.awwaddr=0;up.awwdata=0;up.awwvalid=0;
  repeat(4)@(negedge clk);resetn=1;
  read_one(32'h40080000,0);read_one(32'h40080200,0);read_one(32'h400b0000,1);
  read_one(32'h400b0040,1);read_one(32'h400b0100,0);read_one(32'h400bfe00,0);
  write_one(32'h400800b4,0);write_one(32'h400b0034,1);
  write_one(32'h400b0100,0);write_one(32'h400b00fc,1);
  $display("HDMI_ROUTER_PASS reads=6 writes=4 response_hold=5cycles endpoint_backpressure=4cycles");$finish;
 end
 initial begin #100000;$fatal(1,"Router watchdog");end
endmodule

module tb_hdmi_board_phy;
 reg refclk=0,csrclk=0,memclk=0,resetn=0,clockreset=1;
 always #5 refclk=~refclk;always #10 csrclk=~csrclk;always #2.5 memclk=~memclk;
 mna_gp_ww_itf csr();wire[31:0]addr;wire[3:0]len;wire[2:0]size;wire[1:0]burst;
 wire arvalid,rready,cp,cn;wire[2:0]dp,dn;
 hdmi_board dut(refclk,clockreset,csrclk,resetn,csr.slave,memclk,resetn,
  addr,len,size,burst,arvalid,1'b1,64'd0,2'd0,5'd0,1'b0,1'b0,rready,cp,cn,dp,dn);
 task automatic rd(input[7:0]off,output[31:0]data);
  begin
   @(negedge csrclk);csr.araddr={24'h400b00,off};csr.arvalid=1;csr.rready=0;
   do @(posedge csrclk);while(!csr.arready);
   @(negedge csrclk);csr.arvalid=0;
   wait(csr.rvalid);data=csr.rdata;
   repeat(3)begin @(negedge csrclk);if(!csr.rvalid||csr.rdata!==data)$fatal(1,"CSR response changed under backpressure");end
   csr.rready=1;@(posedge csrclk);@(negedge csrclk);csr.rready=0;
  end
 endtask
 task automatic wr(input[7:0]off,input[31:0]data);
  begin @(negedge csrclk);csr.awwaddr={24'h400b00,off};csr.awwdata=data;csr.awwvalid=1;
   do @(posedge csrclk);while(!csr.awwready);
   @(negedge csrclk);csr.awwvalid=0;
  end
 endtask
 realtime prev,t0,high_ns,period_ns;reg[31:0]value,pcount0,pcount1;
 integer i;reg[2:0]expected_bar;
 initial begin
  csr.araddr=0;csr.arvalid=0;csr.rready=0;csr.awwaddr=0;csr.awwdata=0;csr.awwvalid=0;
  #150;clockreset=0;resetn=1;
  wait(dut.locked===1);repeat(16)@(posedge dut.pixel_clk);
  @(posedge dut.pixel_clk);prev=$realtime;
  repeat(256)begin @(posedge dut.pixel_clk);period_ns=$realtime-prev;prev=$realtime;
   if(period_ns<6.730||period_ns>6.738)$fatal(1,"Pixel period %f",period_ns);
  end
  if(dut.transmitter.family_7.Inst_clk_oserdese2_10to1.txdata!==10'b1111100000)$fatal(1,"ASCII clock literal present");
  @(posedge cp);prev=$realtime;
  repeat(256)begin
   @(negedge cp);high_ns=$realtime-prev;
   @(posedge cp);period_ns=$realtime-prev;
   if(high_ns<3.360||high_ns>3.375||period_ns<6.730||period_ns>6.738||cn!==0)$fatal(1,"TMDS period/duty %f %f",period_ns,high_ns);
   prev=$realtime;
  end
  rd(8'h00,value);if(value!==32'h48444d01)$fatal(1,"Core ABI");
  rd(8'h40,value);if(value!==32'h48445301)$fatal(1,"Board ABI");
  rd(8'h30,value);if(value[1:0]!==3)$fatal(1,"PLL and safe-idle status %h",value);
  rd(8'h38,pcount0);repeat(100)@(posedge csrclk);rd(8'h38,pcount1);
  if(pcount1-pcount0<280||pcount1-pcount0>350)$fatal(1,"Pixel counter CDC");
  wr(8'h34,1);rd(8'h34,value);if(value!==1)$fatal(1,"Static pattern control");
  wait(dut.de===1);@(negedge dut.pixel_clk);
  for(i=0;i<1920;i=i+1) begin
   if(i!=0)@(negedge dut.pixel_clk);
   expected_bar=7-i/240;
   if(!dut.de || dut.transmitter.RGB_i!=={{8{expected_bar[2]}},{8{expected_bar[1]}},{8{expected_bar[0]}}})
    $fatal(1,"Static pattern active pixel=%0d value=%h",i,dut.transmitter.RGB_i);
  end
  wr(8'h0c,1);rd(8'h30,value);if(value[3]!==1)$fatal(1,"START while pattern was not rejected");
  wr(8'h30,8);wr(8'h34,0);rd(8'h34,value);if(value!==0)$fatal(1,"Pattern disable");
  wr(8'h35,1);rd(8'h30,value);if(value[3]!==1)$fatal(1,"Unaligned write not rejected");
  repeat(64)begin @(posedge memclk);if(arvalid)$fatal(1,"Unexpected display DMA in static mode");end
  // Assert reset off-edge; release is checked in the true serializer wrapper.
  @(negedge dut.pixel_clk);#0.3;clockreset=1;#50;
  if(dut.transmitter.family_7.Inst_clk_oserdese2_10to1.int_rst!==1)$fatal(1,"Serializer asynchronous reset");
  clockreset=0;wait(dut.locked===1);repeat(20)@(posedge dut.pixel_clk);
  if(dut.transmitter.family_7.Inst_clk_oserdese2_10to1.int_rst!==0)$fatal(1,"Serializer reset release");
  $display("HDMI_BOARD_PHY_PASS pixel_MHz=148.5 serial_MHz=742.5 forwarded_clock_periods=256 duty=50percent CSR_backpressure counter_CDC pattern_active_pixels=1920 reset no_DMA");$finish;
 end
 initial begin #2000000;$fatal(1,"Board PHY watchdog");end
endmodule

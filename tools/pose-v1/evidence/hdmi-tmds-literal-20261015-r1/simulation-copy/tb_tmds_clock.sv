`timescale 1ps/1ps
// Real reference OSERDESE2/3 wrappers + Xilinx UNISIM behavioral primitives.
// This verifies the literal/serial bitstream bug, NOT Procise electrical timing.
module clock_wave_check #(
 parameter integer HIGH_PS=5000,LOW_PS=5000
)(input wire enable,input wire p,input wire n,output wire complete);
 time rising=0,falling=0;
 integer highs=0,lows=0;
 assign complete=highs>=128 && lows>=128;
 always @(posedge p) if(enable) begin
   if(falling!=0 && $time-falling!=LOW_PS)$fatal(1,"Clock low width %m actual=%0t expected=%0d",$time-falling,LOW_PS);
   if(rising!=0 && $time-rising!=10000)$fatal(1,"Clock period %m actual=%0t",$time-rising);
   rising=$time;lows=lows+1;
 end
 always @(negedge p) if(enable) begin
   if(rising!=0 && $time-rising!=HIGH_PS)$fatal(1,"Clock high width %m actual=%0t expected=%0d",$time-rising,HIGH_PS);
   falling=$time;highs=highs+1;
 end
 always @(p or n) if(enable) begin
   #10;
   if((p!==1'b0 && p!==1'b1) || n!==~p)$fatal(1,"Unknown/non-complementary differential clock %m");
 end
endmodule

module tb_tmds_clock;
 reg pix=0,fast=0,half=0,resetn=0,enable=0;
 reg hs=0,vs=0,de=0;reg [23:0] rgb=0;
 wire p7,n7,pu,nu,b7,bn7,bu,bnu;
 wire [2:0] unused0,unused1,unused2,unused3,unused4,unused5,unused6,unused7;
 wire done7,doneu,doneb7,donebu;
 always #5000 pix=~pix;
 always #1000 fast=~fast;
 always #2000 half=~half;
 uihdmitx #(.FAMILY("7FAMILY")) fixed7(resetn,hs,vs,de,rgb,pix,half,fast,p7,n7,unused0,unused1);
 uihdmitx #(.FAMILY("UFAMILY")) fixedu(resetn,hs,vs,de,rgb,pix,half,fast,pu,nu,unused2,unused3);
 uihdmitx_legacy #(.FAMILY("7FAMILY")) legacy7(resetn,hs,vs,de,rgb,pix,half,fast,b7,bn7,unused4,unused5);
 uihdmitx_legacy #(.FAMILY("UFAMILY")) legacyu(resetn,hs,vs,de,rgb,pix,half,fast,bu,bnu,unused6,unused7);
 clock_wave_check w7(enable,p7,n7,done7);
 clock_wave_check wu(enable,pu,nu,doneu);
 clock_wave_check #(.HIGH_PS(2000),.LOW_PS(8000)) wb7(enable,b7,bn7,doneb7);
 clock_wave_check #(.HIGH_PS(2000),.LOW_PS(8000)) wbu(enable,bu,bnu,donebu);
 // Payload/control changes must not change either forwarded clock waveform.
 always @(negedge pix) begin rgb<=rgb+24'h137bad;de<=~de;hs<=~hs;vs<=hs;end
 initial begin
  #153000;resetn=1;#4000000;
  if(fixed7.family_7.Inst_clk_oserdese2_10to1.txdata!==10'b1111100000 ||
     fixedu.ULTRASCALE_FAMILY.Inst_clk_oserdese3_10to1.txdata!==10'b1111100000)
     $fatal(1,"Fixed literal not present at actual serializer input");
  if(legacy7.family_7.Inst_clk_oserdese2_10to1.txdata!==10'h030 ||
     legacyu.ULTRASCALE_FAMILY.Inst_clk_oserdese3_10to1.txdata!==10'h030)
     $fatal(1,"Original ASCII truncation was not reproduced");
  enable=1;wait(done7&&doneu&&doneb7&&donebu);
  $display("TMDS_LITERAL_AND_WAVEFORM_PASS families=7FAMILY,UFAMILY checked_periods_each=128 pixel_period_ps=10000 fixed_high_ps=5000 fixed_low_ps=5000 original_high_ps=2000 original_low_ps=8000");
  $finish;
 end
 initial begin #10000000;$fatal(1,"TMDS clock watchdog");end
endmodule

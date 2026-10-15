`timescale 1ns/1ps
module scanout_tests(output reg complete=0);
 localparam [31:0] BASE=32'h30100fc0;
 reg csr=0,mem=0,pix=0,resetn=0,pixel_clock_enabled=1;
 reg wvalid=0;wire wready;reg [7:0] offset=0,read_offset=0;reg [31:0] value=0;
 wire [31:0] read_data,araddr;wire [7:0] arlen;wire [2:0] arsize;wire [1:0] arburst;
 wire arvalid,rready,idle,hs,vs,de;wire [23:0] rgb;
 reg active=0;reg [31:0] addr=0;reg [7:0] index=0,last=0;
 reg supply=1,allow_address=1;
 integer requests=0,words=0,pixels=0,lines=0,hs_width=0,de_width=0,vs_lines=0;
 integer old_hs=-1,old_vs=-1,phase=0,issued=0,pixel_cycles=0;
 reg prior_hs=0,prior_vs=0,capturing=0;
 always #7 csr=~csr;
 always #2.5 mem=~mem;
 always begin #3.367;if(pixel_clock_enabled)pix=~pix;end
 function [15:0] pattern(input integer n);pattern=(n*17)^16'habcd;endfunction
 function [23:0] expand(input [15:0] p);expand={p[15:11],p[15:13],p[10:5],p[10:9],p[4:0],p[4:2]};endfunction
 function [63:0] frame_word(input [31:0] a);
   integer n;begin n=(a-BASE)/2;frame_word={pattern(n+3),pattern(n+2),pattern(n+1),pattern(n)};end
 endfunction
 hdmi_scanout #(.FIFO_AW(9)) dut(
   .csr_clk(csr),.csr_resetn(resetn),.write_valid(wvalid),.write_ready(wready),
   .write_offset(offset),.write_data(value),.write_strobe(4'hf),.read_offset(read_offset),.read_data(read_data),
   .mem_clk(mem),.mem_resetn(resetn),.pixel_clk(pix),.pixel_resetn(resetn),.clock_locked(1'b1),
   .araddr(araddr),.arlen(arlen),.arsize(arsize),.arburst(arburst),.arvalid(arvalid),.arready(allow_address&&!active),
   .rdata(frame_word(addr+index*8)),.rresp(2'b0),.rlast(index==last),.rvalid(active&&supply),.rready(rready),
   .safe_idle(idle),.hs(hs),.vs(vs),.de(de),.rgb(rgb));
 always @(posedge mem) if(resetn) begin
   if(arvalid && allow_address && !active) begin
     if(arsize!=3 || arburst!=1 || arlen>15 || (araddr[11:0]+(arlen+1)*8)>4096)
       $fatal(1,"Scanout illegal AXI request");
     active<=1;addr<=araddr;last<=arlen;index<=0;requests=requests+1;
   end
   if(active && supply && rready) begin
     words=words+1;if(index==last)active<=0;else index<=index+1'b1;
   end
   if(idle && (active || arvalid)) $fatal(1,"Scanout false idle");
 end
 // External raster/data observations; counters check the actual registered pins.
 always @(negedge pix) if(resetn) begin
   pixel_cycles=pixel_cycles+1;
   if(hs) hs_width=hs_width+1;
   if(de) de_width=de_width+1;
   if(hs && !prior_hs) begin
     if(old_hs>=0 && pixel_cycles-old_hs!=2200)$fatal(1,"Horizontal total changed");
     old_hs=pixel_cycles;
     if(lines>0 && hs_width!=1+44) $fatal(1,"HS width changed: %0d",hs_width);
     hs_width=1;lines=lines+1;
     if(de_width!=0 && de_width!=1920) $fatal(1,"Active line width changed");
     de_width=0;
     if(vs) vs_lines=vs_lines+1;
   end
   if(vs && !prior_vs) begin
     if(old_vs>=0 && lines-old_vs!=1125) $fatal(1,"Vertical total changed");
     if(old_vs>=0 && vs_lines!=5+1) $fatal(1,"VS line width changed %0d",vs_lines);
     old_vs=lines;vs_lines=1;
   end
   prior_hs=hs;prior_vs=vs;
   if(phase==1 && dut.frame_toggle) capturing=1;
   if(phase==1 && capturing && de) begin
     if(rgb!==expand(pattern(pixels))) $fatal(1,"Scanout pixel mismatch n=%0d rgb=%h expected=%h",pixels,rgb,expand(pattern(pixels)));
     pixels=pixels+1;
   end
   if(phase==2 && rgb!==0) $fatal(1,"Stopped raster must be black");
 end
 task write(input [7:0] a,input [31:0] d);
 begin @(negedge csr);offset=a;value=d;wvalid=1;do @(posedge csr);while(!wready);@(negedge csr);wvalid=0;end endtask
 task command(input [31:0] op,input [31:0] id);
 begin
   write(8'h08,id);write(8'h0c,op);issued=issued+1;
   read_offset=8'h28;wait(read_data==issued);@(negedge csr);
 end endtask
 initial begin
   #101;resetn=1;repeat(15) @(negedge csr);
   write(8'h04,BASE);phase=1;command(1,101);
   wait(pixels==2073600);@(negedge csr);command(3,102);wait(idle);
   repeat(10) @(negedge pix);phase=2;
   if(words!=518400 || requests!=32401 || dut.underflow || dut.core.core.control.faults!=0)
      $fatal(1,"Complete scanout count/fault failure");
   command(0,0);read_offset=8'h14;#1;if(read_data!=102)$fatal(1,"Stop tag not observed");
   // Restart with no data supplied: the first missing active pixel faults.
   supply=0;phase=3;command(1,103);wait(active);wait(dut.underflow);
   repeat(15) @(negedge mem);
   if(idle || !dut.core.core.control.faults[3])$fatal(1,"Underflow must stop but await accepted AXI drain");
   supply=1;wait(idle);repeat(15) @(negedge csr);command(4,0);
   command(0,0);read_offset=8'h20;#1;if(read_data!=0)$fatal(1,"Underflow clear failed");
   // Accepted burst can be safely drained even with pixel clock halted.
   command(1,104);wait(active);pixel_clock_enabled=0;command(3,105);wait(idle);
   pixel_clock_enabled=1;repeat(20) @(negedge pix);phase=2;
   repeat(2300) @(negedge pix);
   $display("CANDIDATE_SCANOUT_PASS pixels=2073600 bytes=4147200 base_offset=4032 raster=2200x1125 hs=44 vs=5 underflow_drain=1 stop_pixel_clock_halted=1");
   complete=1;
 end
 initial begin #90000000;if(!complete)$fatal(1,"Scanout watchdog phase=%0d pixels=%0d",phase,pixels);end
endmodule

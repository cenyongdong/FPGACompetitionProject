`timescale 1ns/1ps
module stream_fifo_tests(output reg complete=0);
 reg wclk=0,rclk=0,resetn=0,push=0,pop=0;
 wire ready,empty;wire [15:0] pixel;
 integer writes=0,reads=0,epoch=0;
 reg [15:0] random_state=16'h8931;
 wire [63:0] data={16'(writes*4+3),16'(writes*4+2),16'(writes*4+1),16'(writes*4)};
 always #2.5 wclk=~wclk;
 always #3.367 rclk=~rclk;
 hdmi_stream_fifo #(.AW(3)) dut(resetn,wclk,push,data,ready,rclk,pop,pixel,empty);
 always @(negedge wclk) begin
   random_state={random_state[14:0],random_state[15]^random_state[13]^random_state[12]^random_state[10]};
   push=resetn && writes<2048 && (random_state[0] || random_state[1]);
 end
 always @(negedge rclk) pop=resetn && (random_state[2] || random_state[3]);
 always @(posedge wclk) if(resetn && push && ready) writes=writes+1;
 always @(posedge rclk) if(resetn && pop && !empty) begin
   if(pixel!==16'(reads)) $fatal(1,"FIFO corruption epoch=%0d pixel=%0d expected=%0d",epoch,pixel,reads);
   reads=reads+1;
 end
 initial begin
   #37;resetn=1;
   wait(reads==8192);repeat(10) @(negedge rclk);
   if(!empty) $fatal(1,"FIFO retained an extra word");
   // Async flush at a partial word, then reuse with fresh pointers/data.
   resetn=0;writes=0;reads=0;epoch=1;#39;resetn=1;
   wait(reads>29);@(negedge rclk);resetn=0;#13;
   writes=0;reads=0;epoch=2;resetn=1;
   wait(reads==8192);repeat(10) @(negedge rclk);
   if(!empty) $fatal(1,"FIFO empty after flush failed");
   $display("CANDIDATE_FIFO_PASS two_async_clocks=1 words_per_epoch=2048 wraparound=1 partial_flush=1");complete=1;
 end
 initial begin #2000000;if(!complete)$fatal(1,"FIFO watchdog");end
endmodule

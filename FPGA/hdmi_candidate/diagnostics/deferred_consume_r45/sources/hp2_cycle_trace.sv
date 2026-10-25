// Passive 200MHz cycle recorder, autonomous from configuration. No AXI/reset
// outputs. Two independent 128-sample windows: first PS RVALID and first PL
// controlled consumption RUN. Each keeps 32 pretrigger + 95 posttrigger samples.
module hp2_trace_bank #(parameter integer SAMPLE_WIDTH=512)(
 input wire source_clk,valid,trigger,input wire [SAMPLE_WIDTH-1:0] sample,
 input wire csr_clk,input wire [6:0] read_address,
 output reg [SAMPLE_WIDTH-1:0] read_data,
 output reg fired=0,done=0,
 output reg [6:0] start_address=0,
 output reg [7:0] valid_count=0,
 output reg [5:0] trigger_index=0,
 output reg [63:0] trigger_cycle=0
);
 (* ram_style="block" *) reg [SAMPLE_WIDTH-1:0] samples[0:127];
 reg [6:0] write_address=0,remaining=0;
 reg [5:0] history=0;
 always @(posedge source_clk)if(valid && !done)begin
  samples[write_address]<=sample;
  write_address<=write_address+1'b1;
  if(history<32)history<=history+1'b1;
  if(!fired && trigger)begin
   fired<=1;remaining<=95;
   start_address<=write_address-history;
   valid_count<=8'd96+history;
   trigger_index<=history;trigger_cycle<=sample[63:0];
  end else if(fired)begin
   remaining<=remaining-1'b1;
   if(remaining==1)done<=1;
  end
 end
 // True dual-clock RAM read. Software is allowed to read only after done has
 // crossed to the CSR domain and the held descriptor has been published.
 always @(posedge csr_clk)read_data<=samples[read_address];
endmodule

module hp2_cycle_trace(
 input wire source_clk,csr_clk,csr_resetn,
 input wire [127:0] ps_read,s01_read,hc2_read,
 input wire [63:0] ps_rdata,s01_rdata,hc2_rdata,
 input wire [31:0] flags,
 mna_gp_ww_itf.slave csr
);
 localparam [31:0] ABI=32'h48505401,FORMAT=32'h02028010;
 // Sample layout (little-endian words): cycle[63:0], PS[72:0], S01[72:0],
 // HC2[72:0], PS RDATA64, S01 RDATA64, HC2 RDATA64, flags32, zero5.
 reg [63:0] hp_cycle=0;
 reg [511:0] sample_stage=0;
 reg stage_valid=0;reg [2:0] previous_drain_state=0;
 always @(posedge source_clk)begin
  hp_cycle[31:0]<=hp_cycle[31:0]+1'b1;
  if(&hp_cycle[31:0])hp_cycle[63:32]<=hp_cycle[63:32]+1'b1;
  sample_stage<={5'd0,flags,hc2_rdata,s01_rdata,ps_rdata,
                 hc2_read[72:0],s01_read[72:0],ps_read[72:0],hp_cycle};
  stage_valid<=1;
  if(stage_valid)previous_drain_state<=sample_stage[506:504];
 end
 // Bank1 now records the controlled consumer entering RUN. Bank0 retains
 // the original first RVALID window; no capture is overwritten by software.
 wire pl_trigger=sample_stage[506:504]==3'd1 && previous_drain_state!=3'd1;
 wire [3:0] source_status;
 wire [6:0] start0,start1;
 wire [7:0] count0,count1;
 wire [5:0] index0,index1;
 wire [63:0] cycle0,cycle1;
 reg [6:0] ram_address=0;
 wire [511:0] ram0,ram1;
 hp2_trace_bank first_return(
  .source_clk(source_clk),.valid(stage_valid),.trigger(sample_stage[126]),.sample(sample_stage),
  .csr_clk(csr_clk),.read_address(ram_address),.read_data(ram0),
  .fired(source_status[0]),.done(source_status[1]),.start_address(start0),
  .valid_count(count0),.trigger_index(index0),.trigger_cycle(cycle0));
 hp2_trace_bank pl_release(
  .source_clk(source_clk),.valid(stage_valid),.trigger(pl_trigger),.sample(sample_stage),
  .csr_clk(csr_clk),.read_address(ram_address),.read_data(ram1),
  .fired(source_status[2]),.done(source_status[3]),.start_address(start1),
  .valid_count(count1),.trigger_index(index1),.trigger_cycle(cycle1));
 (* ASYNC_REG="TRUE",SHREG_EXTRACT="NO" *) reg [3:0] status_meta=0,status_sync=0;
 reg published0=0,published1=0;
 // These descriptors are immutable by the time done reaches the CSR domain.
 // Explicit held-bus and first-stage bounds are required in implementation.
 reg [84:0] descriptor0=0,descriptor1=0;
 always @(posedge csr_clk or negedge csr_resetn)begin
  if(!csr_resetn)begin
   status_meta<=0;status_sync<=0;published0<=0;published1<=0;
   descriptor0<=0;descriptor1<=0;
  end else begin
   status_meta<=source_status;status_sync<=status_meta;
   if(status_sync[1] && !published0)begin
    descriptor0<={cycle0,index0,count0,start0};published0<=1;
   end
   if(status_sync[3] && !published1)begin
    descriptor1<={cycle1,index1,count1,start1};published1<=1;
   end
  end
 end
 wire [6:0] csr_start0=descriptor0[6:0],csr_start1=descriptor1[6:0];
 wire [7:0] csr_count0=descriptor0[14:7],csr_count1=descriptor1[14:7];
 wire [5:0] csr_index0=descriptor0[20:15],csr_index1=descriptor1[20:15];
 wire [63:0] csr_cycle0=descriptor0[84:21],csr_cycle1=descriptor1[84:21];
 wire [14:0] offset=csr.araddr[14:0];
 wire bank1=offset>=15'h3000 && offset<15'h5000;
 wire bank0=offset>=15'h1000 && offset<15'h3000;
 wire [6:0] logical_index=offset[12:6]-7'd64;
 reg [31:0] metadata;
 always @*begin
  metadata=0;
  case(offset)
   15'h0000:metadata=ABI;
   15'h0004:metadata=FORMAT;
   15'h0008:metadata={28'd0,published1,status_sync[2],published0,status_sync[0]};
   15'h000c:metadata=32'd200000000;
   15'h0010:metadata={24'd0,csr_count0};
   15'h0014:metadata={25'd0,csr_start0};
   15'h0018:metadata={26'd0,csr_index0};
   15'h0020:metadata=csr_cycle0[31:0];15'h0024:metadata=csr_cycle0[63:32];
   15'h0030:metadata={24'd0,csr_count1};
   15'h0034:metadata={25'd0,csr_start1};
   15'h0038:metadata={26'd0,csr_index1};
   15'h0040:metadata=csr_cycle1[31:0];15'h0044:metadata=csr_cycle1[63:32];
   default:metadata=32'hbad00004;
  endcase
  if(offset[1:0]!=0)metadata=32'hbad00001;
 end
 reg read_valid=0;
 reg [31:0] read_value=0;
 reg [1:0] read_wait=0;
 reg read_bank=0;
 reg [3:0] read_lane=0;
 assign csr.awwready=csr_resetn; // All writes ignored; no ARM/reset/retry.
 assign csr.arready=csr_resetn && read_wait==0 && (!read_valid || csr.rready);
 assign csr.rvalid=read_valid;
 assign csr.rdata=read_value;
 always @(posedge csr_clk or negedge csr_resetn)begin
  if(!csr_resetn)begin
   read_valid<=0;read_value<=0;read_wait<=0;read_bank<=0;read_lane<=0;ram_address<=0;
  end else begin
   if(read_valid && csr.rready)read_valid<=0;
   if(read_wait!=0)begin
    read_wait<=read_wait-1'b1;
    if(read_wait==1)begin
     read_value<=read_bank ? ram1[32*read_lane+:32] : ram0[32*read_lane+:32];
     read_valid<=1;
    end
   end
   if(csr.arvalid && csr.arready)begin
    if((bank0 || bank1) && offset[1:0]==0)begin
     if(!(bank1 ? published1 : published0))begin read_value<=32'hbad00002;read_valid<=1;end
     else if({1'b0,logical_index}>=(bank1 ? csr_count1 : csr_count0))begin read_value<=32'hbad00003;read_valid<=1;end
     else begin
      ram_address<=logical_index+(bank1 ? csr_start1 : csr_start0);
      read_bank<=bank1;read_lane<=offset[5:2];read_wait<=3;
     end
    end else begin read_value<=metadata;read_valid<=1;end
   end
  end
 end
endmodule

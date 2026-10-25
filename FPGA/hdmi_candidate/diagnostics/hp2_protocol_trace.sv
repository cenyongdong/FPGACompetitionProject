// First transaction-error window plus an independent first-indication witness.
// Recommendations remain in all 160 raw bits, but do not consume the window.
// Autonomous capture survives functional resets. CSR is read-only; no ARM.
module hp2_protocol_trace(
 input wire source_clk,csr_clk,csr_resetn,
 input wire [127:0] ps_read,
 input wire [63:0] ps_rdata,
 input wire [152:0] ps_write,
 input wire [159:0] pc_status,
 input wire [31:0] flags,
 mna_gp_ww_itf.slave csr
);
 // Little-endian: HP cycle64, read73, RDATA64, write153, flags32,
 // pc_status160, zero30. All fields are sampled on the same HP edge.
 reg [63:0] hp_cycle=0;
 reg [575:0] sample_stage=0;
 reg stage_valid=0;
 always @(posedge source_clk)begin
  hp_cycle[31:0]<=hp_cycle[31:0]+1'b1;
  if(&hp_cycle[31:0])hp_cycle[63:32]<=hp_cycle[63:32]+1'b1;
  sample_stage<={30'd0,pc_status,flags,ps_write,ps_rdata,ps_read[72:0],hp_cycle};
  stage_valid<=1;
 end
 localparam [159:0] TRIGGER_MASK=160'hffffffffffffffc00ffffeb7fdffffefefefffff;
 wire [159:0] staged_status=sample_stage[545:386];
 wire trigger=|(staged_status & TRIGGER_MASK);
 reg any_seen=0;
 reg [159:0] any_pc_status=0;
 reg [63:0] any_cycle=0;
 // Pipeline only the indication witness. The event cycle and all status
 // bits travel together; publication is one HP edge later, identity unchanged.
 reg any_candidate=0;
 reg [159:0] any_status_delay=0;
 reg [63:0] any_cycle_delay=0;
 always @(posedge source_clk)begin
  any_candidate<=stage_valid && |staged_status;
  any_status_delay<=staged_status;any_cycle_delay<=sample_stage[63:0];
  if(any_candidate && !any_seen)begin
   any_seen<=1;any_pc_status<=any_status_delay;any_cycle<=any_cycle_delay;
  end
 end
 wire [1:0] source_status;
 wire [6:0] start;
 wire [7:0] count;
 wire [5:0] index;
 wire [63:0] cycle;
 reg [159:0] first_pc_status=0;
 always @(posedge source_clk)
  if(stage_valid && trigger && !source_status[0])first_pc_status<=sample_stage[545:386];
 reg [6:0] ram_address=0;
 wire [575:0] ram;
 hp2_trace_bank #(.SAMPLE_WIDTH(576)) first_error(
  .source_clk(source_clk),.valid(stage_valid),.trigger(trigger),.sample(sample_stage),
  .csr_clk(csr_clk),.read_address(ram_address),.read_data(ram),
  .fired(source_status[0]),.done(source_status[1]),.start_address(start),
  .valid_count(count),.trigger_index(index),.trigger_cycle(cycle));
 (* ASYNC_REG="TRUE",SHREG_EXTRACT="NO" *) reg [5:0] status_meta=0,status_sync=0;
 (* ASYNC_REG="TRUE",SHREG_EXTRACT="NO" *) reg any_meta=0,any_sync=0;
 reg any_published=0;
 reg [159:0] any_status_held=0;
 reg [63:0] any_cycle_held=0;
 reg published=0;
 reg [84:0] descriptor=0;
 reg [159:0] first_status=0;
 // Single-bit live flags cross through two flops. Frozen descriptor/status
 // buses are sampled only after the completed flag has crossed both flops.
 always @(posedge csr_clk or negedge csr_resetn)begin
  if(!csr_resetn)begin
   status_meta<=0;status_sync<=0;published<=0;descriptor<=0;first_status<=0;
   any_meta<=0;any_sync<=0;any_published<=0;any_status_held<=0;any_cycle_held<=0;
  end else begin
   status_meta<={flags[27:25],flags[0],source_status};status_sync<=status_meta;
   any_meta<=any_seen;any_sync<=any_meta;
   if(any_sync && !any_published)begin
    any_status_held<=any_pc_status;any_cycle_held<=any_cycle;any_published<=1;
   end
   if(status_sync[1] && !published)begin
    descriptor<={cycle,index,count,start};first_status<=first_pc_status;published<=1;
   end
  end
 end
 wire [6:0] csr_start=descriptor[6:0];
 wire [7:0] csr_count=descriptor[14:7];
 wire [5:0] csr_index=descriptor[20:15];
 wire [63:0] csr_cycle=descriptor[84:21];
 wire [13:0] offset=csr.araddr[13:0];
 wire low_plane=offset>=14'h1000 && offset<14'h3000;
 wire high_plane=offset>=14'h3000 && offset<14'h3400;
 wire [6:0] logical_index=high_plane ? offset[9:3] : offset[12:6]-7'd64;
 reg [31:0] metadata;
 always @*begin
  metadata=32'hbad00004;
  case(offset)
   14'h0000:metadata=32'h48505002;
   14'h0004:metadata=32'h02018012;
   14'h0008:metadata={26'd0,status_sync[5:2],published,status_sync[0]};
   14'h000c:metadata=32'd200000000;
   14'h0010:metadata={24'd0,csr_count};
   14'h0014:metadata={25'd0,csr_start};
   14'h0018:metadata={26'd0,csr_index};
   14'h001c:metadata=32'h00064003; // ID6, DATA64, AXI3
   14'h0020:metadata=csr_cycle[31:0];
   14'h0024:metadata=csr_cycle[63:32];
   14'h0030:metadata=first_status[31:0];
   14'h0034:metadata=first_status[63:32];
   14'h0038:metadata=first_status[95:64];
   14'h003c:metadata=first_status[127:96];
   14'h0040:metadata=first_status[159:128];
   14'h0050:metadata=any_status_held[31:0];
   14'h0054:metadata=any_status_held[63:32];
   14'h0058:metadata=any_status_held[95:64];
   14'h005c:metadata=any_status_held[127:96];
   14'h0060:metadata=any_status_held[159:128];
   14'h0064:metadata=any_cycle_held[31:0];
   14'h0068:metadata=any_cycle_held[63:32];
   14'h006c:metadata={31'd0,any_published};
   14'h0070:metadata=TRIGGER_MASK[31:0];
   14'h0074:metadata=TRIGGER_MASK[63:32];
   14'h0078:metadata=TRIGGER_MASK[95:64];
   14'h007c:metadata=TRIGGER_MASK[127:96];
   14'h0080:metadata=TRIGGER_MASK[159:128];
   default:metadata=32'hbad00004;
  endcase
  if(offset[1:0]!=0)metadata=32'hbad00001;
 end
 reg read_valid=0;
 reg [31:0] read_value=0;
 reg [1:0] read_wait=0;
 reg [4:0] read_lane=0;
 assign csr.awwready=csr_resetn;
 assign csr.arready=csr_resetn && read_wait==0 && (!read_valid || csr.rready);
 assign csr.rvalid=read_valid;
 assign csr.rdata=read_value;
 always @(posedge csr_clk or negedge csr_resetn)begin
  if(!csr_resetn)begin
   read_valid<=0;read_value<=0;read_wait<=0;read_lane<=0;ram_address<=0;
  end else begin
   if(read_valid && csr.rready)read_valid<=0;
   if(read_wait!=0)begin
    read_wait<=read_wait-1'b1;
    if(read_wait==1)begin read_value<=ram[32*read_lane+:32];read_valid<=1;end
   end
   if(csr.arvalid && csr.arready)begin
    if((low_plane || high_plane) && offset[1:0]==0)begin
     if(!published)begin read_value<=32'hbad00002;read_valid<=1;end
     else if({1'b0,logical_index}>=csr_count)begin read_value<=32'hbad00003;read_valid<=1;end
     else begin
      ram_address<=logical_index+csr_start;
      read_lane<=high_plane ? {4'd8,offset[2]} : {1'b0,offset[5:2]};
      read_wait<=3;
     end
    end else begin read_value<=metadata;read_valid<=1;end
   end
  end
 end
endmodule

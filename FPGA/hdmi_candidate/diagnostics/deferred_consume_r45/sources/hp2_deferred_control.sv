// Diagnostic control only: no functional reset, AXI request, memory write or
// HDMI START output. Requests and held replies use separate toggle/ACK CDC.
module hp2_deferred_control(
 input wire source_clk,csr_clk,csr_resetn,
 input wire ps_resetn,pl_resetn,hp_reset,any_request,reader_ready,rvalid,
 input wire [4:0] rid,input wire [1:0] rresp,
 input wire [31:0] drain_status,input wire [159:0] pc_status,
 input wire pc_ready,pc_system_resetn,
 output wire arm,checker_rearm,
 mna_gp_ww_itf.slave csr
);
 localparam [31:0] ABI=32'h48444301;
 localparam [31:0] CONS=32'h434f4e53,SNAP=32'h534e4150,CHKR=32'h43484b52;
 reg request_toggle=0,ack_toggle=0;
 reg [31:0] held_command=SNAP;
 (* ASYNC_REG="TRUE",SHREG_EXTRACT="NO" *) reg [1:0] request_sync=0,ack_sync=0;
 reg arm_used=0,rearm_used=0,source_error=0;
 reg [63:0] hp_cycle=0,arm_cycle=0;
 reg [31:0] held_status=0;
 reg [159:0] held_pc=0;
 reg [63:0] held_cycle=0,held_arm_cycle=0;
 reg [7:0] held_flags=0;
 wire pending=request_sync[1]!=ack_toggle;
 wire idle=ps_resetn && pl_resetn && !hp_reset && !any_request && !reader_ready;
 wire arm_allowed=!arm_used && drain_status[2:0]==0 && idle && rvalid && rid==0 && rresp==0;
 wire clear_allowed=!rearm_used && arm_used && idle && !rvalid &&
      drain_status[2:0]==2 && drain_status[11:3]!=0 && drain_status[25] &&
      !drain_status[26] && !drain_status[27] && !drain_status[31];
 assign arm=pending && held_command==CONS && arm_allowed;
 assign checker_rearm=pending && held_command==CHKR && clear_allowed;
 always @(posedge source_clk)begin
  hp_cycle[31:0]<=hp_cycle[31:0]+1'b1;
  if(&hp_cycle[31:0])hp_cycle[63:32]<=hp_cycle[63:32]+1'b1;
  request_sync<={request_sync[0],request_toggle};
  if(pending)begin
   // Reply bundle stays fixed until a later request; ACK crosses two CSR edges.
   held_status<=drain_status;held_pc<=pc_status;held_cycle<=hp_cycle;
   held_arm_cycle<=arm_cycle;
   held_flags<={source_error,3'd0,pc_system_resetn,pc_ready,rearm_used,arm_used};
   if(held_command==CONS)begin
    arm_used<=1;
    if(arm_allowed)arm_cycle<=hp_cycle;else source_error<=1;
   end else if(held_command==CHKR)begin
    rearm_used<=1;if(!clear_allowed)source_error<=1;
   end else if(held_command!=SNAP)source_error<=1;
   ack_toggle<=request_sync[1];
  end
 end
 reg [31:0] request_sequence=0,response_sequence=0;
 reg busy=0,command_error=0,arm_issued=0,clear_issued=0;
 reg [31:0] csr_status=0;reg [159:0] csr_pc=0;
 reg [63:0] csr_cycle=0,csr_arm_cycle=0;
 reg [7:0] csr_flags=0;
 reg read_valid=0;reg [31:0] read_value=0,selected;
 wire [7:0] offset=csr.araddr[7:0];
 assign csr.awwready=csr_resetn;
 assign csr.arready=csr_resetn && (!read_valid || csr.rready);
 assign csr.rvalid=read_valid;assign csr.rdata=read_value;
 always @*begin
  selected=32'hbad00004;
  case(offset)
   8'h00:selected={28'd0,clear_issued,arm_issued,command_error,busy};
   8'h04:selected=ABI;
   8'h08:selected=request_sequence;8'h0c:selected=response_sequence;
   8'h10:selected=csr_status;8'h14:selected={24'd0,csr_flags};
   8'h18:selected=csr_cycle[31:0];8'h1c:selected=csr_cycle[63:32];
   8'h20:selected=csr_arm_cycle[31:0];8'h24:selected=csr_arm_cycle[63:32];
   8'h28:selected=csr_pc[31:0];8'h2c:selected=csr_pc[63:32];
   8'h30:selected=csr_pc[95:64];8'h34:selected=csr_pc[127:96];8'h38:selected=csr_pc[159:128];
  endcase
  if(offset[1:0]!=0)selected=32'hbad00001;
 end
 always @(posedge csr_clk or negedge csr_resetn)begin
  if(!csr_resetn)begin
   request_toggle<=0;held_command<=SNAP;ack_sync<=0;
   request_sequence<=0;response_sequence<=0;
   busy<=0;command_error<=0;arm_issued<=0;clear_issued<=0;
   csr_status<=0;csr_pc<=0;csr_cycle<=0;csr_arm_cycle<=0;csr_flags<=0;
   read_valid<=0;read_value<=0;
  end else begin
   ack_sync<={ack_sync[0],ack_toggle};
   if(busy && ack_sync[1]==request_toggle)begin
    csr_status<=held_status;csr_pc<=held_pc;csr_cycle<=held_cycle;
    csr_arm_cycle<=held_arm_cycle;csr_flags<=held_flags;
    response_sequence<=request_sequence;busy<=0;
   end
   if(csr.awwvalid && csr.awwready)begin
    if(csr.awwaddr[7:0]==0 && !busy &&
       (csr.awwdata==SNAP || (csr.awwdata==CONS && !arm_issued) ||
        (csr.awwdata==CHKR && arm_issued && !clear_issued)))begin
     held_command<=csr.awwdata;request_toggle<=!request_toggle;
     request_sequence<=request_sequence+1'b1;busy<=1;
     if(csr.awwdata==CONS)arm_issued<=1;
     if(csr.awwdata==CHKR)clear_issued<=1;
    end else command_error<=1;
   end
   if(csr.arvalid && csr.arready)begin read_valid<=1;read_value<=selected;end
   else if(csr.rready)read_valid<=0;
  end
 end
endmodule

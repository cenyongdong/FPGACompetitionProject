// One outstanding command, stable response bundle and toggle ACK CDC.
// Full counter/history payload exists once per domain, with no waveform RAM.
module startup_guard_csr(
 input wire hp_clk,csr_clk,csr_resetn,
 input wire [1023:0] status_bundle,
 output wire command_valid,output wire [2:0] command,
 input wire wr_valid,input wire [7:0] wr_addr,input wire [31:0] wr_data,output wire wr_ready,
 input wire rd_valid,input wire [7:0] rd_addr,output wire rd_ready,
 output reg rsp_valid,output reg [31:0] rsp_data,input wire rsp_ready
);
 reg request=0,ack=0;reg [2:0] held_command=0;
 (* ASYNC_REG="TRUE",SHREG_EXTRACT="NO" *) reg [1:0] rq=0,ak=0;
 reg [1:0] settle=0;reg [1023:0] held_snapshot=0,snapshot=0;
 reg busy=0,error=0;reg [31:0] request_seq=0,response_seq=0;
 assign command_valid=(rq[1]!=ack)&&settle==0;
 assign command=held_command;
 assign wr_ready=csr_resetn;
 assign rd_ready=csr_resetn&&(!rsp_valid||rsp_ready);
 always @(posedge hp_clk)begin
  rq<={rq[0],request};
  if(rq[1]!=ack)begin
   if(settle==0)settle<=2;
   else if(settle==1)begin held_snapshot<=status_bundle;ack<=rq[1];settle<=0;end
   else settle<=settle-1'b1;
  end
 end
 always @(posedge csr_clk)begin
  // CSR reset is not permission to repeat a source-domain operation.
  ak<={ak[0],ack};
  if(!csr_resetn)begin rsp_valid<=0;rsp_data<=0;end
  else begin
   if(busy&&ak[1]==request)begin snapshot<=held_snapshot;response_seq<=request_seq;busy<=0;end
   if(wr_valid&&wr_ready)begin
    if(wr_addr==0&&!busy&&wr_data<=3)begin held_command<=wr_data[2:0];request<=!request;request_seq<=request_seq+1'b1;busy<=1;end
    else error<=1;
   end
   if(rd_valid&&rd_ready)begin
    rsp_valid<=1;rsp_data<=32'hbad00001;
    case(rd_addr)
     8'h00:rsp_data<={30'd0,error,busy};
     8'h04:rsp_data<=32'h4c534701;
     8'h08:rsp_data<=request_seq;
     8'h0c:rsp_data<=response_seq;
     default:if(rd_addr>=8'h40&&rd_addr<8'hc0&&rd_addr[1:0]==0)rsp_data<=snapshot[(rd_addr-8'h40)*8+:32];
    endcase
   end else if(rsp_ready)rsp_valid<=0;
  end
 end
endmodule

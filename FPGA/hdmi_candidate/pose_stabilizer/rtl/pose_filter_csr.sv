// 4 KiB full-word register aperture. Read responses remain held under backpressure.
module pose_filter_csr #(parameter LANES=1)(
 input wire clk,resetn,wr_valid,input wire [11:0] wr_addr,input wire [31:0] wr_data,output wire wr_ready,
 input wire rd_valid,input wire [11:0] rd_addr,output wire rd_ready,
 output reg rsp_valid,output reg [31:0] rsp_data,input wire rsp_ready
);
 reg [31:0] frame_sequence,inv,ad,k,fc,beta;
 reg [2:0] init_mask,update_mask;
 reg local_reset,commit,input_write;
 reg [6:0] input_index,output_index;
 reg [31:0] input_value;
 wire busy;wire [3:0] error;wire [31:0] completed,cycles;wire signed [31:0] output_value;
 reg [2:0] reading;reg [31:0] reply;
 reg read_output;
 assign wr_ready=resetn;
 assign rd_ready=resetn && reading==0 && (!rsp_valid||rsp_ready);
 pose_filter #(.LANES(LANES)) core(.clk(clk),.resetn(resetn&&!local_reset),
  .input_write(input_write),.input_index(input_index),.input_value(input_value),.commit(commit),.frame_sequence(frame_sequence),.init_mask(init_mask),.update_mask(update_mask),
  .inverse_dt(inv),.derivative_alpha(ad),.k(k),.min_cutoff(fc),.beta(beta),.output_index(output_index),.output_value(output_value),
  .busy(busy),.completed_sequence(completed),.cycles(cycles),.error(error));
 always @(posedge clk)begin
  if(!resetn)begin frame_sequence<=0;inv<=0;ad<=0;k<=0;fc<=65536;beta<=32768;init_mask<=7;update_mask<=7;
   local_reset<=0;commit<=0;input_write<=0;reading<=0;rsp_valid<=0;rsp_data<=0;output_index<=0;end
  else begin
   local_reset<=0;commit<=0;input_write<=0;
   if(wr_valid&&wr_ready)begin
    if(wr_addr[1:0]==0 && wr_addr>=12'h400 && wr_addr<12'h5f8)begin input_write<=1;input_index<=(wr_addr-12'h400)>>2;input_value<=wr_data;end
    else case(wr_addr)
     12'h008:begin if(wr_data==1)commit<=1;else if(wr_data==2)local_reset<=1;end
     12'h00c:if(!busy)frame_sequence<=wr_data;
     12'h01c:if(!busy)init_mask<=wr_data[2:0];
     12'h020:if(!busy)inv<=wr_data;
     12'h024:if(!busy)ad<=wr_data;
     12'h028:if(!busy)k<=wr_data;
     12'h02c:if(!busy)fc<=wr_data;
     12'h030:if(!busy)beta<=wr_data;
     12'h034:if(!busy)update_mask<=wr_data[2:0];
    endcase
   end
   if(rsp_valid&&rsp_ready)rsp_valid<=0;
   if(rd_valid&&rd_ready)begin
    reading<=3;read_output<=0;reply<=32'hbad00001;
    if(rd_addr[1:0]==0 && rd_addr>=12'h800 && rd_addr<12'h9f8)begin read_output<=1;output_index<=(rd_addr-12'h800)>>2;end
    else case(rd_addr)
     12'h000:reply<=32'h504f5301;
     12'h004:reply<={24'd0,error,3'd0,busy};
     12'h010:reply<=completed;
     12'h014:reply<=cycles;
     12'h018:reply<=LANES;
    endcase
   end else if(reading!=0)begin
    reading<=reading-1'b1;
    if(reading==1)begin rsp_valid<=1;rsp_data<=read_output?output_value:reply;end
   end
  end
 end
endmodule

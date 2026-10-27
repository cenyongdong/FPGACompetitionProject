// 4 KiB full-word register aperture. Read responses remain held under backpressure.
module pose_filter_csr #(parameter LANES=1)(
 input wire clk,resetn,wr_valid,input wire [11:0] wr_addr,input wire [31:0] wr_data,output wire wr_ready,
 input wire rd_valid,input wire [11:0] rd_addr,output wire rd_ready,
 output reg rsp_valid,output reg [31:0] rsp_data,input wire rsp_ready
);
 reg [31:0] frame_sequence,inv,ad,k,fc,beta;
 reg [2:0] init_mask,update_mask;
 reg local_reset,commit,input_write,geometry_commit;
 reg [31:0] geometry_sequence;
 reg [2:0] geometry_mask;
 reg [3:0] moment_index,local_error;
 reg [6:0] input_index,output_index;
 reg [31:0] input_value;
 wire filter_busy,geometry_busy;wire busy=filter_busy||geometry_busy;
 wire [3:0] filter_error,geometry_error;wire [3:0] error=filter_error|geometry_error|local_error;
 wire [31:0] completed,cycles,geometry_completed,geometry_cycles,moment_value;wire [2:0] duplicates;wire signed [31:0] output_value;
 reg [2:0] reading;reg [31:0] reply;
 reg read_output,read_geometry;
 assign wr_ready=resetn;
 assign rd_ready=resetn && reading==0 && (!rsp_valid||rsp_ready);
 pose_filter #(.LANES(LANES)) core(.clk(clk),.resetn(resetn&&!local_reset),
  .input_write(input_write),.clear_written(geometry_commit),.input_index(input_index),.input_value(input_value),.commit(commit),.frame_sequence(frame_sequence),.init_mask(init_mask),.update_mask(update_mask),
  .inverse_dt(inv),.derivative_alpha(ad),.k(k),.min_cutoff(fc),.beta(beta),.output_index(output_index),.output_value(output_value),
  .busy(filter_busy),.completed_sequence(completed),.cycles(cycles),.error(filter_error));
 pose_geometry geometry(.clk(clk),.resetn(resetn&&!local_reset),.input_write(input_write),.clear_written(commit),.input_index(input_index),.input_value(input_value),
  .start(geometry_commit),.valid_mask(geometry_mask),.frame_sequence(geometry_sequence),.moment_index(moment_index),.moment_value(moment_value),
  .busy(geometry_busy),.error(geometry_error),.completed(geometry_completed),.cycles(geometry_cycles),.duplicate_mask(duplicates));
 always @(posedge clk)begin
  if(!resetn)begin frame_sequence<=0;inv<=0;ad<=0;k<=0;fc<=65536;beta<=32768;init_mask<=7;update_mask<=7;
   local_reset<=0;commit<=0;geometry_commit<=0;geometry_sequence<=0;geometry_mask<=0;moment_index<=0;local_error<=0;input_write<=0;reading<=0;rsp_valid<=0;rsp_data<=0;output_index<=0;end
  else begin
   local_reset<=0;commit<=0;geometry_commit<=0;input_write<=0;
   if(wr_valid&&wr_ready)begin
    if(wr_addr[1:0]==0 && wr_addr>=12'h400 && wr_addr<12'h5f8)begin input_write<=1;input_index<=(wr_addr-12'h400)>>2;input_value<=wr_data;end
    else case(wr_addr)
     12'h008:begin if(wr_data==1)begin if(geometry_busy||geometry_commit)local_error[0]<=1;else commit<=1;end else if(wr_data==2)begin local_reset<=1;local_error<=0;end end
     12'h00c:if(!busy)frame_sequence<=wr_data;
     12'h01c:if(!busy)init_mask<=wr_data[2:0];
     12'h020:if(!busy)inv<=wr_data;
     12'h024:if(!busy)ad<=wr_data;
     12'h028:if(!busy)k<=wr_data;
     12'h02c:if(!busy)fc<=wr_data;
     12'h030:if(!busy)beta<=wr_data;
     12'h034:if(!busy)update_mask<=wr_data[2:0];
     12'h108:if(wr_data==1)begin if(filter_busy||commit)local_error[0]<=1;else geometry_commit<=1;end
     12'h10c:if(!busy)geometry_sequence<=wr_data;
     12'h11c:if(!busy)geometry_mask<=wr_data[2:0];
    endcase
   end
   if(rsp_valid&&rsp_ready)rsp_valid<=0;
   if(rd_valid&&rd_ready)begin
    reading<=3;read_output<=0;read_geometry<=0;reply<=32'hbad00001;
    if(rd_addr[1:0]==0 && rd_addr>=12'h800 && rd_addr<12'h9f8)begin read_output<=1;output_index<=(rd_addr-12'h800)>>2;end
    else if(rd_addr[1:0]==0&&rd_addr>=12'h140&&rd_addr<12'h17c)begin read_geometry<=1;moment_index<=(rd_addr-12'h140)>>2;end
    else case(rd_addr)
     12'h000:reply<=32'h504f5302;
     12'h004:reply<={24'd0,error,3'd0,busy};
     12'h010:reply<=completed;
     12'h014:reply<=cycles;
     12'h018:reply<=LANES;
     12'h110:reply<=geometry_completed;
     12'h114:reply<=geometry_cycles;
     12'h118:reply<={29'd0,duplicates};
    endcase
   end else if(reading!=0)begin
    reading<=reading-1'b1;
    if(reading==1)begin rsp_valid<=1;rsp_data<=read_output?output_value:read_geometry?moment_value:reply;end
   end
  end
 end
endmodule

// Complete-frame interface. Published output bank is immutable until all lanes finish.
module pose_filter #(parameter LANES=1)(
 input wire clk,resetn,input_write,input wire [6:0] input_index,input wire signed [31:0] input_value,
 input wire commit,input wire [31:0] frame_sequence,input wire [2:0] init_mask,update_mask,
 input wire signed [31:0] inverse_dt,derivative_alpha,k,min_cutoff,beta,
 input wire [6:0] output_index,output reg signed [31:0] output_value,
 output reg busy,output reg [31:0] completed_sequence,cycles,output reg [3:0] error
);
 localparam DEPTH=(126+LANES-1)/LANES;
 reg [125:0] written;
 reg [2:0] initialized;
 reg start,published_bank;
 reg [31:0] active_sequence;
 reg [2:0] active_init,active_update;
 reg signed [31:0] inv,ad,kk,fc,bb;
 wire [LANES-1:0] lane_busy,lane_done,lane_bank;
 wire signed [31:0] lane_value[0:LANES-1];
 wire [31:0] lane_cycles[0:LANES-1];
 reg [LANES-1:0] finished;
 integer j;
 generate for(genvar g=0;g<LANES;g=g+1)begin:lane
  pose_filter_lane #(.LANES(LANES),.LANE(g)) unit(
   .clk(clk),.resetn(resetn),.start(start),.input_write(input_write&&!busy),.input_index(input_index),.input_value(input_value),
   .init_mask(active_init),.update_mask(active_update),.inverse_dt(inv),.derivative_alpha(ad),.k(kk),.min_cutoff(fc),.beta(bb),
   .read_index(output_index/LANES),.published_bank(published_bank),.read_value(lane_value[g]),.busy(lane_busy[g]),.done(lane_done[g]),.output_bank(lane_bank[g]),.cycles(lane_cycles[g]));
 end endgenerate
 reg [6:0] read_delayed;
 always @(posedge clk)begin
  read_delayed<=output_index;
  output_value<=read_delayed<126?lane_value[read_delayed%LANES]:0;
  if(!resetn)begin written<=0;initialized<=0;start<=0;published_bank<=0;busy<=0;completed_sequence<=0;cycles<=0;error<=0;finished<=0;end
  else begin
   start<=0;
   if(input_write)begin if(busy)error[0]<=1;else if(input_index<126)written[input_index]<=1;else error[1]<=1;end
   if(commit)begin
    if(busy)error[0]<=1;
    else if(!(&written)||frame_sequence==0||frame_sequence<=completed_sequence)error[1]<=1;
    else if(inverse_dt<=0||derivative_alpha<=0||derivative_alpha>65536||k<=0||min_cutoff<=0||beta<0)error[2]<=1;
    else begin
     busy<=1;start<=1;cycles<=0;finished<=0;written<=0;active_sequence<=frame_sequence;
     active_init<=init_mask|~initialized;active_update<=update_mask|~initialized;initialized<=3'b111;
     inv<=inverse_dt;ad<=derivative_alpha;kk<=k;fc<=min_cutoff;bb<=beta;
    end
   end
   if(busy)begin cycles<=cycles+1'b1;finished<=finished|lane_done;
    if(&(finished|lane_done))begin busy<=0;published_bank<=lane_bank[0];completed_sequence<=active_sequence;end
   end
  end
 end
endmodule

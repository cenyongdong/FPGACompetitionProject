// Bounded three-person Q16.16 geometry. One pipelined 32x32 multiplier;
// duplicate decisions use integer moments and exact rational thresholds.
module pose_geometry(
 input wire clk,resetn,input_write,clear_written,
 input wire [6:0] input_index,input wire signed [31:0] input_value,
 input wire start,input wire [2:0] valid_mask,input wire [31:0] frame_sequence,
 input wire [3:0] moment_index,output reg [31:0] moment_value,
 output reg busy,output reg [3:0] error,output reg [31:0] completed,cycles,
 output reg [2:0] duplicate_mask
);
 (* ram_style="block" *) reg signed [31:0] samples[0:125];
 reg [125:0] written;
 reg [2:0] active_mask,working_duplicates;
 reg [31:0] active_sequence;
 reg signed [31:0] sums[0:8],published_sums[0:8];
 reg [63:0] radii[0:2],published_radii[0:2];
 reg [63:0] square_sum,centre_square,full_sum,delta_sum;
 reg signed [31:0] xa,xb,ma,mb;
 reg signed [63:0] product;
 reg [4:0] phase;
 reg [1:0] slot,axis,pa,pb,pair_index;
 reg [5:0] index;
 integer i;
 localparam [63:0] FLOOR=64'd52613349376;
 wire [125:0] required={{42{valid_mask[2]}},{42{valid_mask[1]}},{42{valid_mask[0]}}};
 wire [63:0] raw_radius=14*square_sum-centre_square;
 wire [63:0] full=14*full_sum;
 wire [63:0] relative_shape=full-delta_sum;
 wire [63:0] scale=radii[pa]>radii[pb]?radii[pa]:radii[pb];
 wire duplicate=((100*delta_sum<9*scale)&&(100*full<9*scale))||
                ((100*delta_sum<49*scale)&&(25*relative_shape<scale));
 always @* begin
  moment_value=0;
  if(moment_index<9)moment_value=published_sums[moment_index];
  else if(moment_index<15)moment_value=moment_index[0]?published_radii[(moment_index-9)/2][31:0]:published_radii[(moment_index-9)/2][63:32];
 end
 always @(posedge clk)begin
  product<=$signed(ma)*$signed(mb);
  if(input_write&&!busy&&input_index<126)samples[input_index]<=input_value;
  if(busy&&phase==1)xa<=samples[slot*42+index];
  if(busy&&phase==9)begin xa<=samples[pa*42+index];xb<=samples[pb*42+index];end
 end
 always @(posedge clk)begin
  if(!resetn)begin busy<=0;error<=0;completed<=0;cycles<=0;written<=0;duplicate_mask<=0;phase<=0;
   for(i=0;i<9;i=i+1)published_sums[i]<=0;
   for(i=0;i<3;i=i+1)published_radii[i]<=FLOOR;
  end else begin
   if(clear_written)written<=0;
   if(input_write)begin
    if(busy)error[0]<=1;
    else if(input_index<126)written[input_index]<=1;
    else error[1]<=1;
   end
   if(start)begin
    if(busy)error[0]<=1;
    else if(valid_mask==0||(written&required)!=required||frame_sequence==0||frame_sequence<=completed)error[1]<=1;
    else begin busy<=1;cycles<=0;active_mask<=valid_mask;active_sequence<=frame_sequence;written<=0;phase<=0;end
   end
   if(busy)begin
    cycles<=cycles+1'b1;
    case(phase)
     0:begin
      for(i=0;i<9;i=i+1)sums[i]<=0;
      for(i=0;i<3;i=i+1)radii[i]<=FLOOR;
      slot<=0;index<=0;axis<=0;square_sum<=0;centre_square<=0;working_duplicates<=0;phase<=1;
     end
     1:if(active_mask[slot])phase<=2;else if(slot==2)begin pa<=0;pb<=1;pair_index<=0;index<=0;full_sum<=0;delta_sum<=0;phase<=9;end else slot<=slot+1'b1;
     2:begin
      if(xa>32'sd1048576||xa< -32'sd1048576)begin error[2]<=1;busy<=0;end
      else begin sums[slot*3+axis]<=sums[slot*3+axis]+xa;ma<=xa;mb<=xa;phase<=3;end
     end
     3:phase<=4;
     4:begin square_sum<=square_sum+product;
      if(index==41)begin axis<=0;phase<=5;end
      else begin index<=index+1'b1;axis<=axis==2?0:axis+1'b1;phase<=1;end
     end
     5:begin ma<=sums[slot*3+axis];mb<=sums[slot*3+axis];phase<=6;end
     6:phase<=7;
     7:begin centre_square<=centre_square+product;if(axis==2)phase<=8;else begin axis<=axis+1'b1;phase<=5;end end
     8:begin radii[slot]<=raw_radius>FLOOR?raw_radius:FLOOR;
      if(slot==2)begin pa<=0;pb<=1;pair_index<=0;index<=0;full_sum<=0;delta_sum<=0;phase<=9;end
      else begin slot<=slot+1'b1;index<=0;axis<=0;square_sum<=0;centre_square<=0;phase<=1;end
     end
     9:if(active_mask[pa]&&active_mask[pb])phase<=10;else phase<=17;
     10:begin ma<=xa-xb;mb<=xa-xb;phase<=11;end
     11:phase<=12;
     12:begin full_sum<=full_sum+product;if(index==41)begin axis<=0;phase<=13;end else begin index<=index+1'b1;phase<=9;end end
     13:begin ma<=sums[pa*3+axis]-sums[pb*3+axis];mb<=sums[pa*3+axis]-sums[pb*3+axis];phase<=14;end
     14:phase<=15;
     15:begin delta_sum<=delta_sum+product;if(axis==2)phase<=16;else begin axis<=axis+1'b1;phase<=13;end end
     16:begin working_duplicates[pair_index]<=duplicate;phase<=17;end
     17:if(pair_index==2)phase<=18;else begin
      if(pair_index==0)pb<=2;else pa<=1;
      pair_index<=pair_index+1'b1;index<=0;full_sum<=0;delta_sum<=0;phase<=9;
     end
     18:begin
      for(i=0;i<9;i=i+1)published_sums[i]<=sums[i];
      for(i=0;i<3;i=i+1)published_radii[i]<=radii[i];
      duplicate_mask<=working_duplicates;completed<=active_sequence;busy<=0;
     end
     default:begin error[3]<=1;busy<=0;end
    endcase
   end
  end
 end
endmodule

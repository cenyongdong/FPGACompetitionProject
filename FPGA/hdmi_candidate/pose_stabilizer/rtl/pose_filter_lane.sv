// One shared multiplier and one restoring divider per lane. No bus master.
module pose_filter_lane #(parameter LANES=1,LANE=0,DEPTH=(126+LANES-1)/LANES)(
 input wire clk,resetn,start,
 input wire input_write,input wire [6:0] input_index,input wire signed [31:0] input_value,
 input wire [2:0] init_mask,update_mask,
 input wire signed [31:0] inverse_dt,derivative_alpha,k,min_cutoff,beta,
 input wire [6:0] read_index,input wire published_bank,
 output reg signed [31:0] read_value,
 output reg busy,done,output_bank,
 output reg [31:0] cycles
);
 (* ram_style="block" *) reg signed [31:0] inputs[0:DEPTH-1];
 (* ram_style="block" *) reg [95:0] state_mem[0:DEPTH-1];
 (* ram_style="block" *) reg signed [31:0] outputs[0:2*DEPTH-1];
 reg [6:0] index;
 reg [4:0] phase;
 reg signed [31:0] x,px,py,pd,v,d,z,y,ma,mb;
 // Separate the 32x32 product from rounding/saturation at the actual 100 MHz
 // GP clock. Wait phases preserve the fixed-reference arithmetic ordering.
 reg signed [63:0] product;
 reg [16:0] quotient;
 reg [31:0] denominator,remainder;
 reg [5:0] div_bit;
 reg work_bank;
 wire [32:0] shifted={remainder,1'b0};
 wire [7:0] coordinate=index*LANES+LANE;
 wire [1:0] slot=coordinate<42?0:coordinate<84?1:2;
 function automatic signed [31:0] saturate(input signed [63:0] n);
  if(n>64'sh7fffffff)saturate=32'sh7fffffff;else if(n< -64'sh80000000)saturate=32'sh80000000;else saturate=n[31:0];
 endfunction
 function automatic signed [31:0] addq(input signed [31:0] a,b);
  reg signed [32:0] r;begin r=$signed({a[31],a})+$signed({b[31],b});addq=r[32]==r[31]?r[31:0]:r[32]?32'h80000000:32'h7fffffff;end
 endfunction
 function automatic signed [31:0] subq(input signed [31:0] a,b);
  reg signed [32:0] r;begin r=$signed({a[31],a})-$signed({b[31],b});subq=r[32]==r[31]?r[31:0]:r[32]?32'h80000000:32'h7fffffff;end
 endfunction
 function automatic signed [31:0] rounded(input signed [63:0] n);
  reg signed [48:0] r;begin
   r=$signed({n[63],n[63:16]})+$signed({48'd0,(n[15:0]>16'h8000||(n[15:0]==16'h8000&&!n[63]))});
   rounded=(r[48:31]=={18{r[31]}})?r[31:0]:r[48]?32'h80000000:32'h7fffffff;end
 endfunction
 wire signed [31:0] result=rounded(product);
 always @(posedge clk)begin
  product<=$signed(ma)*$signed(mb);
  if(input_write && input_index<126 && input_index%LANES==LANE)inputs[input_index/LANES]<=input_value;
  if(read_index<DEPTH)read_value<=outputs[published_bank*DEPTH+read_index];else read_value<=0;
 end
 always @(posedge clk)begin
  if(!resetn)begin busy<=0;done<=0;cycles<=0;index<=0;phase<=0;output_bank<=0;work_bank<=1;end
  else begin
   done<=0;
   if(start&&!busy)begin busy<=1;cycles<=0;index<=0;phase<=0;work_bank<=!published_bank;end
   else if(busy)begin
    cycles<=cycles+1'b1;
    case(phase)
     0:begin x<=inputs[index];{px,py,pd}<=state_mem[index];phase<=1;end
     1:if(!update_mask[slot])begin x<=px;y<=py;d<=pd;phase<=16;end
       else if(init_mask[slot])begin y<=x;d<=0;phase<=16;end
       else begin ma<=subq(x,px);mb<=inverse_dt;phase<=17;end
     17:phase<=2;
     2:begin v<=result;phase<=3;end
     3:begin ma<=subq(v,pd);mb<=derivative_alpha;phase<=18;end
     18:phase<=4;
     4:begin d<=addq(pd,result);phase<=5;end
     5:begin ma<=d==32'sh80000000 ? 32'sh7fffffff : d<0 ? -d : d;mb<=beta;phase<=19;end
     19:phase<=6;
     6:begin v<=addq(min_cutoff,result);phase<=7;end
     7:begin ma<=v;mb<=k;phase<=20;end
     20:phase<=8;
     8:begin z<=result;phase<=9;end
     // 0 <= z/(1+z) < 1: generate only its 16 fractional bits.
     9:begin denominator<=z+32'd65536;remainder<=z;quotient<=0;div_bit<=15;phase<=10;end
     10:begin
       if(shifted>={1'b0,denominator})begin remainder<=shifted-{1'b0,denominator};quotient<={quotient[15:0],1'b1};end
       else begin remainder<=shifted;quotient<={quotient[15:0],1'b0};end
       if(div_bit==0)phase<=11;else div_bit<=div_bit-1'b1;
     end
     11:begin ma<={15'd0,quotient}+(shifted>={1'b0,denominator});mb<=subq(x,py);phase<=21;end
     21:phase<=12;
     12:begin y<=addq(py,result);phase<=16;end
     16:begin state_mem[index]<={x,y,d};outputs[work_bank*DEPTH+index]<=y;
       if((index+1)*LANES+LANE>=126)begin busy<=0;done<=1;output_bank<=work_bank;end
       else begin index<=index+1'b1;phase<=0;end
     end
     default:begin busy<=0;done<=1;end
    endcase
   end
  end
 end
endmodule

// One 18x18 multiplier, signed 48-bit sum, bounded BRAMs, GP-clock CSR.
// No DMA, HP master, bus reset, clock generator, or implicit device addresses.
module vitals_acf_csr(
 input wire clk, resetn,
 input wire wr_valid, input wire [7:0] wr_addr, input wire [31:0] wr_data, output wire wr_ready,
 input wire rd_valid, input wire [7:0] rd_addr, output wire rd_ready,
 output reg rsp_valid, output reg [31:0] rsp_data, input wire rsp_ready
);
 localparam IDLE=0, FETCH=1, MULTIPLY=2, ACCUMULATE=3;
 reg [1:0] state;
 reg [11:0] length, loaded;
 reg [8:0] last_lag, lag, result_index;
 reg [10:0] sample_index;
 reg [31:0] sequence_id, completed, cycles;
 reg done, fault;
 reg signed [47:0] accumulator;
 (* use_dsp="yes" *) reg signed [35:0] product;
 (* ram_style="block" *) reg signed [47:0] results[0:511];
 wire signed [17:0] sample_a,sample_b;
 reg signed [47:0] result_value;
 wire busy=state!=IDLE;
 wire local_clear=wr_valid&&wr_ready&&wr_addr==8'h08&&wr_data==2;
 wire sample_range=$signed(wr_data)>=-32'sd65535&&$signed(wr_data)<=32'sd65535;
 wire sample_write=wr_valid&&wr_ready&&wr_addr==8'h20&&!busy&&!fault&&!done&&length!=0&&loaded<length&&sample_range;
 wire signed [47:0] extended_product={{12{product[35]}},product};
 wire signed [47:0] next_sum=accumulator+extended_product;
 wire [10:0] second_index=sample_index-{2'd0,lag};
 // Two simple-dual-port copies avoid the adapted library's unsupported
 // two-read/one-write inference. Both copies receive the same sequential load.
 (* keep_hierarchy="yes" *) vitals_acf_ram ram_a(clk,sample_write,loaded[10:0],wr_data[17:0],sample_index,sample_a);
 (* keep_hierarchy="yes" *) vitals_acf_ram ram_b(clk,sample_write,loaded[10:0],wr_data[17:0],second_index,sample_b);
 assign wr_ready=resetn;
 reg [1:0] reading;
 reg [7:0] read_address;
 reg [31:0] read_snapshot;
 assign rd_ready=resetn&&reading==0&&(!rsp_valid||rsp_ready);

 // RAMs are intentionally not reset. loaded/done protect every observable word.
 always @(posedge clk)begin
  if(state==ACCUMULATE&&sample_index==length-1&&!local_clear)results[lag]<=next_sum;
  result_value<=results[result_index];
 end
 always @(posedge clk)begin
  if(!resetn||local_clear)begin
   state<=IDLE;length<=0;loaded<=0;last_lag<=0;lag<=0;sample_index<=0;
   result_index<=0;sequence_id<=0;completed<=0;cycles<=0;done<=0;fault<=0;accumulator<=0;product<=0;
  end else begin
   if(busy)cycles<=cycles+1'b1;
   case(state)
    FETCH:state<=MULTIPLY;
    MULTIPLY:begin product<=sample_a*sample_b;state<=ACCUMULATE;end
    ACCUMULATE:begin
     accumulator<=next_sum;
     if(sample_index==length-1)begin
      accumulator<=0;
      if(lag==last_lag)begin state<=IDLE;done<=1;completed<=sequence_id;end
      else begin lag<=lag+1'b1;sample_index<={2'd0,lag}+1'b1;state<=FETCH;end
     end else begin sample_index<=sample_index+1'b1;state<=FETCH;end
    end
   endcase
   if(wr_valid&&wr_ready)begin
    if(busy)fault<=1;
    else case(wr_addr)
     8'h08:if(wr_data==1&&!fault&&!done&&length!=0&&loaded==length&&last_lag<length&&sequence_id!=0)begin
      state<=FETCH;lag<=0;sample_index<=0;accumulator<=0;cycles<=0;done<=0;
     end else fault<=1;
     8'h0c:if(loaded==0&&!done&&wr_data>=1&&wr_data<=2048)length<=wr_data[11:0];else fault<=1;
     8'h10:if(loaded==0&&!done&&wr_data<=511)last_lag<=wr_data[8:0];else fault<=1;
     8'h14:if(!done&&wr_data!=0)sequence_id<=wr_data;else fault<=1;
     8'h20:if(sample_write)loaded<=loaded+1'b1;else fault<=1;
     8'h28:if(done&&!fault&&wr_data<=last_lag)result_index<=wr_data[8:0];else fault<=1;
     default:fault<=1;
    endcase
   end
  end
 end
 // Capture normal register reads at request time. RAM reads wait two cycles;
 // the response then remains immutable for arbitrary downstream backpressure.
 always @(posedge clk)begin
  if(!resetn)begin reading<=0;rsp_valid<=0;rsp_data<=0;read_address<=0;read_snapshot<=0;end
  else begin
   if(rsp_valid&&rsp_ready)rsp_valid<=0;
   if(rd_valid&&rd_ready)begin
    reading<=2;read_address<=rd_addr;
    case(rd_addr)
     8'h00:read_snapshot<=32'h56414301;
     8'h04:read_snapshot<={23'd0,fault,6'd0,done,busy};
     8'h0c:read_snapshot<={20'd0,length};
     8'h10:read_snapshot<={23'd0,last_lag};
     8'h18:read_snapshot<=completed;
     8'h1c:read_snapshot<=cycles;
     8'h24:read_snapshot<={20'd0,loaded};
     8'h2c,8'h30:read_snapshot<=done&&!busy&&!fault?0:32'hbad00001;
     default:read_snapshot<=32'hbad00001;
    endcase
   end else if(reading!=0)begin
    reading<=reading-1'b1;
    if(reading==1)begin
     rsp_valid<=1;
     if(read_address==8'h2c&&read_snapshot==0&&done&&!busy&&!fault)rsp_data<=result_value[31:0];
     else if(read_address==8'h30&&read_snapshot==0&&done&&!busy&&!fault)rsp_data<={{16{result_value[47]}},result_value[47:32]};
     else rsp_data<=read_snapshot;
    end
   end
  end
 end
endmodule

module vitals_acf_ram(input wire clk,we,input wire [10:0] write_address,input wire [17:0] value,
 input wire [10:0] read_address,output reg signed [17:0] data);
 (* ram_style="block" *) reg [17:0] memory[0:2047];
 always @(posedge clk)begin
  if(we)memory[write_address]<=value;
  data<=memory[read_address];
 end
endmodule

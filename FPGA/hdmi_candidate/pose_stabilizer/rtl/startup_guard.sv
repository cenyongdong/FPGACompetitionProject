// Compact startup observation on one HP edge. The original one-shot drain is external.
// coverage_complete MUST be a build-time trusted capability, never a software override.
// Native protocol status remains a dependency until its mandatory/capacity checks
// have a proven replacement. Removing it ties coverage_complete low (fail closed).
module startup_guard(
 input wire clk,config_resetn,ps_resetn,pl_resetn,hp_reset,
 input wire any_request,any_write,hc_return,reader_ready,
 input wire ps_valid,ps_ready,ps_last,input wire [5:0] ps_id,input wire [1:0] ps_resp,
 input wire s_valid,s_ready,s_last,input wire [4:0] s_id,input wire [1:0] s_resp,
 input wire native_ready,native_seen_reset,coverage_complete,input wire [159:0] native_status,
 input wire [31:0] drain_status,input wire command_valid,input wire [2:0] command,
 output wire arm,output wire checker_rearm,output reg admitted,
 output reg [2:0] state,output reg [31:0] faults,ps_count,s_count,
 output reg [63:0] cycle,first_valid_cycle,arm_cycle,
 output reg [159:0] native_history,
 output reg [31:0] first_identity,ps_last_position,s_last_position,
 output wire [31:0] reset_evidence,arm_ps_count,arm_s_count
);
 localparam OBSERVE=0,ELIGIBLE=1,CONSUMING=2,SAFE_END=3,ADMITTED=4,REJECT=5;
 localparam [159:0] ALLOWED=(160'b1<<58)|(160'b1<<59)|(160'b1<<61)|(160'b1<<92)|(160'b1<<93)|(160'b1<<95);
 reg used,seen_reset,seen_pl_reset,first_seen,last_ps,last_s,rearmed;
 reg [6:0] quiet;
 reg [31:0] ps_at_arm,s_at_arm;
 assign reset_evidence={25'd0,rearmed,last_s,last_ps,first_seen,seen_pl_reset,seen_reset,used};
 assign arm_ps_count=ps_at_arm;assign arm_s_count=s_at_arm;
 wire released=ps_resetn&&pl_resetn&&!hp_reset;
 wire [31:0] current_faults=
  ((!coverage_complete)?32'h001:0)|
  ((any_request||any_write||reader_ready)?32'h002:0)|
  (hc_return?32'h004:0)|
  (((ps_valid&&(ps_id!=6'h20||ps_resp!=0))||(s_valid&&(s_id!=0||s_resp!=0)))?32'h008:0)|
  ((|(native_status&~ALLOWED))?32'h010:0)|
  (((ps_valid&&ps_ready&&last_ps)||(s_valid&&s_ready&&last_s))?32'h020:0)|
  ((first_seen&&!released)?32'h040:0)|
  (((ps_valid||s_valid)&&!native_ready)?32'h080:0);
 wire clean=!(|faults)&&!(|current_faults)&&released&&seen_reset&&seen_pl_reset&&native_seen_reset&&native_ready&&coverage_complete;
 wire seed=clean&&!used&&drain_status[2:0]==0&&ps_count>0&&ps_count<256&&s_count==0&&ps_valid&&s_valid&&!s_ready&&(|native_history[61:58]);
 assign arm=command_valid&&command==1&&seed&&(state==OBSERVE||state==ELIGIBLE);
 assign checker_rearm=command_valid&&command==2&&state==SAFE_END&&clean&&!rearmed;
 wire healthy=clean&&!first_seen&&ps_count==0&&s_count==0&&!ps_valid&&!s_valid&&drain_status==0&&!(|native_status)&&!(|native_history);
 wire consumed=clean&&state==SAFE_END&&rearmed&&!(|native_status)&&!ps_valid&&!s_valid;
 always @(posedge clk)begin
  if(!config_resetn)begin
   state<=OBSERVE;faults<=0;ps_count<=0;s_count<=0;cycle<=0;first_valid_cycle<=0;arm_cycle<=0;
   native_history<=0;used<=0;seen_reset<=0;seen_pl_reset<=0;first_seen<=0;last_ps<=0;last_s<=0;rearmed<=0;admitted<=0;ps_at_arm<=0;s_at_arm<=0;
   quiet<=0;first_identity<=0;ps_last_position<=0;s_last_position<=0;
  end else begin
   cycle<=cycle+1'b1;
   if(!ps_resetn)seen_reset<=1;
   if(!pl_resetn)seen_pl_reset<=1;
   if(ps_valid||s_valid||hc_return)quiet<=0;else if(quiet<127)quiet<=quiet+1'b1;
   if(!admitted)begin
    native_history<=native_history|native_status;
    faults<=faults|current_faults;
    if((ps_valid||s_valid||any_request||any_write||hc_return)&&!first_seen)begin first_seen<=1;first_valid_cycle<=cycle;
     first_identity<={8'd0,hc_return,any_write,any_request,s_valid,s_ready,s_last,s_resp,s_id,ps_valid,ps_ready,ps_last,ps_resp,ps_id};end
    if(ps_valid&&ps_ready)begin ps_count<=ps_count+1'b1;if(ps_last)begin last_ps<=1;ps_last_position<=ps_count+1'b1;end end
    if(s_valid&&s_ready)begin s_count<=s_count+1'b1;if(s_last)begin last_s<=1;s_last_position<=s_count+1'b1;end end
    if(ps_count>=256||s_count>=256)faults<=faults|current_faults|32'h100;
    if(state==OBSERVE&&seed)state<=ELIGIBLE;
    if(arm)begin used<=1;arm_cycle<=cycle;ps_at_arm<=ps_count;s_at_arm<=s_count;state<=CONSUMING;end
    if(state==CONSUMING)begin
     if(drain_status[2:0]>=3)begin state<=REJECT;faults<=faults|current_faults|32'h200;end
     else if(drain_status[2:0]==2)begin
      if(drain_status[11:3]>0&&drain_status[11:3]<256&&drain_status[24:12]>=64&&drain_status[24:12]<4096&&drain_status[25]&&!(|drain_status[31:26])&&
       ps_count==s_count&&s_count-s_at_arm==drain_status[11:3]&&ps_at_arm+(ps_count-ps_at_arm)==s_count&&last_s&&quiet>=64&&!ps_valid&&!s_valid&&clean)state<=SAFE_END;
      else begin state<=REJECT;faults<=faults|current_faults|32'h400;end
     end
    end
    if(state==SAFE_END&&(ps_valid||s_valid||drain_status[31]))begin state<=REJECT;faults<=faults|current_faults|32'h800;end
    if(checker_rearm)rearmed<=1;
    if(command_valid)begin
     if(command==3&&(healthy||consumed))begin admitted<=1;state<=ADMITTED;end
     else if(command!=0&&!arm&&!checker_rearm)begin faults<=faults|current_faults|32'h1000;state<=REJECT;end
    end
    if((|faults)||(|current_faults))state<=REJECT;
   end else if(command_valid&&command!=0)begin faults<=faults|32'h1000;state<=REJECT;admitted<=0;end
  end
 end
endmodule

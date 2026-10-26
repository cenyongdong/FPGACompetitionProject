module guard_fault_case #(parameter N=0)(output reg finished=0);
 reg clk=0;always #2.5 clk=~clk;
 reg rst=0,ps=0,pl=0,hp=0,req=0,wr=0,hc=0,reader=0,pv=0,pr=0,sv=0,sr=0,lastp=0,lasts=0;
 reg [5:0] pid=32;reg [4:0] sid=0;reg [1:0] presp=0,sresp=0;
 reg native_ready=1,seen=1,coverage=1,cv=0;reg [2:0] cmd=0;reg [159:0] native=0;reg [31:0] drain=0;
 wire arm,rearm,admitted;wire [2:0] state;wire [31:0] faults,pc,sc;
 startup_guard d(.clk(clk),.config_resetn(rst),.ps_resetn(ps),.pl_resetn(pl),.hp_reset(hp),.any_request(req),.any_write(wr),.hc_return(hc),.reader_ready(reader),.ps_valid(pv),.ps_ready(pr),.ps_last(lastp),.ps_id(pid),.ps_resp(presp),.s_valid(sv),.s_ready(sr),.s_last(lasts),.s_id(sid),.s_resp(sresp),.native_ready(native_ready),.native_seen_reset(seen),.coverage_complete(coverage),.native_status(native),.drain_status(drain),.command_valid(cv),.command(cmd),.arm(arm),.checker_rearm(rearm),.admitted(admitted),.state(state),.faults(faults),.ps_count(pc),.s_count(sc));
 task tick;begin @(posedge clk);#0.1;end endtask
 task command(input [2:0] n);begin cv=1;cmd=n;tick;cv=0;tick;end endtask
 integer i;
 initial begin
  repeat(2)tick;rst=1;if(N==12)begin ps=1;pl=1;end tick;ps=1;pl=1;tick;
  case(N)
   0:begin pv=1;pid=1;end
   1:begin sv=1;sresp=2;end
   2:req=1;
   3:wr=1;
   4:hc=1;
   5:begin pv=1;tick;ps=0;end
   6:begin pv=1;pr=1;lastp=1;tick;lastp=0;end
   13:begin native_ready=0;pv=1;end
   14:begin sv=1;sr=1;end
   16:begin native=160'b1<<79;end
   17:coverage=0;
  endcase
  if(N>=7&&N<=11||N==15)begin
   native=160'b1<<58;pv=1;pr=1;repeat(2)tick;pr=0;sv=1;tick;command(1);
   if(!arm&&state!=2)$fatal(1,"fault test seed %0d",N);
   drain=1;
   if(N==11)command(1);
   else if(N==7)drain=3;
   else if(N==8)drain=4;
   else begin
    pv=0;sv=1;sr=1;tick;lasts=1;tick;sv=0;sr=0;lasts=0;
    if(N==15)begin repeat(60)tick;pv=1;tick;pv=0;repeat(4)tick;end else repeat(65)tick;
    drain=(1<<25)|(66<<12)|((N==9?3:2)<<3)|2;tick;tick;
    if(N==10)begin if(state!=3)$fatal(1,"late test safe-end absent");pv=1;end
   end
  end
  repeat(3)tick;command(3);repeat(2)tick;
  if(admitted||state!=5||faults==0)$fatal(1,"unsafe case admitted/inconclusive N=%0d state=%0d faults=%h",N,state,faults);
  $display("GUARD_FAULT_PASS case=%0d faults=%h",N,faults);finished=1;
 end
endmodule
module tb_guard_faults;
 wire [17:0] done;
 for(genvar i=0;i<18;i=i+1)begin:cases guard_fault_case #(.N(i)) c(done[i]);end
 initial begin wait(&done);$display("GUARD_FAULTS_PASS cases=18");$finish;end
 initial begin #20000;$fatal(1,"guard fault timeout");end
endmodule

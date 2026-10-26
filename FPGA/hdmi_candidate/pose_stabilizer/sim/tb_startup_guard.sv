module tb_startup_guard;
 reg clk=0;always #2.5 clk=~clk;
 reg resetn=0,ps_resetn=0,pl_resetn=0,hp_reset=0,req=0,wr=0,hc=0,reader=0;
 reg pv=0,pr=0,pl=0,sv=0,sl=0;reg [5:0] pid=6'h20;reg [4:0] sid=0;reg [1:0] presp=0,sresp=0;
 reg native_ready=1,native_reset=1,coverage=1;reg [159:0] native_status=0;
 reg cv=0;reg [2:0] cmd=0;wire arm,rearm,admitted,ready;wire [2:0] state;wire [31:0] faults,pc,sc,drain;
 wire [63:0] cycle,first_cycle,arm_cycle;wire [159:0] history;
 startup_guard guard(.clk(clk),.config_resetn(resetn),.ps_resetn(ps_resetn),.pl_resetn(pl_resetn),.hp_reset(hp_reset),.any_request(req),.any_write(wr),.hc_return(hc),.reader_ready(reader),.ps_valid(pv),.ps_ready(pr),.ps_last(pl),.ps_id(pid),.ps_resp(presp),.s_valid(sv),.s_ready(ready),.s_last(sl),.s_id(sid),.s_resp(sresp),.native_ready(native_ready),.native_seen_reset(native_reset),.coverage_complete(coverage),.native_status(native_status),.drain_status(drain),.command_valid(cv),.command(cmd),.arm(arm),.checker_rearm(rearm),.admitted(admitted),.state(state),.faults(faults),.ps_count(pc),.s_count(sc),.cycle(cycle),.first_valid_cycle(first_cycle),.arm_cycle(arm_cycle),.native_history(history));
 // Test-only reconfiguration recreates original drain's power-up initialization.
 wire [31:0] real_drain;
 hp2_startup_drain consumer(.clk(clk),.ps_resetn(ps_resetn),.pl_resetn(pl_resetn),.hp_reset(hp_reset),.arm(arm),.any_request(req|wr),.reader_ready(reader),.rvalid(sv),.rid(sid),.rresp(sresp),.rlast(sl),.drain_ready(ready),.status(real_drain));
 assign drain=real_drain;
 task tick;begin @(posedge clk);#0.1;end endtask
 task command(input [2:0] v);begin cmd=v;cv=1;tick;cv=0;tick;end endtask
 integer i;
 initial begin
  repeat(3)tick;resetn=1;tick;ps_resetn=1;pl_resetn=1;tick;
  // Retained native dependency rejects capacity/unknown rule 79.
  native_status=160'b1<<79;tick;tick;if(!faults[4]||state!=5||admitted)$fatal(1,"unknown rule admitted");
  resetn=0;native_status=0;ps_resetn=0;pl_resetn=0;tick;resetn=1;tick;ps_resetn=1;pl_resetn=1;tick;
  coverage=0;tick;tick;if(!faults[0]||admitted)$fatal(1,"missing coverage admitted");
  resetn=0;coverage=1;ps_resetn=0;pl_resetn=0;tick;resetn=1;tick;ps_resetn=1;pl_resetn=1;tick;
  command(3);if(!admitted||state!=4)$fatal(1,"healthy admission failed");
  command(3);if(admitted||state!=5||!faults[12])$fatal(1,"repeated admission retained permission");
  resetn=0;ps_resetn=0;pl_resetn=0;tick;resetn=1;tick;ps_resetn=1;pl_resetn=1;tick;
  pv=1;pr=1;native_status=160'b1<<58;repeat(2)tick;pr=0;sv=1;tick;
  command(1);if(!ready||state!=2)$fatal(1,"consumer did not start");
  // command() consumed one S01 beat on its second edge: four remain.
  for(i=0;i<4;i=i+1)begin pv=i<3;pr=i<3;pl=i==2;sl=i==3;tick;end
  pv=0;pr=0;pl=0;sv=0;sl=0;
  repeat(70)tick;
  if(state!=3||faults||pc!=5||sc!=5)$fatal(1,"conservation/terminal failed state=%0d faults=%h ps=%0d s=%0d drain=%h",state,faults,pc,sc,drain);
  command(2);native_status=0;repeat(45)tick;command(3);
  if(!admitted||state!=4)$fatal(1,"consumed admission failed");
  $display("GUARD_PASS healthy known-consume unknown-rule missing-coverage conservation");$finish;
 end
endmodule

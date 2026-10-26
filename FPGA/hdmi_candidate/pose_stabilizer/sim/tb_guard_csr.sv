module tb_guard_csr;
 reg hp=0,gp=0;always #2.5 hp=~hp;always #10 gp=~gp;
 reg resetn=0,wv=0,rv=0,ready=1;reg [7:0] wa=0,ra=0;reg [31:0] wd=0;
 reg [1023:0] status=0;wire cv,wr,rr,valid;wire [2:0] command;wire [31:0] data;integer count=0;reg [31:0] got,frozen;
 startup_guard_csr d(.hp_clk(hp),.csr_clk(gp),.csr_resetn(resetn),.status_bundle(status),.command_valid(cv),.command(command),.wr_valid(wv),.wr_addr(wa),.wr_data(wd),.wr_ready(wr),.rd_valid(rv),.rd_addr(ra),.rd_ready(rr),.rsp_valid(valid),.rsp_data(data),.rsp_ready(ready));
 always @(posedge hp)begin status<=status+1;if(cv)count<=count+1;end
 task tick;begin @(posedge gp);#1;end endtask
 task read(input [7:0] a);begin ra=a;rv=1;tick;rv=0;got=data;tick;end endtask
 initial begin repeat(2)tick;resetn=1;tick;wv=1;wd=0;tick;wv=0;repeat(12)tick;
  read('h0c);if(got!=1||count!=1)$fatal(1,"command/ACK duplicate");read('h40);frozen=got;repeat(12)tick;read('h40);if(got!=frozen)$fatal(1,"snapshot mutated");
  resetn=0;repeat(4)tick;resetn=1;repeat(4)tick;if(count!=1)$fatal(1,"CSR reset repeated command");read('h0c);if(got!=1)$fatal(1,"CSR reset lost sequence");
  wv=1;wd=0;tick;tick;wv=0;repeat(12)tick;read(0);if(!got[1]||count!=2)$fatal(1,"busy duplicate not rejected");
  $display("GUARD_CSR_PASS immutable CDC sequence reset busy");$finish;end
 initial begin #10000;$fatal(1,"CSR watchdog");end
endmodule

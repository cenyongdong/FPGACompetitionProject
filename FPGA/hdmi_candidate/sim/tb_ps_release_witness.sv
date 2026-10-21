`timescale 1ns/1ps
module tb_ps_release_witness;
    reg gp=0,hp=0,hp_running=1,resetn=1,sf=0,cf=0;
    always #5 gp=~gp;
    always #2.5 if(hp_running)hp=~hp;
    reg [19:0] levels=0;
    reg [127:0] ps=0,hdmi=0;
    reg [5:0] lw=0,pw=0;
    mna_gp_ww_itf csr();
    ps_release_witness dut(.source_clk(hp),.csr_clk(gp),.csr_resetn(resetn),
      .source_freeze(sf),.csr_freeze(cf),.levels(levels),.ps_read(ps),.hdmi_read(hdmi),
      .legacy_write(lw),.ps_write(pw),.ps_awaddr(32'h12340000),.csr(csr));
    mna_gp_ww_itf csr_reverse();
    wire [19:0] reverse_levels={levels[19:2],levels[0],levels[1]};
    ps_release_witness reverse_dut(.source_clk(hp),.csr_clk(gp),.csr_resetn(resetn),
      .source_freeze(sf),.csr_freeze(cf),.levels(reverse_levels),.ps_read(ps),.hdmi_read(hdmi),
      .legacy_write(lw),.ps_write(pw),.ps_awaddr(32'h12340000),.csr(csr_reverse));
    task freeze;
      @(negedge hp);sf=1;@(negedge hp);sf=0;
      repeat(4)@(negedge gp);cf=1;@(negedge gp);cf=0;@(negedge gp);
    endtask
    task readword(input integer word_index,output reg [31:0] value);
      @(negedge gp);csr.araddr=32'h400b0600+4*word_index;csr.arvalid=1;
      @(negedge gp);csr.arvalid=0;
      if(!csr.rvalid)$fatal(1,"CSR response missing");value=csr.rdata;
      @(negedge gp);
    endtask
    reg [31:0] v;
    reg [63:0] old_first;
    integer raw_file;
    initial begin
      csr.araddr=0;csr.arvalid=0;csr.rready=1;csr.awwaddr=0;csr.awwvalid=0;csr.awwdata=0;
      csr_reverse.araddr=0;csr_reverse.arvalid=0;csr_reverse.rready=1;
      csr_reverse.awwaddr=0;csr_reverse.awwvalid=0;csr_reverse.awwdata=0;
      resetn=0;repeat(3)@(negedge gp);resetn=1;
      levels[0]=1;repeat(6)@(negedge gp);levels[1]=1;
      repeat(6)@(negedge gp);
      if(!(dut.first_time[0]<dut.first_time[1]))$fatal(1,"PS-first order lost");
      if(!(reverse_dut.first_time[1]<reverse_dut.first_time[0]))$fatal(1,"PL-first order lost");
      // Source-only pulse falls entirely between GP edges.
      @(negedge hp);lw=6'b000011;@(negedge hp);lw=0;
      if(dut.counts[2]!=1)$fatal(1,"Short HP write handshake lost");
      repeat(100)@(negedge gp);
      if(!dut.sampled[7])$fatal(1,"HP activity witness did not start");
      // Reset while HP is stopped is still visible in the GP timeline.
      @(negedge hp);hp_running=0;
      levels[0]=0;repeat(6)@(negedge gp);levels[0]=1;
      repeat(6)@(negedge gp);
      if(dut.last_ps_release<=dut.first_time[0])$fatal(1,"Stopped-clock reset lost");
      repeat(300)@(negedge gp);
      if(dut.sampled[7])$fatal(1,"Stopped HP clock still marked active");
      hp_running=1;
      @(negedge hp);dut.hp_cycles=64'hfffffffe;
      repeat(4)@(negedge hp);
      if(dut.hp_cycles[63:32]!=1)$fatal(1,"64-bit HP timestamp did not extend");
      levels[6]=1;ps[62]=1;ps[69:64]=32;
      repeat(100)@(negedge gp);
      if(!dut.sampled[7])$fatal(1,"Resumed HP activity not recorded");
      if(dut.first_seen[0] || !dut.first_seen[1] || !dut.first_seen[3])$fatal(1,"Unsolicited raw R capture missing");
      // Close GP events deliberately; dedicated first times must survive full log.
      repeat(24)begin levels[19]=~levels[19];repeat(5)@(negedge gp);end
      if(!dut.overflow || dut.event_count!=16)$fatal(1,"Event overflow not explicit");
      levels[1:0]=0;repeat(6)@(negedge gp);levels[1:0]=3;
      repeat(6)@(negedge gp);
      if(dut.last_ps_release!=dut.last_pl_release)$fatal(1,"Coincident releases acquired a false order");
      old_first=dut.first_time[0];freeze();
      readword(0,v);if(v!=32'h50534c01)$fatal(1,"Wrong ABI");
      readword(38,v);if(v!=1)$fatal(1,"Write count not held");
      readword(54,v);if(v!=1)$fatal(1,"First ready R timestamp lost high bits");
      readword(1,v);if(!v[0] || !v[1] || !v[2])$fatal(1,"Publication flags wrong");
      raw_file=$fopen("native-release-snapshot.jsonl","w");
      $fwrite(raw_file,"{\"event\":\"ps_release_snapshot\",\"words\":[");
      for(integer k=0;k<128;k=k+1)begin
        readword(k,v);if(k>0)$fwrite(raw_file,",");$fwrite(raw_file,"%0d",v);
      end
      $fwrite(raw_file,"]}\n");$fclose(raw_file);
      resetn=0;repeat(4)@(negedge gp);resetn=1;
      if(dut.first_time[0]!=old_first || !dut.sealed)$fatal(1,"Local reset erased history");
      readword(1,v);if(v[0])$fatal(1,"Local reset did not hide stale publication");
      $display("PS_RELEASE_WITNESS_PASS PS-first stopped-HP short-write raw-R overflow persistent-history");
      $finish;
    end
    initial begin #200000;$fatal(1,"Simulation watchdog");end
endmodule

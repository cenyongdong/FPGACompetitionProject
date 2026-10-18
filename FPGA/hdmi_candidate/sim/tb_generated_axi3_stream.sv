`timescale 1ns/1ps
// Template: expand GENERATED_* exactly as documented in the adjacent README.
// Only the testbench traffic model changes; the generated DUT remains unchanged.
module tb_generated_axi3_stream;
  localparam integer PER_SOURCE=256, TOTAL=2*PER_SOURCE;
  localparam integer MAX_M_OUTSTANDING=8, MAX_S_OUTSTANDING=8;
  localparam integer WATCHDOG_CYCLES=60000;
  reg clk=0, rstn=0;
  always #2.5 clk=~clk;
  // GENERATED_DECLARATIONS
  // GENERATED_CONNECTIONS
  // GENERATED_CLOCK_RESET

  integer cycles=0, trace_file=0;
  integer submitted[0:1], completed[0:1], source_beats[0:1];
  integer source_peak[0:1], source_ar_cycle[0:1][0:PER_SOURCE-1];
  integer source_returned[0:1][0:PER_SOURCE-1];
  reg source_accepted[0:1][0:PER_SOURCE-1];
  reg source_done[0:1][0:PER_SOURCE-1];
  reg master_seen[0:TOTAL-1], pending[0:TOTAL-1];
  integer master_returned[0:TOTAL-1], master_order[0:TOTAL-1];
  integer master_accepted=0, master_completed=0, master_beats=0;
  integer master_peak=0, out_of_order=0, current_response=-1;
  integer master_ar_stalls=0, master_r_stalls=0;
  integer source_r_stalls[0:1];
  reg master_ar_ready_latched=0;
  integer expected_beats=0;
  reg source_ar_fire[0:1], master_r_fire=0;
  reg [31:0] covered_ids[0:1];
  reg [3:0] covered_lengths=0, covered_responses=0;
  reg source_ar_held[0:1], source_r_held[0:1];
  reg master_ar_held=0, master_r_held=0;
  reg [63:0] previous_source_ar[0:1], previous_master_ar;
  reg [79:0] previous_source_r[0:1], previous_master_r;
  integer i,j,s,seq,index,chosen,oldest,beat;
  reg [63:0] ar_payload;
  reg [79:0] r_payload;

  function automatic integer burst_beats(input integer n);
    case(n%4) 0:burst_beats=1; 1:burst_beats=2;
      2:burst_beats=8; default:burst_beats=16; endcase
  endfunction
  function automatic integer burst_id(input integer n);
    // First 192 requests cover all IDs; final 64 reuse four IDs while pending.
    burst_id=(n<192)? n%32:n%4;
  endfunction
  function automatic [31:0] burst_address(input integer src,input integer n);
    integer offset;
    begin
      // Every transaction owns a page. Half end exactly at a 4KiB boundary;
      // the next transaction begins on the next page, never crossing within AR.
      offset=(n%8>=4)? 4096-8*burst_beats(n):64*(n%4);
      burst_address=32'h01000000+src*32'h08000000+n*4096+offset;
    end
  endfunction
  function automatic [1:0] burst_response(input integer n);
    if(n%13==0) burst_response=2'b10;       // legal SLVERR propagation
    else if(n%17==0) burst_response=2'b11;  // legal DECERR propagation
    else burst_response=2'b00;
  endfunction
  function automatic [63:0] burst_data(input integer src,input integer n,input integer b);
    burst_data=64'hc35a691700000000 ^ (64'h1000000000000000*src)
      ^ (64'h10001*n) ^ (64'h0101010101010101*b);
  endfunction
  function automatic integer decoded_source(input [31:0] address);
    decoded_source=(address>=32'h09000000)?1:0;
  endfunction
  function automatic integer decoded_sequence(input [31:0] address,input integer src);
    decoded_sequence=(address-(32'h01000000+src*32'h08000000))>>12;
  endfunction
  function automatic integer full_id(input integer n);
    full_id=(n/PER_SOURCE)*32+burst_id(n%PER_SOURCE);
  endfunction
  function automatic integer response_eligible(input integer n);
    integer k;
    begin
      response_eligible=pending[n];
      // Only accepted downstream requests are eligible; preserve FIFO per RID.
      for(k=0;k<TOTAL;k=k+1)
        if(pending[k] && full_id(k)==full_id(n) && master_order[k]<master_order[n])
          response_eligible=0;
    end
  endfunction
  task automatic fail(input string message);
    begin
      $display("GENERATED_AXI3_STREAM_FAIL cycle=%0d submitted=%0d/%0d accepted=%0d completed=%0d/%0d master_completed=%0d : %s",
        cycles,submitted[0],submitted[1],master_accepted,completed[0],completed[1],master_completed,message);
      if(trace_file) begin
        $fdisplay(trace_file,"FAIL,%0d,%s",cycles,message);
        $fflush(trace_file); $fclose(trace_file);
      end
      $fatal(1,"%s",message);
    end
  endtask
  task automatic check_source_response(input integer src,input [4:0] rid,
      input [63:0] data,input [1:0] resp,input last);
    integer n,first;
    begin
      first=-1;
      for(n=0;n<PER_SOURCE;n=n+1)
        if(first<0 && source_accepted[src][n] && !source_done[src][n] && burst_id(n)==rid)
          first=n;
      if(first<0) fail($sformatf("Unexpected upstream response source=%0d RID=%0d",src,rid));
      else begin
        n=source_returned[src][first];
        // Error-response RDATA is architecturally unspecified; compare payload
        // bytes only for OKAY, while all RESP/RID/LAST/stability checks remain.
        if(n>=burst_beats(first) || (burst_response(first)==0 && data!==burst_data(src,first,n)) ||
           resp!==burst_response(first) || last!==(n==burst_beats(first)-1))
          fail($sformatf("Upstream payload/RESP/LAST/order source=%0d seq=%0d beat=%0d RID=%0d",src,first,n,rid));
        if(master_returned[src*PER_SOURCE+first]<=n)
          fail("Upstream response has no accepted downstream data beat");
        source_returned[src][first]=n+1;
        source_beats[src]=source_beats[src]+1;
        covered_responses[resp]=1'b1;
        $fdisplay(trace_file,"S_R,%0d,%0d,%0d,%0d,%08h,%0d,%0d,%0d,%0d,%016h",
          cycles,src,first,rid,burst_address(src,first),n,burst_beats(first),last,resp,data);
        if(last) begin source_done[src][first]=1; completed[src]=completed[src]+1; end
      end
    end
  endtask

  // Deterministic backpressure. READY depends on cycle/queue state, never VALID.
  assign S00_AXI_rready=rstn && cycles%11<8;
  assign S01_AXI_rready=rstn && cycles%13<9;
  assign S00_AXI_bready=1'b1;
  assign S01_AXI_bready=1'b1;
  // The room decision is sampled on the falling edge. Using the posedge ledger
  // combinationally here would race the DUT's own active-region AR sampling.
  assign M00_AXI_arready=master_ar_ready_latched;
  assign M00_AXI_awready=1'b1;
  assign M00_AXI_wready=1'b1;

  // Drive on falling edges only. Each VALID and payload remains unchanged until
  // the preceding rising edge actually observed its VALID && READY handshake.
  always @(negedge clk) begin
    cycles=cycles+1;
    if(!rstn) begin
      master_ar_ready_latched=0;
      S00_AXI_arvalid=0; S01_AXI_arvalid=0;
      M00_AXI_rvalid=0; M00_AXI_rid=0; M00_AXI_rdata=0;
      M00_AXI_rresp=0; M00_AXI_rlast=0;
      M00_AXI_bvalid=0; M00_AXI_bid=0; M00_AXI_bresp=0;
    end else begin
      master_ar_ready_latched=cycles%5!=0 &&
        master_accepted-master_completed<MAX_M_OUTSTANDING;
      if(!S00_AXI_arvalid || source_ar_fire[0]) begin
        if(submitted[0]<PER_SOURCE && submitted[0]-completed[0]<MAX_S_OUTSTANDING) begin
          S00_AXI_araddr=burst_address(0,submitted[0]);
          S00_AXI_arid=burst_id(submitted[0]);
          S00_AXI_arlen=burst_beats(submitted[0])-1;
          S00_AXI_arsize=3; S00_AXI_arburst=1; S00_AXI_arvalid=1;
        end else S00_AXI_arvalid=0;
      end
      if(!S01_AXI_arvalid || source_ar_fire[1]) begin
        if(submitted[1]<PER_SOURCE && submitted[1]-completed[1]<MAX_S_OUTSTANDING) begin
          S01_AXI_araddr=burst_address(1,submitted[1]);
          S01_AXI_arid=burst_id(submitted[1]);
          S01_AXI_arlen=burst_beats(submitted[1])-1;
          S01_AXI_arsize=3; S01_AXI_arburst=1; S01_AXI_arvalid=1;
        end else S01_AXI_arvalid=0;
      end
      if(!M00_AXI_rvalid || master_r_fire) begin
        // Finish a selected burst before choosing another. Across bursts choose
        // newest eligible accepted request, deliberately reordering distinct IDs.
        if(current_response>=0 && !pending[current_response]) current_response=-1;
        if(current_response<0) begin
          chosen=-1; oldest=-1;
          for(i=0;i<TOTAL;i=i+1) if(pending[i]) begin
            if(oldest<0 || master_order[i]<master_order[oldest]) oldest=i;
            if(response_eligible(i))
              if(chosen<0 || master_order[i]>master_order[chosen]) chosen=i;
          end
          if(chosen>=0) begin
            if(oldest!=chosen) out_of_order=out_of_order+1;
            current_response=chosen;
          end
        end
        if(current_response>=0 && cycles%7!=0) begin
          s=current_response/PER_SOURCE; seq=current_response%PER_SOURCE;
          beat=master_returned[current_response];
          M00_AXI_rvalid=1; M00_AXI_rid=full_id(current_response);
          M00_AXI_rdata=burst_data(s,seq,beat);
          M00_AXI_rresp=burst_response(seq); M00_AXI_rlast=(beat==burst_beats(seq)-1);
        end else M00_AXI_rvalid=0;
      end
    end
  end

  always @(posedge clk) begin
    if(cycles>WATCHDOG_CYCLES) fail("Fixed cycle watchdog expired");
    source_ar_fire[0]=0; source_ar_fire[1]=0; master_r_fire=0;
    if(rstn) begin
      // Stable payload under backpressure checks use the prior sampled cycle.
      ar_payload={S00_AXI_araddr,S00_AXI_arid,S00_AXI_arlen,S00_AXI_arsize,
        S00_AXI_arburst,S00_AXI_arlock,S00_AXI_arcache,S00_AXI_arqos,S00_AXI_arprot};
      if(source_ar_held[0] && (!S00_AXI_arvalid || ar_payload!==previous_source_ar[0])) fail("S00 AR changed while stalled");
      previous_source_ar[0]=ar_payload; source_ar_held[0]=S00_AXI_arvalid && !S00_AXI_arready;
      ar_payload={S01_AXI_araddr,S01_AXI_arid,S01_AXI_arlen,S01_AXI_arsize,
        S01_AXI_arburst,S01_AXI_arlock,S01_AXI_arcache,S01_AXI_arqos,S01_AXI_arprot};
      if(source_ar_held[1] && (!S01_AXI_arvalid || ar_payload!==previous_source_ar[1])) fail("S01 AR changed while stalled");
      previous_source_ar[1]=ar_payload; source_ar_held[1]=S01_AXI_arvalid && !S01_AXI_arready;
      ar_payload={M00_AXI_araddr,M00_AXI_arid,M00_AXI_arlen,M00_AXI_arsize,
        M00_AXI_arburst,M00_AXI_arlock,M00_AXI_arcache,M00_AXI_arqos,M00_AXI_arprot};
      if(master_ar_held && (!M00_AXI_arvalid || ar_payload!==previous_master_ar)) fail("M00 AR changed while stalled");
      previous_master_ar=ar_payload; master_ar_held=M00_AXI_arvalid && !M00_AXI_arready;
      r_payload={M00_AXI_rdata,M00_AXI_rid,M00_AXI_rresp,M00_AXI_rlast};
      if(master_r_held && (!M00_AXI_rvalid || r_payload!==previous_master_r)) fail("Slave model R changed while stalled");
      previous_master_r=r_payload; master_r_held=M00_AXI_rvalid && !M00_AXI_rready;
      r_payload={S00_AXI_rdata,S00_AXI_rid,S00_AXI_rresp,S00_AXI_rlast};
      if(source_r_held[0] && (!S00_AXI_rvalid || r_payload!==previous_source_r[0])) fail("S00 R changed while stalled");
      previous_source_r[0]=r_payload; source_r_held[0]=S00_AXI_rvalid && !S00_AXI_rready;
      r_payload={S01_AXI_rdata,S01_AXI_rid,S01_AXI_rresp,S01_AXI_rlast};
      if(source_r_held[1] && (!S01_AXI_rvalid || r_payload!==previous_source_r[1])) fail("S01 R changed while stalled");
      previous_source_r[1]=r_payload; source_r_held[1]=S01_AXI_rvalid && !S01_AXI_rready;
      if(master_ar_held) master_ar_stalls=master_ar_stalls+1;
      if(master_r_held) master_r_stalls=master_r_stalls+1;
      if(source_r_held[0]) source_r_stalls[0]=source_r_stalls[0]+1;
      if(source_r_held[1]) source_r_stalls[1]=source_r_stalls[1]+1;

      if(S00_AXI_arvalid && S00_AXI_arready) begin
        seq=submitted[0];
        if(seq>=PER_SOURCE || source_accepted[0][seq]) fail("Duplicate/extra S00 AR");
        source_accepted[0][seq]=1; source_ar_cycle[0][seq]=cycles;
        submitted[0]=seq+1; source_ar_fire[0]=1; covered_ids[0][burst_id(seq)]=1;
        covered_lengths[seq%4]=1;
        $fdisplay(trace_file,"S_AR,%0d,0,%0d,%0d,%08h,0,%0d,0,0,0",cycles,seq,burst_id(seq),burst_address(0,seq),burst_beats(seq));
      end
      if(S01_AXI_arvalid && S01_AXI_arready) begin
        seq=submitted[1];
        if(seq>=PER_SOURCE || source_accepted[1][seq]) fail("Duplicate/extra S01 AR");
        source_accepted[1][seq]=1; source_ar_cycle[1][seq]=cycles;
        submitted[1]=seq+1; source_ar_fire[1]=1; covered_ids[1][burst_id(seq)]=1;
        covered_lengths[seq%4]=1;
        $fdisplay(trace_file,"S_AR,%0d,1,%0d,%0d,%08h,0,%0d,0,0,0",cycles,seq,burst_id(seq),burst_address(1,seq),burst_beats(seq));
      end
      if(M00_AXI_arvalid && M00_AXI_arready) begin
        s=decoded_source(M00_AXI_araddr); seq=decoded_sequence(M00_AXI_araddr,s);
        if(seq<0 || seq>=PER_SOURCE) fail("Downstream address outside bounded stimulus");
        else begin
          index=s*PER_SOURCE+seq;
          if(!source_accepted[s][seq] || master_seen[index] ||
             M00_AXI_araddr!==burst_address(s,seq) || M00_AXI_arid!==full_id(index) ||
             M00_AXI_arlen!==(burst_beats(seq)-1) || M00_AXI_arsize!==3 || M00_AXI_arburst!==1 ||
             M00_AXI_arlock!==0 || M00_AXI_arcache!==0 || M00_AXI_arprot!==0 || M00_AXI_arqos!==0)
            fail($sformatf("Downstream AR route/metadata source=%0d seq=%0d",s,seq));
          if(M00_AXI_araddr[11:0]+8*burst_beats(seq)>4096 || M00_AXI_araddr[2:0]!=0)
            fail("Stimulus burst violates alignment or 4KiB boundary");
          master_seen[index]=1; pending[index]=1; master_order[index]=master_accepted;
          master_accepted=master_accepted+1;
          $fdisplay(trace_file,"M_AR,%0d,%0d,%0d,%0d,%08h,0,%0d,0,0,0",cycles,s,seq,M00_AXI_arid,M00_AXI_araddr,burst_beats(seq));
        end
      end
      if(M00_AXI_rvalid && M00_AXI_rready) begin
        if(current_response<0 || !pending[current_response]) fail("Model R lacks accepted pending request");
        else begin
          index=current_response; s=index/PER_SOURCE; seq=index%PER_SOURCE;
          beat=master_returned[index];
          if(M00_AXI_rid!==full_id(index) || M00_AXI_rdata!==burst_data(s,seq,beat) ||
             M00_AXI_rresp!==burst_response(seq) || M00_AXI_rlast!==(beat==burst_beats(seq)-1)) fail("Slave model corrupted its own held response");
          master_returned[index]=beat+1; master_beats=master_beats+1; master_r_fire=1;
          $fdisplay(trace_file,"M_R,%0d,%0d,%0d,%0d,%08h,%0d,%0d,%0d,%0d,%016h",
            cycles,s,seq,M00_AXI_rid,burst_address(s,seq),beat,burst_beats(seq),M00_AXI_rlast,M00_AXI_rresp,M00_AXI_rdata);
          if(M00_AXI_rlast) begin pending[index]=0; master_completed=master_completed+1; end
        end
      end
      if(S00_AXI_rvalid && S00_AXI_rready) check_source_response(0,S00_AXI_rid,S00_AXI_rdata,S00_AXI_rresp,S00_AXI_rlast);
      if(S01_AXI_rvalid && S01_AXI_rready) check_source_response(1,S01_AXI_rid,S01_AXI_rdata,S01_AXI_rresp,S01_AXI_rlast);
      for(s=0;s<2;s=s+1) begin
        if(submitted[s]-completed[s]>source_peak[s]) source_peak[s]=submitted[s]-completed[s];
        if(submitted[s]-completed[s]>MAX_S_OUTSTANDING) fail("Source acceptance ledger exceeds stimulus limit");
      end
      if(master_accepted-master_completed>master_peak) master_peak=master_accepted-master_completed;
      if(master_accepted-master_completed>MAX_M_OUTSTANDING) fail("Downstream model queue exceeds configured limit");
      if(S00_AXI_bvalid || S01_AXI_bvalid || M00_AXI_awvalid || M00_AXI_wvalid) fail("Unexpected write traffic in read-only test");
      if(completed[0]+completed[1]==TOTAL) begin
        if(submitted[0]!=PER_SOURCE || submitted[1]!=PER_SOURCE || master_accepted!=TOTAL || master_completed!=TOTAL ||
           source_beats[0]+source_beats[1]!=expected_beats || master_beats!=expected_beats)
          fail("Final conservation mismatch");
        if(covered_ids[0]!==32'hffffffff || covered_ids[1]!==32'hffffffff ||
           covered_lengths!==4'b1111 || covered_responses!==4'b1101 || master_peak<2 || out_of_order==0 ||
           master_ar_stalls==0 || source_r_stalls[0]==0 || source_r_stalls[1]==0)
          fail("Required finite coverage not reached");
        $display("GENERATED_AXI3_STREAM_PASS cycles=%0d submitted=%0d accepted=%0d downstream_beats=%0d upstream_beats=%0d completed=%0d peak_outstanding=%0d source_peaks=%0d/%0d IDs=%08h/%08h lengths=%b RESP=%b out_of_order=%0d",
          cycles,submitted[0]+submitted[1],master_accepted,master_beats,source_beats[0]+source_beats[1],
          completed[0]+completed[1],master_peak,source_peak[0],source_peak[1],covered_ids[0],covered_ids[1],covered_lengths,covered_responses,out_of_order);
        $fdisplay(trace_file,"SUMMARY,cycles=%0d,submitted=%0d,accepted=%0d,downstream_beats=%0d,upstream_beats=%0d,completed=%0d,peak_outstanding=%0d,source_peaks=%0d/%0d,IDs=%08h/%08h,lengths=%b,RESP=%b,out_of_order=%0d",
          cycles,submitted[0]+submitted[1],master_accepted,master_beats,source_beats[0]+source_beats[1],
          completed[0]+completed[1],master_peak,source_peak[0],source_peak[1],covered_ids[0],covered_ids[1],covered_lengths,covered_responses,out_of_order);
        $display("GENERATED_AXI3_STREAM_STALLS M_AR=%0d M_R=%0d S_R=%0d/%0d",
          master_ar_stalls,master_r_stalls,source_r_stalls[0],source_r_stalls[1]);
        $fdisplay(trace_file,"STALLS,M_AR=%0d,M_R=%0d,S_R=%0d/%0d",
          master_ar_stalls,master_r_stalls,source_r_stalls[0],source_r_stalls[1]);
        $fflush(trace_file); $fclose(trace_file); $finish;
      end
    end
  end

  initial begin
    // GENERATED_INPUT_INITIALIZATION
    if($bits(S00_AXI_arid)!=5 || $bits(S01_AXI_arid)!=5 || $bits(M00_AXI_arid)!=6 ||
       $bits(S00_AXI_arlen)!=4 || $bits(S01_AXI_arlen)!=4 || $bits(M00_AXI_arlen)!=4 ||
       $bits(S00_AXI_rdata)!=64 || $bits(S01_AXI_rdata)!=64 || $bits(M00_AXI_rdata)!=64)
      $fatal(1,"Generated DUT port widths differ from reviewed AXI3 contract");
    trace_file=$fopen("generated_axi3_stream.csv","w");
    if(!trace_file) $fatal(1,"Cannot create fresh handshake CSV");
    $fdisplay(trace_file,"event,cycle,source,sequence,id,address_hex,beat,burst_beats,last,resp,data_hex");
    for(s=0;s<2;s=s+1) begin
      submitted[s]=0; completed[s]=0; source_beats[s]=0; source_peak[s]=0;
      source_r_stalls[s]=0;
      covered_ids[s]=0; source_ar_fire[s]=0; source_ar_held[s]=0; source_r_held[s]=0;
      previous_source_ar[s]=0; previous_source_r[s]=0;
      for(j=0;j<PER_SOURCE;j=j+1) begin
        source_accepted[s][j]=0; source_done[s][j]=0;
        source_returned[s][j]=0; source_ar_cycle[s][j]=0;
      end
    end
    for(i=0;i<TOTAL;i=i+1) begin
      master_seen[i]=0; pending[i]=0; master_returned[i]=0; master_order[i]=-1;
      expected_beats=expected_beats+burst_beats(i%PER_SOURCE);
    end
    previous_master_ar=0; previous_master_r=0;
    // Release away from both clock edges; all generated clock/reset pins share
    // this same clock. This is functional simulation, not physical timing.
    repeat(16) @(negedge clk);
    #1 rstn=1;
  end
endmodule

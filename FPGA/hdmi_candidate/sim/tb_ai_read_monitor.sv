`timescale 1ns/1ps
module tb_ai_read_monitor;
    reg source_clk=0,csr_clk=0,source_running=1,resetn=0;
    always #2.5 if(source_running)source_clk=~source_clk;
    always #5 csr_clk=~csr_clk;
    reg [767:0] channels=0;
    reg [4:0] source_flags=5'b11001;
    mna_gp_ww_itf csr();
    ai_read_monitor dut(.source_clk(source_clk),.csr_clk(csr_clk),.resetn(resetn),
        .channels(channels),.source_flags(source_flags),.witness_gp_reset(1'b0),.csr(csr.slave));

    // Independent expected state: only public CSR write handshakes and sampled
    // source pins are observed. No DUT private state is read or forced.
    reg model_arm_toggle=0,model_freeze_toggle=0;
    reg [1:0] model_arm_sync=0,model_freeze_sync=0;
    reg model_arm_seen=0,model_freeze_seen=0,model_active=0;
    integer model_release=0;
    reg [31:0] expected_live[0:103],expected_snapshot[0:103];
    integer mi,mc,mb;
    reg [127:0] sample;
    always @(posedge source_clk or negedge resetn) begin
        if(!resetn) begin
            model_release<=0;model_arm_sync<=0;model_freeze_sync<=0;
            model_arm_seen=0;model_freeze_seen=0;model_active=0;
            for(mi=0;mi<104;mi=mi+1) begin expected_live[mi]=0;expected_snapshot[mi]=0;end
            expected_live[0]=32'h41495201;
        end else begin
            if(model_release<3)model_release<=model_release+1;
            if(model_release>=3) begin
                model_arm_sync<={model_arm_sync[0],model_arm_toggle};
                model_freeze_sync<={model_freeze_sync[0],model_freeze_toggle};
                if(model_arm_sync[1]!=model_arm_seen) begin
                    for(mi=0;mi<104;mi=mi+1)begin expected_live[mi]=0;expected_snapshot[mi]=0;end
                    expected_live[0]=32'h41495201;model_active=1;
                    model_arm_seen=model_arm_sync[1];
                end else if(model_freeze_sync[1]!=model_freeze_seen) begin
                    for(mi=0;mi<104;mi=mi+1)expected_snapshot[mi]=expected_live[mi];
                    model_active=0;model_freeze_seen=model_freeze_sync[1];
                end else if(model_active) begin
                    // The cycle label is the pre-increment epoch cycle. Update
                    // it last so first-error/last-event timestamps use that cut.
                    expected_live[2]={27'd0,source_flags};
                    if(source_flags[2] || !source_flags[3])expected_live[3]=expected_live[3]+1;
                    for(mc=0;mc<6;mc=mc+1) begin
                        mb=8+16*mc;sample=channels[128*mc+:128];
                        if(sample[60] && sample[61]) begin
                            expected_live[mb]=expected_live[mb]+1;
                            expected_live[mb+8]=sample[31:0];
                            expected_live[mb+9]={4'd0,sample[59:32]};
                            expected_live[mb+15]=expected_live[mb+15]+sample[41:38]+1;
                        end
                        if(sample[62] && sample[63]) begin
                            expected_live[mb+1]=expected_live[mb+1]+1;
                            if(sample[72])expected_live[mb+2]=expected_live[mb+2]+1;
                            expected_live[mb+10]={23'd0,sample[72:64]};
                            if(sample[71:70]!=0) begin
                                expected_live[mb+3]=expected_live[mb+3]+1;
                                if(!expected_live[mb+12][31]) begin
                                    expected_live[mb+12]=32'h80000000|sample[72:64];
                                    expected_live[mb+13]=expected_live[1];
                                end
                            end
                        end
                        if(sample[60] && !sample[61])expected_live[mb+4]=expected_live[mb+4]+1;
                        if(sample[62] && !sample[63])expected_live[mb+5]=expected_live[mb+5]+1;
                        if(sample[60])expected_live[mb+6]=expected_live[mb+6]+1;
                        if(sample[62])expected_live[mb+7]=expected_live[mb+7]+1;
                        expected_live[mb+11]={4'd0,sample[72],sample[71:70],sample[69:64],
                            sample[46:45],sample[44:42],sample[41:38],sample[37:32],sample[63:60]};
                        if((sample[60] && sample[61]) || (sample[62] && sample[63]))
                            expected_live[mb+14]=expected_live[1];
                    end
                    expected_live[1]=expected_live[1]+1;
                end
            end
        end
    end

    task write_command(input [8:0] address,input [31:0] value,input integer accepted_kind);
        begin
            @(negedge csr_clk);csr.awwaddr=32'h400b0200+address;csr.awwdata=value;csr.awwvalid=1;
            @(posedge csr_clk);
            if(!csr.awwready)$fatal(1,"CSR write handshake absent");
            // Only commands independently expected to be accepted toggle model.
            if(accepted_kind==1)model_arm_toggle=~model_arm_toggle;
            if(accepted_kind==2)model_freeze_toggle=~model_freeze_toggle;
            @(negedge csr_clk);csr.awwvalid=0;
        end
    endtask
    task read(input [8:0] address,output [31:0] value);
        integer guard;
        begin
            @(negedge csr_clk);csr.araddr=32'h400b0200+address;csr.arvalid=1;csr.rready=0;
            guard=0;
            do begin @(posedge csr_clk);guard=guard+1;if(guard>12)$fatal(1,"CSR read request deadline");end while(!csr.arready);
            @(negedge csr_clk);csr.arvalid=0;
            if(!csr.rvalid)$fatal(1,"CSR read response absent");value=csr.rdata;
            repeat(2)begin @(posedge csr_clk);if(!csr.rvalid || csr.rdata!==value)$fatal(1,"CSR read changed under backpressure");end
            @(negedge csr_clk);csr.rready=1;
            @(posedge csr_clk);@(negedge csr_clk);csr.rready=0;
        end
    endtask
    task expect_register(input [8:0] address,input [31:0] wanted);
        reg [31:0] actual;
        begin
            read(address,actual);
            if(actual!==wanted)$fatal(1,"CSR mismatch offset=%03h actual=%08h expected=%08h",address,actual,wanted);
        end
    endtask
    task wait_completion(input [31:0] wanted,input [31:0] wanted_status);
        reg [31:0] actual;integer guard;
        begin
            actual=32'hffffffff;guard=0;
            while(actual!==wanted && guard<30)begin read(9'h00c,actual);guard=guard+1;end
            if(actual!==wanted)$fatal(1,"Expected command ACK absent seq=%0d",wanted);
            expect_register(9'h008,wanted);expect_register(9'h000,wanted_status);
        end
    endtask
    task reset_all;
        begin
            #1 resetn=0;model_arm_toggle=0;model_freeze_toggle=0;
            channels=0;source_flags=5'b11001;
            // Resume strictly away from the oscillator's 2.5ns ticks so source
            // edges cannot accidentally coincide with CSR command sampling.
            #29.7 source_running=1;
            #1 resetn=1;
            repeat(12)@(negedge csr_clk);
            expect_register(9'h000,0);expect_register(9'h008,0);expect_register(9'h00c,0);
        end
    endtask
    task compare_snapshot;
        reg [31:0] actual;integer n;
        begin
            for(n=0;n<104;n=n+1) begin
                read(9'h040+4*n,actual);
                if(actual!==expected_snapshot[n])
                    $fatal(1,"Snapshot mismatch word=%0d actual=%08h expected=%08h",n,actual,expected_snapshot[n]);
            end
        end
    endtask
    function automatic [127:0] stimulus(input integer channel,input integer step);
        reg [127:0] v;
        begin
            v=0;v[31:0]=32'h10000000+step*4096+channel*64;
            v[37:32]=32+channel;v[41:38]=(step==0)?0:(step==1)?1:(step==4)?15:7;
            v[44:42]=3;v[46:45]=1;v[48:47]=step%3;
            v[52:49]=channel;v[55:53]=step;v[59:56]=channel;
            v[60]=1;v[61]=(step!=2 && step!=5);
            v[62]=(step!=5);v[63]=(step!=2);
            v[69:64]=40+channel+step;v[71:70]=(step==1)?2:(step==2 || step==3)?3:0;
            v[72]=(step==0 || step==3);stimulus=v;
        end
    endfunction
    reg [31:0] value;integer k,n,b;
    initial begin
        csr.awwaddr=0;csr.awwdata=0;csr.awwvalid=0;
        csr.araddr=0;csr.arvalid=0;csr.rready=0;
        #31 resetn=1;repeat(12)@(negedge csr_clk);
        expect_register(9'h004,32'h41495201);expect_register(9'h010,104);
        // FREEZE before ARM is rejected, with no request/ACK fabricated.
        write_command(0,2,0);expect_register(0,2);expect_register(8,0);expect_register(12,0);
        reset_all();
        // A second ARM after successful ARM is rejected until a FREEZE/reset.
        write_command(0,1,1);wait_completion(1,0);
        write_command(0,1,0);expect_register(0,2);expect_register(8,1);expect_register(12,1);
        reset_all();

        // Activity before ARM must never leak into the new diagnostic epoch.
        @(negedge source_clk);channels={768{1'b1}};
        repeat(5)@(negedge source_clk);
        channels=0;write_command(0,1,1);wait_completion(1,0);
        expect_register(9'h040,0);expect_register(9'h1dc,0);
        for(k=0;k<6;k=k+1) begin
            @(negedge source_clk);
            for(n=0;n<6;n=n+1)channels[128*n+:128]=stimulus(n,k);
            source_flags=(k==1)?5'b11101:(k==2)?5'b10001:5'b11001;
        end
        @(negedge source_clk);channels=0;source_flags=5'b11001;
        write_command(0,2,2);wait_completion(2,0);compare_snapshot();
        // Fixed independent arithmetic checks complement the cycle scoreboard.
        expect_register(9'h040,32'h41495201);expect_register(9'h04c,2);
        for(n=0;n<6;n=n+1) begin
            b=9'h040+4*(8+16*n);
            expect_register(b+0,4);expect_register(b+4,4);expect_register(b+8,2);
            expect_register(b+12,2);expect_register(b+16,2);expect_register(b+20,1);
            expect_register(b+24,6);expect_register(b+28,5);expect_register(b+60,27);
            expect_register(b+48,32'h80000000 | (2<<6) | (41+n));
        end
        // Mutating all pins after FREEZE cannot alter the published 104 words.
        @(negedge source_clk);channels={768{1'b1}};source_flags=0;
        repeat(7)@(negedge source_clk);compare_snapshot();
        @(negedge source_clk);channels=0;source_flags=5'b11001;
        write_command(0,1,1);wait_completion(3,0);
        expect_register(9'h040,0);expect_register(9'h1dc,0);
        write_command(0,2,2);wait_completion(4,0);compare_snapshot();
        for(n=0;n<6;n=n+1)expect_register(9'h040+4*(8+16*n),0);
        // Keep events asserted through the FREEZE request and ACK. The expected
        // pipeline model checks that the recognition edge itself is excluded,
        // rather than merely testing a freeze while event inputs are idle.
        write_command(0,1,1);wait_completion(5,0);
        @(negedge source_clk);
        for(n=0;n<6;n=n+1)channels[128*n+:128]=stimulus(n,0);
        source_flags=5'b01010;
        write_command(0,2,2);wait_completion(6,0);
        @(negedge source_clk);channels=0;
        compare_snapshot();expect_register(9'h048,10);read(9'h060,value);
        if(value==0)$fatal(1,"FREEZE-cut test produced no active event");

        reset_all();write_command(0,1,1);wait_completion(1,0);
        // A stopped source cannot ACK FREEZE. A second command is rejected and
        // the finite caller deadline is explicitly an expected negative result.
        @(negedge source_clk);source_running=0;
        write_command(0,2,2);write_command(0,1,0);
        repeat(8)begin expect_register(12,1);expect_register(8,2);expect_register(0,3);end
        $display("AI_READ_MONITOR_EXPECTED_TIMEOUT source_stopped busy=1 completion_unchanged rejected_command=1");
        #1 source_running=1;wait_completion(2,2);compare_snapshot();
        // Reset clears sticky error and cancels a pending request even while
        // the source clock is stopped. No stale ACK may survive the reset.
        reset_all();write_command(0,1,1);wait_completion(1,0);
        @(negedge source_clk);source_running=0;write_command(0,2,2);
        expect_register(0,1);expect_register(12,1);
        reset_all();expect_register(9'h040,0);expect_register(9'h1dc,0);
        write_command(0,1,1);wait_completion(1,0);
        write_command(0,2,2);wait_completion(2,0);compare_snapshot();
        $display("AI_READ_MONITOR_PASS 104_words six_channels parallel_handshakes length_sum full_6bit_ID first_error freeze_cut stable_reads reset stopped_source busy_rejection");
        $finish;
    end
    initial begin #1000000;$fatal(1,"AI read monitor finite simulation watchdog");end
endmodule

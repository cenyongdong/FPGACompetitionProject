`timescale 1ns/1ps
module tb_ai_boot_witness;
    reg source_clk=0,csr_clk=0,source_running=1,resetn=0,gp_reset=0;
    always #2.5 if(source_running)source_clk=~source_clk;
    always #5 csr_clk=~csr_clk;
    reg [767:0] channels=0;
    reg [4:0] source_flags=5'h19;
    mna_gp_ww_itf csr();
    ai_read_monitor #(.BOOT_WITNESS(1)) dut(
        .source_clk(source_clk),.csr_clk(csr_clk),.resetn(resetn),
        .channels(channels),.source_flags(source_flags),
        .witness_gp_reset(gp_reset),.csr(csr.slave));
    reg [31:0] before_key[0:18],after_key[0:18],later[0:18];
    reg [31:0] value,old_cycles;
    integer i,n;
    task read_csr(input [8:0] address,output [31:0] data);
        begin
            @(negedge csr_clk);csr.araddr={23'd0,address};csr.arvalid=1;csr.rready=0;
            @(posedge csr_clk);while(!csr.arready)@(posedge csr_clk);
            @(negedge csr_clk);csr.arvalid=0;
            while(!csr.rvalid)@(negedge csr_clk);
            data=csr.rdata;csr.rready=1;
            @(negedge csr_clk);csr.rready=0;
        end
    endtask
    task write_command(input [31:0] command);
        begin
            @(negedge csr_clk);csr.awwaddr=0;csr.awwdata=command;csr.awwvalid=1;
            @(posedge csr_clk);while(!csr.awwready)@(posedge csr_clk);
            @(negedge csr_clk);csr.awwvalid=0;
        end
    endtask
    task wait_command(input [31:0] expected_sequence);
        begin
            n=0;read_csr(0,value);
            while(value!=0 && n<100)begin read_csr(0,value);n=n+1;end
            if(value!=0)$fatal(1,"command failed/busy seq=%0d status=%h",expected_sequence,value);
            read_csr(8,value);if(value!=expected_sequence)$fatal(1,"request differs");
            read_csr(12,value);if(value!=expected_sequence)$fatal(1,"response differs");
        end
    endtask
    task epoch(input [31:0] start_sequence);
        begin
            write_command(1);wait_command(start_sequence+1);
            repeat(20)@(negedge source_clk);
            write_command(2);wait_command(start_sequence+2);
        end
    endtask
    function [8:0] witness_address(input integer index);
        if(index<11)witness_address=9'h014+4*index;
        else witness_address=9'h1e0+4*(index-11);
    endfunction
    task dump_words(input integer phase_id);
        integer k;
        begin
            $write("BOOT_WITNESS_RAW {\"phase\":%0d,\"words\":[",phase_id);
            for(k=0;k<19;k=k+1)begin
                if(k)$write(",");
                if(phase_id==0)$write("%0d",before_key[k]);
                else if(phase_id==1)$write("%0d",after_key[k]);
                else $write("%0d",later[k]);
            end
            $display("]}");
        end
    endtask
    initial begin
        csr.awwvalid=0;csr.awwaddr=0;csr.awwdata=0;csr.arvalid=0;csr.araddr=0;csr.rready=0;
        #31;resetn=1;
        repeat(12)@(negedge source_clk);
        // Fault precedes all CSR commands. No handshake/request is manufactured.
        channels[640+62]=1;channels[640+61]=1;channels[640+64+:6]=6'h20;
        channels[512+62]=1;channels[512+61]=1;
        repeat(40)@(negedge source_clk);
        epoch(0);
        for(i=0;i<19;i=i+1)read_csr(witness_address(i),before_key[i]);
        if(before_key[0]!=32'h42545201 || !before_key[1][3] || !before_key[1][1])
            $fatal(1,"early RVALID history missing");
        if(before_key[3]!=0 || before_key[4]!=0 || before_key[5]!=0 || before_key[6]!=0)
            $fatal(1,"backpressure invented a request/response handshake");
        if(before_key[9][24:19]!=6'h20 || before_key[10]+40>=before_key[2])
            $fatal(1,"first response timing/ID not retained from before ARM");
        if(before_key[13]!=0 || before_key[14]!=0)$fatal(1,"invented initial reset edge");
        read_csr(9'h044,old_cycles);
        read_csr(9'h1bc,value);if(value!=old_cycles)$fatal(1,"legacy PS RVALID window changed");
        $display("BOOT_WITNESS_EARLY_RESPONSE_PASS");

        // GP witnesses reset while the MIG-derived source clock is stopped.
        @(negedge source_clk);source_running=0;
        @(negedge csr_clk);gp_reset=1;resetn=0;source_flags=5'h15;
        repeat(12)@(negedge csr_clk);
        gp_reset=0;source_flags=5'h19;resetn=1;
        repeat(6)@(negedge csr_clk);source_running=1;
        repeat(12)@(negedge source_clk);
        read_csr(8,value);if(value!=0)$fatal(1,"local reset did not clear CSR request");
        read_csr(12,value);if(value!=0)$fatal(1,"local reset did not clear CSR response");
        epoch(0);
        for(i=0;i<19;i=i+1)read_csr(witness_address(i),after_key[i]);
        if(after_key[13]!=1 || after_key[14]!=1 || after_key[16]!=12 || after_key[17]!=12)
            $fatal(1,"actual GP/HP reset pulse lost: edges=%0d/%0d cycles=%0d/%0d",after_key[13],after_key[14],after_key[16],after_key[17]);
        if(after_key[9]!=before_key[9] || after_key[10]!=before_key[10] || !after_key[1][3])
            $fatal(1,"local reset erased first response history");
        $display("BOOT_WITNESS_RESET_WITH_STOPPED_HP_CLOCK_PASS");

        // Traffic while the old observer is inactive must still be counted.
        @(negedge source_clk);
        channels[640+60]=1;channels[640+:32]=32'h12340000;
        channels[640+32+:6]=6'h20;channels[640+38+:4]=3;
        channels[512+60]=1;channels[512+:32]=32'h12340000;channels[512+38+:4]=3;
        @(negedge source_clk);channels[640+60]=0;channels[512+60]=0;
        channels[640+63]=1;channels[512+63]=1;
        repeat(4)@(negedge source_clk);
        channels[640+63]=0;channels[512+63]=0;
        for(i=0;i<19;i=i+1)begin
            read_csr(witness_address(i),value);
            if(value!=after_key[i])$fatal(1,"published witness changed without FREEZE");
        end
        epoch(2);
        for(i=0;i<19;i=i+1)read_csr(witness_address(i),later[i]);
        if(later[3]!=1 || later[4]!=4 || later[5]!=1 || later[6]!=4)
            $fatal(1,"pre-ARM traffic counts differ");
        if(later[7]!=32'h12340000 || later[11]!=32'h12340000 || later[8][9:4]!=6'h20)
            $fatal(1,"first address/request ID differs");
        if(later[9]!=before_key[9] || later[10]!=before_key[10])$fatal(1,"first event overwritten");
        read_csr(9'h1a0,value);if(value!=0)$fatal(1,"legacy epoch included old PS request");
        $display("BOOT_WITNESS_HISTORY_AND_FREEZE_PASS");
        dump_words(0);dump_words(1);dump_words(2);
        $display("AI_BOOT_WITNESS_PASS");$finish;
    end
    initial begin #200000;$fatal(1,"boot witness watchdog");end
endmodule

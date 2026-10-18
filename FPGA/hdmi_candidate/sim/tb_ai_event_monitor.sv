`timescale 1ns/1ps
module tb_ai_event_monitor;
    reg source_clk=0,csr_clk=0,source_running=1,resetn=0;
    always #2.5 if(source_running)source_clk=~source_clk;
    always #5 csr_clk=~csr_clk;
    reg [15:0] events=0;
    reg [7:0] sample_update=0;
    reg [255:0] sample_data=0;
    mna_gp_ww_itf csr();
    ai_event_monitor dut(source_clk,csr_clk,resetn,events,sample_update,sample_data,csr.slave);
    task write(input [7:0] address,input [31:0] value);
        begin
            @(negedge csr_clk);csr.awwaddr=32'h400b0100+address;csr.awwdata=value;csr.awwvalid=1;
            @(posedge csr_clk);if(!csr.awwready)$fatal(1,"Write not accepted");
            @(negedge csr_clk);csr.awwvalid=0;
        end
    endtask
    task read(input [7:0] address,output [31:0] value);
        begin
            @(negedge csr_clk);csr.araddr=32'h400b0100+address;csr.arvalid=1;csr.rready=0;
            do @(posedge csr_clk);while(!csr.arready);
            @(negedge csr_clk);csr.arvalid=0;
            if(!csr.rvalid)$fatal(1,"Read response absent");value=csr.rdata;
            repeat(3)begin @(posedge csr_clk);if(!csr.rvalid || csr.rdata!==value)$fatal(1,"Read backpressure changed data");end
            @(negedge csr_clk);csr.rready=1;
            @(posedge csr_clk);@(negedge csr_clk);csr.rready=0;
        end
    endtask
    task snapshot(input [31:0] expected);
        reg [31:0] seq;integer n;
        begin
            write(0,1);seq=0;n=0;
            while(seq!=expected && n<20)begin read(8'h0c,seq);n=n+1;end
            if(seq!==expected)$fatal(1,"Snapshot response generation absent");
        end
    endtask
    reg [31:0] value;integer k;
    initial begin
        csr.awwaddr=0;csr.awwdata=0;csr.awwvalid=0;
        csr.araddr=0;csr.arvalid=0;csr.rready=0;
        #30;resetn=1;repeat(12)@(posedge csr_clk);
        read(4,value);if(value!==32'h41494401)$fatal(1,"Monitor ABI");
        @(negedge source_clk);events=16'h0003;sample_update=8'hff;
        for(k=0;k<8;k=k+1)sample_data[32*k+:32]=32'h12340000+k;
        repeat(9)@(posedge source_clk);
        @(negedge source_clk);events=0;sample_update=0;
        snapshot(1);
        read(8'h40,value);if(value!==9)$fatal(1,"Counter zero mismatch");
        read(8'h44,value);if(value!==9)$fatal(1,"Counter one mismatch");
        read(8'h48,value);if(value!==0)$fatal(1,"Inactive counter changed");
        for(k=0;k<8;k=k+1)begin read(8'h80+4*k,value);if(value!==32'h12340000+k)$fatal(1,"Metadata mismatch");end
        // Updating the source does not mutate the currently published snapshot.
        @(negedge source_clk);events=1;sample_update=1;sample_data[31:0]=32'habcd;
        repeat(5)@(posedge source_clk);@(negedge source_clk);events=0;sample_update=0;
        read(8'h40,value);if(value!==9)$fatal(1,"Snapshot mutated before new request");
        snapshot(2);read(8'h40,value);if(value!==14)$fatal(1,"Second snapshot counter");
        read(8'h80,value);if(value!==32'habcd)$fatal(1,"Second snapshot metadata");
        // A stopped source cannot manufacture completion; a busy request is rejected.
        @(negedge source_clk);source_running=0;
        write(0,1);write(0,1);repeat(12)@(posedge csr_clk);
        read(8'h0c,value);if(value!==2)$fatal(1,"Stopped clock produced new response");
        read(0,value);if(value!==3)$fatal(1,"Busy/rejected-command status");
        source_running=1;repeat(12)@(posedge csr_clk);
        read(8'h0c,value);if(value!==3)$fatal(1,"Clock resume snapshot missing");
        // Reset both domains during an outstanding snapshot, then request afresh.
        @(negedge source_clk);source_running=0;write(0,1);
        #3;resetn=0;#30;source_running=1;resetn=1;
        repeat(15)@(posedge csr_clk);snapshot(1);
        read(8'h40,value);if(value!==0)$fatal(1,"Counter not reset");
        read(0,value);if(value!==0)$fatal(1,"Status not reset");
        $display("AI_EVENT_MONITOR_PASS atomic snapshots, backpressure, stopped clock, busy rejection, reset");
        $finish;
    end
    initial begin #100000;$fatal(1,"Simulation deadline");end
endmodule

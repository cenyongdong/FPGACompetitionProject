`timescale 1ns/1ps
// Exercise the exact generated reset IP: constant-ready baseline versus DDR
// readiness. This is a mechanism test, not a board clock trace.
module tb_hp2_reset_clock_stop;
    reg hp_clk=0,clock_running=1,ext_resetn=1,track=0,domain_ready=0;
    wire [0:0] peripheral_aresetn,ready_gated_aresetn,cold_ready_aresetn;
    integer assertions=0,ready_gated_assertions=0;
    always #2.5 begin
        if(clock_running) hp_clk=~hp_clk;
        else hp_clk=0;
    end
    ps_ai_proc_sys_reset_0_0 dut(
        .slowest_sync_clk(hp_clk),.ext_reset_in(ext_resetn),
        .aux_reset_in(1'b1),.mb_debug_sys_rst(1'b0),.dcm_locked(1'b1),
        .peripheral_aresetn(peripheral_aresetn),.mb_reset(),
        .bus_struct_reset(),.peripheral_reset(),.interconnect_aresetn());
    ps_ai_proc_sys_reset_0_0 ready_gated(
        .slowest_sync_clk(hp_clk),.ext_reset_in(ext_resetn),
        .aux_reset_in(1'b1),.mb_debug_sys_rst(1'b0),.dcm_locked(domain_ready),
        .peripheral_aresetn(ready_gated_aresetn),.mb_reset(),
        .bus_struct_reset(),.peripheral_reset(),.interconnect_aresetn());
    // The candidate must also establish reset at configuration, before DDR
    // readiness, without relying on a later external key pulse.
    ps_ai_proc_sys_reset_0_0 cold_ready(
        .slowest_sync_clk(hp_clk),.ext_reset_in(1'b1),
        .aux_reset_in(1'b1),.mb_debug_sys_rst(1'b0),.dcm_locked(domain_ready),
        .peripheral_aresetn(cold_ready_aresetn),.mb_reset(),
        .bus_struct_reset(),.peripheral_reset(),.interconnect_aresetn());
    always @(negedge peripheral_aresetn[0]) if(track) assertions=assertions+1;
    always @(negedge ready_gated_aresetn[0]) if(track) ready_gated_assertions=ready_gated_assertions+1;
    task automatic released;
        #5000;
        if(peripheral_aresetn!==1'b1)
            $fatal(1,"Reset IP failed to release: out=%b clk=%b GSR=%b ext_n=%b lpf=%b seq=%b",
                peripheral_aresetn,hp_clk,glbl.GSR,ext_resetn,dut.U0.lpf_int,dut.U0.SEQ_n_4);
        if(ready_gated_aresetn!==1'b1) $fatal(1,"Ready-gated IP failed to release");
    endtask
    initial begin
        // Establish known IP state with a real input reset before comparing
        // subsequent pulses; do not rely on a power-on-only release sequence.
        ext_resetn=0;#200;ext_resetn=1;#200;
        if(cold_ready_aresetn!==1'b0) $fatal(1,"Cold ready gate did not establish reset");
        domain_ready=1;released();
        if(cold_ready_aresetn!==1'b1) $fatal(1,"Cold ready gate did not release reset");
        $display("HP2_RESET_COLD_READY_GATE_PASS");track=1;
        // Positive control: an input pulse is recognized with a running clock.
        ext_resetn=0;#200;ext_resetn=1;released();
        if(assertions!=1 || ready_gated_assertions!=1)
            $fatal(1,"Running clock reset not recognized: %0d/%0d",assertions,ready_gated_assertions);
        $display("HP2_RESET_RUNNING_CLOCK_PASS assertions=%0d",assertions);

        // A pulse entirely inside a stopped-clock interval is not sampled.
        clock_running=0;#25;domain_ready=0;ext_resetn=0;#200;ext_resetn=1;
        #25;clock_running=1;#200;
        if(ready_gated_aresetn!==1'b0) $fatal(1,"Ready gate did not hold reset during recovery");
        domain_ready=1;released();
        if(assertions!=1) $fatal(1,"Stopped-clock pulse unexpectedly recognized: %0d",assertions);
        if(ready_gated_assertions!=2) $fatal(1,"Ready gate missed recovery reset: %0d",ready_gated_assertions);
        $display("HP2_RESET_STOPPED_CLOCK_PULSE_MISSED assertions=%0d",assertions);
        $display("HP2_RESET_READY_GATE_RECOVERY_PASS assertions=%0d",ready_gated_assertions);

        // Positive control: holding the same input until clocks return restores
        // recognition, without changing IP configuration or reset polarity.
        clock_running=0;#25;ext_resetn=0;#200;clock_running=1;
        #200;ext_resetn=1;released();
        if(assertions!=2) $fatal(1,"Held-until-restart pulse not recognized: %0d",assertions);
        if(ready_gated_assertions!=3) $fatal(1,"Ready-gated positive control failed: %0d",ready_gated_assertions);
        $display("HP2_RESET_HELD_UNTIL_CLOCK_RETURN_PASS assertions=%0d",assertions);
        $display("HP2_VENDOR_RESET_CLOCK_STOP_PASS");$finish;
    end
    initial begin #50000;$fatal(1,"Vendor reset test timed out");end
endmodule

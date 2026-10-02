`timescale 1ns / 1ps

module tb_lite_led_chaser;
    reg clk = 1'b0;
    wire [3:0] led_every_cycle, led_seven, led_nineteen;
    integer cycle;
    reg [3:0] expected;

    always #5 clk = ~clk; // Actual board period: 10 ns.

    lite_led_chaser #(.TICKS_PER_STEP(1)) dut_one(clk, led_every_cycle);
    lite_led_chaser #(.TICKS_PER_STEP(7)) dut_seven(clk, led_seven);
    lite_led_chaser #(.TICKS_PER_STEP(19)) dut_nineteen(clk, led_nineteen);

    task check_led(input [3:0] observed, input integer ticks, input integer count);
        begin
            // Independent specification table, not the DUT bit permutation.
            case ((count / ticks) % 4)
                0: expected = 4'b0001; // LED1
                1: expected = 4'b0100; // LED3
                2: expected = 4'b0010; // LED2
                3: expected = 4'b1000; // LED4
                default: $fatal(1, "FAIL invalid expected phase");
            endcase
            if (observed !== expected)
                $fatal(1, "FAIL cycle=%0d ticks=%0d expected=%b observed=%b",
                       count, ticks, expected, observed);
        end
    endtask

    initial begin
        #1;
        check_led(led_every_cycle, 1, 0);
        check_led(led_seven, 7, 0);
        check_led(led_nineteen, 19, 0);
        $display("TRACE ticks=1 cycle=0 observed=%b", led_every_cycle);
        for (cycle = 1; cycle <= 200; cycle = cycle + 1) begin
            @(posedge clk);
            #1; // Sample after the nonblocking assignments.
            check_led(led_every_cycle, 1, cycle);
            check_led(led_seven, 7, cycle);
            check_led(led_nineteen, 19, cycle);
            if (cycle <= 8)
                $display("TRACE ticks=1 cycle=%0d observed=%b", cycle, led_every_cycle);
        end
        $display("PASS: initialization, exact step boundaries, one-hot LED1->3->2->4 order and wrap; 3 divisors x 200 cycles");
        $finish;
    end

    initial begin
        #3000;
        $fatal(1, "FAIL simulation timeout");
    end
endmodule

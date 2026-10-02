`timescale 1ns/1ps
module tb_lite_led_chaser;
    reg clk = 1'b0;
    always #5 clk = ~clk;
    wire [3:0] led1, led7, led19;
    lite_led_chaser #(.TICKS_PER_STEP(1)) dut1(.clk_100m(clk), .led(led1));
    lite_led_chaser #(.TICKS_PER_STEP(7)) dut7(.clk_100m(clk), .led(led7));
    lite_led_chaser #(.TICKS_PER_STEP(19)) dut19(.clk_100m(clk), .led(led19));

    reg [3:0] unit_state = 4'b0000;
    wire [3:0] unit_next;
    reg unit_pass = 1'b0;
    integer input_value;
    reg [3:0] expected_unit;
    led_state_concat unit_ip (
        .In0(unit_state[3]), .In1(unit_state[2]),
        .In2(unit_state[0]), .In3(unit_state[1]), .dout(unit_next)
    );
    // Independent exhaustive truth table; does not repeat the RTL expression.
    initial begin
        for (input_value = 0; input_value < 16; input_value = input_value + 1) begin
            case (input_value)
                0: expected_unit=4'h0; 1: expected_unit=4'h4;
                2: expected_unit=4'h8; 3: expected_unit=4'hc;
                4: expected_unit=4'h2; 5: expected_unit=4'h6;
                6: expected_unit=4'ha; 7: expected_unit=4'he;
                8: expected_unit=4'h1; 9: expected_unit=4'h5;
                10: expected_unit=4'h9; 11: expected_unit=4'hd;
                12: expected_unit=4'h3; 13: expected_unit=4'h7;
                14: expected_unit=4'hb; 15: expected_unit=4'hf;
            endcase
            unit_state = input_value;
            #1;
            if (unit_next !== expected_unit)
                $fatal(1, "FAIL IP input=%h observed=%h expected=%h",
                       unit_state, unit_next, expected_unit);
            $display("IP_TRACE input=%h next=%h", unit_state, unit_next);
        end
        unit_pass = 1'b1;
        $display("PASS: xlconcat all 16 input combinations");
    end

    task automatic check_led(input [3:0] observed,
                             input integer ticks, input integer count);
        reg [3:0] expected;
        begin
            case ((count / ticks) % 4)
                0: expected=4'b0001;
                1: expected=4'b0100;
                2: expected=4'b0010;
                3: expected=4'b1000;
            endcase
            if (observed !== expected)
                $fatal(1, "FAIL LED ticks=%0d cycle=%0d got=%b expected=%b",
                       ticks, count, observed, expected);
            if (!(observed == 4'b0001 || observed == 4'b0100 ||
                  observed == 4'b0010 || observed == 4'b1000))
                $fatal(1, "FAIL LED not one-hot");
        end
    endtask
    integer cycle;
    initial begin
        #1;
        check_led(led1,1,0); check_led(led7,7,0); check_led(led19,19,0);
        $display("LED_TRACE cycle=0 ticks1=%b ticks7=%b ticks19=%b",led1,led7,led19);
        for (cycle=1; cycle<=200; cycle=cycle+1) begin
            @(posedge clk); #1;
            check_led(led1,1,cycle); check_led(led7,7,cycle); check_led(led19,19,cycle);
            if (cycle <= 8)
                $display("LED_TRACE cycle=%0d ticks1=%b ticks7=%b ticks19=%b",
                         cycle,led1,led7,led19);
        end
        if (unit_pass !== 1'b1) $fatal(1, "FAIL IP unit test incomplete");
        $display("PASS: initialization and LED1-3-2-4 sequence, ticks=1/7/19, 200 cycles each");
        $finish;
    end
    initial begin #3000; $fatal(1, "FAIL simulation timeout"); end
endmodule

`timescale 1ns / 1ps

// Wujing Lite / JFMQL30TAI676H. PL LEDs are active high.
// The register initial values are configuration-time INIT values;
// check the Procise netlist and the board rather than assuming portability.
module lite_led_chaser #(
    parameter integer TICKS_PER_STEP = 25000000
) (
    input  wire       clk_100m,
    output wire [3:0] led
);
    reg [24:0] tick_count = 25'd0;
    reg [3:0] led_state = 4'b0001;

    always @(posedge clk_100m) begin
        if (tick_count == TICKS_PER_STEP - 1) begin
            tick_count <= 25'd0;
            led_state <= {led_state[2:0], led_state[3]};
        end else begin
            tick_count <= tick_count + 1'b1;
        end
    end

    assign led = led_state;
endmodule

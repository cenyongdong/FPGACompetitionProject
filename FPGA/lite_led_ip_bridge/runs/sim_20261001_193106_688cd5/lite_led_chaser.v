`timescale 1ns/1ps
// Physical implementation: Procise JFMQL30TAI676H.
// Vivado-generated xlconcat is used without editing its vendor HDL.
module lite_led_chaser #(parameter integer TICKS_PER_STEP = 25000000) (
    input wire clk_100m,
    output wire [3:0] led
);
    reg [24:0] tick_count = 25'd0;
    reg [3:0] led_state = 4'b0001;
    wire [3:0] next_state;
    led_state_concat state_permutation (
        .In0(led_state[3]), .In1(led_state[2]),
        .In2(led_state[0]), .In3(led_state[1]), .dout(next_state)
    );
    always @(posedge clk_100m) begin
        if (tick_count == TICKS_PER_STEP - 1) begin
            tick_count <= 25'd0;
            led_state <= next_state;
        end else begin
            tick_count <= tick_count + 1'b1;
        end
    end
    assign led = led_state;
endmodule

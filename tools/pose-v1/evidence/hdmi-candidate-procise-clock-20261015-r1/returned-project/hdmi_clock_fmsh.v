// Native Procise primitives, per installed primitive manual pp49-53 and
// FMA language templates. 100MHz board oscillator; no SDI-derived input.
// 100 / 5 * 37.125 = 742.5MHz VCO; pixel /5, serial /1.
// Primitive acceptance is verified separately for JFMQL30TAI676H; silicon
// jitter, electrical 1080p60 compatibility and TMDS placement remain unproven.
module hdmi_clock_fmsh(
    input wire ref_100m, input wire reset,
    output wire pixel_clk, output wire serial_clk, output wire locked
);
    wire feedback,feedback_global,pixel_raw,serial_raw;
    PLL_MM_SIMPLE #(
        .BANDWIDTH("OPTIMIZED"),.CLKIN0_PERIOD(10.0),
        .CLKFBOUT_MULT_F(37.125),.DIVCLK_DIVIDE(5),
        .CLKOUT0_DIVIDE_F(5.0),.CLKOUT1_DIVIDE(1),.STARTUP_WAIT("FALSE")
    ) clock_generator (
        .CLKIN0(ref_100m),.CLKFBIN(feedback_global),.CLKFBOUT(feedback),
        .CLKOUT0(pixel_raw),.CLKOUT1(serial_raw),.LOCKED(locked),
        .PWRDWN(1'b0),.RST(reset)
    );
    GLCLK feedback_buffer(.CLKIN(feedback),.CLKOUT(feedback_global));
    GLCLK pixel_buffer(.CLKIN(pixel_raw),.CLKOUT(pixel_clk));
    IOCLK serial_buffer(.CLKIN(serial_raw),.CLKOUT(serial_clk));
endmodule

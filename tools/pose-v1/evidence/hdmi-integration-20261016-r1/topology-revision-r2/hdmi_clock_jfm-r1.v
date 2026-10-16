// Front-end equivalents of the qualified FMSH MMCM/global/IO clock primitives.
// JFM's installed 030ai adaptation and factory implementation remain required.
module hdmi_clock_jfm(
    input wire ref_100m,input wire reset,
    output wire pixel_clk,output wire serial_clk,output wire locked
);
    wire feedback_raw,feedback,pixel_raw,serial_raw;
    MMCME2_BASE #(.BANDWIDTH("OPTIMIZED"),.CLKIN1_PERIOD(10.0),
        .CLKFBOUT_MULT_F(37.125),.DIVCLK_DIVIDE(5),
        .CLKOUT0_DIVIDE_F(5.0),.CLKOUT1_DIVIDE(1),.STARTUP_WAIT("FALSE")) mmcm(
        .CLKIN1(ref_100m),.CLKFBIN(feedback),.CLKFBOUT(feedback_raw),
        .CLKOUT0(pixel_raw),.CLKOUT1(serial_raw),.LOCKED(locked),
        .PWRDWN(1'b0),.RST(reset));
    BUFG feedback_buffer(.I(feedback_raw),.O(feedback));
    BUFG pixel_buffer(.I(pixel_raw),.O(pixel_clk));
    BUFIO serial_buffer(.I(serial_raw),.O(serial_clk));
endmodule

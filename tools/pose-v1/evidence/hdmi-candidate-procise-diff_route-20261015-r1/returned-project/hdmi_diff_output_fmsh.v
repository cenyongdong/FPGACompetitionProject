// Compatibility candidate from the installed FMA IODU_DS_LIC_EN template.
// A real differential macro, with receiver disabled and output enabled; never
// synthesize two ordinary GPIO inversions as a substitute for a TMDS pair.
// Primitive synthesis acceptance alone is NOT bank/electrical/route signoff.
module hdmi_diff_output_fmsh(
    input wire serial_bit,inout wire tmds_p,inout wire tmds_n
);
    IODU_DS_LIC_EN #(
        .DIFF_TERM("FALSE"),.IBUF_LOW_PWR("TRUE"),.IOSTANDARD("TMDS_33"),
        .SLEW("SLOW"),.USE_IBUFDISABLE("TRUE")
    ) differential_output(
        .O(),.IO(tmds_p),.IOB(tmds_n),.I(serial_bit),.T(1'b0),
        .DCITERMDISABLE(1'b1),.IBUFDISABLE(1'b1)
    );
endmodule

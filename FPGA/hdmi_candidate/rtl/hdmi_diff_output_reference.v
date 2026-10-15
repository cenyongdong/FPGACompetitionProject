// Original reference output-only differential primitive, isolated compatibility
// probe. Procise implementation must verify its mapping before production use.
// Not a replacement for the complete serializer, clock or PS/AI design.
module hdmi_diff_output_reference(
    input wire serial_bit,output wire tmds_p,output wire tmds_n
);
    OBUFDS #(.IOSTANDARD("TMDS_33"),.SLEW("SLOW")) differential_output(
        .I(serial_bit),.O(tmds_p),.OB(tmds_n)
    );
endmodule

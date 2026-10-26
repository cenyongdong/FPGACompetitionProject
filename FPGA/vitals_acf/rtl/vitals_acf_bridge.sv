// Optional front-end in the existing 50MHz GP chain; all other addresses pass.
// Reuses the qualified project's GP interface/router; no HP or DMA connection.
module vitals_acf_bridge(
 input wire clk,resetn,
 mna_gp_ww_itf.slave upstream,
 mna_gp_ww_itf.master downstream
);
 mna_gp_ww_itf acf();
 hdmi_cam_router #(.HDMI_BASE(32'h400b2000),.DECODE_LSB(8)) router(
  .clk(clk),.resetn(resetn),.upstream(upstream),.camera(downstream),.hdmi(acf.master));
 vitals_acf_csr core(.clk(clk),.resetn(resetn),
  .wr_valid(acf.awwvalid),.wr_addr(acf.awwaddr[7:0]),.wr_data(acf.awwdata),.wr_ready(acf.awwready),
  .rd_valid(acf.arvalid),.rd_addr(acf.araddr[7:0]),.rd_ready(acf.arready),
  .rsp_valid(acf.rvalid),.rsp_data(acf.rdata),.rsp_ready(acf.rready));
endmodule

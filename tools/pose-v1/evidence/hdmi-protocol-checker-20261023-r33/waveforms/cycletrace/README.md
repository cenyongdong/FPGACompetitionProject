# HP2 实板连续波形

Bank 0: 未触发／未发布，不生成虚构波形。

Bank 1: 128 点，触发 HP 周期 11603128，握手 {'PS_AR': 0, 'PS_R': 0, 'S01_AR': 0, 'S01_R': 0, 'HC2_AR': 0, 'HC2_R': 0}。

采样器在 FPGA 配置后自主工作，512 bit × 128 点 × 2 窗口，每点名义 5 ns。保留触发前最多32点与触发后95点；PS出口、互联S01、AI HC2在同一HP域取样。AI四路和视频源端隔离接线保持。软件只读冻结缓冲，未加载SDK、未发DMA或HDMI START。

PNG/SVG供直接查看，VCD供波形工具逐拍检查，CSV包含全部样本，RDATA/ARADDR以十六进制保存以避免表格软件截断64位精度。VCD时间0对应各窗口首样本；末端置X表示超出观测范围。raw.json为原始32位CSR读值，decoded.json为按RTL布局解码的结果。

- BRAM recorder, not a vendor ILA export.
- Flags are pin levels sampled in HP domain; asynchronous flags have edge uncertainty.
- No coverage before PL configuration or while HP clock is absent.
- RDATA/RID/RRESP/RLAST have protocol meaning only when RVALID=1.
- DDR_calibrated is PL MIG init_calib_complete, not a PS DDR initialization indicator.
- Initial high does not establish an observed reset release edge.
- No PS internal FIFO occupancy or reset completion proof.

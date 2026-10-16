# Lite板HDMI、参考时钟及按键引脚核对

2026-10-15，只读核对Docs/开发板手册/JFMQL30TAI_LITE.pdf的PDF第9、10、19、21、22页，实际图纸Sheet标签为9、10、23、25、26；完整页面与放大图已目视检查。页脚沿用JFMQL100TAI标题，U1器件符号明确为JFMQL30TAI；下表同时与原工程XDC及候选已执行的引脚探针对照，不凭文件名或标题推断兼容。

| 作用 | 原理图网络 | FPGA球位 | BANK／供电 | 使用契约 |
|---|---|---|---|---|
| 独立参考时钟 | PL_100MHz | AC14 | 12／3.3V | G1标称100MHz，MRCC；不是SDI或MIG推导时钟 |
| TMDS时钟P／N | HDMIO_FCLK_P/N | AC17／AC16 | 12／3.3V | 原生差分输出，两端配对 |
| TMDS数据0 P／N | HDMIO_FD0_P/N | AA15／AA14 | 12／3.3V | 对应HDMI D0 |
| TMDS数据1 P／N | HDMIO_FD1_P/N | Y16／Y15 | 12／3.3V | 对应HDMI D1 |
| TMDS数据2 P／N | HDMIO_FD2_P/N | W16／W15 | 12／3.3V | 对应HDMI D2 |
| 热插拔输入 | HDMIO_HPD | AE16 | 12／3.3V | 经R353/R354分压，不等于已取得EDID或显示器时序支持 |
| DDC时钟 | HDMIO_FSCL | AA17 | 12／3.3V | Q4电平转换至HDMI侧5V上拉；只允许下拉/释放，需核验实际双向接口 |
| DDC数据 | HDMIO_FSDA | AB17 | 12／3.3V | Q5电平转换；只允许下拉/释放，不推挽驱动 |
| CEC | HDMIO_CEC | AB16 | 12／3.3V | 可选独立控制，不与DDC互换 |
| 原sys_rst输入 | PL_KEY2 | F8 | 34／1.5V | SW7松开为低，按下为高；它是PL按键，不是PS上电复位 |

第22页显示PL_KEY2经R400 10K下拉、R401串接与C571滤波，按钮接PL_VCC1V5。若用于候选reset，则物理请求为高有效；仍需在各时钟域实现规范的复位同步/释放，并保持AXI复位协调，不能把按钮抖动或局部复位当在途读完成。此核对补齐了原F8极性未知项，未修改当前RTL或板上复位。

第19页显示FPGA IO直接通过电容/保护网络到HDMI，没有专用发送器。该页明确指出1080p60不能保证，建议专用HDMI输出芯片，IO直驱支持720p及以下。现行1080p60仍是用户批准的候选目标；此处不自动改成720p，也不能把逻辑仿真、100MHz引脚布线探针当1.485Gb/s输出验收。最终仍须实际器件/IO时序、完整布线和显示器确认。

这些球位和电气网络不能提供PS7/PCPU7内部AI_IN/AI_OUT原语端口定义。PS配套问题见[JFM核对结果](JFM-COMPATIBILITY-REVIEW.md)。完整原值和SHA见[本批证据](../../tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/REPORT.md)及pin-contract.json。当前未接入HPD/DDC/CEC新功能，没有MMIO、EDID读取或硬件测量。

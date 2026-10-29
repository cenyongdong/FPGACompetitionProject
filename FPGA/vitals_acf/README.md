# 心率自相关 PL 核心

**最终范围（2026-10-29）：** 心率功能冻结，本核未进入最终整机位流；已有仿真／OOC 不等于板端功能。当前交付与后续边界见[项目进度](../../PROJECT-PROGRESS.md)。

2026-10-26。已实现、仿真并完成独立综合；**尚未完成整机实现、bit／BOOT 或上板验证**。本次软件和真实 CSI 结果统一见[心率开发记录](../../software/vitals/HYBRID-20261026.md)。

## 分工与资源依据

PS 保留同包天线相位差、时间适配、滤波、频谱、归一化与心率判定；PL 只计算有界有符号自相关点积。使用现有 50MHz GP 时钟，无 DMA、HP 主机、新时钟或全局复位。默认 CPU 可独立工作，PL 是可替换计算后端。

[防闪现模块](../hdmi_candidate/pose_stabilizer/README.md)目前推荐 r45＋CPU，1／4 路 PL 滤波分别为 1250／3448 LUT，均超其原预算，尚未部署。因此不能把实验版滤波或未获资格的诊断裁剪当作已经占用／释放的实际资源。r45 实际为 18996／19650 Slice；剩余 Slice 的打包、布线和时序仍须整机验证。

Vivado2018.3、既有适配目标 `xc7z030ffg676-2`、OOC 综合：

| 项目 | 最终 CSR 核心 |
|---|---:|
| LUT | 381 |
| FF | 237 |
| BRAM36 | 3 |
| DSP48 | 1 |
| OOC setup／hold slack | +16.243／+0.153ns |

资源包含 CSR，不包含额外 GP 路由器。OOC 端口没有整机外部延迟，**这些 slack 不代表完整物理时序通过**。早期 2314／1714 LUT 版本因输入 RAM 未推成 BRAM 而不采用；最终通过保留层次的两份双端口输入 RAM 推出 3 个 BRAM36，保留原失败／中间报告。

## 数学与接口

PS 按块峰值缩放到 ±65535，18 位有符号样本，48 位有符号累加；最大 2048 样本、lag 511，最大整数绝对和小于 2^43。每个乘加 3 周期。1500 样本、lag 501 实测 RTL 计算 1881747 周期，50MHz 下 37.635ms；四特征心率＋呼吸计算约 173.44ms，不含 PS MMIO、轮询和软件成本，不宣称端到端加速。

候选 GP 地址 `0x400b2000–0x400b20ff`，寄存器均 32 位：

| 偏移 | 内容 |
|---|---|
| 00 | ABI `56414301` |
| 04 | busy bit0、done bit1、fault bit8 |
| 08 | 写 1 启动、写 2 仅复位本计算模块 |
| 0c／10 | 样本数／最后 lag |
| 14／18 | 请求序号／完成序号 |
| 1c | 计算周期数 |
| 20／24 | 顺序写入完整有符号样本／已写计数 |
| 28 | 读取结果的 lag 索引 |
| 2c／30 | 累加结果低 32 位／高 16 位符号扩展到 32 位 |

写齐、空闲、参数合法、非零新序号后才启动。结果在 done／序号成立后读取，响应保持到读握手；错误及超时隔离后端。PS 适配器不包含物理地址映射，须由部署所有者提供经核验的读写回调及新硬件资格；旧 r45 在首次 MMIO 前被拒绝。`FallbackCorrelation` 隔离出错后端并用 CPU 继续，不重试、不释放仍由部署控制器拥有的设备。

## 整合与验证

`prepare_overlay.py` 只生成独立 r45 源码覆盖层：在原 GP 链前插入 `vitals_acf_bridge`，所有其它地址继续交给旧链。保留 AI 四路、HP 分配、原有限消费和全部诊断／约束；不使用精简守卫覆盖层，也不改原 r45 文件。输出资格固定为 false，须完成目标器件整机实现、时序与有限板测后才能启用。

已通过整数黄金向量（N=8／129／2048／1500）、边界／不完整装载／忙时提交／局部复位／读背压测试；GP 桥接仿真验证新地址读写、正负累加结果、HDMI／旧控制／非匹配地址透传和保持响应。

证据目录：`.local/vitals-hybrid-20261026/rtl-r3`、`synth-r3`、`bridge-r1`、`r45-overlay`。包含原生命令、退出码、日志、utilization／timing 与 DCP。原项目 `mna_itf.sv`／`hdmi_cam_router.sv` 通过既有本地参考路径复用。

```powershell
python FPGA/vitals_acf/run_offline.py simulate --output .local/new-acf-sim
python FPGA/vitals_acf/run_offline.py synthesize --output .local/new-acf-synth
python FPGA/vitals_acf/run_offline.py bridge --output .local/new-acf-bridge
python FPGA/vitals_acf/prepare_overlay.py --output .local/new-acf-overlay
```

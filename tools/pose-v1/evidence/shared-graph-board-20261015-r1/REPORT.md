# 共享细化计算图导出、Icraft 转换与 Lite 首帧计时报告

执行日期：2026-10-15。**完整 ONNX 已从训练服务器导出并拉回本地，Icraft 五阶段全部成功，板端已完成一次实际推理；首帧数值逐位比较失败，按原门禁停止，未执行后两个窗口。** 因此交付的是可检查的转换产物、首帧计时和完整失配证据，不是板端数值验收通过或稳定性能结论。

## 1. 范围、位置与执行条件

本轮“共享权重”沿用此前用户批准并经过 7824 帧验证的**共享细化计算**：同一帧的重复细化特征仅计算一次，保留每个候选自己的参考坐标及输出顺序。没有合并原本不同层的参数，没有训练或替换 epoch442 权重。两处 TopK、100 个整人候选、14 个关节均保留；两处 ScatterND 继续为零。

| 阶段 | 实际平台、工作目录 | 预算与结果 |
|---|---|---|
| 导出与 FP32 核验 | `gpu-server`，`/public/cyd/Person-in-WiFi-3D-repo`；已有 PersonInWIFI 环境，torch 1.13.1、ONNX 1.7.0、ORT 1.19.2，CPU 单线程 | 内层 600 s／进程组外层 650 s；导出核验 17.020 s，包装器 20.747 s，exit 0 |
| 转换 | Windows，`D:/FPGACompetitionProject/model/piw24_shared-20261015-r1`；`C:/Icraft/CLI v3.39.0/bin/icraft.exe`，已核 CUDA DLL | 总预算 3600 s／单阶段 1200 s；实际 37.987 s，五阶段 exit 0 |
| ARM 构建 | 已有 FPAI 容器，GCC 9.4，`/tmp/shared-20261015-r1` | 新独立目标 `pose_shared_timing` 构建通过，保留原 unused-function 警告 |
| 板端 | Lite `192.168.126.49`，`/tmp/wifi-pose-shared-20261015-r1`，SDK 3.39.0，原 BOOT／内核 | 计划三窗各一次；子进程预算 120 s／退出宽限 5 s；实际一次后比较失败，exit 1 |

前置核验包括源码／checkpoint 身份、原参考输入输出、SDK／BOOT／内核、FPGA operating、端口与后台进程。转换停止条件包括非零退出、超时、文件配对／MD5／身份错误、端口不符或 ScatterND 重现；板测另在非有限值、非法索引、SDK 异常、内核日志变化或任何输出字节差异时停止。没有自动重试、没有放宽逐位比较。

## 2. 完整 ONNX 与导出核验

完整产物及导出脚本保留在：

`D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/exportONNX/shared-refine-20261015-r1/`

- `person_in_wifi_2024_best_epoch442_full_shared.onnx`：52,526,949 字节，opset 11，1202 节点、248 initializers，TopK 2、ScatterND 0。
- `export_shared.py`、`run_export.py`、两份实际 Python 源码快照、29 份核验输入输出、日志及远程原始清单均已回传。
- 固定 FP32 输入 `csi_tokens[1,180,60]`；输出 `scores[1,100]` 和 `poses[1,100,14,3]`。这是固定单帧推理图，不声明支持任意动态 batch。
- 使用 27 个覆盖完整测试列表的样本，加上板端 308／309／310 三窗，去重共 **29 份真实输入**。导出包装器与实际 Python 细化输出逐位相同；新旧 ONNX 经同一 ORT CPU 对照，分数逐位相同，姿态最大差 **2.384185791e-7 模型单位（0.000238419 mm）**，低于导出门限 1e-5 模型单位。
- 此处只证明 FP32 导出符合已批准的共享实现；不能替代后面的 FP16 板端比较。

远程完整归档 50,892,765 字节，SHA256 `8379a811de7a4869ee58b72451df955ea446dadd0c2a554c3b5d87b79522302c`，本地逐成员核验通过。详情见 [export-summary.json](export-summary.json)、[export-verification.json](export-verification.json) 与 [onnx-local-review.json](onnx-local-review.json)。

## 3. Icraft 转换与计算规模

保留目录：`D:/FPGACompetitionProject/model/piw24_shared-20261015-r1/`。实际 `piw24_shared.toml`、`compile_icraft.py`、五对 JSON／RAW、每阶段命令／退出码／日志和输入 ONNX 均在该目录。

配置沿用紧邻的去 ScatterND 版：ZG330、FP16、4 rows × 4 cols × 1 core，CSI 输入 FP32，CLI layout FD、XIR layout **C，预处理全部 NOP。仅更改网络名和 ONNX 路径。TOML 头部关于“原始 TOML 未保留”的注释来自更早首次转换历史；本轮直接沿用 14 日已保留的 TOML，未另行猜测精度参数。

| 阶段 | 退出码 | 墙钟秒 | 逻辑算子数 | RAW 字节 |
|---|---:|---:|---:|---:|
| parse | 0 | 6.7374 | 566 | 58,713,412 |
| optimize | 0 | 3.8386 | 632 | 58,715,272 |
| quantize | 0 | 1.4697 | 658 | 29,366,478 |
| adapt | 0 | 16.3278 | 1538 | 29,594,694 |
| generate | 0 | 8.5319 | 1027 | 35,481,378 |

总转换墙钟 **37.9870 s**，含阶段间核验等开销。最终图含 **1021 HardOp**，六个直接 Host 节点为 Input0、TopK188、GatherElements192、TopK437、原生 Gather442、Output565。两处 TopK 均保留，未恢复 ScatterND 注册、CPU 核、暂存或其专用轮询。130 个原始 Matmul 经 FP16 量化；adapt 另产生两个 TF32 Matmul，见转换阶段算子审查原值。

与共享改造前的去 ScatterND 图相比，最终 RAW 从 **53,200,782 降至 35,481,378 字节（减少 33.31%）**，HardOp 从 1158 降至 1021。优化后的实际矩阵形状如下，说明共享已进入计算图：

| 细化计算示例 | 原去 ScatterND 图 | 新共享图 |
|---|---|---|
| 多头 cross-attention Q×K | `[800,14,32] × [800,32,180]` | `[8,14,32] × [8,32,180]` |
| FFN | `[14,100,256] × [1,256,1024]` | `[14,1,256] × [1,256,1024]` |
| 坐标回归 | `[100,14,256] × [1,256,3]` | `[1,14,256] × [1,256,3]` |

800／8 包含 8 个注意力头；整人候选仍为 100，只消除了共享特征的重复计算。原始形状表见 [icraft-refine-matmul-shapes.json](icraft-refine-matmul-shapes.json)。

## 4. 板端绑定、数值门禁与精度观察

新独立引擎依据 SDK 公开 `hardop_map`／`merge_from`／`idx_map` 核验原 HardOp 唯一、完整覆盖，再推导融合计数及等待区间。没有套用旧图 group ID 或最终计数。

| 实际融合组 | 起始计数 | 层数 | 原 HardOp 成员 |
|---|---:|---:|---:|
| 8139 | 0 | 223 | 365 |
| 8140 | 223 | 11 | 19 |
| 8141 | 234 | 242 | 410 |
| 8142 | 476 | 4 | 7 |
| 8143 | 480 | 132 | 220 |

1021 个成员完整且无重复，连续覆盖到 **612**，首帧实际完成计数也是 612；Host callback 5 次、ZG callback 5 次。TopK／GatherElements 的必要桥及通用失败证据保留，原生 Gather 仍由 SDK 实现。

首帧 `S11_01_308` 的输入和**全部 100 分数逐位一致**，4200 个姿态坐标全部有限，但 **78 个坐标字节不同**：

| 项目 | 实测 |
|---|---:|
| 最大坐标绝对差 | 0.001953125 模型单位 = **1.953125 mm** |
| 最大关节欧氏差（全部候选） | **1.953125 mm** |
| 最高分候选最大关节差 | **0.9765625 mm** |
| 单帧旧去 ScatterND 版 MPJPE | 131.374832153 mm |
| 单帧共享版 MPJPE | 131.379043579 mm |
| 单帧 MPJPE 变化 | **+0.004211426 mm** |

MPJPE 离线使用原服务器 `WifiPoseDataset.calc_mpjpe`，同一真实 GT，模型单位按原方法乘 1000 转毫米；两版匹配候选均为索引 0。它是这一个样本的 GT 辅助误差，不能扩展为完整数据集精度或检测准确率结论。旧版输出来自此前已逐位通过的冻结参考。

两版姿态均可由 FP16 精确表示，差值呈 FP16 步长特征；**确切差异产生于哪个编译或低精度计算步骤尚未定位**，不能直接认定为可忽略舍入。此前 FP32 全数据集损失很小的结论，不自动适用于本次 FP16 板图。

完整实际输入／100 分数／4200 坐标先保存，再比较，原停止原因是 `Complete output differs; stop without retry`，不是 SDK 异常或超时。**计划 3 帧，实际推理 1 帧，逐位验收 0 帧，309／310 未执行。** 没有重跑失败 Session、替换参考或提高容差。

该停止遵循 [AGENTS.md](../../../../AGENTS.md) 的“有限性、严格比较和异常停止规则保持”及“禁止……自动重试失败负载”。本报告只继续离线分析已保存数据。任何后续板测均需先讨论本次数值偏差与验收标准／精度处理方案。

## 5. 实际首帧耗时

以下全为 **一次推理样本**，没有 warmup、均值、P95 或常驻吞吐结论。Engine 从开始预处理至完成输出与选择；保存、比较和初始化另列。

| 分段 | 首帧 ms |
|---|---:|
| CSI 预处理 | 5.64953 |
| 输入准备 | 0.08056 |
| 帧状态清理 | 0.00511 |
| `forward`（含中途必要等待与 Host 运算） | **16.33242** |
| `forward` 返回后最终完成等待 | **0.64366** |
| 输出读回 | 1.17285 |
| 最高分选择 | 0.00104 |
| **Engine 完整处理** | **24.19628** |
| Engine 线程 CPU 时间 | 24.17400 |
| 保存完整实际输出（Engine 外） | 0.45510 |
| 原严格比较（Engine 外） | 0.00211 |

细分 `forward` 的桥内墙钟：等待 **6.93210 ms**、CPU 数学核 **3.05682 ms**、copy API **0.38632 ms**、Host 分配 **0.08356 ms**、描述准备 **0.08801 ms**；Host callback 其余 **3.34169 ms**，ZG 提交 callback **0.81112 ms**，未覆盖区间 **1.63313 ms**。这些是软件观测区间；等待中的 CPU 活动和设备执行可能重叠，不能再作为独立硬件时间累加。

其中两处 TopK inclusive 分别 **5.00964／3.94499 ms**，GatherElements **3.67178 ms**，原生 Gather **1.14794 ms**。TopK 时间包含等上游结果，不代表 TopK 数学本身这么慢。完整算子／阶段时间见 [stopped-analysis.json](stopped-analysis.json)，原始 timeline 在 `returned/run-wall/results`。

本次解析／加载／打开设备／Session 创建及 apply 的初始化总计 **26,803.969 ms（26.804 s）**，其中 `session_apply` **23,266.692 ms**。这是当前已运行系统中新进程的 Session 初始化，不是断电后的首次启动验收，也不计入 24.196 ms。

此前去 ScatterND 版同一窗口 Engine **190.77754 ms**，本次为 **24.19628 ms**，观察比值约 **7.88×**。旧版三窗均值 **184.16291 ms**是另一种统计量，不能与本次单帧混称均值对照。两者不是同 Session 受控 A/B，且共享版数值门禁失败，**不将 7.88× 写成已验收性能收益**。主要末端等待显著缩短，符合减少细化重复计算的方向，但仍需数值方案确定后的有效样本验证。

未调用此前返回无效值的 `getLayerTime`；纯 NPU 算术、DDR 停顿、精确 SDK 调度耗时仍未知。没有运行 VPU、TCP、RTSP、GUI 或整机频率测试；板上用户原有 MobaXterm 监控进程保留，其影响未独立量化。

## 6. 关键身份与交付证据

| 对象 | SHA256 |
|---|---|
| 固定 epoch442 checkpoint | `6493e2250b83aef59ce4825e15d2d0043a59490275f75933f9a59867867d3221` |
| 新 ONNX | `bd8b2d8665687ae8ffbcb9840e838a77effed33d0ffb323e5fdc60e95fcf7cbd` |
| 实际 TOML | `16efc43f6e09c96c2209e2fdc1931b2f6033b8002eda52fab2b08c1470b73c22` |
| 最终 `piw24_shared_ZG.json` | `a1395205eed11112ac0e23dacf8eec4c09d7dfec120e99b060a9361cb9c812cc` |
| 最终 `piw24_shared_ZG.raw` | `d235ec300f2872f1b78ce6101bc98fd2cc13c47a53fe99f76e045587148279dd` |
| ARM `pose_shared_timing` | `47c2aed35b3cc1cb4df27073856968f0452bcdd998493a0d6e2c0373654bd9a2` |
| 板端传输包 `transfer.tar` | `abd66d29d0b1ce380beadb93a0b42f3559993b0b0d1b40eb41bbc245126c29d4` |

导出固定使用服务器配置 SHA `9851f018…`，与此前 7824 帧验证相同；本地历史训练配置为 `9986559f…`，两者仅 data loader 规模、resume_from、gpu_ids 不同，**model AST 相同**。已另存两份原配置和 diff；导出显式 CPU eval、严格加载 epoch442，不读取 resume checkpoint、不启动训练、不覆盖本地配置。详情 [config-identity-review.json](config-identity-review.json)。

- [stopped-analysis.json](stopped-analysis.json)：全部首帧结果、算子计时、融合绑定及单帧 MPJPE；[analyze_stopped.py](analyze_stopped.py) 为实际使用的离线分析器。`analyze.py` 是继承的三帧通过路径，**本轮没有运行**。
- [returned/run-wall](returned/run-wall)：板端原始完整输出、stderr、失败 JSON、时间线、前后资源／内核、身份及逐文件哈希；[return.tar](return.tar) 保留原回传包。
- [source.tar.gz](source.tar.gz)：135 份独立 ARM 测试源码／构建文件；[source-manifest.json](source-manifest.json) 保存每份源码身份，[symbol-audit.txt](symbol-audit.txt) 核验本次二进制无 Scatter 符号。
- [delivery-audit.json](delivery-audit.json)：五对模型身份／RAW MD5、源码归档、未重试和最终状态。[documentation-revision.json](documentation-revision.json) 记录现行项目文档此次修订，不回写旧完成清单。
- 初始探索文件 `first-output-differences.json` 的 `first_candidate_delta_mm` 实为模型单位；原文件保留，[更正文件](first-output-differences.corrected.json) 已明确改名，正式毫米结论以 stopped-analysis 为准。

## 7. 停止状态与后续讨论边界

本批板端推理进程、子进程及代理连接已结束，最终 FPGA operating，内核日志前后相同；FPAI 在确认只剩 bash 后恢复停止。未规整、未清缓存、未重启，未更改 SDK／内核／BOOT／正式演示。旧 DATA 首次坏读调查继续暂停。本次保存的失败不证明旧 DATA 问题复发，也不证明其已解决。

后续需由用户讨论确定：对于共享计算改变低精度执行形状带来的数值差异，是保留逐位要求并定位差异，还是制定有依据的 FP16 误差／数据集指标门限后再开展新验证。本轮未选择新精度配置、改门限或继续负载；目前可确认的成果是完整图与转换交付，以及一个已保存、数值门禁失败的首帧计时样本。

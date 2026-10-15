# 去 ScatterND 模型的 Lite 板端推理与耗时报告

日期：2026-10-15，Asia/Shanghai。结论范围：独立新引擎、固定三个真实 CSI 窗口，无 VPU/TCP 并发。

**新 JSON/RAW 已传至板端并实际推理通过。三个窗口全部 100 个分数和 100×14×3 姿态，与原板端参考逐位一致；ScatterND 回调、专用暂存及计数轮询均未执行。** Engine 三帧平均耗时 184.163ms，相较 2026-10-13 同窗口的历史 195.098ms 少 10.935ms，约 5.61%。这是有限历史对照，不是同轮受控 A/B 或长期性能验收。

## 1. 实际部署与引擎改造

执行平台：Windows 主机、已有 FPAI 容器内 GCC9.4/AArch64 交叉编译、Lite FMQL30TAI/ZG330。Icraft/CustomOp 3.39.0、BOOT、内核及六份 SDK 动态库身份与已验基线一致。没有安装、升级、重启、清缓存或内存规整。

主机模型为 `D:/FPGACompetitionProject/model/piw24_noscatter-20261014-r3` 中最终生成的 `piw24_noscatter_ZG.json/.raw`。它是**仅去 ScatterND、尚未共享细化**的模型，两处 TopK 和全部 100 个候选保留。原 TOML 未改。

| 对象 | SHA256 |
|---|---|
| ZG JSON | `0720b375edb7fddd7ee6f074be0e8fd0852592ae1fcbe600762525f276139ce5` |
| ZG RAW | `29dce9c1bd1fc940cdd1364d148353227d01ec0cef82861f7d2c9045e12ee1ce` |

板端独立目录：`/tmp/wifi-pose-noscatter-20261015-r1`。其中 `models/` 保存新 JSON/RAW，`pose_noscatter_timing` 是本轮实际 ARM 引擎，`run-wall/` 保存完整结果。它不是启动时自动运行的服务；正式演示入口和旧部署没有覆盖。

本机生成源码在 `D:/FPGACompetitionProject/.local/noscatter-source-20261015-r1`，交付包在 `.local/noscatter-delivery-20261015-r1`。从冻结且已验证的计时引擎导出独立候选，复用原 CSI 预处理、TopK/GatherElements 数学核与公开 SDK 读写。变更边界如下：

- 删除 ScatterND 类型注册、形状/常量索引检查与 CPU scatter kernel 分支。
- 删除 ScatterND 582/649 的 Host staging 路径和预期回调；注册清单只保留 TopK188/437、GatherElements192，原生 Gather442 的 SDK 注册保持。
- 删除 582 专用的 `waitFresh` 完成计数轮询；不把该轮询迁移到其他正常路径。
- 删除旧 192 生产者观测对固定融合组/原始节点 ID 的依赖；保留必要的通用输入存储检查、异常 Host 拥有字节、存储身份和两轮公开 SDK 源读取，且继续抛原错误。
- 新图不使用旧 1173 HardOp/七组/745 门禁。通过 SDK `forward_info`、`merge_from`、`idx_map` 核对原始 1158 个 HardOp 的完整、唯一覆盖与连续同步区间后，确定实际完成计数；逐帧继续采用原 `reset(1)`，禁止失败重建或重试。
- 已知异常的 `getLayerTime` 不再调用；profiling 关闭，保留可核验墙钟和线程 CPU 观测。不伪造纯 NPU、DDR 停顿或 SDK 精确调度时间。

实际 apply 后的融合如下；每个原始 HardOp 恰好属于一个组：

| 新融合组 | 原始 HardOp 数 | 同步起点 | 层数 | 区间终点 |
|---|---:|---:|---:|---:|
| 9052 | 366 | 0 | 223 | 223 |
| 9053 | 19 | 223 | 11 | 234 |
| 9054 | 412 | 234 | 243 | 477 |
| 9055 | 7 | 477 | 4 | 481 |
| 9056 | 354 | 481 | 255 | 736 |
| 合计 | **1158** | — | **736** | **736** |

全部 1164 个逻辑节点得到追溯；直接 Host 绑定为 Input0、188、192、437、442、Output664。每帧实际执行 5 个 Host 回调（Input及四个计算算子）、5 个 ZG 提交回调。三个窗口最终计数均为 736。这里的 736 已有实际融合元数据和三次完成读数支持，区别于先前仅有的静态层数和。

## 2. 数值与实际推理效果

输入为 S11_01_308、S11_01_309、S11_01_310，沿用历史计时的原始 CSI、预处理 FP32 输入和完整板端输出参考。一次新 Session、无预热、每帧先保存完整实际输入/输出再严格逐位比较，比较失败即停止。120秒进程预算、5秒退出宽限；实际三帧退出0。

独立分析逐项核对返回归档哈希、32,400 个输入 FP32、12,900 个输出 FP32、有限性、形状、融合成员、计数、回调、搬运及时间线嵌套。**三帧全部输出逐位一致，最大绝对误差0。** 未通过候选重排、只比较最高分或放宽误差边界来判定通过。

另外使用原 `WifiPoseDataset.calc_mpjpe` 在 CPU 重新计算地面真值指标；三份 GT 哈希与此前完整7824帧评估记录一致：

| 窗口 | 人数 | 原板端 MPJPE/mm | 去 ScatterND 后/mm | 差值/mm |
|---|---:|---:|---:|---:|
| S11_01_308 | 1 | 131.374832153 | 131.374832153 | 0 |
| S11_01_309 | 1 | 116.487495422 | 116.487495422 | 0 |
| S11_01_310 | 1 | 141.021408081 | 141.021408081 | 0 |
| 逐帧平均 | — | **129.627911886** | **129.627911886** | **0** |

这是三个单人窗口的结果，不能称全测试集、多人数或置信度检测精度验收。原指标依赖 GT 在全部候选中 greedy 匹配，不是最高分候选误差。

## 3. Engine 各部分耗时

下表为三帧平均，单位 ms。右列为本轮实测；左列来自2026-10-13历史同三窗口、同SDK/BOOT/内核、无VPU/TCP的计时。冷缓存、系统状态和采样扰动没有通过同轮 A/B 消除。

| 阶段 | 历史含 ScatterND | 本轮去 ScatterND |
|---|---:|---:|
| Engine总处理 | 195.098 | **184.163** |
| CSI预处理 | 5.622 | 8.588 |
| 输入张量准备 | 0.057 | 0.060 |
| 帧状态清零 | 0.005 | 0.004 |
| `Session.forward` 调用 | 187.617 | **16.010** |
| 末端输出 ready 等待 | 0.227 | **157.975** |
| 输出读取/校验 | 1.257 | 1.192 |
| 最高分候选选择 | 0.001 | 0.001 |

三个 Engine 实际值分别为 190.778、180.853、180.858ms。第一帧预处理14.517ms，后两帧约5.625/5.622ms，拉高了当前平均；不删除首帧来夸大加速。完整输出保存平均0.475ms、比较0.012ms在 Engine 计时之外。

**`Session.forward` 约16ms不代表完整推理只需16ms。** 去掉两处 ScatterND 后，后半段 NPU 工作可以连续异步提交，原来发生在 ScatterND 回调里的等待大量转移到末端 `waitForReady`。本轮从 forward 开始至输出 ready 的实测时间线区间平均 **173.990ms**；纯算术时间仍未分离。

## 4. forward 内部时间分解

以下嵌套在16.01073ms的 forward 时间线内，不与上一表直接相加：

| 组成 | 平均/ms | 解释 |
|---|---:|---|
| 剩余CPU桥输入ready等待 | 6.941223 | TopK/GatherElements输入等待，不能等同纯NPU时间 |
| 自定义CPU核 | 3.063540 | 两TopK及GatherElements，不含原生Gather442独立核时间 |
| 设备→Host搬运API | 0.375770 | 剩余四次自定义桥读取的API区间 |
| Host暂存分配 | 0.081407 | 必要TopK/GatherElements输入暂存 |
| 规格检查 | 0.089213 | 形状/布局/类型检查 |
| 自定义输出写回 | 0 | 本轮没有该区间 |
| Host回调其他 | 3.187503 | 包括原生Gather442及未覆盖的回调工作 |
| 五个ZG提交回调 | 0.652487 | 提交区间，不是NPU执行总时长 |
| forward回调外剩余 | 1.619587 | SDK、观测及未覆盖工作，不全归因调度 |
| 并集分解合计 | **16.010730** | 与时间线forward区间闭合 |

原含Scatter图已观测自定义CPU核约14.121ms；本轮约3.064ms，少约11.06ms。原自定义桥设备→Host逻辑搬运8次/115,360B，本轮 **4次/48,160B**，减少4次/67,200B（58.25%）。这是该桥的逻辑字节，不是全部DDR流量，末端输出读回另计。

| 剩余Host算子 | 回调整体/ms | 输入等待/ms | 自定义CPU核/ms |
|---|---:|---:|---:|
| TopK188 | 5.017417 | 3.854727 | 0.329210 |
| GatherElements192 | 3.674613 | 0.014050 | 2.470363 |
| TopK437 | 3.950447 | 3.072447 | 0.263967 |
| 原生Gather442 | 1.012513 | 未独立测量 | 未独立测量 |
| ScatterND582/649 | **无回调** | **无对应桥等待** | **无对应核** |

Engine进程CPU计时平均181.251ms。该值和就绪等待均是宿主观测，不能据此推导NPU算术、DMA完成或DDR停顿。

## 5. 初始化、证据与剩余边界

本轮初始化 **29.206s**，包含图解析2.317s、参数加载0.896s、设备打开0.013s、Session创建0.462s、`apply`约24.969s及验证/快照等其他工作；不计入单帧处理。

原始回传位于 [returned/run-wall](returned/run-wall)，完整归档为 `return.tar`。可复查入口：

- [机器可读分析及逐算子/逐帧原值](analysis.json)、[分析脚本](analyze.py)。
- [实际执行步骤](steps.json)、[执行范围与停止条件](execution-plan.json)、[部署包身份](package.json)。
- [完整可构建源码归档](source.tar.gz)、[源码与二进制符号复核](source-review.json)、[最终源码清单](source-manifest-final.json)。交叉编译使用FPAI既有工具链及SDK；本轮启动的空闲构建容器已停止。
- [融合覆盖摘要](returned/run-wall/results/engine/binding-summary.json)、[完整绑定](returned/run-wall/results/engine/bindings.jsonl)、[注册清单](returned/run-wall/results/engine/registry.jsonl)。
- [单调时间线](returned/run-wall/results/monotonic-spans.jsonl)、[完整每帧结果](returned/run-wall/results/frames.jsonl)、[设备搬运事件](returned/run-wall/results/transfers.jsonl)。
- 原始输出在 `returned/run-wall/results/frame-0..2/`，每帧保存 `input.f32/scores.f32/poses.f32`，没有用参考值替换实际值。
- [最终板端现场](99-final-state.txt)：无本批推理进程、FPGA operating；设备/进程已回收、SSH连接已结束，内核日志前后不变。

编译最初发现关闭SDK计时的shim参数数量不匹配，保留编译失败后修正为四参数；部署安装命令的语法错误也保留，发生在执行任何语句之前，无设备初始化或推理。两者修正后才首次启动新Session，没有失败推理负载重跑。本机分析发现手动墙钟span没有线程CPU值，按unknown保留；本地完整评估文件哈希与服务器不同，停止该指标步骤并取得已固定SHA的服务器快照，确认 `calc_mpjpe` AST一致后计算，不修改本地数据集源码。相关错误及核验记录原样保留。

本轮没有调用此前异常的SDK层计时接口，故纯NPU算术、DDR停顿和精确SDK调度仍报告未知。三个窗口通过不证明长期可靠性、视频并发或旧DATA首次坏读根因已经解决；旧DATA调查继续暂停。正式演示基线、旧JSON/RAW、SDK/BOOT和共享细化源码保持。新模型和独立引擎已经留在板端，后续可从本包继续受控开发。

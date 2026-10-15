# 项目进度总览

更新日期：2026-10-15。最近实际验证另包括HDMI只读盘点：当前BOOT/三份SDK核心库身份相同、FPGA operating；未发现Linux显示或HDMI时钟观测接口，像素时钟/PLL与安全停止尚缺依据，色条未启动。用户已批准先核配套再静态图、翻帧/停止、骨架的有条件顺序；[讨论记录](ARCHITECTURE-DISCUSSION-20261015.md)、[本次证据](tools/pose-v1/evidence/hdmi-stage1-20261015-r2/REPORT.md)。共享模型最近实际验证：共享新包三窗、30秒/1131次及30分钟/62,945次实板串行推理完成，数值/内存观察通过、未观察到崩溃，全部原值回传独立复核；11次>1秒、最长4.158秒的时延长尾待定位（D41）。仅三个冻结来源，无视频/网络叠加；现行score>0.2/3mm规则保持，旧失败原值保留。正式核心原CPU107/整机复核仍待另验，旧DATA暂停。历史快照见[归档索引](ADR/history/20261013/README.md)。

## 当前阶段与任务状态

2026-10-15共享新包稳定性已完成：原编译包三窗、30秒/1131次及30分钟/62,945次实板串行推理的数值/内存观察通过，完整实际输入/输出回传后SHA及现行门禁独立复核通过。暖机后RSS75204→73628KiB、PSS73887→71779KiB，Private_Dirty/VmData不增，FD13/线程3/映射86保持；Engine均值23.278220ms，含保存/比较速率34.969次/秒。无崩溃/SDK异常/新增内核日志，但11次process超过1秒、最大4.158秒（forward4.151秒/进程CPU20.177ms），时延长尾原因未知，列D41，不称实时性通过。Engine正常销毁、本批进程和连接结束。r1可选/proc接口失败原样保留，r2兼容修复4项本机检查后经用户明确允许新Session继续；归档SSH超时只监测/取回原归档，未重跑推理。模型/RAW/数学/CPU注册/NPU分配/SDK/BOOT不改，常规诊断限前三帧，异常证据路径保留。仅三个冻结输入，无视频/网络叠加，不能扩展为整机或任意输入绝对无泄漏保证。[完整报告](tools/pose-v1/evidence/shared-stability-20261015-r2/REPORT.md)。正式演示不换，旧DATA继续暂停。

现行共享图门禁与阶段认可：用户明确仅对score>0.2候选检查关节三维差≤3mm，低分位置仅留诊断；全部输入/分数逐位及所有候选有限性、SDK/索引/身份等停止规则保持。[ADR_48现行v2](ADR/ADR_48.md)和Agents已更新，21组边界/拒绝自测、同一C++模块三份原板端输出回放、NumPy独立复核及新ARM构建通过。三窗各只有候选0受检，最大关节差0.9765625/0.9765625/0.48828125mm，全部符合；旧5.524mm超限槽score0.001296997被按授权排除位置硬门限，原值保留。共享细化阶段按用户新范围已获阶段性认可；该门禁修改阶段无新上板/部署（后续独立稳定性实板结果见本页首段），旧运行exit1不回写。新源码/ARM包当时已准备，FPAI恢复停止；正式演示/旧DATA暂停不变。物理偏置/训练漂移假设未证，不扩展到完整数据集或长期验收。[最新复核与记录](tools/pose-v1/evidence/shared-confidence-gate-20261015-r1/REPORT.md)。以下首帧/v1阶段为历史条件及原始结果。

2026-10-15共享细化图已导出并回传至原算法仓库exportONNX/shared-refine-20261015-r1；固定epoch442、两TopK/100候选保留、ScatterND0。29真实样本FP32导出核验通过；本机Icraft五阶段exit0、37.987s，TOML/五对JSON-RAW保留model/piw24_shared-20261015-r1，最终1021 HardOp、RAW35,481,378字节（较去Scatter图少33.31%）。原首帧1.953125mm差异触发逐位门禁exit1，原失败完整保留：[首次报告](tools/pose-v1/evidence/shared-graph-board-20261015-r1/REPORT.md)。随后用户明确最大误差3mm，已按[ADR_48](ADR/ADR_48.md)实现仅该固定共享FP16图的全部候选最大关节三维差≤3mm、输入/分数逐位的门检，12组边界/拒绝自测与新ARM构建通过。新目录/新Session三窗复验：308/309均1.953125mm通过；310最大坐标3.90625mm、最大关节5.524271728mm超限，实际推理3/接受2/拒绝1，exit1停止、无重试。三窗MPJPE均值129.627911886→129.622596741mm，不能豁免单关节超限；Engine实测均值27.83871ms包含失败样本，不是通过基准。实际SDK融合1021成员完整覆盖五组/612，三次计数612；源码/原值/日志全部回传，前后BOOT/SDK身份一致、内核日志同，进程和连接回收、FPAI恢复停止。物理偏置未证、数值差异具体来源未知；正式演示未换、旧DATA暂停，未进一步提高门限。[最新门检与结果](tools/pose-v1/evidence/shared-gate-policy-20261015-r1/REPORT.md)。

2026-10-15去ScatterND图板测完成：model/piw24_noscatter-20261014-r3最终JSON/RAW哈希一致部署至Lite /tmp/wifi-pose-noscatter-20261015-r1，独立ARM引擎移除Scatter注册/CPU分支/暂存和582专用计数轮询，TopK/Gather必要桥及异常证据保留。SDK实际融合1158 HardOp→5组9052–9056、区间连续0→736，三次实际完成736；308/309/310共12900输出FP32逐位原板端参考，三帧MPJPE129.627911886mm不变。Engine184.163ms，forward16.010ms后仍末端等157.975ms，不能当16ms完整推理；自定义CPU核3.064ms、桥读4次/48160B。相较历史同三窗195.098ms少5.61%，非同轮受控A/B/长期结论。完整日志/实际输出/源码已回传，进程和设备回收，内核/BOOT/SDK同；无重启/规整/VPU/TCP。此图尚未共享细化，正式演示不覆盖、旧DATA暂停。[完整报告](tools/pose-v1/evidence/noscatter-board-20261015-r1/REPORT.md)。

2026-10-14算法源码候选：用户批准单帧推理共享细化并保留两处TopK，本机两份Python源码已修改、哈希一致部署至训练服务器。固定2024 epoch442、GPU0 FP32、完整7824帧/100候选对照exit0，总MPJPE123.085352129→123.085352227mm（+9.78e-8mm），最大关节差0.000533mm；分数逐位一致，姿态存在舍入差异，不称逐位通过。训练细化损失/2424838梯度及回退路径逐位通过，实际注意力/回归batch100→1。服务器含探针整模型12.212→11.081ms，不代表Lite性能。完整原始输入/两版输出/指标约1.17GB已回传并独立核验，资源回收。[源码、结果与证据](tools/pose-v1/evidence/shared-refine-20261014-r1/README.md)。14日阶段没有共享ONNX/Icraft；15日新增产物与数值失败见本页首段，不将FP32全数据集通过替代FP16板端验收；正式板端基线保持，旧DATA暂停。

2026-10-14主机转换产物：Icraft3.39.0完成去ScatterND完整ONNX的parse→optimize→quantize→adapt→generate，五阶段exit0、RAW配对MD5/身份/固定FP32端口通过。实际TOML与五对JSON/RAW保留 `model/piw24_noscatter-20261014-r3`；FP16据原130 Matmul精度明确配置，原量化TOML未留存。r1/r2输入参数失败保留，新r3总68.688秒通过。最终1158 HardOp/四计算Host/ScatterND0；14日736仅静态层数和，15日另有上述实际融合与三窗验证。正式Engine/旧模型未替换；共享图15日已另行转换并首帧失配停止，完整数据集量化数值和长期性能仍待验，旧DATA暂停。[原转换产物与证据](tools/pose-v1/evidence/icraft-no-scatter-20261014-r1/README.md)。

项目处于**预采CSI回放首版已具备端到端演示，性能和长期可靠性待收敛**阶段。主链为PC原始CSI→TCP→Lite PS预处理→PS/NPU混合推理→独立显示子进程→VPU H264→RTSP/TCP→PC实时GUI。HDMI没有进入当前演示。

- 当前demo已切换software/core六个功能目录；旧pose_v1与历史测试保持。重构后的11组本机、ARM构建、CPU107/59600 FP32及3窗口全数值/354编码/294 GUI解码通过；规整0，资源回收完成，当前无后台项目工作。[ADR_47](ADR/ADR_47.md)／[证据](tools/pose-v1/evidence/core-refactor-20261013-r1/README.md)。
- 2026-10-14正式核心复核：新11组本机/固定字节对照、主机prepare-only和ARM构建通过，14程序与已验证重构同SHA，原警告保持；新增[接口手册](software/core/INTERFACES.md)。本轮SSH只读连接超时，未部署/未运行新CPU107或三窗口，用户选择待板端恢复后完成；Agents.md规范尚未落实。[检查与恢复步骤](tools/pose-v1/evidence/core-check-20261014-r1/README.md)。
- 独立Engine计时已完成有限板测：baseline/wall各3窗口完整输出逐位通过，wall均值Engine195.098ms、forward187.617ms、输入ready等待162.294ms、已观测CPU核14.121ms、搬运API0.771ms。SDK模式第1次输出正确，但745项硬件计时中215项负值，已保存停止、未重试；纯NPU算术、DDR停顿及精确SDK调度仍未知。预检内核版本比较修正为同一dmesg来源，正式模型/SDK/BOOT/核心保持；退出回收、FPGA operating。不恢复旧DATA排查。[实测表](tools/pose-v1/evidence/engine-timing-board-20261013-r2/timing-table.md)／[证据](tools/pose-v1/evidence/engine-timing-board-20261013-r2/README.md)。
- 高负载DATA96/800、192索引与582更新值的首次读取异常根因尚未解决，按用户要求**继续暂停排查**；没有实施首次Host目的租约/CPTR失败对照方案。
- 一次获准可控重启已经使用；永久首启动、严格整机5Hz、整机30分钟、HDMI、真实采集与零拷贝未验收（共享图独立串行30分钟已通过）。
- 本页汇总实际工程状态；阶段审批、分工与停止条件以[Agents.md](Agents.md)和最新用户指令为准，历史授权不自动变成新任务。

## 已完成主链与验证边界

| 工作包 | 已完成内容 | 验证范围及剩余限制 |
|---|---|---|
| FPGA与工具基础 | 原生/MCP流水灯、真实xlconcat从Vivado源码到Procise实现及Lite观察；SD启动/扩容、SSH、FPAI交叉编译 | 简单明文IP方法验证，不扩大为任意IP、Flash/BOOT或整机AI验收；[ADR_03](ADR/ADR_03.md) |
| CSI契约及PS预处理 | 原始复数CSI窗口、PIWCSI1完整记录、拥有值接收；九组300真实输入逐位核验 | 当前固定窗口规格；人工±π边界失败仍保留；[300结果](tools/pose-v1/RESULTS-300.md) |
| 模型与独立参考 | 固定2024 epoch442 ONNX/ZG JSON/RAW，独立ORT CPU环境；27样本部署误差报告获用户阶段验收 | 同槽与最佳候选误差分别报告，跨端query身份未证；不是真实标签/MPJPE验收；[ADR_04](ADR/ADR_04.md) |
| CPU适配 | TopK188/437、GatherElements192、ScatterND582/649应用注册/全有效布局适配；原Gather保留 | 107例、12注册、22输出/59600 FP32独立核验；受限当前规格，未补全CPU Matmul；[ADR_05](ADR/ADR_05.md) |
| PS/NPU混合图 | 1173 HardOp追溯七ZG融合组，真实RAW参数；reset(1)/最终745与不同输入响应 | 数值及有限回归通过；高负载首次读旧值仍待定位，Matmul保持NPU；[技术说明](ADR/TechDetails.md) |
| 显示/编码/网络 | 主线程Engine、SDK无关显示子进程、拥有NV12与AU、有界队列、常驻两缓冲VPU、受保护RTSP | 显示来源/PTS/回收分阶段验证；首启动连续页依赖未永久修复，NoInput/重复不计新姿态；[ADR_02](ADR/ADR_02.md)、[ADR_15](ADR/ADR_15.md) |
| 有界正式演示 | software/demo，指定wifipose目录自然序2Hz回放、10fps预览，PC实际GUI | 三窗口＋60窗口通过，旧故障暂停、HDMI排除；[演示结果](tools/pose-v1/DEMO-RESULTS-20261011.md) |

### 2026-10-11完整演示的数据（历史范围）

| 项目 | 三窗口short | 默认60窗口demo |
|---|---:|---:|
| 原始CSI接收/消费/输出 | 3/3/3 | 60/60/60 |
| 不同姿态输出 | 3 | 60 |
| 编码/原码流离线解码 | 352 | 637 |
| 主机实际RTSP GUI解码 | 292 | 577 |
| 真实姿态来源完整覆盖 | 3 | 60 |
| 可见投影关节核验 | 42 | 840 |
| 成功阶段内存规整 | 0 | 0 |

共63次真实推理、989编码图像和869主机实时解码；60窗口没有待处理槽覆盖。两阶段前三份308/309/310的原始输入、PS张量、全部分数/姿态逐位旧参考，其余57份只完成结构、有限性、最高分选择及视频映射核验，不称完整精度通过。旧Host107/59600数学证据复用，本轮未新跑Host107。

正常drain/LAST、两STREAMOFF、线程join后Engine销毁、端口/进程回收及最终BOOT/SDK/模型/内核同、FPGA operating通过。首连续页失败、39.27594ms规整无效、入口目录与Producer配置遗漏保留，新demo_engine集中配置修正有效；用户批准的一次重启已执行且用完，CMA/BOOT/SDK/模型未改。成功阶段规整0不代表整批从未规整。

## 仍待解决或验收

| 项目 | 当前认识 | 下一步边界 |
|---|---|---|
| 首Host读取残留前输入 | 独立生产者inv94 DATA96全同上一B，INDEX正确，四物理晚源94080字节正确；早期即时Host采样尚缺 | **暂停**，恢复须明确指令；保留原首次文件/晚源读，不能认定NPU/cache/DMA责任；[ADR_44](ADR/ADR_44.md) |
| VPU连续普通页 | 固件512KiB普通连续页失败，CMA空闲不等同可分配；两缓冲/常驻与规整是缓解 | 永久首启动另验，不默认扩大CMA；[ADR_02](ADR/ADR_02.md) |
| 性能和延迟 | 核心短期5.24655Hz，不代表整机；整机4.99165/4.998467Hz不能舍入成严格5Hz | 有界单钟计量证据保留，长期及真实全链待验；[ADR_06](ADR/ADR_06.md)、[ADR_32](ADR/ADR_32.md) |
| HDMI | 目标1080p60；15日只读盘点BOOT/SDK同、FPGA operating，未找到Linux显示/HDMI时钟节点；当前demo未接入 | 保持BOOT，先补当前版本无SDI时钟/PLL及安全停止契约，再色条/换帧/骨架；[本轮报告](tools/pose-v1/evidence/hdmi-stage1-20261015-r2/REPORT.md) |
| 扩展精度与真实采集 | 额外57演示样本无完整数值参考；预采回放不是实时无线设备 | 完整输出参考/实际采集接口与同步/新场景验证另立任务 |
| 30分钟与零拷贝 | 没有长期整机结论，现用SDK Host拥有快照桥 | 保留首版先跑全流程决策，优化不得覆盖基线；[ADR_01](ADR/ADR_01.md) |

算法训练旁支保持归档：26版迁移10轮收益不稳定；全新500轮在第6轮末分支衰退停止，零衰减对照10轮完成但梯度问题仍待。部署仍固定2024 epoch442，不把训练数量累计为板端进度。

## 工程就绪度估计

沿用已批准回放首版的**83/100（约80%–85%）管理估计**，本次重构回归不增加份额。这不是功能通过率、实测工作量、工期或比赛评分；真实采集作品不在该百分比中。

| 工作包 | 规划权重 | 已具备份额（估计） |
|---|---:|---:|
| 平台与工具链 | 15 | 15 |
| CSI契约与PS预处理 | 15 | 15 |
| 首版模型与参考环境 | 10 | 9 |
| PS/NPU混合运行 | 20 | 18 |
| 部署数值阶段 | 10 | 9 |
| 正式应用与性能 | 10 | 7 |
| HDMI、编码及RTSP | 15 | 10 |
| 长期运行与交付验收 | 5 | 0 |
| 合计 | 100 | 83 |

完整演示材料已有交付，但完整首版的HDMI和长期门检尚缺，估计保持而非按新增文件或重复实验累加。

## 基线、连接资料与恢复入口

2026-10-13本轮重新核对BOOT/SDK/模型/内核与FPGA operating；固定身份保持。后续使用前仍应核验实际身份。2026-10-11完整演示及重启记录保留各自范围。

| 对象 | 配置/资料入口 |
|---|---|
| 板子 | 悟净Lite/FMQL30TAI/ZG330；SSH root@192.168.126.49，用户已提供认证信息，运行时通过内存输入 |
| 工具链 | Windows Procise2025.1.1 temp/SVN32494、Vivado2019.1辅助；FPAI是本机交叉编译容器名，ARM64 GCC9.4/CMake3.24.2；Icraft3.39.0 |
| 设备协议 | axi://zg330aiu?npu=0x40000000&dma=0x80000000；device25122301 / icore FMSHZGV3TECH-AID - 24160628 |
| 模型/启动身份 | [TechDetails](ADR/TechDetails.md)及[演示完成清单](tools/pose-v1/evidence/demo-20261011-r4/completion-review.json)；固定JSON/RAW和BOOT哈希，不在本页重复维护 |
| 当前重构demo | 构建.local/pose-v1-build/demo-refactor-20261013-r1，板端/tmp/wifi-pose-demo-refactor-20261013-r1；3窗口回归通过。[运行说明](software/demo/README.md)、[核心导读](software/core/README.md) |
| 当前恢复点 | HDMI按已同意顺序推进，第一阶段只读身份/接口盘点完成，时钟与安全停止资料待补；[门槛与证据](tools/pose-v1/evidence/hdmi-stage1-20261015-r2/REPORT.md)。共享图稳定性及正式旧图重构分别保持原范围，无本批后台 |
| 暂停故障恢复点 | [producer-prepared next-checkpoint](tools/pose-v1/evidence/producer-prepared-20261011-r1/next-checkpoint.json)及[原下一方案](tools/pose-v1/PRODUCER-PREPARED-NEXT-20261011.md)；未实施，不重跑旧Session |
| 历史工具路径/调用示例 | [迁出的工具资料](ADR/history/20261013/toolchain-runbook.md)、[REFERENCES](REFERENCES.md)；旧D:/FPGACompetitionProject路径为历史来源，不直接替代当前工作区 |
| 文档整理记录 | [ADR_46](ADR/ADR_46.md)、[难点索引](DIFFICULTIES.md)、[历史与迁移清单](ADR/history/20261013/README.md) |

当前重构及已批准CPU107/三窗口验证完成，不继续60窗口或恢复暂停排查。原重启前/tmp已清空，原失败已本机归档；后续不能使用旧句柄或接续已失败Engine。

# 项目进度总览（2026-10-07）

> 2026-10-08当前：VPU启动资源修正三次独立进程通过，同进程有限工作者32前向/987编码及全部源映射通过。[启动结果](tools/pose-v1/VPU-STARTUP-RESULTS-20261008.md)、[常驻/视频](tools/pose-v1/RESIDENT-RESULTS-20261008.md)、[检查点](tools/pose-v1/evidence/resident-20261008-r6/next-checkpoint.json)。下一在线owned AU/RTSP；不是常驻daemon或整机/长期验收，HDMI仍待配套。旧“启动未过”对应六缓冲/后台Engine失败，历史保留。管理粗估81/100保持，非用户暂停，无后台。

> 2026-10-08最新：同进程真实推理→画面→VPU有限链路已核验，但无规整的新进程重复在MVX固件连续页分配失败。[完整结果](tools/pose-v1/PIPELINE-RESULTS-20261008.md)、[下一分配取证](tools/pose-v1/PIPELINE-NEXT-20261008.md)。两成功不记稳定启动/实时RTSP验收，主观管理估计81/100保持；HDMI/整机5Hz/30分钟仍待。已关闭测试与连接，无后台；旧RTSP准备合并条目按历史理解。

> 当前已推进到独立RTSP传输/重连和直接播放器通过：[RTSP结果](tools/pose-v1/RTSP-RESULTS-20261007.md)、[当前检查点](tools/pose-v1/evidence/rtsp-20261007-r3/next-checkpoint.json)。两会话200帧＋直接播放器100帧像素逐位原视频，下一为真实推理→编码→RTSP接入；显式色彩/HDMI/整机长期仍待。管理工作包估计更新81/100（约80%），仅主观工程份额，不是功能通过率或工期；历史78分记录保留。

<details>
<summary>此前阶段状态与暂停记录（历史，当前入口见上方）</summary>

> 当前视频任务已恢复，V2-A真实骨架文件编码与独立上下文重复通过：[r5结果/视频](tools/pose-v1/VIDEO-DESCRIPTOR-R5-RESULTS-20261007.md)、[当前检查点](tools/pose-v1/evidence/video-descriptor-20261007-r5/next-checkpoint.json)。54帧/27来源主机核验，MMAP cookie兼容修正后两次码流逐位一致，无新增内核异常。HDMI1080p60配套仍缺时序/scanout/安全停止证据，未写入；下一独立RTSP准备与动态样片审查。整机/长期仍待，管理粗估78/100保持。下方暂停、未编码等条目为各轮历史。

> 当前任务已按用户要求暂停：[恢复入口](tools/pose-v1/RESUME-VIDEO-20261007.md)、[检查点](tools/pose-v1/evidence/video-sequence-20261007-r1/next-checkpoint.json)。新有限VPU API构建/27真实画面与54输入/协商通过，真实编码触发固件MMU ABORT（9提交/3归还/仅3部分帧），未动态验收。HDMI只读配套与离线1080p色条完成，真实时序/安全scanout仍缺证、未写入。会话全部关闭/认证前补查已取消；等待用户唤醒，无自动工作。首版估算78/100保持，新增故障不计功能份额。

> 最新授权：用户已审查H264样片，允许HDMI测试，撤销下方暂停。[下一视频计划](tools/pose-v1/NEXT-VIDEO-PLAN-20261007.md)先做真实骨架动态文件与HDMI配套核对，再1080p60实屏/RTSP/真实推理合并。当前仅整理计划，未新时序切换或板测，管理估算78/100保持。

> 当前最新：独立VPU H.264文件编码与Windows主机30帧解码审查通过，[样片/结果](tools/pose-v1/VPU-RESULTS-20261007.md)。720p10fps/3秒，原始/MP4两文件回传哈希及解码像素一致；没有实时NPU并发/RTSP/长期结论。用户接屏后将HDMI目标改为1920×1080@60Hz并暂停测试，硬件时序未修改。新[恢复点](tools/pose-v1/evidence/vpu-20261007-r1/next-checkpoint.json)，下方未编码/未接屏文字为历史。

> 当前最新：E1-C CPU渲染与三帧网络结果绘图已通过，[真实预览与结果](tools/pose-v1/RENDER-RESULTS-20261007.md)。V0确认了MVX多平面/NV12/NV21/H264枚举，尚未实际编码；HDMI未接屏、720p配套未确认。新[检查点](tools/pose-v1/evidence/render-20261007-r1/next-checkpoint.json)；下方E1-A/B入口按此前阶段理解。

> 当前最新：E1-A生产接口与E1-B TCP回放首批已实板通过，[38次全输出回归与网络结果](tools/pose-v1/APPLICATION-RESULTS-20261007.md)。接收→PS预处理→PS/NPU→完整候选结果已连通，尚缺骨架画面与HDMI/RTSP。新[恢复点](tools/pose-v1/evidence/application-20261007-r2/next-checkpoint.json)；此前P2恢复点按历史保留。

> 最新：用户已验收现有27样本数值阶段，P2单时钟定位与lazy-r4优化验证完成，处理核心基线5.24655Hz/P95 190.75409ms；正式应用、双路视频与长期闭环仍待。原query身份推断不改写，N2非阻断。旧N1/P1状态按此前日期理解。下一恢复点见[checkpoint](tools/pose-v1/evidence/perf-20261007-lazy-r4/next-checkpoint.json)。

</details>

用户确认当前异构方案完成首版全流程，零拷贝/图/新算子性能优化后置。[ADR_01](ADR/ADR_01.md)记录困境，[全流程计划](tools/pose-v1/FULL-FLOW-PLAN-20261007.md)明确接口→网络→渲染→独立视频→双路长期验收。原规划归档未计功能份额；现按已实测E1-A/B更新管理估计。

当前处于**真实异构推理→骨架→有限同进程常驻编码已核验，本轮启动三次回归通过，准备在线RTSP合并**的阶段。
E0/N1/P1、H0、P2、E1-A/B/C已完成工程门检，全部会话关闭；V0只完成部分配套核对，后续按独立编码/视频与双路长期门检推进，候选身份诊断非阻断。

## 完成了多少

以已批准的“原始CSI回放→Lite PS预处理→PS/NPU推理→14关节骨架→1080p60 HDMI＋H.264 RTSP”首版为范围，HDMI按用户最新要求暂停、目标替代原720p60，H264独立分支仍720p10fps。
**工程就绪度粗估约80%（81/100）**。这是下面工作包加权的规划估计，不是实测工作量、剩余工期、比赛评分或功能通过率。
基础平台和推理难点已取得实测成果，后续未知数据、整机性能和视频闭环仍需要验证；该估算不表示剩余工期。

| 工作包 | 规划权重 | 已具备份额（估计） | 当前事实与尚缺内容 |
| --- | ---: | ---: | --- |
| 平台与工具链 | 15 | 15 | SD启动/扩容、SSH历史通信、FPAI编译、Procise流水灯与IP交接、Lite运行身份已验证；完整显示配套另列 |
| CSI契约与PS预处理 | 15 | 15 | 九组300份真实窗口跨主机/Lite逐位一致，非法输入拒绝；人工±π仍保留失败诊断，不扩展为任意输入通过 |
| 首版模型与参考环境 | 10 | 9 | 2024 epoch442/固定ONNX/ZG/RAW与隔离ORT环境保持；27份参考核验完成，不扩大为未知数据精度通过 |
| PS/NPU混合运行 | 20 | 18 | 无固定Tokens依赖的生产入口与验证入口8次全输出回归通过；网络3/27帧真实前向通过，长期应用仍待 |
| 部署数值验收 | 10 | 9 | 现有27样本阶段由用户明确验收；原误差保留，query身份未证，不推广至未知数据 |
| 正式应用与性能 | 10 | 7 | 网络结果及CPU画面接入通过，27帧ARM渲染/三格式逐位一致；核心短期5.25Hz保持，整机争用/吞吐与长期仍待 |
| HDMI、编码与RTSP双路 | 15 | 8 | 真实27骨架/54帧VPU与重复通过，独立RTSP200帧和标准播放器100帧通过；实际推理有限工作者32前向/987编码及本轮三启动通过，在线合并/色彩标记仍待，HDMI1080p60配套及实屏未通过 |
| 长期运行与交付验收 | 5 | 0 | 30分钟闭环、端到端性能、异常恢复演示及最终交付材料仍待 |
| 合计 | 100 | 81 | 粗略表达为约80%，只用于管理；历史58/64/69/72/75/78分保留，不是工期/比赛评分 |

上述份额是本次整理采用的主观估算，后续按验收成果更新，不因新增文件或重复实验自动增加。
更广义的最终比赛作品还涉及真实采集设备、同步和新场景验证；回放首版尚不代表实时感知作品完成，当前未给最终作品单独估算百分比。

## 已验证、待验证与旁支研究

**已验证的主链成果：** 平台可启动、工具可构建；300份真实CSI预处理一致；CPU最小适配107例/12注册/22输出59,600个FP32逐位一致；
r6混合图在308/309/310及同Session重复308上有效响应，三帧输出不同、重复首帧全部捕获及输出一致。
原1173 HardOp由七个ZG实际执行组完整追溯，六计算Host保留；Matmul仍由NPU执行。

**已解决的主要阻断：** 环境和清单问题、CPU算子注册/全有效布局受限适配、Session融合映射核验，以及跨帧旧计数导致读旧结果。
r6使用官方SDK状态清理`reset(1)`，执行前确认0、输出就绪及最终745后才进入下一帧。745是当前固定图的验收基线，不能推广到其他模型。

**数值阶段与适用范围：** 现有27样本由用户明确验收，完整误差保留。S52_18_317离群帧支持排名交换推断，跨端query身份仍未证明；不推广为未知数据、MPJPE或物理标定通过。

**尚未通过的验收：** 实际推理与VPU/RTSP合并、HDMI、整机吞吐及30分钟闭环未通过。CPU骨架绘图与格式正确性已核验，绘图约12ms、同时生成三种诊断格式约89ms尚须按真实输出与工作者方案测争用；lazy-r4的5.24655Hz仍为独立短期核心计量。此前4.65420Hz作为历史基线保留。

**算法旁支单独记录：** 2026版迁移10轮已结束，最佳122.873804mm相对24版123.085352mm改善约0.212mm，不能认定稳定收益；
全新500轮实验在第6轮分支退化停止，未完成500轮；零衰减10轮完成，但后期分化/细化注意力抽检梯度仍为0。
这些实验已归档并保持停止，首版部署继续使用2024 epoch442；不把训练实验数量累计成板端系统进度。

## 当前任务完成位置与下一步

E0/N1/P1＋H0、P2及首批E1-A/B均已完成；当前应用依据为[E1结果](tools/pose-v1/APPLICATION-RESULTS-20261007.md)与[完成证据](tools/pose-v1/evidence/application-20261007-r2/completion-review.json)，独立[P2性能基线](tools/pose-v1/P2-RESULTS-20261007.md)与[r2扩展数值结果](tools/pose-v1/RUNTIME-RESULTS-20261007.md)保留。

| 阶段 | 最新状态 | 尚未通过的边界 |
| --- | --- | --- |
| E0运行核心 | 原核心证据保持，新生产/验证两入口8次与r6逐位一致 | 生产入口无冻结参考依赖；未知数据分布精度和长期应用仍待 |
| N1九组扩展 | ORT27独立核验、Lite28次、476捕获/CPU364000值与全误差报告完成；用户明确验收 | query身份未证明，不推广至未知数据或MPJPE |
| P1/P2性能 | profiling关闭、单时钟分段与消息构造优化；Host107/原样本回归通过，30计量5.24655Hz | 仅处理核心短期基线，未包含网络/渲染/编码或30分钟 |
| H0/V0/V2部分配套 | 源拓扑/显示符号、MVX实际planes/stride/色彩协商/30帧H264及主机解码通过 | HDMI1080p60时序/换帧未确认，用户已允许测试；H264时间戳/VUI与RTSP待接，关节名称/标定未知 |
| E1应用与双路输出 | 生产接口/TCP与CPU绘图连通；27静态ARM画面、三帧新推理绘图、独立有限编码通过 | HDMI/RTSP及实时合并/最终闭环未完成；有限CLI不是长期服务 |

下一批按[新视频计划](tools/pose-v1/NEXT-VIDEO-PLAN-20261007.md)封装有界VPU接口，使用真实预生成骨架帧、确认capture时间戳与H264色彩信号并接独立RTSP，再按工作者方案合并真实推理，测关键路径/CPU-DDR争用/过载。HDMI已接屏且测试允许，先匹配当前BOOT时钟/scanout/换帧与1080p60目标，再实屏、双路与30分钟。N2非阻断、深度优化后置。
新恢复点：[video-next-plan-20261007.json](tools/pose-v1/evidence/video-next-plan-20261007.json)。此前检查点保留为历史，不重复执行已完成阶段。

## 项目文件导航

| 位置 | 用途 |
| --- | --- |
| [PROJECT-PROGRESS.md](PROJECT-PROGRESS.md) | 全项目当前阶段、估算口径和验收差距；首先阅读 |
| [Done.md](Done.md) | 已完成开发/验证及历史失败修正，保持“工程内容总结＋后续开发参考”模板 |
| [ToDoLists.md](ToDoLists.md) | 当前任务顺序和未完成清单，包含暂停与批准边界 |
| [Agents.md](Agents.md) | 执行权限、历史批准范围、停止条件 |
| [REFERENCES.md](REFERENCES.md)／[ADR_00](ADR/ADR_00.md)／[ADR_01](ADR/ADR_01.md) | 资料索引、首版架构/验收目标、当前异构取舍与延期优化 |
| [最新检查点](tools/pose-v1/evidence/render-20261007-r1/next-checkpoint.json) | CPU骨架画面完成、V0查询与后续编码/HDMI配套边界，旧入口保留 |
| `software/pose_v1` | 预处理、已验证检查器、CPU适配与新隔离运行核心；源码不等同验收 |
| `tools/pose-v1`／`evidence` | 准备/构建/审查工具、命令说明和实际证据；旧r1–r5为历史 |
| `.local` | 隔离Conda、模型样本包、构建副本和完整生成物，保留身份，不覆盖旧产物 |
| `FPGA` | 流水灯及IP交接工程；不是已完成的AI＋HDMI系统工程 |
| `tools/pose26-*` | 独立算法实验及停止结果；本轮不恢复训练 |
| `Logs` | 用户日志存放入口；实际验收仍引用各阶段完整evidence |

本次采用总览、恢复入口和历史折叠整理，不移动、删除或重命名已有工程、模型、构建和失败证据。

主要依据：[300份PS结果](tools/pose-v1/RESULTS-300.md)、[CPU结果](tools/pose-v1/CPU-ADAPTER-RESULTS-20261006.md)、
[r6实板结果](tools/pose-v1/MIXED-FRAME-STATE-R6-RESULTS.md)、[r6完成核验](tools/pose-v1/evidence/mixed-20261006-frame-state-r6/completion-review.json)、
[新核心构建核验](tools/pose-v1/evidence/runtime-20261006-r1/build.acceptance.json)、[原暂停检查点](tools/pose-v1/evidence/runtime-20261006-r1/pause-checkpoint.json)。

2026-10-07新增依据：[完整结果](tools/pose-v1/RUNTIME-RESULTS-20261007.md)、[误差报告](tools/pose-v1/evidence/runtime-20261007-r2/ONNX27-comparison.json)、[性能基线](tools/pose-v1/evidence/runtime-20261007-r2/P1-performance-analysis.json)。

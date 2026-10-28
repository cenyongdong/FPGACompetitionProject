# HDMI交接与恢复入口

## 当前入口（整理于 2026-10-28）

**最新本地交付：TopK=1、无置信度阈值启动包已完成，尚未部署或实板测试。** [启动包](../../Deliverables/pose180-top1-no-threshold-20261028-r1.tar.gz)（30,687,380 字节）、[SHA256](../../Deliverables/pose180-top1-no-threshold-20261028-r1.tar.gz.sha256)及[使用说明](../../software/pose180_pipeline/resident/STARTUP-PACKAGE.md)。包内独立携带原 epoch99 JSON／RAW、ARM64 程序、PC 观察端、核心源码及同一合格 BOOT 备份，不依赖旧测试包目录；手动启停，不安装 SDK 自启动或自动重试。程序 SHA256 `0a7b0b93632f9ec0524da38a30b73acd46f03c9fede4c883af57584a806b5721`；完整交付身份见[package.json](../../.local/pose180-top1-no-threshold-20261028-r1/package.json)。

本地后处理／HDMI／显示状态／缓冲／日志检查通过；无阈值 mock 完成 30 次推理，PC 六项检查及实际解包观察端的低分／零分／负分接收通过；正常停止与异常后重试保护通过。压缩包内源码另行解出后，以现有工具链重新编译 `pose180_demo` 成功。精确原值见[验证目录](../../.local/pose180-top1-no-threshold-20261028-r1/verification.json)和[解包重建](../../.local/pose180-top1-no-threshold-20261028-r1/source-check.json)。这些结果不替代无阈值实板验证；下方设备结束状态和遗留远端收尾保持。

**最新状态：用户要求结束测试，当前原 epoch99／TopK=1／严格 score >0.2 测试已安全退出；随后设备以太网断开，不自主重连或续跑。** 最后新包 `.local/csi-open-space-top1-020-20261027-r4` 完成 8344 次新推理／HDMI 采纳／PC 接收，最后 SSH 状态证明 native_exit=0、完整 SDK／HDMI 关闭、设备占用为空，PC／串口观察已退出。进程总时长 605.508 s 包含初始化／退出，按用户停止而非完整处理期验收；原时长／停止原因门 `passed=false` 保留。最后核验 boot_id `3c398048-a8b7-4225-b6c1-c57a9735940e`、合格默认 BOOT 不变，断开后的实时状态未知。

**待收尾（不需要新 SDK 或重启）：** 当前包远端取消关闭回执未写成，临时板端 `.50.49/24` 地址未能撤销／核验；TX／RX3 临时 LAN SSH 未能恢复原禁用设置；六个已关闭旧包及本包的完整原生证据归档尚未取回，文件仍保存在各板端目录。不得把这些动作写成已完成；待用户重新连接后再处理，不为取证自主重连。当前启动文件在本轮启动后已经恢复为同一合格默认镜像，不需要降级到历史参考位流。

[最后已观察安全停止](../../.local/csi-open-space-top1-020-20261027-r4/results/summary.json)、[原始 SSH 状态回执](../../.local/csi-open-space-top1-020-20261027-r4/results/last-observed-native-outcome.json)、[具体待办](../../.local/csi-open-space-top1-020-20261027-r4/results/pending-cleanup.json)及[全部实时测试](../../software/pose180_pipeline/resident/CSI-INTEGRATION-20261027.md)。原图恢复后的 r3 完成完整有限测试和模型 SHA／加载路径核对；新 epoch130 图已转换及有限实测，现场效果相近或更差，未认定精度改善，候选独立保留。

**此前完整有限验证：自适应实时 CSI 已接入七色条／v5 系统并完成修订后实板连续性复测。** 当时 boot_id 为 `ad98882f-5b4d-4860-9516-31f148b3e826`，合格默认 BOOT 内容不变；当前已验证软件选择见 [default_boot.json](default_boot.json)。此前两包均已关闭，SDK／HDMI／PC 负载及临时采集地址已释放；原预处理保持，精确结果、首轮坏记录及恢复见[实时集成记录](../../software/pose180_pipeline/resident/CSI-INTEGRATION-20261027.md)。此前启动身份均作历史保留，当前身份以上方暂停状态为准。

**最新发布：用户已要求将已合格 `probe-free-drain-filter-v1` 设为默认启动位流，并选择软件七色条待机。现已安装、启动验证及最终写回核验；当前运行和下次启动均为这份位流，原参考 BOOT 仅作为恢复备份保留。** 七色条在显示服务完成初始化后、第一份推理结果前显示，随后切回原骨架场景；不是 FPGA 上电即显示，也没有设置 SDK／推理开机自启。具体发布记录见下节，机器可读选择为 [default_boot.json](default_boot.json)。

**用户已暂停布线并取消本轮新增 PL 开发，全部本批实现进程已停止，无后台续跑。** `.local/pose-post-integration-20261027-r1` 仅保留未完成实现及检查点，没有物理资格、新 bit／BOOT 或该候选的 SDK／启动，不得作为部署候选。v5 设计与离线结果见[实施记录](../../software/pose180_pipeline/resident/PRESENTATION-20261026.md#2026-10-27v5-后处理与已取消的-pl-扩展)；随后已编译匹配下表既有合格硬件 profile 的 CPU 候选，并完成新参数板测。新增 PL 不自主恢复。

当前阶段为[官方训练／测试集演示](../../software/pose180_pipeline/resident/DATASET-DEMO.md)：本地输入、实时入口关闭、两端 UI 不变。最新 v5 PS 参数为 **0.5／0.3／1**；六片段 HDMI／PC 同时实测完成 3024 次新推理，复用下表合格位流。`.local/pose-demo053-*` 共七个有限包（含首次 PC 观察器失败及独立补测），每包实际 1 候选／1 SDK／1 原 BOOT 回退，全部关闭、余额 0。此前 `.local/pose-dataset-*-20261027-r2` 两包的 46／287 次结果仍保留，不与新参数结果混算。

此前六片段阶段最后实际回退原 BOOT，身份 `73197d05-0e84-422d-9733-c5b0a8205443`；该历史结果与关闭证明见[数据集实板记录](../../software/pose180_pipeline/resident/DATASET-DEMO.md)，不再代表下节发布后的当前启动文件。下次仍须核对实时设备身份，不直接复用旧身份或已关闭包。

| 版本／用途 | 当前资格与选择边界 | 产物／证据入口 |
|---|---|---|
| 原参考 BOOT | 保留的恢复备份，已由下方合格版本替换为默认启动；不删除历史身份 | 下节恢复资产 |
| r45 完整诊断基线 | 原物理资格及历史板测保留；匹配旧准入 | [r45 物理结果](../../tools/pose-v1/evidence/hp2-deferred-consume-20261024-r45/RESULTS.md) |
| `probe-free-drain-v1` | 去旁路诊断／协议 IP，保留主动消费；物理资格与有限真实闭环已验证 | [独立工程及结果](probe_free_drain/README.md) |
| `probe-free-drain-filter-v1` | **当前默认启动选择、本轮最近核验运行位流**；实际 100 MHz，4 路滤波保留；软件默认 PS 0.5／0.3／1 | [物理与板测](../../software/pose180_pipeline/resident/PRESENTATION-20261026.md#pl-计算与资源)；构建 `.local/pose-filter-integration-20261026-r2`，其 `boot-package/` 与 `reports/qualification.json` |
| `tracked-one-euro-v5` 软件 | PS 0.5／0.3／1、输入前七色条；自适应真实 CSI 集成和有限连续性复测完成，PL 调用为 0；防闪现观感仍开放 | 最新构建 `.local/csi-integration-20261027-r2/arm64/pose180_demo`；[实时结果](../../software/pose180_pipeline/resident/CSI-INTEGRATION-20261027.md)；下文发布及此前[六片段实测](../../software/pose180_pipeline/resident/DATASET-DEMO.md)保留 |
| `pose-stabilizer-offline-v1` 精简守卫 | 覆盖缺口仍在，**不可部署**；不是上述已测保留消费候选 | [离线阶段结果](pose_stabilizer/README.md) |
| 心率 PL 覆盖层 | 核与 OOC 完成，无整机实现／板测，不属于当前合格位流 | [专项状态](../../software/vitals/HYBRID-20261026.md)、[PL 核](../vitals_acf/README.md) |

恢复时先核对实际设备、BOOT／软件 profile 与安全停止状态，再选择独立新包；必要板测、重启及回退按[自主授权](../../Agents.md#自主权限与重大问题)执行，不复活旧次数。复用路由器开机服务，不并行启动旧无线负载。原 BOOT 文件恢复与实际回退启动分别核验；PL_KEY1 运行中复位恢复未通过，不能作为常规恢复捷径。无 RTL／约束变化不重复整机构建。

## 2026-10-27 默认启动发布与七色条

本批 `.local/hdmi-startup-20261027-r1` 复用既有物理资格，没有 RTL、频率、约束、模型或 SDK 变更，也没有新增 EDA。默认 BOOT 为 `.local/pose-filter-integration-20261026-r2/boot-package/BOOT-pose-filter-r2.bin`，SHA256 **`a22faaa71cfde653e03898d2d77bd3adee633f3d0b47b710b87c76bf2a22e291`**。当前运行 boot_id 为 **`ba3327af-25df-4425-9b1b-0d4d34aaf4f0`**；新软件 SHA256 `129beb8feb92882e17640dcd7a49a2328f8a46c1da6a2186ec78a66d5a6026ee`。

`hdmi_renderer.cpp` 在首次结果前绘制 1920×1080 全高七色条，顺序为白、黄、青、绿、品红、红、蓝，采用原 RGB565 帧通道；没有骨架或伪造结果。主线程先以独立 tag 提交待机并取得原采纳证明，再开放本地数据集输入。收到结果后恢复原画面；结果后的漏检／重同步提示、PC 页面及蓝色骨架保持。原生像素、等待／恢复、提交标签与计数测试通过；ARM64 Release 编译通过，仅有既有 raster565 符号比较警告。

实板使用官方 test／S11_02 的 49 个 CSI 样本，保持 PS 参数 0.5／0.3／1，同时开启 HDMI／PC。启动前主动消费 **6 拍**异常返回，安全终态后初始化 SDK；没有恢复协议检查 IP。HDMI 先接纳 `tag=1、has_result=false` 的待机，再完成 **49 次新推理／49 次结果接纳**，显示更新合计 50；PC 原始及派生各接收 49 帧，候选／源身份一致。没有输入替换、过期或记录丢弃；EOF、`native_exit=0`、tagged STOP 和帧释放完成，设备占用为空，内核日志无新增。未取得新的实屏人工确认，不把采纳证明写成实屏观感验收。

实际 **1 次候选启动、1 次 SDK、0 次参考回退启动**；BOOT 文件写入 3 次：安装候选、测试期间恢复参考文件以备故障恢复、验证安全结束后再次安装同一候选为默认。最终卸载分区后独立读回全部 BOOT，确认其它启动文件未变。当前运行位流来自本次同一候选启动，最终写文件不宣称又进行了一次启动。包已关闭，所有剩余次数为 0，串口／PC 观察及构建容器均退出，没有后台推理。

原参考恢复文件保存在本机 `.local/hdmi-startup-20261027-r1/board-bundle/common/BOOT-original.bin` 和板端 `/root/demo-v1-20261022-r1/hdmi-startup-20261027-r1/common/BOOT-original.bin`，SHA256 `ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef`。历史参考包未改。启动消费仍是同次配置一次性行为，下一次 SDK 验证使用新包和新启动，不在本包重复初始化。

[汇总](../../.local/hdmi-startup-20261027-r1/results/summary.json)、`results/promote.json`／`closed.json`／`final-audit.json` 及 `round-1-result-evidence.tar.gz` 保留实际默认文件、启动、消费、待机和安全结束证据；`pc-observation/` 保留本轮原始／派生输出。`run_release.py` 仅为已关闭本批执行记录，不直接重跑。

后续 `prepare_presentation.py` 默认读取 `default_boot.json` 选择合格硬件及当前已安装 BOOT 作为新包的参考／回退基线，避免普通测试隐式退回旧参考版本；必要时可显式 `--reference-boot` 指定已核对备份。本机新包准备已验证默认哈希／profile 一致，检查包 `.local/hdmi-startup-next-package-check-20261027` 未部署或运行。原参考备份不因更新新包基线而覆盖。

## 历史状态摘录

以下“当前／最新／暂停”等词均指记录当时；其启动身份、额度和阶段结论不覆盖上面的当前入口。原始失败与包关闭状态保留。

2026-10-26 本轮恢复：[展示精简、后处理复验和 PS／PL 滤波比较](../../software/pose180_pipeline/resident/PRESENTATION-20261026.md)。CPU 显示包已关闭，原 BOOT 实际回退通过；新增 PL 流水线候选已完成物理资格及有限板测，原 BOOT 实际回退通过、全部关闭、无后台负载，下一步依据该记录，勿复用下述旧包。

2026-10-26 较早状态：追加 r3 已结束，首轮 PL_KEY1 运行中复位后黑屏失联，完整断电恢复；后两轮各 300 秒及现场画面确认通过，其中第 2 轮 SDK 前有界消费 16 拍返回后正常运行。最终已回原 BOOT，启动编号 `7170b447-f844-421f-b5d6-36140b450e1a`；全部新包关闭、余额 0，无本批活动负载。按键恢复仍未解决，r1／r2 不复活；[唯一结果与产物入口](probe_free_drain/README.md)，精确状态见 `tools/pose-v1/evidence/hdmi-probe-free-drain-20261026-r3/state.json`。

2026-10-26 当前专项已完成：[去除诊断、保留异常消费的 r45 派生候选](probe_free_drain/README.md)。完整物理资格及三轮各 5 分钟真实全链路测试通过，原 BOOT 文件和实际回退启动均已核验，三包关闭、无本批后台工作。产物、精确结果、恢复身份和限制统一见该记录；日志位于 `tools/pose-v1/evidence/hdmi-probe-free-drain-20261026-r1`，运行资产位于 `.local/hdmi-probe-free-drain-20261026-r1`。不复活下述历史额度或独立暂停任务。

2026-10-26 心率专项恢复：[PS 流式模块与实采](../../software/vitals/HYBRID-20261026.md)、[小型 PL 自相关核](../vitals_acf/README.md)。已完成 OOC／仿真和保留全部 r45 保护的独立覆盖层，未生成新整机位流或上板；HDMI／旧问题恢复边界仍按下文。

最新离线工作：[防闪现后处理与精简硬件](pose_stabilizer/README.md)。软件CPU后端、派生展示、1／4路RTL及OOC比较已完成；LUT预算与精简守卫覆盖缺口如实保留，未生成候选位流或部署。板端暂停与r12恢复边界不变；后续不将该覆盖层直接用作启动位流。

前一批次：[r6持续TX租约](../../software/pose180_pipeline/resident/TX-LEASE.md)已按1候选／1 SDK／10分钟／1原BOOT回退完成并关闭，全部余额0、无本批负载。该批原BOOT身份、恢复证据及剩余卡顿以r6记录为准；下述r5及更早状态保留历史，不复用旧额度。

上一批次：[r7共同窗口优化](../../software/pose180_pipeline/resident/WINDOW-RECOVERY.md)已执行并关闭，1候选／1 SDK／600秒运行期／1原BOOT回退，全部余额0、无本批负载；该批原BOOT身份及实际结果以r7记录为准。无窗恢复等待已缩短，显示器黑屏／闪屏已按用户确认的[显示规格限制](../../software/pose180_pipeline/resident/WINDOW-RECOVERY.md#显示规格限制)移出待定位故障。必要新验证可按[最新自主板测规范](../../Agents.md#自主权限与重大问题)另记新批次直接执行，不复活旧包。

当前最新批次：[r10／r11／r12](../../software/pose180_pipeline/resident/TOP3-VALIDATION.md)。r12有限推理及PC接收验证完成，随后用户关闭板端并要求暂停工作。原BOOT文件已恢复，但未执行回退启动核验；本机观察进程已结束，无本批活动负载，不自动恢复。实际次数、身份、未取回证据及恢复边界以该记录为准。

2026-10-25较早批次：[r5卡顿优化与PC联合长测](../../software/pose180_pipeline/resident/STUTTER-VALIDATION.md)已完成30分钟、RX物理恢复及PC离线实屏验证，正常停止、回原BOOT并关闭。实际1候选／1SDK／1回退，全部余额0；无本批活动负载，该批恢复身份与原值统一见r5记录及本机`.local/pose180-resident-stutter-20261025-r5/run-state.json`。r4及更早包均保持关闭。

2026-10-25新决策：[ADR_50](../../ADR/ADR_50.md)已批准端到端演示优先、有界缓存、PC／归档解耦及分级恢复，无需严格30Hz。实现与本轮真实CSI→推理→HDMI有界结果见[常驻演示记录](../../software/pose180_pipeline/resident/README.md)，用户已现场确认多轮骨架更新；最新包状态与恢复身份以该记录为准。下一步见[待办](../../ToDoLists.md)；下述旧包失败与关闭额度不回写。

2026-10-25较早严格主链实测：180-query新主链已部署；原BOOT有界测试止于Host归档1秒保护，修正后完成软件验证。新HDMI包`pose180-hdmi-20261025-r2`在SDK前因新增RCAM_UNDERFLOW状态未过准入，实际1候选/0 SDK/1原BOOT回退，已关闭、余额0；当前原BOOT、无占用及详细证据统一见[新主链实测](../../software/pose180_pipeline/RESULTS.md)。下述r53保留历史，不作为当前启动身份或新额度。

入口整理：2026-10-25。HDMI旧板测r53已回原BOOT；实际1次候选/1次SDK/1次回退，包关闭、余额全部0，批次结束时无本批后台工作。后续独立180-query批次的恢复见[部署实测](../../tools/pose180/deploy/RESULTS.md)；恢复时不能将历史运行身份视作实时身份。现行执行边界见[项目总览](../../PROJECT-PROGRESS.md)。

## r53历史核验状态与原始证据

| 用途 | 唯一维护入口 |
|---|---|
| 当前事实、恢复身份、问题及原始数据位置 | [r53 RESULTS](../../tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/RESULTS.md)、[state.json](../../tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/state.json) |
| 原BOOT运行、启动文件/SDK及无占用核验 | [final-audit.json](../../tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/final-audit.json)、[closed.json](../../tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/closed.json)；历史boot_id不得直接作为下次会话身份 |
| r53首读/即时副本/两轮SDK晚读和协议完整原值 | [candidate-evidence.tar.gz](../../tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/candidate-evidence.tar.gz)、[离线字节比较](../../tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/index-read-analysis.json) |
| 当前源码、硬件与数据流 | [INTEGRATION](INTEGRATION.md)、[r45硬件源码](diagnostics/deferred_consume_r45/sources)、[r53主调度](diagnostics/native_rgb565_r53/joint/main.cpp)、[SDK显示适配](diagnostics/native_rgb565_r53/display/hdmi_output.cpp) |
| 当前硬件物理资格与BOOT对应关系 | [r45 RESULTS](../../tools/pose-v1/evidence/hp2-deferred-consume-20261024-r45/RESULTS.md)；r46～r53复用，无重新EDA或新增时序例外 |
| 隔离/逐拍波形/原生协议历史 | [S01隔离](diagnostics/S01-ISOLATION.md)、[r30波形](diagnostics/waveforms-r30-20261022/README.md)、[r37协议结果](../../tools/pose-v1/evidence/hp2-startup-protocol-20261023-r37/RESULTS.md) |
| 实际异常消费后有限业务 | [r52 RESULTS](../../tools/pose-v1/evidence/hdmi-long-git-20261024-r52/RESULTS.md)；不以r53健康消费0的样本替代 |
| 完成、难点、下一计划 | [Done](../../Done.md)、[DIFFICULTIES](../../DIFFICULTIES.md)、[ToDoLists](../../ToDoLists.md) |

## r53 当时结论与执行边界

r53健康启动（AR=0/R=0、消费0），完成187次HDMI采纳后第189次推理首读索引1568字混入同帧姿态内容。晚读正确不能修补首读，产生环节未定；用户只见瞬间骨架，持续实屏和联合长期均未通过。

保留原有限消费及AI四路：HC0→HP0、HC1→HP1、HC2→HP2/S00、HC3→HP3；HDMI→HP2/S01。官方说明HP FIFO位于PL，撤下PS内部HP FIFO残留的既定解释；D45根因未关闭，文档任务不恢复已中止的根因板测。

所有旧包保持关闭；新增BOOT/重启、失败SDK负载再执行按具体新包授权，不复活旧次数。旧DATA独立暂停，不删模块、不修FAT、不改模型/数学/SDK/NPU分配/帧协议，不接入Vivado MCP。SSH为主、COM7备用，未来操作前重新核验实际身份与恢复通道。

正确按键为PL_KEY1/SW6/F8；PL_KEY2/SW7/E7用于SDI GTX。观测器清零、PL互联复位、宏内部事务状态分别认定。旧r26与10月18日暂停报告保留历史，不作为最新状态或新操作授权。

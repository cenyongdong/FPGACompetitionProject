# 项目进度总览

更新：2026-10-25。**180-query主图及有界完整回传已部署实测，稳定性尚未通过。** 原BOOT测试取得完整有效输出后触发Host归档1秒保护，NVMe及预写修正已完成软件验证；获准的新HDMI包在SDK前因启动准入失败停止，已回原BOOT并关闭。继续主机模拟输入，暂不接CSI实采；[本轮结果与恢复](software/pose180_pipeline/RESULTS.md)为唯一详细入口。

180-query迁移最佳模型已完成训练、转换及独立部署；30分钟124,518次新推理在获准忽略误差的范围内正常结束，数值精度及耗时长尾仍未验收。真实CSI已完成1发3收共同事件采集和软件对齐；无PC板端候选仅完成软件验证及ARM64编译，尚未实板。HDMI历史r53及本次180-query新包均已关闭，当前原BOOT运行；持续实屏和联合长期未通过。各分支证据及恢复入口见下表，不将历史独立验证合并为整机验收。

架构按[ADR_49](ADR/ADR_49.md)：PS＋NPU感知，PS绘制本地骨架帧，PL读帧并输出HDMI，PC独立3D展示；未来正式主链停用VPU／RTSP，旧演示保留。10月25日用户进一步明确采集／推理正式链不经过PC，路由器直接进入开发板；PC展示与开发诊断的角色分别保留，实施边界见[板端候选](tools/nexmon/board/README.md)。

## 已完成内容与验收范围

| 模块 | 已完成 | 当前边界与资料 |
|---|---|---|
| 预处理与混合推理核心 | 固定输入预处理、CPU算子注册和NPU执行链已验证；共享FP16候选按现行数值门禁获阶段认可 | 模型／RAW、数学、SDK及NPU分配保持；范围见[ADR_48](ADR/ADR_48.md)、[核心说明](software/core/README.md) |
| 180-query主推理图 | 迁移最佳epoch99转换及历史独立压测完成；新主链已接入该图、固定池、入口信用和PIWFUL3完整回传，软件验证及ARM64编译完成 | 新主链已有部分实板完整输出，Host归档修正未重新实板验证；HDMI启动准入未过，D48数值与长尾未验收。[本轮实测](software/pose180_pipeline/RESULTS.md)。[主入口](software/pose180_pipeline/README.md)、[原独立部署](tools/pose180/deploy/RESULTS.md)、[训练快照](tools/pose180/STATUS.md) |
| 独立共享模型稳定性 | 10月15日完成30分钟、62,945次串行推理，数值与内存／句柄观察通过 | 有D41时延长尾；该历史配置没有叠加HDMI，不能替代当前联合长期验收。[阶段记录](ADR/ADR_48.md#2026-10-15后续独立实板与30分钟验证) |
| HDMI构建与显示 | 原厂适配工具路线、真实波形与完整160位协议检查已接入；r45完成合格bit/BOOT，r46～r53复用 | 原AI两项Min Period例外保留，无新增例外；D44/D45未关闭。[物理结果](tools/pose-v1/evidence/hp2-deferred-consume-20261024-r45/RESULTS.md)、[当前结构](FPGA/hdmi_candidate/INTEGRATION.md) |
| 新推理到HDMI | r40健康启动90帧有界联动和现场更新通过；r52真实异常消费16拍后同启动完成90次采纳及数值门检 | r52吞吐积压；r53数值错误停止，用户仍只见瞬间骨架，联合长期未通过。[r52](tools/pose-v1/evidence/hdmi-long-git-20261024-r52/RESULTS.md)、[r53](tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/RESULTS.md) |
| 启动故障诊断 | 视频源端隔离后仍复现；r37抓到AR=0时早期RVALID及原生协议报警，r46/r52同启动有限消费16拍 | 缓解不等于根治；保留历史报警，检查器独立重置后fresh160准入，AI四路未改。[协议原值](tools/pose-v1/evidence/hp2-startup-protocol-20261023-r37/RESULTS.md)、[消费规则](FPGA/hdmi_candidate/diagnostics/mmio32_r46/README.md) |
| HDMI PS渲染与调度 | 直接1080p RGB565，扩大视口且骨架/标注大小保持；r47 CPU绘制/转换140.694→3.225ms；r51静态准备重叠、r53单SDK线程流水 | CPU收益和短样本29.521Hz分别认定，r53未成为稳定默认版本。[渲染](tools/pose-v1/evidence/hdmi-render-speed-20261024-r47/RESULTS.md)、[流水边界](tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/RESULTS.md) |
| PC骨架传输与实时3D | `demo_v1`以论文复数CSI窗口作输入，完成实际新推理、完整回传与实时Three.js；短测和52,800窗有界验证完成 | 无真实无线直采、无HDMI；严格逐帧时限仍未通过，D47未根治。[新链路与实测](demo_v1/RESULTS.md)。原60帧历史分支保留在[回放观察台](software/pc_viewer/README.md) |
| 纯PS离线动作与求助原型 | 独立C++17状态机、监测状态及虚拟时间PL反馈完成；原始包／97,770份标注／训练链核查、36项合成检查和15,648份结果回放通过 | 确认14×3、米制及训练保留索引；解剖索引、物理up、原动作时间及目标身份仍未核实，真实动作未知。无新推理或硬件操作。[实现及验证](software/pose_events/README.md) |
| 真实CSI采集 | 1发3收共同事件采集、固定网格软件对齐完成；四机角色及地址已保存 | 严格共同窗口345/402（85.82%）；稳定300Hz、相位、节点幅度及人体效果未验收，model_ready=false。[采集与恢复](tools/nexmon/README.md) |
| 无PC板端采集／推理候选 | C++三流接收、同帧组窗、原预处理及180-query SDK包装完成软件验证与ARM64编译 | 尚未部署或执行实机SDK，仅支持单次有界任务；三节点幅度配置未填，常驻及HDMI未接入。[软件候选](tools/nexmon/board/README.md) |
| 心率独立参考 | C++参考、合成验证及历史Nexmon的50Hz诊断适配完成 | 缺40秒连续合格真实数据及同步生理参考，真实心率未验收；不占主链关键路径。[模块状态](software/vitals/README.md) |
| 旧VPU／RTSP演示 | 原预采CSI有界网络演示和相关代码、失败证据保留 | 属于历史分支，不再作为新展示主链的必做路径。[历史演示](software/demo/README.md) |

各项成果按发生时配置分别认定；历史回放、一次新推理、启动可靠性和连续长期互不替代。完整阶段记录见[Done.md](Done.md)。

## 主要难点与下一步顺序

- **D47是HDMI旧链恢复联合验证前的正确性问题。** r53第189次首读的1568个索引字逐位等于同帧姿态同偏移，晚读正确；不能据此归责HDMI仲裁或用晚值修补。后续需先核实公开SDK完成/可见性契约，见[r53实测、原值及恢复](tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/RESULTS.md)。
- **D45根因仍开放，有限消费已有实测。** 隔离源端不能消除异常；r52同启动消费后90次合法采纳扩大了缓解证据，但未证明启动可靠性。官方说明HP FIFO位于PL，不能继续把“PS内部HP FIFO残留”当既定主要解释；当前不恢复已中止的根因板测。[官方资料判读](FPGA/hdmi_candidate/diagnostics/PROTOCOL-CHECKER-REVIEW-20261023.md)。
- **D46真实输入适配仍未完成。** 三独立接收节点已有共同事件软件对齐；仍缺稳定300Hz、相位及各节点幅度／模型适配和人体效果证据，不能把单节点经验尺度套给三节点或将对齐通过写成模型输入验收。[四机实测](tools/nexmon/evidence/multirx-20261025-r1/REPORT.md)。
- **D48新模型数值误差独立保留。** 180-query的无TopK独立压测不关闭D47，也不替代数值精度及严格实时验收。[部署实测](tools/pose180/deploy/RESULTS.md)。
- **D44、D29／D41及联合长期仍保留。** 首次reader失败根因、严格实时和长尾需分别验证；健康启动后的短时显示不等于长期稳定。

详细事实集中在[DIFFICULTIES.md](DIFFICULTIES.md)，后续验证顺序见[ToDoLists.md](ToDoLists.md)。本轮实测结果见[新主链实测](software/pose180_pipeline/RESULTS.md)；当前无后台负载，不恢复旧DATA及已中止的D45根因调查。

## 当前状态与执行边界

最新HDMI包`pose180-hdmi-20261025-r2`实际1候选/0 SDK/1原BOOT回退，已关闭、余额0；当前原BOOT、SDK及无占用核验见[本轮实测](software/pose180_pipeline/RESULTS.md)。r53等旧包继续关闭，不复活次数；未来板测重新核验实时身份并按具体新范围执行。

服务器上的180-query训练属独立模型分支；迁移已结束，从零训练与条件续训以[唯一恢复入口](tools/pose180/STATUS.md)中明确日期的快照为准，本轮未查询或操作训练进程。180-query候选未替换原100-query演示基线；demo_v1取证值属于此前有界验证。

用户10月22日随后批准D47两阶段有界隔离；一次静态和一次真实负载均已结束，预算内完成取证，两次额度耗尽并关闭，未追加负载或用晚值修补。保持BOOT／模型／SDK、不接HDMI，恢复仅见[demo_v1 state](demo_v1/state.json)。旧DATA独立暂停，不删模块、不修FAT、不接入Vivado MCP；HDMI长期仍需单独批准。

AI四路、模型/RAW、SDK、数学、NPU分配与帧协议保持。旧DATA独立暂停，不删模块、不修FAT、不接入Vivado MCP；新BOOT/重启或失败SDK负载再执行须按具体新包授权。无HDMI demo_v1的历史长测仍按原配置认定，CSI分支状态以[采集入口](tools/nexmon/README.md)为准。

## 资料与恢复入口

| 用途 | 唯一维护入口 |
|---|---|
| 当前阶段、完成范围与暂停边界 | 本页；执行规则见[Agents.md](Agents.md) |
| 下一步实施顺序及验收条件 | [ToDoLists.md](ToDoLists.md) |
| 稳定问题、已尝试方法及未知项 | [DIFFICULTIES.md](DIFFICULTIES.md) |
| 历史成果与原始结果 | [Done.md](Done.md)，各实验原始归档不回写 |
| HDMI接手、实际DCP／源码／BOOT及复核命令 | [工程师交接](FPGA/hdmi_candidate/HDMI-FAULT-HANDOFF.md)、[恢复入口](FPGA/hdmi_candidate/RESUME.md) |
| 本轮故障恢复状态及下一技术方案 | [180-query实测及恢复](software/pose180_pipeline/RESULTS.md)、[版本归档](software/pose180_pipeline/evidence/20261025/README.md)；r53等旧实验原值与关闭记录保留 |
| 真实CSI、PC展示与模型数值契约 | [Nexmon](tools/nexmon/README.md)、[PC观察台](software/pc_viewer/README.md)、[ADR_48](ADR/ADR_48.md) |
| 设备／SDK身份与原厂工具路线 | [HDMI交接第7节](FPGA/hdmi_candidate/HDMI-FAULT-HANDOFF.md#7-实际工程与产物定位)、[REFERENCES.md](REFERENCES.md) |

旧待办和历史计划只保留当时事实，不构成当前授权。历史原值优先读对应归档／Git历史；不通过重复构建、测试或新增文档数量累加完成度。

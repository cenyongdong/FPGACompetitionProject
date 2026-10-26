# 项目进度总览

2026-10-26 去探针／保留消费候选的追加三轮已结束：首轮运行中按 PL_KEY1 后黑屏失联，完整断电恢复；后两轮各 5 分钟通过并获实屏更新确认，其中第 2 轮 SDK 前实际消费 16 拍异常返回后成功运行。运行中按键恢复仍未解决，不能称三轮全部稳定。原 BOOT 实际回退已核验，全部新包关闭、无本批后台负载。[结果与当前恢复入口](FPGA/hdmi_candidate/probe_free_drain/README.md)。

2026-10-26 已完成[剔除 r45 诊断、保留异常消费](FPGA/hdmi_candidate/probe_free_drain/README.md)：综合、仿真、完整物理资格及三次独立启动、每轮 5 分钟真实全链路测试通过，正常停止并核验原 BOOT 实际回退，三包关闭、无本批后台负载。CSI 缺窗可自动恢复；未复现 HP2 异常，未作现场实屏确认。产物、精确结果和恢复身份以该记录为准，旧 DATA、姿态偏置及 D45 全面调查的独立边界保持。

2026-10-26 按用户要求整理并沿用[完整 HDMI 工程](Deliverables/HDMI_Complete_20261026/README.md)，包含真实 top、源码与父 BD，完整顶层综合及最终链接完成；复用同源合格 r26 位流进行四次软件重启，未复现 HP2 启动异常。原 BOOT 文件及运行回退均已核验，两批关闭；额外增量路由按用户要求取消，日志／检查点保留。当前板端状态、范围及限制以[实板记录](Deliverables/HDMI_Complete_20261026/board-validation/README.md)为准，未启动 SDK 或 HDMI 负载，不解除旧 DATA、姿态偏置及 D45 全面调查的独立暂停。

2026-10-26 按用户要求继续[心率模块开发](software/vitals/HYBRID-20261026.md)：完成流式 PS 算法、故障隔离、可选小型 PL 自相关核及有限真实 CSI 采集；尚未检出可信心率，该项未做新整机位流或上板。心率恢复入口以该记录为准。

更新：2026-10-25。**真实CSI→板端180-query新推理→HDMI有界闭环已跑通，用户现场确认能看到多轮骨架更新。** 按[ADR_50](ADR/ADR_50.md)实现常驻核心、最新窗口、有界记录、PC解耦和网络恢复；无需严格30Hz。完整结果、版本、资源、回退状态及证据只维护在[本轮实施记录](software/pose180_pipeline/resident/README.md)。

已完成原BOOT回放输入新推理、真实CSI接入与跨断流恢复，以及HDMI有限联合验证。软件故障注入和有界滚动整理通过；启动可靠性、全天无人值守和人体识别精度仍未验收。

最新按用户要求完成[四台CSI路由器开机自启动](software/pose180_pipeline/resident/autostart/README.md)，逐机重启、持续TX续期、三RX晚接入及接收端断开重连验证通过；当前保持启用。后续板测复用该服务，不并行运行旧无线load／guard。此项仅验证采集源，未新增板端SDK或HDMI运行。

持续采集守护、独立启停和日志上限已投入实测；此前[r5卡顿优化与PC联合长测](software/pose180_pipeline/resident/STUTTER-VALIDATION.md)完成30分钟运行期、RX1单路断线恢复、PC物理离线超过5分钟期间HDMI持续更新及PC自动恢复。已正常停止、回原BOOT并关闭，该批恢复身份、计数与证据见r5记录。普通秒级缺窗仍存在；问题1姿态偏置继续搁置，旧包不复活。

最新[r6持续TX租约实测](software/pose180_pipeline/resident/TX-LEASE.md)已完成获准10分钟运行、正常停止及原BOOT回退，包关闭、余额0。同一TX任务续期成功，新版HDMI外观获现场确认；仍有共同窗口缺失后的长停顿与自动恢复，整体卡顿尚未解决。该批恢复身份与精确结果以r6记录为准。

[r7共同窗口优化实测](software/pose180_pipeline/resident/WINDOW-RECOVERY.md)已完成600秒运行期、正常退出与原BOOT回退并关闭；真实结果覆盖约428秒，无窗恢复长间隔缩短至约3.1～3.2秒，缺窗仍存在。现场黑屏／闪屏已归入[显示规格限制](software/pose180_pipeline/resident/WINDOW-RECOVERY.md#显示规格限制)，不再列为待定位故障。r7历史身份及精确结果见其记录。用户已授权必要验证可自主上板、无需再次询问，现行边界见[规范](Agents.md#自主权限与重大问题)。

较早[r10／r11／r12验证](software/pose180_pipeline/resident/TOP3-VALIDATION.md)复用r45，r12完成2973次推理及PC结果接收。当时按用户要求关闭／暂停，原BOOT文件已恢复但尚未核验回退启动；当前板端状态见上方 2026-10-26 HDMI 实板记录。随后获准的[防闪现后处理、精简守卫与1／4路PL滤波](FPGA/hdmi_candidate/pose_stabilizer/README.md)已完成软件、离线回放、RTL仿真和OOC资源比较；该项没有上板或整机实现。两版LUT超预算，CPU为当前推荐，精简硬件保持不可部署。姿态偏置、旧DATA及D45全面调查仍暂停。

| 用途 | 唯一入口 |
|---|---|
| 本轮实现、实际闭环、限制及恢复 | [常驻核心与实测](software/pose180_pipeline/resident/README.md) |
| 当前技术实现总览与历史分界 | [ADR/TechDetails.md](ADR/TechDetails.md) |
| 当前架构及执行规则 | [ADR_50](ADR/ADR_50.md)、[ADR_49](ADR/ADR_49.md)、[Agents.md](Agents.md) |
| 下一步与验收顺序 | [ToDoLists.md](ToDoLists.md) |
| 稳定问题与历史成果 | [DIFFICULTIES.md](DIFFICULTIES.md)、[Done.md](Done.md) |
| 合格bit／BOOT、已有时序例外及HDMI恢复 | [RESUME](FPGA/hdmi_candidate/RESUME.md)、[r45物理结果](tools/pose-v1/evidence/hp2-deferred-consume-20261024-r45/RESULTS.md) |
| 旧严格主链、模型与CSI历史 | [旧主链实测](software/pose180_pipeline/RESULTS.md)、[180-query部署](tools/pose180/deploy/RESULTS.md)、[Nexmon](tools/nexmon/README.md) |

模型／RAW、SDK、原预处理、NPU分配、AI四路和帧协议保持。D45根因、旧D47和D48数值误差仍保留；旧DATA及D45全面根因调查独立暂停。未查询或操作训练旁支，不以本轮短时闭环改写旧失败，新的BOOT／重启／失败SDK重试仍按具体范围授权。

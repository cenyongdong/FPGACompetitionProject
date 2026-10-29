# Wi-Fi 人体三维姿态演示工程

截至 2026-10-29，项目已完成可部署的端到端演示：CSI 输入 → Lite 板端 PS 预处理 → NPU 姿态推理 → PS 后处理 → PL 本地 HDMI，同时向可选 PC 三维页面发送结果。实时采集与官方预采 CSI 两个接口均保留；当前交付默认在板端顺序读取官方单人、双人、三人片段。

**当前成果是有限实板验证完成的演示系统。** 全天稳定性、人体姿态精度、间歇性启动异常根因仍有未完成项，详见下列进度与困难记录。

## 从哪里开始

| 想了解的内容 | 入口 |
|---|---|
| 最终交付、已完成范围与验收边界 | [项目进度](PROJECT-PROGRESS.md) |
| 部署和现场操作 | [最终包部署说明](Deliverables/pose180-three-clips-20261029-r3-DEPLOY.md)、[当前设备与恢复入口](FPGA/hdmi_candidate/RESUME.md) |
| 一路遇到的困难、处理结果和遗留限制 | [困难记录](DIFFICULTIES.md) |
| 所有 Markdown 文档的位置、用途与历史属性 | [完整文档目录](DOCUMENTATION.md) |
| 当前源码如何组织 | [主工程](software/pose180_pipeline/README.md)、[核心模块](software/pose180_pipeline/src/README.md) |
| 系统架构、接口和资源生命周期 | [技术说明](ADR/TechDetails.md)、[架构决策](ADR/README.md) |
| 后续验证与冻结范围 | [保留边界](DIFFICULTIES.md#后续验证与冻结范围) |
| 历史成果与资料 | [Done](Done.md)、[REFERENCES](REFERENCES.md) |
| 提交用技术文档 | [技术文档完成版](Docs/提交资料/技术文档_完成版_20261029.docx)（本机文件，原模板保留） |

## 目录职责

| 目录 | 内容 |
|---|---|
| `software/pose180_pipeline/` | 当前 180-query 主链；`src/` 核心、`control/` 启停和输入准备、`host/` PC、`tests/` 测试、`tools/` 构建打包、`resident/` 使用与验证记录 |
| `software/core/`、`demo_v1/` | 早期共享核心与旧演示链，供历史复现和独立实验，不是当前主链的维护入口 |
| `FPGA/` | 已验证 HDMI 硬件、源码／约束、启动恢复、诊断和已取消扩展的历史记录 |
| `model/` | 原模型、转换产物及独立候选；当前选择由最终包身份和模型说明确定 |
| `tools/` | 开发工具、训练／部署与历次问题取证；旧 `NEXT`、`PLAN` 不代表当前待执行任务 |
| `Deliverables/` | 最新演示包、源码快照；旧软件与模型包在 `history/`，硬件交付在 `hardware/` |
| `Docs/` | 厂商资料与提交稿；`提交资料/技术文档_完成版_20261029.docx` 为本次完成稿，原模板和首版稿保留；早期选材清单不替代当前部署说明 |
| `ADR/` | 决策与技术说明；`history/` 保留文档原始快照 |
| `.local/` | 本机验证、清理清单及保留证据；不保证随 Git 克隆提供 |

执行规则见 [Agents.md](Agents.md)。文档中的历史启动地址、旧包额度和“下一步”均须按记录日期理解；当前操作只从上面的部署与恢复入口开始。

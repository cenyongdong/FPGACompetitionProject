# 2026-10-25阶段归档

结论集中维护于[本轮实测](../../RESULTS.md)，工程成果见[主入口](../../README.md)。本目录保存合并主分支所需的身份、实测原值和必要日志；不重新构建、板测或恢复已关闭包。整机稳定性、HDMI持续实屏及D48精度均未验收。

| 目录 | 内容 |
|---|---|
| `original-boot/` | 180-query原BOOT批次的完整归档检查、Host汇总、末帧原值核对、资源分析与软件包身份；`board-evidence.tar.gz`含原始SDK stdout/stderr、前后身份、资源采样、退出结果和末帧未确认拥有值；`host-metadata.tar.gz`含完整sent/received/交付时间记录及原始Host日志 |
| `software/` | 原始构建步骤、Native/ARM64与主机定向检查日志、C++→Node完整协议交叉结果；`checks.tar.gz`保留首个编译/分析失败及修正后的结果。NVMe的900帧mock和3.94GB writer结果仅为软件证据 |
| `hdmi/` | 新包启动准入失败、关闭状态和最终原BOOT/SDK核验；`board-evidence.tar.gz`含首次CSR、周期轨迹、原生协议窗口、授权与BOOT操作记录；`uart-evidence.tar.gz`含两次串口原始接收、标记证明和关闭结果 |
| `hdmi/execution/` | 本次新包的控制器和本机执行脚本冻结副本，配套依赖身份见`hdmi/manifest.json`。只用于复核，不能直接作为新包执行或恢复次数 |

[归档索引](index.json)记录阶段源码提交、模型/软件包身份、部署包既有哈希及大体积原值位置。584,424,960字节`actual.full`继续保留在原本机目录，已计算一次SHA256供以后身份核对；没有将该原值、模型、BOOT或部署大包再次复制进Git。原本机目录与旧失败现场保持。

原BOOT批次在最后一帧Host归档等待超过1秒后停止；新HDMI包在SDK前因消费前已出现bit79 `AXI_AUXM_RCAM_UNDERFLOW`停止，实际1候选/0 SDK/1原BOOT回退，全部余额0。归档中的`passed=true`只适用于对应解析或软件检查，不代表整机通过。SDK/BOOT恢复身份是本批关闭时快照，未来操作须重新核验。

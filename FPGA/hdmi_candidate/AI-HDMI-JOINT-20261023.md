# AI → HDMI 联合测试状态（2026-10-23）

最新（2026-10-24）：r40完成90/90新推理、完整保存与HDMI采纳，现场显示正常；数值和四路读事务通过。消费后恢复、旧偶发超时及持续5Hz仍未验收。以下保留r35/r36历史；当前结果见[r40实测报告](../../tools/pose-v1/evidence/ai-hdmi-timing-20261024-r40/RESULTS.md)。

**以下为r35/r36当时结果：没有通过联合测试。** 已完成最新软件链路接入与编译，但两次有界尝试没有产生新的推理结果或 HDMI 采纳帧。第二次在 SDK 加载前复现启动异常，已停止并恢复原 BOOT 运行。

## 使用的设计

主分支 `master/0a5e5987` 的 `demo_v1`：主机发送原论文 complex128 CSI 窗口，板端保持原轴对齐、预处理、共享 FP16 图、CPU 算子、SDK 3.39 和 NPU 分配；完整返回每条实际输入、100 分数和全部姿态，主机保存后回执，板端执行有限性与既有三冻结参考门检。

新 HDMI 接入复用已有 skeleton_render、1080p RGB565 canvas 和公开 SDK UDMA Output。Session 分配完成后通过可选回调传出同一 Device；publisher 不操作 SDK，经过保存回执及原数值门检后，一槽拥有值交给主线程绘制、提交并核对 ID／地址采纳，随后才发原展示确认。关闭先证明 STOP，再释放双帧及 Engine。PIWCSI2／PIWFUL2／PIWPOSE1 字段不变。

硬件复用已合格、HDMI 分支已连接的 r26 BOOT：setup +0.030ns、hold +0.007ns，保留仅原批准 AI 最小周期例外。HC0→HP0、HC1→HP1、HC2→HP2 S00、HC3→HP3；HDMI／旧视频 S01 保持连接，未删模块、未改四路连接。该位流没有原生 AXI Protocol Checker，也没有 r30 的逐周期 BRAM 窗口。

## 实际执行结果

原定一次 90 窗、现有 basic 5Hz 模式的有限功能联测，HDMI 按既有扫描设计持续读帧；不是 30Hz 或长期验收。

- r35：启动健康，唯一 Device::Open／Session apply 成功，两块各 4,147,200 字节的完整 SDK 写读均逐位一致。主机 Node 创建 Python 节拍子进程被 Windows 执行环境拒绝 `spawn EPERM`；在第一窗输入前停止，输入／推理／HDMI 采纳均 0。板端原生 exit1 是连接 EOF，无 SDK／数值／总线异常；新 STOP 响应、安全空闲及释放均证明。完整失败现场和原值保留，批次关闭。
- 主机修正：使用已安装 Python 的绝对路径及允许子进程的执行权限，独立三节拍 5Hz 测试 exit0。新增拥有值交接离线测试覆盖顺序、双向异常唤醒、首次异常保留和错误完成 ID，四项通过。未用板端重试代替这项主机验证。
- r36：使用同一 BOOT、同一已编译软件建立新批次。**启动健康门未通过，Device::Open／Session／CSI 输入／推理／HDMI_START 都没有执行。** 未开启主机联测或追加候选启动。

## 本次启动异常的关键事实

| 观测 | 实际值 |
|---|---|
| 启动后累计 PS HP2 AR 握手 | 0 |
| 启动后累计 PS HP2 R 握手 | 6 |
| 首次原始 PS RVALID 的 HP 周期 | 342534 |
| 首次 PL 就绪时仍见 PS RVALID 的 HP 周期 | 11636514 |
| 首次 RVALID 时 PS_HP2_resetn | 1 |
| 同时 PL_HP2_resetn／HP_reset | 0／1，即 PL 互联仍复位 |
| 同时 FCLK_RESET0_N／PL DDR calibrated | 0／0 |
| 同时 PS_ARVALID／HDMI_ARVALID | 0／0 |
| 计数溢出掩码／事件溢出 | 0／false |

此后 PL 复位释放，HDMI 一侧也可观测到 RVALID；累计仍无 AR。SDK 尚未打开，不能归因本次 AI 推理发起请求或 HDMI_START。另一方面，配置前与无时钟区间没有覆盖，不能把“观测范围内 AR=0”扩大成 PS 上电以来绝无历史请求；GP 事件首条的 resetn 已高，也不能当作 GP 域捕获到了其释放边沿。此次 r26 的证据是启动见证和原始计数，不能包装为新的逐周期完整波形或原生协议检查结论。

PS_HP2_resetn 来自 PS 接口输出，本设计用于观测；PL_HP2_resetn 由 HP 时钟域复位控制器产生，按 PL MIG DDR 就绪释放，连接 HP2 AXI 互联。HP_reset 为 PL HP 域高有效复位，经取反用于 HDMI／旧视频复位。它们覆盖的状态范围并不相同。

## 对官方建议的复核与下一步

官方《PSOC GP HP 问题调试经验总结 V1.0》实际案例是 GP 写响应早于数据接收及 ID 处理问题；不能直接判定就是本工程读返回异常的根因。其 HP 排查建议支持抓完整握手并使用协议检查，也明确该系列 HP FIFO 在 PL。文档的“运行中重载位流后 HP re-enable／level shifter”分支不能不加核对地套用到本次完整 BOOT 启动；不猜测 FMQL30TAI 寄存器，不自动套用 Xilinx／旧 A7 定义。

下一步应先定位启动复位与协议边界，不能继续加载有异常未匹配返回的候选运行时。建议保持四路 AI 及 HP 分配不变，准备 HDMI 已连接的协议检查诊断候选，保留复位前后完整 AR/R 与 checker 状态；首个有效错误触发需区分 READY 复位建议位与真实事务错误，避免缓冲先被建议位占满。新设计必须完成实际布局布线、setup／hold／DRC，再生成核验 bit。若需要改变 PS 初始化、复位拓扑、频率或豁免，应先取得匹配当前器件的官方契约并作为重大变更评估，不能靠反复启动直到偶然正常来代替修复。

## 恢复与范围

最终运行 ID `9157c6a6-a370-4d08-afd8-f6b6f297ab55`，原 BOOT SHA256 `ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef`；9 个启动文件及 6 个 SDK 库吻合，设备 owner 为空，串口 RX 采集已关闭、TX=0。本任务两次候选启动和两次原 BOOT 回退均已关闭，没有板端后台负载。本次没有修复启动偶发问题或 D47，也没有通过真实 AI→HDMI、物理画面、30Hz 联合吞吐或长期稳定性验收。主工作区原有未提交改动未改动或提交。

## 源码复现

`scripts/prepare_demo_hdmi_source.py --project-root D:/FPGACompetitionProject --output 新目录` 以主分支最新 demo_v1 和本工作树已有 HDMI 核心导出实际联测源码；输出目录必须全新。导出的 56 个实际构建源文件与本次构建源逐字节复核一致，未更改主工作区文件。独立 CMake 构建保留 `DEMO_READ_DIAGNOSTIC=ON`、`DEMO_D47_ISOLATION=ON`，只编译 `pose_demo_v1`；使用原 ARM64 SDK 3.39 和原模型身份。执行导出脚本本身不会构建、连接板卡或赋予新的启动／负载次数。

`software/hdmi_handoff.hpp` 是新增的一槽拥有值交接；`software/tests/hdmi_handoff_test.cpp` 配合 `software/tests/mock/application_core.hpp` 可独立编译测试，不使用 SDK。最新链路的仅两处核心改动是可选 Device 完成回调的声明和调用；计算与搬运原顺序未更改。

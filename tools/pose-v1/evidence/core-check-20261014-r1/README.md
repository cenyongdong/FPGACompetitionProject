# 2026-10-14 正式核心编译与运行复核

当前状态：本机检查与新 ARM 构建通过；本轮板端首次 SSH 连接超时，CPU107 和三窗口均未启动。用户选择稍后恢复板端连接再完成检查，`Agents.md` 开发基准规范暂未落地。

## 实际执行与证据

工作目录 `D:/FPGACompetitionProject`。复用既有 FPAI、GCC9.4、SDK3.39.0，以及既有 Python3.10.21/NumPy2.2.5/h5py3.16.0 环境；启动原 Docker Desktop/FPAI，没有安装或更换工具。独立 Engine 计时实验不在正式目标中，本轮不恢复旧 DATA 排查。

| 检查 | 结果与证据 |
|---|---|
| 来源与构建隔离 | [source-review.json](source-review.json)、[static-review.json](static-review.json)：正式源码与已验证重构逐字节相同；126 旧锁文件、926 冻结文件保持；52 C++ 逐 token 等价，生产目标只使用新核心 |
| Python 语法 | [python-syntax.json](python-syntax.json)：核心与演示 Python 逐文件 compile；这项只证明语法 |
| 11 组本机回归 | [完整结果](../../../../.local/core-refactor/native-20261014-r1/steps.json)、[复核](native-20261014-r1.review.json)：TCP、AU、Host 原值/阶段/调用/生产者/身份/读取、显示 IPC、预处理、渲染通过；没有本机模拟 NPU 成功 |
| 固定输入与像素 | 同上：308/309/310 CSI 编码、预处理与旧实现/固定参考逐字节一致；20 份像素文件与旧渲染一致 |
| 主机输入入口 | [host-prepare-review.json](host-prepare-review.json)：实际执行 `host/run.py --prepare-only`，成功导入并准备 3 个完整原始窗口，负载与编码检查逐字节一致；没有网络或推理 |
| FPAI ARM 构建 | [build-review.json](build-review.json)、[命令与退出码](build-command.json)、[56 步完整日志](../../../../.local/pose-v1-build/demo-core-check-20261014-r1/build-steps.json)：3 演示程序和 11 回归程序构建成功；15 SDK 头、189 厂商文件核对通过；14 个二进制均与原已验证重构版本同 SHA |
| 编译警告 | 1 个私有未使用 `need(std::string)` 助手警告，与旧源码及上次重构一致；没有将其隐去或称作零警告 |
| 接口可链接性 | [ARM 符号表](pose_demo.symbols.txt)、[接口边界](interface-link-review.json)：当前实现入口为 encodeResident/serveGuardedAccessUnits；4 个保留历史声明没有当前目标定义，接口手册明确禁止据声明误判可链接 |
| 本轮板端入口 | [SSH 原日志](board-readonly.txt)、[停止记录](board-attempt.json)：port22 超时、exit255；未认证成功、未部署、未开启负载、未自动重试 |

[run_local.py](run_local.py)仅将复用检查器的报告重定向到本目录，避免回写原重构证据。[run_board.py](run_board.py)及 harness 副本仅适配新远端目录和用户已有的内存认证来源，保留300秒 CPU / 180秒 short预算；本轮在只读连接前置阶段停止。

## 文档和剩余步骤

新增[接口与开发指南](../../../../software/core/INTERFACES.md)，说明六个模块、应用/主机入口、数据形状、资源所有权、线程、释放顺序、异常及保留声明范围。开发规范候选见[待落实条款](agents-rule.proposed.md)，不把文档准备完成写成板端通过。

连接恢复后使用新证据/远端目录，执行 CPU107 并逐个比较22输出/59600 FP32，再执行308/309/310三窗口：完整原始CSI/预处理/分数/姿态、实际视频来源、drain/LAST/两STREAMOFF、线程/子进程/端口回收与最终身份。失败保存停止，不重试失败负载或延长预算。全部检查通过再写入 Agents.md，并补全本条 Done 和最新进度。

本轮没有60窗口、HDMI、严格5Hz、长期或永久首启动验收；旧DATA坏读根因与独立SDK计时负值问题保持各自未解决范围。此前实板成功证据属于2026-10-13，不能替代本轮新板测记录。

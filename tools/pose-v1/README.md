# 首版实施工具与证据

状态与边界见 [软件说明](../../software/pose_v1/README.md)。此目录不包含已通过的完整推理/双路显示系统。

- `Invoke-BoardAudit.ps1` / `board_probe.py`：严格主机密钥验证，读取FAT16启动分区、设备树。
  不挂载、不改启动文件、不访问未知寄存器；交互输入密码，不写入源码/证据。
- `validate_preprocess.py`：用实际训练AST、合成CSI和三个测试集原始MAT与FPAI的Linux主机C++比较。
- `Invoke-BoardPreprocessTest.ps1` / `board_preprocess_test.py`：核对测试包SHA256后在唯一`/tmp`目录
  运行arm64数值程序，报告误差及异常输入；不调用AI、视频或修改系统配置。
- `replay_raw_csi.py` / `csi_io.py`：原始数据客户端，板端接收服务尚未实现，不作为网络联调通过。
- `audit_assets.py`：只读记录所选模型、源码、生成物哈希及Host/NPU图分工。
- `test_replay.py`：Windows本机TCP回环，强制碎片读取验证3个原始窗口字节不变；不代表板端网络验收。
- `diagnose_phase_boundary.py`：只在离线参考中替换标量angle以排查边界；当前替换未解释C++偏差，
  不改变生产代码/训练文件，也不构成误差容限批准。

执行源码来自当前Codex worktree；FPAI挂载原`D:\FPGACompetitionProject`。本次源码明确复制到
容器`/tmp/pose-v1-source`构建，未修改原项目挂载、镜像、工具链或已安装SDK。
临时主机/arm64二进制、输入/参考张量在`.local/pose-v1-build`与`.local/pose-v1-validation`，不提交生成物。

`evidence/host-preprocess-initial-failure.json`保留零幅值移植错误；`host-preprocess.json`为修正后主机结果，
`board-preprocess.json`为实际板端结果。每个case的名称/原始文件由主机报告关联；不得抹去π边界失败。
本次实际数值参考是上述WindowsConda版本，不据此声称原训练服务器软件栈已重验。

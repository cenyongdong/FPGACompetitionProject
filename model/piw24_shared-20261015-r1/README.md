# 共享细化 Icraft 产物

> 本页为历史模型记录，仅说明文档纳入 Git；下列本机附件不随克隆提供。当前部署模型见 [模型索引](../README.md)。

2026-10-15 使用本机 Icraft CLI 3.39.0，按实际 `piw24_shared.toml` 完成 parse／optimize／quantize／adapt／generate，五阶段 exit 0。ZG330、FP16、4×4／1 core，CSI 预处理 NOP；固定 FP32 输入 [1,180,60]、分数 [1,100]、姿态 [1,100,14,3]。两 TopK 保留、ScatterND 0，最终 1021 HardOp。

最终部署配对为 piw24_shared_ZG.json（本机附件：`piw24_shared_ZG.json`） 与 piw24_shared_ZG.raw（本机附件：`piw24_shared_ZG.raw`），RAW 35,481,378 字节。配置、脚本、全部阶段配对、源 ONNX 和逐阶段完整日志保留；原 `summary.json`／`files.json` 是转换结束时快照，不回写其中“尚未板测”字段。

后续实际 Lite 首帧 Engine 24.19628 ms，但 78/4200 姿态坐标未逐位原参考，最大关节差 1.953125 mm；原门禁停止，余两帧未跑。这不是板端验收通过或正式部署替换。最新状态、报告及原始板测证据见 完整报告（本机附件：`../../tools/pose-v1/evidence/shared-graph-board-20261015-r1/REPORT.md`） 和 delivery-audit.json（本机附件：`../../tools/pose-v1/evidence/shared-graph-board-20261015-r1/delivery-audit.json`）。

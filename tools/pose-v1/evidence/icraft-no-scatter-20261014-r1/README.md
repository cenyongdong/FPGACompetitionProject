# 主机Icraft去ScatterND转换证据

2026-10-14用户授权新完整ONNX的主机parse/optimize/adapt等阶段，JSON/RAW保存model，后明确要求保留实际TOML。

成功候选：[model/piw24_noscatter-20261014-r3](../../../../model/piw24_noscatter-20261014-r3/README.md)。五阶段parse/optimize/quantize/adapt/generate均实际exit0，总68.688秒，五对RAW大小/MD5/SHA、固定FP32端口和XIR **C通过，62原文件逐SHA独立复核。实际TOML、源ONNX、完整日志和SDK配置留model。

实际配置SHA `dcc4e37f7b9ec31767020cc4c47f5abc02aca2112f44a33b02883dde48c212e7`，最终JSON SHA `0720b375edb7fddd7ee6f074be0e8fd0852592ae1fcbe600762525f276139ce5`，RAW SHA `29dce9c1bd1fc940cdd1364d148353227d01ec0cef82861f7d2c9045e12ee1ce`。

Icraft3.39.0/ZG330，FP16依据已验原130 Matmul精度，原TOML缺失所以不伪称全文恢复。最终1164节点/1158 HardOp/四Host188、192、437、442，ScatterND0；静态层数和736不是板测阈值。CLI布局FD、四个NOP字段对应原CSI，无图像预处理。

[completion-review.json](completion-review.json)独立核验实际运行。r1缺3个NOP字段、r2CLI不支持XIR **C，两者网络加载前exit1停止，失败TOML/调用/日志保留在model。修正后用新r3，没有续用失败目录或重试推理负载。控制台ANSI信息保留。

原模型、正式Engine、SDK/BOOT未替换，没有量化数值、设备/板测/性能执行；旧Engine1173/六Host/七融合组/745及Scatter注册不能直接适用于新图。旧DATA排查继续暂停。

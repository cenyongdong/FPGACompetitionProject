# 真实生产者参考与mock部署结果

2026-10-11。本轮执行已批准的PRODUCER-CONTRACT-NEXT第一项：原RAW仅读、19成员数学／布局参考；随后用文档支持的mock协议核对独立部署范围。原正式推理器与失败Engine未重跑。

| 项目 | 实际结果 | 边界 |
|---|---|---|
| 源图映射 | adapted图19来源全部对应HardOp，Value／dtype逐项相同 | 不仅按名字判断 |
| 原RAW | 三模型MD5校验通过；22项导出、6144字节指令 | XIR-only，无XRT／Device／Session |
| 真实权重 | 8507：42个FP16一＋6个零；adapted逐位同；optimized为42个FP32一 | 未替换真实参数 |
| NumPy参考 | 两图案，23520 FP32；标量地址／原Matmul逐位同，重放同 | 仅有限FP16／TF32精确可表示值 |
| 独立mock部署 | 原19成员→有效9185，sync `0→11`；四边界非OCM；两日志8016／655字节 | mock内存／Session，无真实NPU前向 |

真实数据输入为17280字节的 `[1,3,180,16]` FP16，42有效／6填充。依据adapted图转置和PruneAxis属性，输出为30240字节 `[1,180,42]` FP32。400字节100索引经实际Matmul权重广播、转置和去填充，输出16800字节 `[1,100,42]` FP32。参考保存完整两输入、两输出及逐算子逻辑指纹；TF32中间数组不是物理19位存储编码，不外推一般舍入行为。

RAW检查器SHA256：`1c26d03806ea88388e2b31cd4d0ee3b8ebd2adad244a85bac2e989da07bfb3af`。
mock检查器SHA256：`7cc0e0b63d094ef8b1471fa88d632329a1e8d20a53c6ae85a0169b0d4c028884`。
真实模型／RAW的原哈希保持75ffdc37…43acb8a0／3991a679…e054d3。

最初r1编译的HardOp→bool不受SDK支持；新r2用公开defined()修正，旧失败保留。三模型JSON／RAW以及四份匹配头身份固定；公开lazyFileOffset的原始字节二次核对通过。两执行阶段exit0、stderr空、内核跨阶段同，未新Host107／实际NPU／VPU或并发回归。mock确实创建模拟Device／Session，不能将其等同物理设备操作。

内存规整0，无清缓存／重启／BOOT／CMA／SDK／模型改变。最终无项目进程，连接已关闭；MemAvailable751576／CmaFree21992KiB仅快照。原异常读取与坏索引门禁保持，首次读根因未修，83/100和103／严格5Hz／长期／HDMI待验状态不变。

完整来源与原始字节在本机保留；Git文本摘要不能代替完整证据。[RAW核验](evidence/producer-reference-20261011-r2/raw.review.json)、[参考核验](evidence/producer-reference-20261011-r2/reference-review.json)、[参考重放](evidence/producer-reference-20261011-r2/reference-replay.json)、[mock核验](evidence/producer-reference-20261011-r2/mock.review.json)、[ADR_38](../../ADR/ADR_38.md)、[下一门检](PRODUCER-REFERENCE-NEXT-20261011.md)。

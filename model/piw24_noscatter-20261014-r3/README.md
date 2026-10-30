# 完整去ScatterND ONNX：Icraft3.39.0主机转换

> 本页为历史模型记录，仅说明文档纳入 Git；下列本机附件不随克隆提供。当前部署模型见 [模型索引](../README.md)。

2026-10-14（Asia/Shanghai），代理在Windows主机 `D:/FPGACompetitionProject/model/piw24_noscatter-20261014-r3` 实际执行五阶段并独立核验。保留的TOML就是实际传给CLI的配置。

## 实际产物

| 阶段 | JSON | RAW字节 | 耗时/秒 | exit |
|---|---|---:|---:|---:|
| parse | piw24_noscatter_parsed.json（本机附件：`piw24_noscatter_parsed.json`） | 64,390,468 | 9.905 | 0 |
| optimize | piw24_noscatter_optimized.json（本机附件：`piw24_noscatter_optimized.json`） | 64,392,328 | 4.871 | 0 |
| quantize | piw24_noscatter_quantized.json（本机附件：`piw24_noscatter_quantized.json`） | 32,205,006 | 1.498 | 0 |
| adapt | piw24_noscatter_adapted.json（本机附件：`piw24_noscatter_adapted.json`） | 32,433,222 | 33.157 | 0 |
| generate | piw24_noscatter_ZG.json（本机附件：`piw24_noscatter_ZG.json`） | 53,200,782 | 17.708 | 0 |

每份JSON同目录有同名RAW。五对 `params_bytes`、RAW实际大小、`params_md5`和完整SHA均独立核验通过；每阶段ScatterND为0。

最终ZG JSON SHA256：`0720b375edb7fddd7ee6f074be0e8fd0852592ae1fcbe600762525f276139ce5`。

最终ZG RAW SHA256：`29dce9c1bd1fc940cdd1364d148353227d01ec0cef82861f7d2c9045e12ee1ce`。

## 配置、身份与参数

- 实际 piw24_noscatter.toml（本机附件：`piw24_noscatter.toml`），SHA256 `dcc4e37f7b9ec31767020cc4c47f5abc02aca2112f44a33b02883dde48c212e7`；五次调用前后同值。
- 实际脚本（本机附件：`compile_icraft.py`），调用 `C:/Icraft/CLI v3.39.0/bin/icraft.exe <stage> piw24_noscatter.toml`，cwd为本目录。CLI版本 `3.39.0.0-431be90(2608211646)`，每步 `--dry_run` 展开、调用/PID和完整日志保留。
- 使用已验独立CUDA依赖，三DLL逐SHA核对，只修改子进程PATH；没有全局PATH或工具版本变更。preflight（本机附件：`preflight.json`）保存运行时、exe/DLL身份，`source/toolchain-configs/`保存comb/Zhuge optimizer/adapter TOML快照。
- 完整源ONNX（本机附件：`source/person_in_wifi_2024_best_epoch442_full_noscatter.onnx`），SHA `a8c3261b614cc14e6b4818d0efaf8a61dc3127bbe08020096600e654bc1b9c75`，52,526,508字节。
- 输入是已预处理FP32 CSI `[1,180,60]`；输出FP32分数 `[1,100]`、姿态 `[1,100,14,3]`。CLI特征布局为 `FD`，实际XIR为 `@layout(**C)`。method/scale/mean/channel_swap全部 `nop`，没有图像resize/缩放/均值或通道交换。
- target=zhuge/ZG330、qdtype=fp16、rows4/cols4/cores1。原量化TOML未留存，FP16依据原图130个Matmul的FP16输入/权重确定；本配置是明确的新配置，不伪称恢复旧配置全文。新quantized图130个Matmul输入均FP16，SDK插入所需TF32中间转换；没有INT8校准、自定义混合精度或自动调优。

## 最终静态图及后续边界

最终1164逻辑节点：1158 HardOp、4计算Host、Input/Output各1。Host为TopK188、GatherElements192、TopK437、原Gather442，无ScatterND或Host Matmul。HardOp `layer_count`静态总和736，不是本次NPU完成计数或Session融合绑定结果。

当前正式Engine仍锁旧1173 HardOp/六Host/七融合组/745及582/649注册检查，不能直接换新JSON/RAW后沿用旧门禁。后续须重新核Host注册、1158成员追溯、同步表、帧计数和数值；本阶段没有改旧Engine或旧部署模型。

## 停止条件和原失败

总预算3600秒、每阶段1200秒，实际68.688秒。非0退出、超时、身份变化、缺JSON/RAW、MD5失配、端口变化或残余ScatterND时保存停止后续步骤。所有转换进程结束，无设备/SSH/Session.forward或后台工作。

前两次是网络加载前参数校验失败：r1缺pre_scale/pre_mean/channel_swap；r2误将XIR **C作为CLI布局，实际CLI仅支持NHWC/NDHWC/FD。依本机原始文档NOP占位和当前签名，在独立r3配置中修正。邻近r1/r2保留原TOML、源ONNX、调用、完整错误与exit1，不覆盖，不重跑失败推理负载。

初次启动器默认RuntimeRoot绑定失败发生在CLI启动前，显式路径查询成功，实际脚本沿用同一已验DLL路径。文档通用layout描述与当前CLI签名的差异保留，最终核XIR **C与原输入一致。重定向控制台时SDK stderr出现 `SetAnsiMode failed ... error code:6`，原样保留；五阶段exit0及产物门检不由控制台信息替代。

## 原始证据

summary.json（本机附件：`summary.json`）、files.json（本机附件：`files.json`）、progress.json（本机附件：`progress.json`）保留原运行摘要和冻结清单。`logs/<stage>.stdout.log/.stderr.log/.invocation.json/.exit.json/.graph-review.json`记录完整参数、cwd、PID、退出码、图类型/目标/MD5/哈希；`logs/<stage>/`保留厂商日志，`pipeline.stdout.log/.stderr.log`保存编排结果。

独立完成复核（本机附件：`../../tools/pose-v1/evidence/icraft-no-scatter-20261014-r1/completion-review.json`）核62原文件、五对RAW和端口/layout；后追加说明和工具配置另有交付清单，不回写原清单。

通过范围为主机转换和产物结构/身份；没有量化数值、新图板端正确性/吞吐/长期结论。旧ONNX/ZG/RAW、正式核心、BOOT/SDK及暂停DATA排查保持。

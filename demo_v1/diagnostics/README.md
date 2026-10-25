本目录是op192首次读回诊断覆盖层。原`shared_fp16/`全部文件及其身份清单保持不变，默认构建仍使用原实现。`--read-diagnostic`选择覆盖层；下述两种构建的历史结果分别保留。

`--read-diagnostic --d47-isolation`用于已完成的两阶段隔离诊断：不增加layerCount查询，保留原wait／read顺序和原值环形快照；保存已拥有的Host TopK索引，仅作op192首次值的独立逐位比较。另构建`pose_static_read`，通过公开SDK独立分配静态PLDDR源、不加载模型／运行NPU。`board_guard.py --isolation-stage static|live`限制一次静态和一次真实负载，静态异常禁止进入真实负载，错误关闭本批，不重试。该包本轮次数已耗尽；实际结果统一见[RESULTS](../RESULTS.md)。

以下为仅`--read-diagnostic`的原计数观测模式，不能与隔离模式混称：

相对原实现，只增加每输入在wait前后及copy前后的四次公开`layerCount()`观测，保留最后256条op192复制元数据和最近8次调用的两个原Host快照。数据读回、wait、数学、NPU分配及错误处理沿用原实现；正常路径无新增设备数据读取、等待或重试。计数只作观测，不证明DMA或缓存完成。

异常时先保存首次Host值、独立post-copy快照，再执行原有两轮公开SDK源读取以取证；异常永久停止该Engine。最近原值与元数据在退出时保存，不用晚读继续计算。每输入4次查询、每op192共8次查询可能扰动时序；未复现只能作为本次有界观测结果。

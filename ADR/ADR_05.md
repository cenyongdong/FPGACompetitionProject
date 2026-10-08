# ADR_05：受限CPU适配、融合追溯与每帧完成协议

- 日期：2026-10-08；状态：首版工程已实板通过，适用范围固定。
- 决策：仅补正式混合图缺失CPU算子，NPU Matmul/Gather现有实现/SDK优化保持；有证据的边界适配优于猜测性改模型、ready或缓存。

## 问题到解决的证据链

1. **缺失注册**：TopK188/437、GatherElements192、ScatterND582/649没有Host条目；Gather442已有。直接编入应用注册单元，在Session前显式注册初始化/前向，注册前校验基线，禁止覆盖。复用SDK明文common内核。全CPU Matmul未补，不把CPU参考失败解释为ZG不支持Matmul。
2. **布局拒绝**：便携内核拒绝merged_distr。静态声明九项在当前图覆盖完整有效范围。适配仅接受当前FP32/轴/形状/reduction=NONE，核验分布轴、mask、全有效、字节/布局后，只临时内核描述去除冗余分布；模型和输出声明保持，非法/非全有效拒绝。[107例](../tools/pose-v1/CPU-ADAPTER-RESULTS-20261006.md)含18正常89拒绝，12注册22输出59,600FP32逐位NumPy，非通用去填充实现。
3. **ADDR不能直接当CPU指针**：桥等待SDK就绪，SDK复制到Host CPTR再计算；提供合法输出则SDK写回，否则返回Host结果。BOTH/ADDR不解引用，Linux cache helper不当同步证明。两16KiB设备缓冲六读回24,576FP32逐位一致只是搬运门检；真实混合路径主要返回Host，提供输出writeback未被本轮真实图覆盖。[内存证据](../tools/pose-v1/MIXED-MEMORY-RESULTS-20261006.md)。
4. **apply后原HardOp ID看似失绑定**：r1/r2于8622失败，无forward；公共快照证明原1173HardOp融合成七组9185–9191。正式r3以merge_from追溯完整唯一覆盖，核对同后端实例/组成员/同步表及八Host，原layer_count0不当缺计算。未重复调用autoMerge或改SDK默认优化。[正式apply](../tools/pose-v1/MIXED-FUSION-R3-APPLY-RESULTS.md)通过1181逻辑追溯，不能只凭七组数目宣称1173覆盖。
5. **不同输入全部输出首帧**：r3/r4三样本失败保留，PS/Input0变化而后段停留首帧；真实CPU暂存重算一致，回调和ready标记不足以证明新内容。r5观察完成计数首次0→745、次帧745→1222，SDK绝对阈值提前满足。r6在安全帧边界使用官方reset(1)，确认0，等输出就绪和最终745才下一帧，不reset(0)/直接寄存器/重建Session。[r6结果](../tools/pose-v1/MIXED-FRAME-STATE-R6-RESULTS.md)三份输出不同、重复308全部捕获逐位一致；失败39ms不能算性能。

## 实现与验收约束

Host→真实RAW/PS离线→SDK内存→apply→单帧→不同三帧＋重复各自验收，真实K=100/ScatterND完整索引来自RAW，不用合成参数替代。源码、包、SDK、设备身份变化即停止。数学、模型、BOOT不随诊断改动；原失败全量保留。

长期同步、通用布局、所有输出缓冲分支与零拷贝仍另行验证。首版性能取舍见[ADR_01](ADR_01.md)，常驻线程归属见[ADR_02](ADR_02.md)。

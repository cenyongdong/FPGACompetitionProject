# 2026-10-14：共享细化源码与完整测试集对照

状态：服务器完整7824帧对照 exit0；本机完整回传、归档身份、30个成员和独立数组/指标核验全部通过。测试及传输进程已结束。

## 工程内容总结

用户批准共享细化方案，要求保留两处 TopK。校园网问题期间按用户要求暂停；用户明确恢复后重新核验源码、权重和空闲 GPU，再实施修改。没有恢复旧 DATA 首次坏读排查。

本机算法目录为 `D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo`；服务器工作目录为 `/public/cyd/Person-in-WiFi-3D-repo`，结果目录为 `result/shared_refine_20261014_r1`。经已有 `ssh gpu-server`、密钥和严格主机密钥核验传输，实际部署记录见 [deployment.json](deployment.json)。未执行 Git push；这里的推送是向服务器传输并更新两份指定源码。

修改 [transformer.py](D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/opera/models/utils/transformer.py:566) 与 [petr_head.py](D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/opera/models/dense_heads/petr_head.py:325)：

- 单图像、eval 模式、没有额外注意力参数时，14 个关节的注意力特征只计算一份；encoder memory 不再按 100 个候选重复。
- decoder 和 head 的回归分支均只计算一份偏移，保持原来的逐层加法顺序，广播至全部候选坐标。
- transformer 返回的特征仍通过只读 expand 视图保留原候选维度，最终输出仍为 100 个分数/姿态，候选顺序不变。
- 训练、多图像 batch、额外注意力参数沿用原路径。eval 的广播加法使用非原地操作，训练保留原地加法。
- 两个包含 TopK 的函数 AST 完全一致，query 数、关节数、max_per_img、数据划分及权重均未改变。原去 ScatterND 全张量加法继续保留。

原源码完整保存为 [transformer.before.py](transformer.before.py)、[petr_head.before.py](petr_head.before.py)，最终快照和差异为 `*.after.py`、`*.diff`；本机和服务器字节一致。两个最终源码 SHA256：

- transformer：`74ffb67cda14faf475ae1b73f8b0496beac67a7bd6aeab61cc9eb37cfdd5ae20`
- petr_head：`5758dc05c7c8e07370b8178f2782d5828b0a9e19b94de363c3a9c9669b57fdad`

## 实际验证与证据

复用服务器 PersonInWIFI Python、PyTorch 1.13.1+cu117、MMCV 1.5.3 与 RTX A5500 GPU0。固定 epoch442 checkpoint SHA256 为 `6493e2250b83aef59ce4825e15d2d0043a59490275f75933f9a59867867d3221`。一张空闲 GPU、FP32、batch1、worker2；同一已预处理输入配对，before/after 交替执行顺序，TF32 关闭，无优化器或重新训练。对照基线是已去 ScatterND、尚未共享的源码；AST 提取原方法后在同一加载模型内切换三处方法，其他计算共用且保持不变。

执行脚本为 [paired_eval.py](paired_eval.py)，实际展开、目录、PID、退出码见 [execution.json](execution.json)。本轮固定 1800 秒上限，实际 wrapper 452.797 秒、exit0；全测试与诊断约 447.151 秒，不作为单次推理延迟。发生 OOM、超时、非有限值、身份变化、非法索引/形状、分数差异或超出预先设定坐标边界时，先保存输出后停止，不自动重跑。

新源码数值比较边界为坐标绝对差 1e-5 模型单位、总 MPJPE 绝对差 0.01mm，分数必须逐位一致。这是此轮候选验证的预先明确条件，不放宽正式部署门检，也不把边界内差异改写为逐位一致。

完整 **7824 帧、每帧 100 候选、14 关节**，实际比较 **102,494,400 个 FP32 值**。原输入、两版 boxes/poses/两层 references 全部先落盘再比较；完整指标见 [summary.json](summary.json)，逐帧值见 [frames.jsonl](frames.jsonl)。

| MPJPE（mm） | 改前 | 共享后 |
|---|---:|---:|
| 全部 7824 帧 | 123.0853521290001 | 123.08535222675658 |
| 一人，2586 帧 | 99.66472365887518 | 99.66472387793262 |
| 两人，3184 帧 | 123.11500986377199 | 123.11500993326082 |
| 三人，2054 帧 | 152.52610918656063 | 152.52610917541742 |

总差 **+9.77564838e-8 mm**，没有观察到实际精度下降。分数逐位一致；坐标及引用值存在舍入量级差异，不能称全部输出逐位一致。最大坐标绝对差 **4.76837158203125e-7 模型单位**（按原评估米转毫米为 **0.000476837158203125mm**）；全部比较字段共有 3,393,277 个 FP32 位值不同。单帧 MPJPE 最大绝对变化 **0.0001220703125mm**。

[独立回传核验](delivery-review.json)重新读取全部数组并核对哈希、形状、有限性、分数、逐帧均值及人数分组。最大三维关节位移差 **0.0005331201499700045mm**；2772帧的FP32 MPJPE位值有变化，7203帧的姿态数组有至少一个位值不同。上述差异完整保留，不以相同显示小数位代替逐位一致。

[guards.json](guards.json)：使用真实加载权重及真实模块验证训练损失与 **2,424,838 个梯度值**逐位一致；多图像 batch 和额外注意力参数的回退结果逐位一致。前后整个 state_dict 摘要一致。全 7824 帧探针确认两层注意力的候选 batch 从 `[100,100]` 变为 `[1,1]`，四次回归分支调用的 batch 从 `[100,100,100,100]` 变为 `[1,1,1,1]`。

| 服务器计时（排除前10帧，7814帧平均） | 改前 | 共享后 | 减少 |
|---|---:|---:|---:|
| 整模型同步墙钟 | 12.211762ms | 11.081056ms | 9.259% |
| refine_decoder CUDA event 区间 | 2.958172ms | 1.818552ms | 38.524% |

两项计时为嵌套区间，不能相加；包含验证探针，CUDA event 区间不等同纯算术时间。不是无诊断基准或 Lite/NPU 性能，不能外推板端加速比例。

[cleanup.json](cleanup.json)确认本轮 wrapper、子进程及所属进程组均已退出；两名 dataloader worker 显式回收，其他用户的 GPU 进程未触碰。原 key position encoding 警告完整保留，没有掩盖异常。

## 对后续开发的参考

本轮是现有2024模型推理计算共享，不是模型重新训练。精度协议仍为原 `WifiPoseDataset.calc_mpjpe` 对全部候选的 GT 辅助 greedy 匹配与逐帧平均，不等同置信度驱动的人数检测准确率。

保留原候选坐标，按原层序广播偏移，避免先把偏移相加再与粗姿态相加而改变浮点结合顺序。训练 dropout、梯度和多图像语义不能直接按单帧推理共享。后续若引入候选坐标条件化注意力，当前共享前提必须重新检查。

本轮未新导出 ONNX、未执行 Icraft 转换或板端推理。`exportONNX/scatter-add-20261014-r1` 和 `model/piw24_noscatter-20261014-r3` 仍是共享改造前的去 ScatterND 图，实际 TOML 原样保留。新共享图的导出、量化数值、算子映射和板端性能均待验证；正式 Engine/模型/RAW/SDK/BOOT 未替换。

完整回传目录为 `D:/FPGACompetitionProject/.local/shared-refine-20261014-r1/shared_refine_20261014_r1`，包含约 1.17GB 原始证据。归档身份见 [archive.json](archive.json)，安全解包及全部成员哈希核验见 [unpack-review.json](unpack-review.json)，独立数组/逐帧指标核对见 [delivery-review.json](delivery-review.json)。保留 [verify_delivery.py](verify_delivery.py) 供后续检查。

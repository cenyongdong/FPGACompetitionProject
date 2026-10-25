# 180-query共享模型：训练状态与恢复入口

文档整理：2026-10-25。本轮仅修正文档，未连接服务器查询或控制训练；以下进度、PID与资源值均为已保存快照，不能作为当前实时状态，也不构成重新启动或后台监督许可。此前19:54的第88轮／等待续训描述已由后续完成记录替代，原快照文件及Git历史保留。

最新保存的训练快照：2026-10-24 23:17，Asia/Shanghai。**迁移训练100轮及最终交付已完成；从零训练前100轮已正常完成，条件续训首次失败原因已修复，快照时独立extra100_r2目录正在第101/200轮。** 原失败退出码和日志保留；该次训练核验未连接Lite、未操作服务器其它任务。迁移方案见[PLAN.md](PLAN.md)，结果及进程恢复入口见下。

## 已完成结果与独立实验的保存快照

迁移实验`piw24_pose180_shared_20261022_r1`于10月23日22:05正常结束，native exit0；100轮各评估7,824帧，最终epoch100／562200微批迭代。原监督器和torchrun均已退出。最佳为epoch99，最终完整CPU评估、对照核验及ONNX／ORT均已完成，不再等待训练结束。[选择结果](results/final-delivery-20261023-r1/selection.json)、[交付完成](results/final-delivery-20261023-r1/completion.json)、[独立核验](results/final-delivery-20261023-r1/verification.json)。

| 相同7,824帧测试集 | 原100-query epoch442 | 新180-query迁移最佳epoch99 |
|---|---:|---:|
| 原口径MPJPE，mm | 123.0853 | 120.9958 |
| score>0.2匹配MPJPE，mm | 156.4514 | 149.2080 |
| 人数MAE，score>0.2 | 0.06429 | 0.07362 |

新图的平均位置指标改善，人数MAE略差，单人／多人表现也不同；原口径含GT辅助匹配且候选数改变，置信度匹配均值不计未匹配对象，不能据此认定全部部署质量改善。[同源完整对照与指标定义](results/final-delivery-20261023-r1/comparison/comparison.json)。训练后最佳ONNX保持180候选，TopK／GatherElements／ScatterND均为0；三份真实输入的PyTorch／ORT最大分数差约5.54e-6、姿态差约2.74e-6，通过既定导出门。[原生导出核验](results/final-delivery-20261023-r1/onnx/verification.json)。权重及ONNX保存在服务器原run的`final-delivery-20261023-r1/`；本次只取回缺失的少量原生JSON，没有重新评估或复制权重。

从零实验`/public/cyd/Person-in-WiFi-3D-repo/result/piw24_pose180_scratch_20261023_r1`于10月24日22:58正常完成100轮，native exit0；100次评估各7,824帧，epoch100／iter562200，两DDP rank最终query身份一致，原监督器PID325965和torchrun PID325968均已退出。全100轮最佳为epoch89 MPJPE146.6445mm，epoch100为151.9092mm，仍高于原100-query的123.0853mm及迁移最佳120.9958mm。初始化、模型与首100轮训练配方保持原批准范围。[完整首100轮评估](results/scratch-20261023-r1/evaluations.jsonl)、[完成与对照](results/scratch-20261023-r1/comparison_with_transfer.json)、[DDP结束记录](results/scratch-20261023-r1/ddp_completion.json)、[原生退出码](results/scratch-20261023-r1/jobs/formal-r1/state.json)。

一次性条件衔接已触发，首次续训目录`piw24_pose180_scratch_20261024_extra100_r1`成功恢复epoch100权重、两rank各218项AdamW状态与step281100，但在第101轮首个优化更新前因梯度非有限退出，native exit1、无新增完整轮次评估。根因是MMCV梯度累积钩子把剩余迭代边界562200与全局iter562200比较，误用余数0作为损失除数。最初CPU验证只覆盖恢复而漏掉首个更新；原生失败与日志保持，不回写为通过。[首次失败状态](results/scratch-extra100-20261024-r1/state.json)、[完整原始报错](results/scratch-extra100-20261024-r1/training.stderr.log)。

修复仅位于独立注册的`Pose180ResumeOptimizerHook`，将累积边界转换为全局1124400，保持除数2及全部有限值硬门；未修改共享MMCV库、模型、损失、学习率或有效batch。CPU验证复现原除数0，覆盖完整／余数边界，并用epoch100与真实样本完成两微批、一次AdamW更新，step281100→281101，query及joint参数更新，loss／梯度／参数／优化器状态均有限；验证模型丢弃，不进入正式训练。[回归原值](results/scratch-extra100-20261024-r2/continuation-optimizer-validation.json)。

按已批准的新增100轮范围，从未修改的epoch100检查点在独立目录`/public/cyd/Person-in-WiFi-3D-repo/result/piw24_pose180_scratch_20261024_extra100_r2`恢复第101～200轮。上述快照时为第101轮850/5622微批，iter563050，loss6.505323、query梯度0.426119、joint梯度0.090976，均有限；当时尚无第101轮完整MPJPE。两rank初始恢复身份一致，继续主lr2e-6、有效batch32，保留旧结果与全程最佳；监督PID384703/start_ticks210245931，torchrun PID384773/start_ticks210246123，rank0 PID384778。快照中原GPU1任务3887468保持9,138MiB，本批每卡约1,880MiB。该次未建立定时检查或自动重试循环。[保存状态](results/scratch-extra100-20261024-r2/state.json)、[进度快照](results/scratch-extra100-20261024-r2/progress.json)、[实际恢复证明](results/scratch-extra100-20261024-r2/resumption.json)。

后续获准恢复查询时，先只读已记录的`extra100_r2`目录下`state.json`、`progress.json`、`resumption.json`，核对进程实际状态及PID创建tick；`extra100_r1`是已关闭失败目录。算法根目录下现有Python查询入口为`tools/pose180/continue_scratch.py status --output result/piw24_pose180_scratch_20261024_extra100_r2`，本轮未执行。不得重复start或新增定时监督。迁移最终评估已完成，不重复；续训全200轮是否完成须以后续实际结果核验。10月24日后续已按新授权完成Icraft转换、独立候选部署及忽略误差的30分钟饱和测试，数值误差与实测结果统一见[部署实测](deploy/RESULTS.md)；当前100-query演示基线及外部帧协议保持。

## 迁移阶段的历史记录

以下训练中快照截至2026-10-23 10:06：当时完成51轮、正在第52轮；[监督快照](results/supervision.json)是历史记录，不能作为当前运行状态。[启动取证](results/startup.json)保持。

## 迁移阶段的实现与批准配置（历史）

- encoder的180份提案按原token顺序进入180-query pose decoder；入口、出口TopK及候选Gather移除，180份分数和姿态不排序、不截断。
- joint decoder仍使用14关节query，每个输入计算一份共享特征，再对该输入的180份独立参考姿态广播偏移；训练和推理都走共享路径。`[14,B,256]`的B是输入batch，正式训练每卡B=8；180候选维保留在`[B,180,14,3]`参考姿态中。
- 从epoch442加载554份兼容状态，唯一重新初始化对象为全部`[180,512]`人体query embedding；未恢复旧优化器或训练计数。新模块通过配置注册，旧head／transformer／基线配置身份核对保持。
- 使用用户指定的物理GPU **1、6**；两rank×每卡batch8×累积2步，有效全局batch32。GPU1原有负载保留，每rank CUDA分配器上限为单卡显存40%；未结束／重启其他任务。
- AdamW、主学习率2e-5、weight_decay1e-4、100epoch、第80轮后学习率乘0.1、FP32、seed0、clip0.1。原参数学习率分组与损失权重保留。

## 迁移阶段的实际验证（历史）

| 项目 | 结果 |
|---|---|
| 迁移与结构／梯度 | `validate-r1` native exit0；真实1人／2人输入，输出`[2,180]`与`[2,180,14,3]`。两层joint输入均`[14,2,256]`；共享／非共享eval最大差2.384185791e-7。query、encoder、joint与joint回归梯度有限且非零；零正例损失为0，输入间隔离与候选同槽对应通过。 |
| ONNX／ORT | `export-r1` native exit0；opset11，TopK=0、GatherElements=0、ScatterND=0，保留形状／常量用途的Gather。三份真实输入分数最大差2.682209015e-7、姿态最大差1.859664917e-5，符合预先设定2e-5门限。该图为正式训练前初始化候选，不是训练后最佳模型。 |
| 原生评估入口 | `eval-r1` native exit0；3份真实输入经完整`simple_test`与新评估器，均保持180候选；报告原口径MPJPE及置信度／人数诊断。小样本初始化结果不是精度验收。 |
| 两卡短测 | 最终`smoke-r3` native exit0，6个微批迭代／3次优化更新；两rank各218份优化器状态，最终query逐位身份一致且已发生更新，峰值CUDA分配约1.01GiB。短测配置、权重和日志独立保存，不进入正式训练。 |
| 正式训练 | `formal-r1`于10月22日21:32启动；10月23日10:06核对原监督器／torchrun PID及创建tick一致，两rank仍运行。完成51轮完整评估，当前第52轮、全局287950微批迭代；本次loss6.0257、query梯度0.0349、joint梯度0.0770，均有限。两rank正式初始化与结构验证一致，未使用短测更新。 |

## 过半监督结果（10月23日10:06历史）

截至上述监督时点，每轮评估7,824帧。原口径最佳MPJPE为第39轮127.1275mm，最佳checkpoint已保存；第51轮MPJPE为130.0476mm，置信度>0.2候选匹配MPJPE为173.2291mm、人数MAE为0.1476。原口径含GT辅助候选匹配，不能据此单独认定部署精度改善。[逐轮评估原值](results/evaluations.jsonl)。

当时周期checkpoint已生成至`epoch_50.pth`，`latest.pth`指向该文件；每卡上下文约1,782MiB，CUDA峰值分配约1.01GiB，GPU1原PID3887468的9,138MiB上下文仍在。该次监督未见OOM／非有限值／异常退出。后续100轮及训练后最佳导出已完成，当前结论见文首。

首次`smoke-r1`在分布式初始化前因当前Torch1.13的双UUID枚举使设备计数为0而退出，未进入模型训练；原exit1与日志保留。已先核对GPU UUID，再使用`CUDA_VISIBLE_DEVICES=1,6`的数字枚举；`smoke-r2`通过，随后完善监督输出并以独立`smoke-r3`验证当前入口，未升级工具或改动其他任务。ONNX沿用已验证的子进程protobuf Python实现兼容方式，未安装或降级依赖。

## 迁移阶段的远程代码与日志（历史）

主机：`ssh gpu-server`（c01）；算法根目录：`/public/cyd/Person-in-WiFi-3D-repo`；环境：`/home/ubuntu/miniconda3/envs/PersonInWIFI/bin/python`，Torch1.13.1+cu117／MMCV1.5.3／MMDetection2.25.0。

本机算法代码：`D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/opera/models/pose180/`；配置：`configs/wifi/petr_wifi_pose180_shared.py`；工具：`tools/pose180/`。仅上传本轮14份明确源码／配置，未全目录同步或执行GitHub push。

迁移实验历史目录：`/public/cyd/Person-in-WiFi-3D-repo/result/piw24_pose180_shared_20261022_r1/`，该实验已结束；从零续训的保存目录与后续查询入口见文首`extra100_r2`。

- `jobs/formal-r1/state.json`：原生命令、GPU、监督及torchrun PID／创建tick；`stdout.log`、`stderr.log`为完整原始日志。
- `initialization.json`：两rank的迁移、初始query、空优化器与epoch0／iter0身份；`progress.json`及`progress.jsonl`记录迭代、有限loss／梯度和显存。
- `evaluations.jsonl`及框架原始日志：每轮完整7,824帧评估；周期／最佳／最终checkpoint保存在本目录。
- `gates/`、`jobs/validate-r1/`、`jobs/export-r1/`、`jobs/eval-r1/`和`smoke-r3/`：结构、导出、原生评估和最终短测原值／日志。
- 启动时监督PID262977、torchrun PID262980（start_ticks 192348156）；主rank PID262985。后续须重新核对PID创建时间与命令归属，不直接复用历史PID停止进程。

迁移实验的历史只读查询入口（本轮未执行，不用于查询从零续训）：

```powershell
python tools/pose180/remote.py run 'cd /public/cyd/Person-in-WiFi-3D-repo && python3 tools/pose180/manage.py status'
```

迁移正式训练已结束，**不得再次运行start formal**。SSH断开／工具等待超时不等于原生进程失败；先确认原进程、日志和检查点变化。OOM、非有限值和明确逻辑错误保存后停止受影响批次，不自动重试／调参／续跑。

## 迁移阶段监督安排（历史）与后续边界

迁移训练启动时曾记录每90分钟监督，ID `180-query-90`；这是旧阶段安排，不表示当前从零实验启用定时监督。本次没有创建或变更定时任务。迁移最佳／最终权重及训练后CPU ONNX／ORT核验现已完成，从零实验和条件续训恢复见文首。

上述迁移训练阶段未运行Lite／SDK。10月24日后续部署、耗时及稳定性实测见[部署实测](deploy/RESULTS.md)，独立候选未替换原演示基线或帧协议。新180-query模型不沿用旧100-query模型的逐位分数门禁；数值／量化精度仍独立保留。D47未根治，旧DATA独立暂停，HDMI长期边界保持。

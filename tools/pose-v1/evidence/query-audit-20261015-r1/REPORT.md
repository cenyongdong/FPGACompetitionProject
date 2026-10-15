# 当前2024推理模型的query规模与冗余分析

日期：2026-10-15，Asia/Shanghai。范围：本机源码审查、已归档7824帧输出的离线统计；无新模型推理、训练、导出、部署或板端操作。

结论：Pose decoder的100个候选槽相对于数据集每帧1–3人具有容量余量，但当前权重下不能无损删除大多数候选。Joint/refine decoder实际只有14个关节query；原路径在100个候选batch上重复同一计算，这部分冗余已经被共享细化实验验证。不能将二者合称为“两套100个query”。本分析不作缩减query数量的架构决定。

## 实际模型与代码证据

当前部署来源仍为2024版epoch442，区别于归档的2026训练旁支。实际张量路径为：预处理CSI `[1,180,60]` → Linear(60,256) → 六层encoder `[180,1,256]` → encoder姿态/分数头、TopK100初始坐标 → 三层Pose decoder `[100,1,256]` → 最终置信度TopK100 → 两层Joint/refine decoder → 100个分数及 `[100,14,3]` 姿态。

- `D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/result/code_faithful/petr_wifi.py`：num_query100、encoder6层、pose decoder3层、refine decoder2层、14关节、维度256、8头、FFN1024、max_per_img100。配置中保留ResNet/neck声明，但实际PETR.simple_test直接reshape CSI并调用self.head，不经过图像backbone/neck。
- `opera/models/utils/transformer.py:414`：细化嵌入为 `Embedding(num_keypoints, embed_dims*2)`，即14个关节query。原始细化输入是 `[14,100,256]`；100属于候选batch维，各候选之间不在这个维度做self-attention。
- `opera/models/utils/transformer.py:248,327`：两类decoder均先调用attention layer；reference坐标在回归后做加法，没有送进attention。Pose decoder仍有不同的100个可学习query及query之间的self-attention，不能按细化的共享方法直接合并。
- `opera/models/utils/transformer.py:566`、`opera/models/dense_heads/petr_head.py:325`：当前单图像eval共享细化，attention/回归batch从100变为1，原100套坐标继续按层加上公共偏移。训练dropout、多图像、额外attention参数保留原路径；不能将该结论推广到候选条件化的新版模型。
- `opera/core/bbox/assigners/hungarian_assigner.py`、`opera/models/dense_heads/petr_head.py:720`：分类与关键点代价Hungarian一对一匹配，每人一个正样本，其余背景分类；关节回归只监督匹配正样本。这说明100是候选容量，不是人数或关节数。
- `opera/datasets/wifi_pose.py:244`：现有MPJPE用GT在全部候选间做全局greedy一对一匹配，不依赖置信度筛掉背景。该指标不是人数检测、漏检或当前最高分单骨架演示的精度。

论文也明确将Pose decoder设为100个可学习query、三层decoder；这是所采用模型的设计配置，并非证明100为本项目最优值的消融证据：[CVPR2024原论文](https://openaccess.thecvf.com/content/CVPR2024/papers/Yan_Person-in-WiFi_3D_End-to-End_Multi-Person_3D_Pose_Estimation_with_Wi-Fi_CVPR_2024_paper.pdf)。本轮网页搜索返回相应原文摘要，PDF直接抓取403；本地源码是本报告的实现判定依据。

## 本轮实际离线统计

执行位置Windows，工作目录 `D:/FPGACompetitionProject`；已有Python3.14.6/NumPy2.5.2，无安装。运行 [analyze_saved_candidates.py](analyze_saved_candidates.py)，一次执行exit0、80.791秒，预算120秒。前置条件为已归档的共享前完整FP32输出及本机对应GT；两个输出SHA256与原summary一致，7824份GT全部与原逐帧SHA256一致，分数已降序。身份/形状不符、非有限值、无法匹配、超预算或独立基准误差达到0.001mm即停止，不重跑负载。

使用原100候选模型保存的最终输出，按最终置信度截取前K个，再在这些候选内按原greedy规则与GT匹配。为避免依赖PyTorch，距离用NumPy float64重算；全100的总体123.085352080mm，对比原FP32记录123.085352129mm；逐帧最大差0.000121051mm。统计不是新精度验收门禁，不影响正式逐位比较要求。

| 最终保留候选K | 全7824帧MPJPE/mm | 相对全100增加/mm | 原全100匹配的人体候选保留率 | 三人帧MPJPE/mm |
|---|---:|---:|---:|---:|
| 100 | 123.085 | 0 | 100.00% | 152.526 |
| 50 | 124.232 | 1.147 | 94.71% | 154.651 |
| 20 | 126.381 | 3.296 | 90.67% | 157.863 |
| 10 | 129.151 | 6.066 | 88.50% | 161.903 |
| 5 | 132.039 | 8.954 | 86.18% | 166.782 |
| 3 | 140.360 | 17.274 | 79.25% | 189.639 |

这里的“保留率”只表示原全100 GT匹配所选候选是否仍在前K，不能称人体检测召回率；其他候选仍可能给同一GT提供足够好的替代预测。greedy匹配也不是全局最优分配，缩小集合的误差不具有一般的单调保证。

15116个人体GT对应的全100匹配候选，其置信度排名中位数2、90百分位17、95百分位53、99百分位91。平均置信度≥0.5的候选仅1.916个、最大3个，这与多数输出被分类为低置信度相容，但低置信度输出仍可被GT辅助评估选中。单人2586帧最高分Top1误差109.228mm，而全100辅助匹配99.665mm，不能把后者直接作为最高分演示精度。

本轮得到的结论是“当前排序并不保证最准确姿态都在前几个”；并未证明重新训练的小query模型必然损失同样精度。最终排名也不是原query编号，本轮没有统计原query槽的长期激活频率。

## 已有共享细化证据与优化取舍

[共享细化原报告](../shared-refine-20261014-r1/README.md)已经对完整7824帧验证：MPJPE123.085352129→123.085352227mm；分数逐位一致，最大关节差0.000533mm，坐标不是逐位一致。服务器含探针整模型12.212→11.081ms、细化区间2.958→1.819ms，不代表Lite收益。2026-10-15已完成的去ScatterND板测图仍未共享细化；本轮只查资料，不将其他并行工作的待运行目录当作完成证据。

优先方向是复用已验证的共享细化，在全部100候选保留的前提下消除重复attention/回归。14个query分别对应14个输出关节，本身不是因人数少而可直接删的对象；整个细化模块是否值得保留，需要单独消融，不能由“公共偏移”推断为无效。

Pose decoder减少100→20/10值得作为后续候选实验，但需要用户决定精度与部署目标：只保留末端TopK不减少此前100个Pose query的计算；真正减少query会改变self-attention上下文、encoder初始TopK坐标与学习query的配对和已训练参数槽。需要同步处理num_query、two_stage_num_proposals、嵌入和max_per_img，通常要微调或重训，再以固定数据/预算比较。不能只改num_query或凭最多3人直接截成3。

其self-attention交互项随Q²变化、与encoder的cross-attention交互项随Q×180变化，FFN及query侧投影随Q变化；encoder和memory侧投影不随Q同比减少。不能将query数量下降90%写成整模型或板端耗时下降90%。应同时报告GT辅助MPJPE、按置信度的人数/漏检/误检与姿态精度，以及Lite完整Engine延迟、内存和实现情况。

实际产物为本报告、完整[results.json](results.json)及可重算脚本。没有更改源码、权重、模型图、部署、两处TopK或暂停故障任务。

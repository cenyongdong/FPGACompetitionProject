# 最终门检完整保存与晚源取证结果

本轮新增取证及保存功能通过，较高负载数据可靠性仍未通过。Host及原三窗正常；一次固定QPC5.05Hz诊断第25个返回失配，已停止。没有重试旧fps505、继续停止的Engine或调整频率。

## 工程与身份

隔离final_evidence_check/bridge通过明确接口调用SDK无关Recorder、公开SDK适配和save-only模块。返回原始输入/分数/姿态/raw先保存再执行冻结严格比较；结束序列化不再oracle。每帧主线程释放旧四个源句柄/拥有Host值并保留当帧437/582写回前CPU值。最终比较失败先通知workers停止，再在Engine存活且无下一forward/reset时读两轮。

- 新ELF：`bca60bb4edc5cc7097eb7a5b5de7cbd2408c6f7784df06b2276845b8d1cc86a3`。
- manifest：`8f0adfb2fe3221bd6af310ac61a041dbab61145303bd52461512fece903afcd2`；403载荷、138来源。
- 33原ELF逐位上一批，全部冻结源、SDK3.39/头库/BOOT/模型/RAW/数学/两缓冲/cookie/745/reset(1)/profiling-off保持。
- r1 SDK自检缩进Werror构建停止未板测，日志保留；r2使用新文件修正，额外核对晚读取dtype/region/chunk/offset/kind/address，Native/ARM均通过。首次控制命令误指package子目录，未启动Host，修正根路径后才运行一次Host，旧日志及空归档保留。

## 模块与正常回归

Native/ARM拥有值、线程所有权、字节上限、重复条目/目录拒绝、逐帧清除、两轮与部分读取失败、有限坏值/NaN原始保存通过；保存后原数学异常分别仍为`Timing actual model output differs`和`Timing score nonfinite`。真实图Host公开read8次/134400字节，四源67200及三CPU输出17600字节逐位核验，不打开设备。

Host107、12条注册和59600FP32通过。三窗＋重复4次/60400FP32逐位旧参考，490编码/460网络/全部4来源/实际PTS/Native像素/2688关节核验通过；八项保存任务成功，正常drain/LAST/STREAMOFF/子回收/网络source0/Engine在join后毁/内核同。

## 一次诊断的失败数据

前24次正确362400FP32，第25次inv24/frame100024/S53_02_301有限姿态失配128项，最大绝对差0.2705078125模型单位。输入10800值和分数100值逐位正确；25份返回全部写出root结果、时钟、索引及presaved，包括失败帧60400字节F32＋86400原始CSI。八项持久化全部成功，不再因重复oracle丢失汇总结果。

| 证据 | 结果 |
| --- | --- |
| 582数据输入、649数据输入 | Host及两轮晚read全部逐位gold |
| 582更新输入、649更新输入 | Host各128不同；两轮晚read与各自bad Host逐位一致，仍各128不同 |
| 437 CPU两输出 | 各100值逐位gold，值及索引均正确 |
| 582写回前CPU输出 | 128项不同；从本次实际bad输入及真实RAW独立NumPy重建4200值逐位一致 |
| 649独立NONE重建 | 本次实际输入＋真实RAW重建4200值逐位最终姿态；未单独捕获649 CPU输出 |
| 对象/声明/归属 | 400记录/200输入，跨复制无对象变化，87个Host目标地址；192查询200条全部234，计数不作为DMA/cache fence |

两轮四源共134400字节全部读成功、跨首末读0.81511ms，无取证错误；四份Host源67200、三CPU输出17600及原8输入115360字节均保留。更新源地址分别109187072/109146112，ADDR、offset0/capacity16800、同固定设备。静态图582更新值4418的生产HardOp为8131，Gather442与TopK437是其祖先；未捕获442输入/即时输出及该ZG边界，不能认定哪个生产者有问题。

独立重建使用两份真实RAW参数50400字节，均与N1参数逐位同，SHA256 `168c35ff2cd1f557bfcbc8744b4931f38a532c9c37568eec66ac918b5c6dafe2`，4200个唯一合法坐标。数据异常已存在于582收到的更新输入；本次582内核计算和真实索引没有制造额外错误。错误位位置沿途相同不等于各阶段错误值相同，完整张量也不直接相等。

## 边界与清理

PC发送27（无接收确认）、板收26/消费25/返回25、0覆盖/拒绝；仅24正确结果发布显示。347输入提交/346归还、347采样/345捕获图像/315网络前缀逐NAL、真实PTS、像素一致；23个真实来源可见。前缀检查器按25返回记录列missing23/24：23为正确尾源未捕获，24为失配且未发布，不能记作正确已完成源。两采样尾帧未捕获，无正常drain/LAST；两abort STREAMOFF成功、子进程错误路径回收、网络sources0、Engine在workers join后销毁，内核同，端口与项目进程全部结束。客户端10053随失败结束，不据此判网络导致坏值。

两次准备普通512KiB等价页21和16，本批规整0；最终MemAvailable749480KiB/CmaFree9876KiB/普通16仅快照，不证明无泄漏或任意碎片下首次启动可靠。未清缓存、重启、改CMA/内核/BOOT/模型/SDK或初始化HDMI。

两轮晚read不是独立硬件观察：可能物理复用，且与原输入读取共享SDK/UDMA路径。因此证据削弱“只在第一次Host复制中瞬时读错、后来源已恢复”的解释，但不排除共用读取路径、上游生产/存储或未捕获写入。CPU437正确也不能证明原Gather442或ZG8131正确。本批保存I/O和句柄保留改变时序，不作严格5Hz/长期/根因已修结论。

证据：`evidence/final-evidence-20261010-r2`的build、Host、三窗acceptance，failure-review、failure-host-comparison、failure-scatter-math、objects、counts、视频/网络前缀及completion-review。下一见FINAL-EVIDENCE-NEXT及ADR_33。项目管理83/100保持。

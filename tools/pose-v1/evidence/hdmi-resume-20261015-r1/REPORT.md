# HDMI候选恢复执行报告

执行日期：2026-10-15，Asia/Shanghai。执行平台Windows，工作目录`D:/FPGACompetitionProject`。用户明确唤醒后恢复原批准的1080p60隔离候选，未连接板端、未下载/替换BOOT、未修改SDK/模型/RAW/CPU注册/NPU分配，旧DATA调查继续暂停。本轮因仿真外层超时已停止该负载，没有自动重跑。

## 结果

| 项目 | 实际执行/产物 | 结论与限制 |
|---|---|---|
| 暂停身份 | 核对暂停清单17项源码，全部相同，见resume.json；原资源审查38项再次SHA核对 | 38项参考/BOOT均保持，完整前后值见protected-reference-identities.json |
| 页边界复现r3 | 新偏移64/4032完整帧用例；4032在167.5ns报faults=2，xsim工具exit0但门检正确exit1 | 红例原始日志/源码保留，不改为通过 |
| 页边界修正r4 | 保留64字节帧址对齐，按剩余页字数/帧字数/16拍最小值拆burst；编译/展开/仿真exit0 | 偏移0/64/4032各518400字/4147200字节完整地址/数据通过，相应32400/32401/32401 burst；后两者各2个短burst |
| 新扫描逻辑 | stream_fifo、pixel_scan、scanout；控制器新增display_running和欠载输入/同步/fault位3 | CSR→AXI→FIFO→并行RGB逻辑已组合，尚未PS/DDR/TMDS物理集成 |
| 原生综合 | Procise2025.1.1temp/SVN32494，JFMQL30TAI676H，预算180秒；10.6197179秒exit0，真实EDIF | 新扫描FIFO实际1个RAMH36E1；仅展开/综合，自动导出FDC无时钟/时序约束，不能代替布局布线或时序验收 |
| 扩展仿真r5 | 编译1.422秒exit0、展开6.078秒exit0；原始xsim.log全部断言完成，内核run elapsed88秒、仿真时间50.015838873ms | 外层simulate调用90秒TimeoutExpired，驱动exit1，**整体不验收**；不能以日志PASS掩盖超时 |
| 新验证入口 | 拆分core/pixel独立展开根、FIFO单元结束停钟；超时保存原始输出/源码与清理本次进程树 | 仅Python AST静态语法通过，未动态执行；r6/r7新目录不存在，须新批次确认 |

脚本实际命令：`python FPGA/hdmi_candidate/scripts/simulate.py r3`、`... r4`、`... r5`和`python FPGA/hdmi_candidate/scripts/procise_check.py scanout r1`。每个仿真阶段90秒，新目录、无自动重试；原生展开/综合总180秒，超时仅终止该批进程树，不进行位流或设备操作。r3发现边界逻辑问题后修正，再以新r4验证；r5外层超时后停止该负载，未延长预算或新开同负载。

## 代码与行为

帧控制器按4KiB边界拆分burst，不再把合法64字节对齐帧址交给读主机后拒绝；本地拒绝且reader已idle时清waiting，避免停止状态锁死。原AXI只读主机保持一次在途、AR稳定、RVALID&&RREADY接受、停止丢弃排空以及缺失RLAST不伪造完成。

新增FIFO是64位写/16位读、低位像素优先、四像素后释放字、Gray指针各两级同步，RAM同步读端用末像素的下一字地址预取，字间无空拍。深512字/4096字节。flush只在内存safe_idle成立后进行，两个域各三级同步释放。FIFO单元日志覆盖两异步时钟、2048字多次环绕/随机背压、部分字flush后复用。

像素扫描自由运行2200×1125，HS44/VS5正极性，活动区1920×1080。START在新帧边界启用，避免启动途中消费空FIFO；STOP保持同步和DE、RGB转黑。欠载同步回mem域，faults位3置位、停止新请求并排空已接受AXI；显示读停止与物理扫描分开。r5原始日志记录2073600个实际RGB像素逐点比对、完整4147200字节、页尾4032帧址、欠载等待在途AXI排空，以及像素停钟后的STOP通过断言。仍受外层超时整体失败约束。

safe_idle只用于证明候选不再访问帧DDR，不表示最后像素已被屏幕显示；本地复位不能代替在途AXI完成。DMA窗口为已知udmabuf范围参数，应用必须另持有对应实际帧块。按148.5MHz活动像素计算4096字节FIFO约13.79µs余量，1080p60读带宽248832000字节/秒，仅数学需求；真实DDR仲裁、NPU/VPU并发和硬件欠载尚未验证。

## 超时证据与修正范围

旧脚本使用subprocess.run封装.bat，TimeoutExpired时未写本阶段stdout/执行结果，且只终止启动器不能保证完整进程树被停止。此次独立xsim.log记录断言完成并自然退出；随后Get-Process核对procise/xsim/xelab/xvlog为空，没有结束其他用户进程。原execution.json保留其只有前两阶段的实际内容，另建timeout-review.json，不回写历史成功清单。

新增脚本准备了Popen显式记录超时、taskkill仅指向本次PID进程树、失败也保存源码/日志和result=false；新core/pixel根减少长扫描时无关用例时钟事件。不把这份修正准备或AST静态检查称动态通过。下一批拟用r6 core，第一组通过才r7 pixel，每阶段仍90秒；任何超时/非零/Fatal/缺PASS立即保存停止。具体入口见[RESUME](../../../../FPGA/hdmi_candidate/RESUME.md)。因Agents.md规定禁止自动重试失败负载，需用户明确确认新批次。

## 原工程、物理层与约束审查

原XPR101项引用中93存在，8项process_control Tcl缺失；JFM_Kits中有6项同名，place_pre/post缺失，与已有REFERENCES一致。PS_AI BD、wrapper、MIG/XCI和AI_Mate EDIF均有资料基础，不能由缺8项hook就声称没有核心源码或一定无法复现。没有安装hook、复制补丁、替换数据库、迁移/升级IP或更换工具。当前2019.1仅用于RTL辅助仿真，不能反过来要求2018.3安装，也不能把2018参考工程直接当已在2019.1复现。

已审查HP2原读写所有权和GP0 cam窗口/低9位地址别名。新增显示读主机需明确取代旧读通道并保留原相机写端；新CSR需显式总线适配/解码，当前尚无新板端基地址。没有改原`display_en`或在当前BOOT访问新偏移。

原源码`uihdmitx.v:92,136`时钟序列器使用字符串"1111100000"，ASCII截断低10位为0x030/二进制0000110000，而预期二进制1111100000是0x3e0；原序列器复位含组合反馈。是源码风险，原文件未改、当前BOOT对应未证，**不是已证明的实屏故障原因**。原语手册支持PAR2SER10位级联，仍缺完整TMDS差分/电平/742.5MHz支路与1485Mb/s能力的实现证据，不能用两只普通BUFOUT猜测替代。

已形成[集成/时钟/复位/Gray/邮箱CDC约束清单](../../../../FPGA/hdmi_candidate/INTEGRATION.md)；未加载占位FDC、未做布局布线、setup/hold/未约束路径签核。原生时钟模块此前综合结果保留原范围，未接入当前扫描顶层或进行PLL器件仿真/频率实测。显示器用户现场仍为已接入但不支持时序，误点稳定画面作废。

## 证据与结束状态

- r3/r5在各自目录新增failure-work-copy，保留当时源码/原日志和xsim诊断；旧执行/manifest不改。
- r4保存完整仿真产物/日志；Procise scanout r1保存完整returned-project和EDIF。各目录另存files.sha256.json，不引用变动中的工作源码代替历史快照。
- 本轮保存before文档、最终候选源码快照、documentation-revision.json、protected-reference-identities.json和final-state.json。历史暂停清单/原完成清单不回写。
- 所有工具调用已返回，本批工具进程盘点为空；没有板端SSH、Docker或其他后台作业。旧DATA仍暂停，下一次仿真须新批次确认；本次不把整个HDMI任务标为完成。

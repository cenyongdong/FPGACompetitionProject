# 当前待办（2026-10-11）

当前：software/demo端到端有界演示完成，源码/说明/TechDetails已交付，全部测试退出。下一由用户审查首版展示；不自动启动长测或恢复旧坏读排查。旧PRODUCER-PREPARED-NEXT暂停保留，恢复时核对ADR_44及原失败身份，不能接续失败Session。后续仍为永久首启动、完整57样本精度参考、严格5Hz/30分钟、真实采集与HDMI独立验收。[本批结果](tools/pose-v1/DEMO-RESULTS-20261011.md)／[检查点](tools/pose-v1/evidence/demo-20261011-r4/next-checkpoint.json)。以下当前为历史。

当前：目录预建本批结束，198完整正确＋inv94 DATA96失败，四晚物理源正确。[下一首次Host目的租约与公开CPTR失败对照](tools/pose-v1/PRODUCER-PREPARED-NEXT-20261011.md)仅准备，未实现执行。保持原异常读取，不重跑旧Session，不以目录整改或晚源正确计on100/完整103/严格5Hz/长期/HDMI通过。

2026-10-11最新：[ADR_43](ADR/ADR_43.md)记录源租约/Host188160字节read过、153前向正确、有VPUinv49目录等待915.86ms且准备截止成功拦截，物理晚源read未触发／根因未修；[结果](tools/pose-v1/PRODUCER-SOURCE-READ-RESULTS-20261011.md)／[下一目录预备](tools/pose-v1/PRODUCER-SOURCE-READ-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-source-read-20261011-r2/next-checkpoint.json)。221 NoInput视频前缀/abort清理过，所有连接结束，原异常读取保持，下一未执行，以下当前为历史。

2026-10-11最新：[ADR_42](ADR/ADR_42.md)记录高地址SDK前缀控制、四调用/off100通过、on inv49 DATA800逐位前帧A的独立更小失配；首次输出已错但无晚源证据，责任未证。214 NoInput视频前缀/abort清理过，全部连接结束；[结果](tools/pose-v1/PRODUCER-ADDRESS-RESULTS-20261011.md)／[下一失败只读租约](tools/pose-v1/PRODUCER-ADDRESS-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-address-20261011-r2/next-checkpoint.json)。下一未执行、原正式异常读取保留，以下当前为历史。

2026-10-11最新：[ADR_41](ADR/ADR_41.md)归档reset前分段／准备后绝对时隙、off/on各100及307 NoInput视频正常回收。2352000 FP32逐位，旧1.764秒尖峰未复现，保存区间等待已观察但底层原因未证，正式坏读未修；[结果](tools/pose-v1/PRODUCER-PHASE-RESULTS-20261011.md)／[下一公开高地址可行性](tools/pose-v1/PRODUCER-PHASE-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-phase-20261011-r2/next-checkpoint.json)。原异常读取保持、下一未执行、程序连接全结束，以下当前为历史。

2026-10-11最新：[ADR_40](ADR/ADR_40.md)记录同身份off100通过、on82数值正确后时隙失败及reset前1.764秒空档，正式根因未修。271packet／270 NoInput图像／162复制交叠、异常清理通过，正常drain-LAST未过；[结果](tools/pose-v1/PRODUCER-VPU-RESULTS-20261011.md)／[下一分段观察](tools/pose-v1/PRODUCER-VPU-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-vpu-20261011-r2/next-checkpoint.json)。原异常读取保留，下一未执行，全部程序连接结束，以下当前为历史。

2026-10-11最新：[ADR_39](ADR/ADR_39.md)记录独立19成员物理部署／四调用、mock无数据搬运的门检修正与locale只读核验。47040 FP32／0→11／释放通过，正式并发根因未修；[结果](tools/pose-v1/PRODUCER-GROUP-RESULTS-20261011.md)／[下一有无VPU对照](tools/pose-v1/PRODUCER-GROUP-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-group-20261011-r2/next-checkpoint.json)。100调用未实施，原异常读取保持，以下当前为历史。

2026-10-11最新：[ADR_38](ADR/ADR_38.md)记录真实参数／19来源映射／受限FP16-TF32参考及mock独立0→11。数学参考已闭合，物理读取根因未修；[结果](tools/pose-v1/PRODUCER-REFERENCE-RESULTS-20261011.md)／[下一](tools/pose-v1/PRODUCER-REFERENCE-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-reference-20261011-r2/next-checkpoint.json)。无新物理前向／并发通过，全部程序和连接结束，以下当前为历史。

2026-10-11最新：[ADR_37](ADR/ADR_37.md)记录生产者检查器条件copy、零指令Cast、19成员参考缺口、官方部署映射与日志门检/误检索修正。[结果](tools/pose-v1/PRODUCER-CONTRACT-RESULTS-20261011.md)／[下一](tools/pose-v1/PRODUCER-CONTRACT-NEXT-20261011.md)／[数据核验](tools/pose-v1/evidence/producer-contract-20261011-r2/data-review.json)／[恢复](tools/pose-v1/evidence/producer-contract-20261011-r2/next-checkpoint.json)。无模型前向，新根因未修；r3 exit1为一/两日志数量错误，原码/数据保留，r4仅编译。全部会话结束，以下当前为历史。

2026-10-11最新：[ADR_36](ADR/ADR_36.md)匹配AXI／UDMA责任审查及两方法／四条件内存对照完成；400动态对过，无NPU生产，原模型根因未修。锁／轮询／cache同步存在但生产完成未知。[结果](tools/pose-v1/AXI-READ-RESULTS-20261011.md)／[责任证据入口](tools/pose-v1/AXI-READ-RESPONSIBILITY-20261011.md)／[下一](tools/pose-v1/AXI-READ-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/axi-pair-20261011-r4/next-checkpoint.json)。本批已结束、无规整／后台；以下当前为历史。

最新批次结束：正确链接ReadPhase及Host107／四窗全链通过，唯一QPC5.05诊断48正确后192失败，立即592坏值等于前输入同偏移，CPU前不变，两晚源正确。下一优先匹配AXI region／共享UDMA暂存实际read完成／资源所有权机制，见[结果](tools/pose-v1/READ-PHASE-RESULTS-20261011.md)／[方案](tools/pose-v1/READ-PHASE-NEXT-20261011.md)／[恢复点](tools/pose-v1/evidence/read-phase-20261011-r3/next-checkpoint.json)。保留全部异常读取，不猜延时/cache或用第二read修补继续；新方案未执行，103完整／严格5Hz／长期／HDMI待，以下当前为历史。

最新批次已结束：原Gather／ZG公开边界模块、Host107及四窗口通过；唯一QPC5.05诊断55正确后192失败，初始Host索引异常、两晚源正确，保存与清理完整，根因未修。下一先核对实际SDK读完成接口，再设计read返回后立即拥有快照／CPU调用前目标字节观察。见[结果](tools/pose-v1/UPSTREAM-BOUNDARY-RESULTS-20261011.md)／[方案](tools/pose-v1/UPSTREAM-BOUNDARY-NEXT-20261011.md)／[恢复点](tools/pose-v1/evidence/upstream-boundary-20261011-r4/next-checkpoint.json)。新方案未执行，不重跑旧失败／调频／猜cache或自动修补坏值继续；严格5Hz／长期／HDMI待。以下当前为历史。

2026-10-10最新：[完整保存与晚源结果](tools/pose-v1/FINAL-EVIDENCE-RESULTS-20261010.md)／[ADR_33](ADR/ADR_33.md)／[下一边界方案](tools/pose-v1/FINAL-EVIDENCE-NEXT-20261010.md)／[当前恢复点](tools/pose-v1/evidence/final-evidence-20261010-r2/next-checkpoint.json)。保存缺口已解决，582上游数据异常未解决；本批已停止、无后台，严格5Hz/长期/HDMI保持待验。以下最新为历史。

2026-10-10当前：新组合三窗／2Hz103／名义5Hz103有限内容通过，5.05Hz有限姿态异常已完整保存；下一先按[方案](tools/pose-v1/COMBINED-READ-NEXT-20261010.md)实现有界最终门检设备源/CPU输出捕获及save-only模块，Host／三窗后新目录一次诊断，不再调频率或重跑旧失败。 以下当前为历史。

2026-10-10当前任务已从用户暂停恢复，公开read候选107真实画面及完整数值／编码有限门检通过，底层根因与长期待验。下一按[新方案](tools/pose-v1/INPUT-READ-NEXT-20261010.md)进行独立显示／TCP／owned-AU组合回归，再有界5Hz；不回填旧程序或重跑旧失败。先读[当前检查点](tools/pose-v1/evidence/input-read-20261010-r1/next-checkpoint.json)。本批程序／连接全结束，无后台。以下待办为历史。

2026-10-10当前：无视频真实混合模型三窗＋103完成，107前向1615700 FP32逐位正确、对象及计数合法，规整0、全会话结束。旧数值故障未复现／根因未修，下一[同身份模型／合成VPU有限对照](tools/pose-v1/MODEL-ONLY-NEXT-20261010.md)仅准备，未新视频或并发门检。先读[恢复点](tools/pose-v1/evidence/model-only-20261010-r1/next-checkpoint.json)。稳定并发103、长期／持续5Hz、HDMI／采集终版／零拷贝待。以下当前为历史。

2026-10-10当前：公开PL DDR管理器／容量与合法较高SDK来源对照完成，动态100对＋VPU100对2388000 FP32正确／227图像PTS过、自有块归还、规整0，全项目程序与代理会话结束。无模型／NPU前向，旧192异常仍未解决。下一[原混合Engine移除视频负载三窗→103](tools/pose-v1/PLDDR-POSITION-NEXT-20261010.md)仅准备，尚未执行。先读[恢复点](tools/pose-v1/evidence/plddr-position-20261010-r1/next-checkpoint.json)。稳定并发103／持续5Hz／长期／HDMI／采集终版／零拷贝待，以下待办为历史。

2026-10-10当前：真实类型静态／动态／动态＋VPU独立对照已全部完成，原主／Host107保持，3582000 FP32正确、226合成编码ID与PTS过，无模型Session／NPU前向，旧坏块未复现。一次规整完整取证，程序／会话关闭。[恢复点](tools/pose-v1/evidence/typed-scratch-20261010-r1/next-checkpoint.json)。下一[公开管理器容量与合法较高位置](tools/pose-v1/TYPED-SCRATCH-NEXT-20261010.md)仅准备，未申请占位或新模型测试；稳定103／持续5Hz／长期／HDMI／采集终版／零拷贝待。以下待办为历史。

2026-10-10当前：实际对象身份候选已完成新Host107和三窗全内容；唯一103在inv72／192索引128非整数拒绝，对象／类型／范围稳定，7坏段同前次复制，两晚源正确；已停止，规整0、会话全关闭。下一[真实类型常量→动态模式SDK scratch](tools/pose-v1/TENSOR-IDENTITY-NEXT-20261010.md)仅准备，先独立对照，不用重复制／cache／等待猜修复。完整稳定103／性能／长期／HDMI／采集终版及零拷贝继续待。[当前检查点](tools/pose-v1/evidence/tensor-identity-20261010-r3/next-checkpoint.json)。以下待办为历史。

2026-10-10当前：批准的独立SDK scratch门检完成，无VPU／编码并发各100对正确，200合成图像与实际PTS通过；原Host107身份复用，未新模型前向，模型数值可靠性未解决。代理会话关闭、规整0。[结果](tools/pose-v1/SCRATCH-COPY-RESULTS-20261010.md)／[检查点](tools/pose-v1/evidence/scratch-copy-20261010-r3/next-checkpoint.json)。下一[实际对象身份候选](tools/pose-v1/SCRATCH-COPY-NEXT-20261010.md)尚未实施；保持原复制／等待／数学／模型和异常读取，不猜同步或零拷贝。稳定103、持续5Hz／长期、HDMI／采集终版继续待；以下待办为历史。

2026-10-09当前：192计数诊断已完成Host／三窗；103第4次索引拒绝时公开计数已234，不能将等待到234当修正。七项取证完整，测试／连接全结束。下一[受控双源搬运方案](tools/pose-v1/PRODUCER-COUNT-NEXT-20261009.md)先无NPU验证30240／16800 SDK scratch，再设计有界VPU并发，尚未执行。完整103／稳定性能／长期／HDMI／采集终版待；当前完整输出门禁及旧源读取保持。

2026-10-09当前：单帧取证和独立落盘已接入，Host／新三窗完成。103第12次192拒绝，已停止、全会话关闭；不能勾选完整103或性能验收。下一按[最小方案](tools/pose-v1/INVOCATION-GUARD-NEXT-20261009.md)先区分192生产组234完成与SDK连续搬运残留，保留所有原异常／门禁；不重跑旧失败，不猜缓存或零拷贝。完整稳定性／长期／HDMI／采集终版继续待。以下待办以其历史状态理解。

## 当前接续：有限输出取证与独立落盘

- [x] 同身份独立第一轮103完整内容/593编码563网络核验，严格4.999251559Hz未过如实记录。
- [x] 第二轮38返回/37正确、39接收及完整异常数据/部分视频；第三轮停止。
- [x] 姿态652值/35行不同，分数及最佳骨架一致；同CSI早前inv10正确，不降为最高分门检。
- [x] 保存再比较耦合定位；SDK-free Frame/flush Native/ARM各12拒绝，原异常和后续任务保存通过。
- [x] 匹配SDK缓存助手、UDMA路径和六Host生产组静态审计，不直接映射或改SDK。
- [ ] 新隔离接入observer/独立落盘，Host107＋实际Host最终比较异常模拟，前门通过后新三窗和单次103取证。
- [ ] 同板异常根因、稳定5Hz/长期、HDMI/采集终版、合法映射与一致性继续待。

[结果](tools/pose-v1/STARTUP-GUARD-RESULTS-20261009.md)／[ADR_20](ADR/ADR_20.md)／[接入契约](tools/pose-v1/INVOCATION-EVIDENCE-INTEGRATION-NEXT-20261009.md)／[恢复点](tools/pose-v1/evidence/startup-guard-20261009-r1/next-checkpoint.json)。旧阶段通过和失败仍为历史。

## 当前接续：Host快照与582生产组完成检查回归完成

- [x] 新隔离快照/地址及容量/FP32对齐/计数等待；Native/ARM各11拒绝，Host107及真实47040字节shadow核验。
- [x] 原三窗＋重复4次完整数值/视频/网络；新103全部收到、消费和返回，无覆盖，完整1555300FP32、592编码562网络通过。
- [x] 824快照元数据和103计数，均首次638，没有额外等待；旧失败及异常源读取继续保留，不宣布根因。
- [x] 本次100计量画面5.000193338Hz/P95 251.199778ms达到既有有界门限，区别于长期稳定性和计算容量。
- [ ] 冻结当前诊断基线，独立首次启动/更长有界回归；复发时比较shadow、拒绝后暂存及晚源，不自动修补。
- [ ] SDK搬运/实际映射/生命周期/缓存与完成契约调查；根因与永久修复、HDMI、30分钟、采集终版仍待。

入口：[结果](tools/pose-v1/STAGE-GUARD-RESULTS-20261009.md)、[ADR_19](ADR/ADR_19.md)、[检查点](tools/pose-v1/evidence/stage-guard-20261009-r1/next-checkpoint.json)。以下待实现/103失败状态保留为历史。

## 当前接续：103实施后数据故障取证

- [x] 103/104预算与清理、30/100/105/180秒全边界、新低日志程序及独立画面参考；Host107/新三窗完整通过。
- [x] 103实际执行并在第61次异常后停止，前60完整输出906000FP32逐位核验，完整现场与部分视频回传。
- [x] 首次实际设备源两轮67200字节；同CSI旧中间值核对，暂存0有2096值差异/四NaN、两源稍后均正确。
- [x] 匹配实际AXI插件与默认跨区临时/read/write路径审计，不把API名称不同当修复。
- [ ] 复制返回Host shadow、目标地址对齐/区域/时间、异常Receiver计数：仅设计准备，未新硬件执行。
- [ ] 根因与最小修正后103/100计量验收；严格5Hz/HDMI/长期继续待，不能关闭数值拒绝或用规整修复坏值。

最新[结果](tools/pose-v1/BOUNDED-LOAD-RESULTS-20261009.md)／[ADR_18](ADR/ADR_18.md)、[ADR_17](ADR/ADR_17.md)。下面此前待实现103的条目是历史，当前已实现但负载未通过。

## 当前接续：2026-10-09 有限覆盖已完成

- [x] 异常Host暂存/源元数据/两轮SDK读取保留并写入规范；正常路径无新增读取。
- [x] 同身份33次2Hz及33次5Hz纯计时：996,600FP32、997编码937网络/5,446关节及释放核验。
- [x] 32次1,856条纯计时，额外查询0；区分有限输入节拍、画面完成和未覆盖回调范围。
- [ ] 103低日志入口：请求/worker/记录/时长/客户端/独立画面参考协调，保留捕获；尚未实现/执行扩展负载。
- [ ] 模型异常设备源读取与实际区域DMA/cache路径；旧坏值及尖峰原因未证，不能关闭捕获。
- [ ] 严格整机5Hz、永久首次启动、HDMI和30分钟，不能用本轮诊断通过替代。

结果与恢复入口：[SOURCE-COVERAGE-RESULTS](tools/pose-v1/SOURCE-COVERAGE-RESULTS-20261009.md)。下列接续项为此前状态，已完成有限覆盖由上方统一标记。

## 最新接续：r4源读回工具与未复现异常

- [x] 只在异常后保存源元数据与两轮SDK读回；Host107及Host字节一致性。
- [x] 保留控制超时/404，新就绪控制及三窗完整数值/真实视频回归。
- [ ] 模型异常时的设备源两轮数据，当前未触发；继续区域DMA/cache审计。
- [ ] 议定有限覆盖/自然首启动取证；禁止循环制造故障或把未复现写成修复。
- [ ] 原尖峰、严格5Hz、103负载、HDMI和30分钟。

## 最新接续：2026-10-09 数据块异常

- [x] 独立计时与额外SDK查询分离；异常保存拥有的Host输入。
- [x] Host107/12注册/59,600FP32、模拟非法索引和持久化契约；r2停止与r3修正归档。
- [x] 720字节实际失败、96/84周期块差异、120回传及资源清理审查。
- [ ] 有界源Tensor元数据和SDK读回判别，按证据最小修正；不重跑旧失败。
- [ ] 修复后完整数值/视频来源回归，再尖峰、103计量、严格5Hz、HDMI与长期。

## 最新接续：forward取证与索引失败

- [x] 隔离构建、Host107/IPC、原三窗完整数值与实际视频核验。
- [x] 失败145回传/213时钟、异常释放、规整前后归档；103身份计划准备。
- [ ] 新隔离纯计时控制，分离额外SDK状态查询；异常拥有值输入捕获。
- [ ] 新Host/三窗后有限诊断，定位GatherElements192索引来源及原inv28尖峰。
- [ ] 实施103有界低日志入口与完整来源核验；严格5Hz、启动可靠性、故障负载、HDMI及30分钟仍待。

2026-10-08最新：[独立显示子进程结果](tools/pose-v1/DISPLAY-PROCESS-RESULTS-20261008.md)、[恢复点](tools/pose-v1/evidence/display-process-20261008-r1/next-checkpoint.json)。70数值/视频来源正确；名义5Hz33全消费/无覆盖，实际4.99165Hz严格5Hz未通过，管理83/100保持，无后台。

- [x] 实际独立SDK无关显示进程、容量2/IPC信用1、拥有字节及退出回收；Host107/IPC/9拒绝通过。
- [x] 原三窗重复、2Hz及5Hz全参考/视频/时钟/进程回收门检。
- [ ] invocation28 forward221.61ms尖峰有限单钟定位与更长有界统计入口，见[下一方案](tools/pose-v1/DISPLAY-PROCESS-NEXT-20261008.md)。
- [ ] 全链超载/断流/重连/子进程错误/慢客户端清理、严格5Hz及30分钟。
- [ ] 安全连续申请/首次启动资源与HDMI匹配接口；本轮一次规整已用完，不自动再规整/重启。

<details>
<summary>历史清单与停止记录（不作当前任务指令）</summary>

2026-10-08最新：[整机计量结果](tools/pose-v1/SYSTEM-TIMING-RESULTS-20261008.md)、[恢复点](tools/pose-v1/evidence/system-timing-20261008-r2/next-checkpoint.json)。62前向和视频来源正确；4.22311Hz未通过5Hz，管理估计83/100保持，无后台。

- [x] 独立低日志/同steady_clock计量及Host107/传输身份拒绝测试。
- [x] 2Hz三预热＋30计量，全部33消费，完整数值/来源通过。
- [x] 5Hz33输入负载取证：29消费/4覆盖，扣预热26计量，严格参考与视频通过。
- [ ] [SDK无关显示worker](tools/pose-v1/SYSTEM-TIMING-NEXT-20261008.md)：保持Engine主线程，容量2拥有值队列及释放/异常门检，新修订回归。
- [ ] 首启动资源条件与安全连续分配；最终order7+为0，不自动再次规整/清缓存/重启/CMA改变。
- [ ] 超载/断流/重连/慢客户端完整清理、HDMI和30分钟。


2026-10-08最新：[保存优先/单次规整结果](tools/pose-v1/PRESAVED-RESULTS-20261008.md)、[检查点](tools/pose-v1/evidence/tcp-presaved-20261008-r1/next-checkpoint.json)。有限TCP三/27全链32前向通过，旧失配未复现/原因未知，长期内存可靠性另验；下方阻断为历史。

- [x] 全输出保存后原门检，Host/协议/保存契约及32完整前向逐位验证。
- [x] 一次规整取证、两个VPU进程/984编码/864网络完整来源/PTS/像素。
- [ ] 独立低日志整机计量、超载/断流；旧失配复现时使用完整保存数据分类。
- [ ] 匹配驱动CMA/预分配/MMU/DMA/释放方案及可靠性；HDMI、30分钟仍待。

下一批具体建议见[当前进度与后续方案](tools/pose-v1/PROJECT-STATUS-AND-NEXT-20261008.md)。本轮仅整理，未新板测。


2026-10-08当前：[guarded/TCP结果](tools/pose-v1/TCP-INTEGRATION-RESULTS-20261008.md)、[检查点](tools/pose-v1/evidence/tcp-evidence-20261008-r1/next-checkpoint.json)。guarded与TCP三窗通过，27第六窗失配，取证身份Host107通过而VPU普通order7分配失败。旧待guarded固化条目为历史。

- [x] guarded策略适配与身份/Host/32真实来源回归。
- [x] TCP完整Window、预先arm协调、三窗＋重复全链核验。
- [x] 失败捕获、Native/ARM字节与原异常契约、44来源构建及Host107。
- [ ] 用户选择首启动恢复方式，新目录三窗后27失败实际值/修复验证。
- [ ] 27通过后整机计量/超载/长期；HDMI配套仍待。

2026-10-08最新：[真实串联/候选模块结果](tools/pose-v1/LIVE-RESULTS-20261008.md)及[恢复点](tools/pose-v1/evidence/live-20261008-completion/next-checkpoint.json)。本地固定三/27窗32前向/980编码/650网络/全部来源与实际PTS通过，guarded独立正负通过但未入r2；旧“实时合并待测”是历史。无后台，原授权继续。

- [x] 真实capture→AU→RTSP，主线程Engine全窗口存活，完整三/27窗/来源/时间/像素与释放。
- [x] 晚加入40帧定位与协同修正，16秒91帧预算不足保留并30秒223帧控制通过。
- [x] 独立guarded候选正常/慢客户端发送错误传播与TCP上限，ADR_09/10归档。
- [ ] 新目标固化guarded并身份/Host/真实源回归，再接既有TCP完整窗口接口。
- [ ] 整机5Hz/P95/过载/30分钟；HDMI1080p60配套与双路，显式SPS色彩。

2026-10-08：全项目[ADR主题归档](ADR/README.md)及高内聚/低耦合规范已写入；owned AU模块Native/ARM、493记录AU→200帧网络字节/PTS/像素门检通过。首批网络帧来自NoInput，补独立延后加入骨架来源覆盖；不把记录字节门检记真实实时闭环。下一[接入入口](tools/pose-v1/ONLINE-INTEGRATION-NEXT-20261008.md)。

- [x] 从开始到当前难点/解决/限制归档ADR_03–08，保留ADR_00–02。
- [x] 独立AU解析/容量8通道/事件循环适配Native/ARM/有限网络门检。
- [x] 实际capture→AU网络与三/27窗通过；慢客户端候选另验证，正式固化仍见最新待办。

2026-10-08最新：两缓冲启动三次回归、有限主线程Engine＋后台编码三/27输入及987源映射通过。下一在线AU/live555与27网络门检，整机/长期/HDMI未验收。[结果](tools/pose-v1/RESIDENT-RESULTS-20261008.md)。旧“启动仍未通过”仅指旧失败候选，证据保留。

- [x] 独立ADR_02及逐难点索引/规范。
- [x] r7分配取证、两缓冲启动三次回归，无CMA/BOOT修改。
- [x] 有界同进程工作者、实际PTS/全部源码与视频源映射；r5失败/主线程对照记录。
- [ ] 在线owned AU→RTSP、网络争用与整机长期；永久服务部署另列。

2026-10-08当前：[有限接入结果](tools/pose-v1/PIPELINE-RESULTS-20261008.md)、[下一门检](tools/pose-v1/PIPELINE-NEXT-20261008.md)。有限内容通过，启动稳定性未过，优先定位REQBUFS/STREAMON内存；常驻/真实PTS/在线RTSP仍待。

当前接续：[RTSP结果](tools/pose-v1/RTSP-RESULTS-20261007.md)、[F0门检](tools/pose-v1/F0-INTEGRATION-PREP-20261007.md)。

- [x] 用户审查动态视频；独立RTSP实际参数集、IDR加入、保活、断开重连和有限退出。
- [x] 两会话200帧＋直接播放器100帧完整像素对照、录制MP4和SPS信号检查。
- [x] F0实际Engine结果→渲染→VPU有限同进程内容接入和完整输出回归（两成功，非稳定启动验收）。
- [ ] F0启动可靠性：无规整重复固件连续页分配失败；先分配阶段取证和有依据修正，不自动规整/重试。
- [ ] 有界实时工作者/owned AU桥、实际帧源映射与27帧网络联调。
- [ ] 显式色彩元数据、HDMI配套及实屏、整机性能和长期闭环。

下方旧“RTSP未测”等条目按历史保留。

当前视频恢复点：[r5报告](tools/pose-v1/VIDEO-DESCRIPTOR-R5-RESULTS-20261007.md)。

- [x] V2-A真实27骨架/54帧编码、回传、主机全部帧核验及独立上下文重复。
- [ ] 动态样片人工审查；独立RTSP actual NAL/PTS/owned AU、加入/重连及60秒门检。
- [ ] HDMI当前BOOT的时序/scanout/停止协议证据，确认后1080p60实屏。
- [ ] 实际推理→渲染→编码/双路合并、整机性能与长期闭环。

旧暂停/故障和未编码条目按历史保留，详见新检查点。

> 当前用户主动暂停：真实骨架编码r1触发H264ENC MMU ABORT，已停止/回传/核验；HDMI只读配套未能建立实际时序/scanout停止接口，没有写入。恢复先读[RESUME-VIDEO](tools/pose-v1/RESUME-VIDEO-20261007.md)与[检查点](tools/pose-v1/evidence/video-sequence-20261007-r1/next-checkpoint.json)，先最小VPU映射/IOCTL取证方案，再新修订；不重跑r1/复位/自动连接。原HDMI授权保留，当前整轮暂停。

> 最新授权与安排：用户已审查样片并允许HDMI测试，撤销此前暂停；先[NEXT-VIDEO-PLAN](tools/pose-v1/NEXT-VIDEO-PLAN-20261007.md) V2-A真实骨架动态文件＋V1-A当前BOOT配套，再有依据的1080p60实屏/RTSP/真实推理合并。本轮未新板测，不重复已完成门检。

> 最新：独立VPU720p10fps H26430帧文件编码/回传/主机解码已通过，[样片与报告](tools/pose-v1/VPU-RESULTS-20261007.md)。下一步有界编码接口、真实预生成画面、时间戳/色彩信号和独立RTSP，再真实推理合并与争用计量。用户已接DELL E2421HN且要求HDMI1080p60，测试暂停，硬件时序未改；旧未接屏/未编码文字为历史。不重跑本轮已通过门检。

> 最新：E1-C CPU绘图、ARM27图/三格式与三帧新推理绘图已通过，[结果](tools/pose-v1/RENDER-RESULTS-20261007.md)。V0完成MVX能力查询，实际编码/HDMI仍待，屏幕未连接。下一步独立H264编码/配套，不重跑已有门检。

> 最新：E1-A生产接口及E1-B TCP首批已实板完成，见[结果](tools/pose-v1/APPLICATION-RESULTS-20261007.md)。下一步是E1-C渲染与V0视频配套；全流程路线已批准，不重跑已验收阶段。

> 最新：数值阶段已验收，P2已完成；下一步是未知窗口生产接口、网络/渲染与视频具体方案。处理核心5.25Hz不替代整机/长期验收。

首版路线已确认：[ADR_01](ADR/ADR_01.md)。[全流程方案](tools/pose-v1/FULL-FLOW-PLAN-20261007.md)已批准，首批生产接口/TCP实板通过；零拷贝/图/新算子深度优化后置，视频尚未初始化。

状态：原批准E0/N1/P1、H0资料整理及P2定位优化已由代理完成，全部会话关闭。现有27样本数值阶段由用户验收，处理核心短期5Hz基线已验证；整机与视频仍待。
全项目阶段与估算见[项目总览](PROJECT-PROGRESS.md)，最新结果见[P2报告](tools/pose-v1/P2-RESULTS-20261007.md)；N2身份诊断为非阻断可选事项。

## 本轮已完成（历史执行清单，不重跑）

- [x] 完成新运行核心、封装函数、runner及审查脚本的独立复核。
- [x] 在新修订中补齐P1测量前r6三帧完整输出校验，保存r1包/构建及旧参考不覆盖。
- [x] 独立核验27样本ORT参考及首帧重复、86项身份和旧308参考；修订包时记录对应关系。
- [x] Lite恢复后核对身份/资源并新目录传输，先一次Host107回归。
- [x] E0：一次180秒308/309/310/308，完整输出与r6逐位一致，逐阶段核验。
- [x] N1：一次120秒27＋重复共28次，真实PS/CPU/NPU轨迹与完整ONNX误差报告。
- [x] P1：一次120秒3预热＋30计量，SDK profiling保持，报告处理吞吐/P95/内存。
- [x] H0：归档关节顺序、720p时序/时钟/位流、VPU与RTSP配套资料，冲突不自行判定。

注：H0完成资料归档，不表示关节语义、720p时序或视频配套已确认。

## 后续需讨论的实施与验收

- [ ] N2（非阻断，可选）：离群帧query身份进一步诊断，副本/依赖另议；不作为当前验收前置。
- [x] P2：用户批准关闭profiling；单时钟拆分与消息构造优化已完成，处理基线5.24655Hz，整机/视频仍待。

- [x] 现有27样本数值阶段按用户明确决定验收，原误差不改写；跨端query身份未证明。
- [x] E1至双路闭环的分阶段方案与门检归档，不计功能实现。
- [x] E1-A：不依赖固定Tokens的生产接口、验证包装器、全部校验与8次入口回归通过。
- [x] E1-B：TCP完整组包/单Engine/最新槽位、自检与2Hz三/27帧网络逐位对照通过；不算过载或长期5Hz验收。
- [x] E1-C：源14条连接/显示C2符号核对，固定视角ARM CPU画面及真实结果绘图通过；不宣称解剖名称/物理标定。
- [x] V0部分：MVX多平面/NV12/NV21/H264及720p枚举与CPU缓冲区核对，不算编码通过。
- [ ] V2准备：实际协商planes/stride/色彩矩阵，有限720p合成H264文件编码与解码，随后RTSP。
- [ ] 当前25122301位流的720p60可行路径与独立视频门检，随后HDMI＋H.264 RTSP接入。
- [ ] ≥5Hz有效骨架更新、板端画面P95≤500ms、播放器延迟和30分钟闭环验收。
- [ ] 最终演示、异常场景、性能与工程资料整理；真实采集终版另定实施范围。
- [ ] 首版闭环后再按整机证据选择真实指针映射/零拷贝、图优化、内核/算子或调度优化。

算法训练旁支保持已停止，不重启500轮或延长10轮；本轮首版继续采用2024 epoch442。
已完成事项集中在[Done.md](Done.md)，不在本清单重复计进度。

</details>

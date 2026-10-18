# HDMI候选当前状态

## 当前入口（2026-10-18，离线任务已恢复）

2026-10-18，r9执行包已获用户明确批准并实际完成有界执行。候选安装／启动一次，SSH恢复34.344秒后先还原原BOOT并完整核验；64B DMA全字节往返通过，4KiB写在5.191秒触发SDK内部5000ms超时，child exit71。按失败停止规则，64KiB／1MiB、三窗新推理和HDMI START均未执行，没有重试失败负载。已用本包唯一原BOOT回退，SSH恢复28.688秒；运行中与启动文件均回到原BOOT，六SDK／九启动文件符合、FPGA operating、owner为空，串口均关闭。候选／回退额度均为0，本地及板端本包授权已关闭，旧DATA仍暂停。**D45与新推理→HDMI全链尚未解决。**

104字真实快照已验证：观测窗口约5.064秒，HC2接受9笔AR而R握手0；共享HP2对PS出口接受8笔AR、R握手2后持续背压；HDMI入口AR握手0、RVALID且RREADY=0覆盖整个窗口。ARM后未记录复位异常。疑点收敛到HP2共享返回通道及其初始化／分发状态，但没有逐事务台账或ARM前历史，不能唯一断定错路由、ID丢失或复位原因。实际发布DCP只读检查确认S00接HC2、S01接HDMI、6位PS RID进入返回流水线，未发现直接错线或显然ID截断；这不证明互联运行正确。 [r9报告](../../tools/pose-v1/evidence/hdmi-live-20261018-r9/REPORT.md)、[统一状态](../../tools/pose-v1/evidence/hdmi-live-20261017-r3/continuation-state.json)。只可继续未受失败停止阻断的离线调查；现有包不支持再上板或再运行SDK。

## r2历史暂停与随后恢复（不覆盖2026-10-18整体暂停）

2026-10-17本轮实际结果：用户明确唤醒后完成观测候选v2的CDC、布局布线、时序／DRC及BOOT封装；经用户另行明确批准执行一次候选启动及一次原BOOT回退。候选启动后先还原原BOOT文件，SDK同Device快照有效；独立DMA仅64字节往返通过，4KiB写再次抛SDK异常exit71，后两档、三窗新推理及HDMI START全部未执行。已保存完整原错和24字快照、停止失败负载，使用本包回退恢复原BOOT运行。恢复后BOOT／六SDK符合、FPGA operating、设备owner为空、两段UART均关闭，当前boot_id 9ca535cd-5ea2-4bcc-9b58-1f3699a515e8。本包两次重启额度均已使用；旧DATA独立暂停。全链尚未打通，根因仍待证。用户最新明确要求暂停，等待唤醒。本轮已在原BOOT回退核验、失败取证和本地静态审查结束处停止，无后台续作；未启动更多候选构建、部署或板测。恢复须由用户明确唤醒；旧DATA继续独立暂停。

继续入口：[r2报告](../../tools/pose-v1/evidence/hdmi-live-20261017-r2/REPORT.md)及[状态](../../tools/pose-v1/evidence/hdmi-live-20261017-r2/continuation-state.json)。该次暂停现已由本轮明确唤醒解除当前任务的暂停；旧DATA仍独立暂停。进一步候选启动须另有具体包及授权，不复用已用完的额度。以下资料为历史记录。

2026-10-17最新：用户明确恢复HDMI接入验证和渲染。原r5候选下动态图案及历史真实骨架回放实屏通过，PL三个ID采纳、fault0、在途STOP与双缓冲释放通过。新推理联动停在Session.apply参数上传SDK DMA异常；新推理0，未启动HDMI hook，不自动重试。首次START reader fault2尚未查明。无新位流、重启或BOOT／SDK修改；旧DATA暂停。[报告](../../tools/pose-v1/evidence/hdmi-display-20261017-r1/REPORT.md)、[当前收尾状态](../../tools/pose-v1/evidence/hdmi-display-20261017-r1/continuation-state.json)。以下较早暂停／恢复门禁是历史范围，不能覆盖此次明确指令，也不能用于恢复其它任务。

2026-10-16：**下一阶段实施按用户要求暂停，等待后续项目架构确定及明确恢复指令。** 本轮仅完成FPGA工作总结和文档交接，未连接板卡或执行构建。最近实际验证为同日HDMI双ABI／PLL／约148.5MHz像素计数及稳定八色条实屏通过。原BOOT已恢复、运行中候选为上次封存确认状态，本轮没有重新核验实板。DDR读帧／翻帧／在途STOP和整机实时性尚未验收；FAT脏标志及未引用链来源未明、未修复，旧DATA继续暂停。 [负责范围、原厂位流操作及交接](../FPGA-WORK-SUMMARY-20261016.md)。

## 此前阶段资料（保留当时结果，当前入口见上）

2026-10-16当前结果：用户安装的D:/vivado18.3/Vivado/2018.3已按新授权就地打原版030ai补丁；未复制完整工具。34文件/63,130,403字节备份SHA通过，九项最终目标匹配厂商源，其余备份文件未变。真实扩展PS的RTL展开29.826517秒、综合22.396529秒，工具均exit0；全部4527个命名连接/3868个AI连接可绑定，实际EDIF/DCP已生成。Liberty总数断言失败保留，独立核对证实运行库/实例7212位引脚一致，仅调试元数据表示差异及未调用DEBUGDATA160。通用转换后Procise导入3.833887秒exit1，PCPU7端口不匹配，已停止未重跑。本地JFM确有Vivado实现hook＋可选Procise位流后处理，尚未采用；其HARC、速度和DRC影响需讨论。 [本批证据](../../tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/REPORT.md)、[后续实现路径](JFM-FLOW-REVIEW.md)。当前180秒阶段授权已实际执行，取消完整工具副本方案；原生导入失败后停止实现。以下较早状态保留当时范围。

2026-10-15历史版本路线：用户确认官方资料已全部本地保存且无2019.1配套，要求先评估迁移、不可行再下载2018.3。实际2019.1运行库PS7的3305个位引脚与安装Liberty一致；030ai配套有7213个位引脚，工程使用的3868个AI_端口在现运行库全部缺失、在配套Liberty全部存在。九项替换源有八项受保护，现有资料不能形成可验证的完整2019.1迁移；普通RTL/IP成果保持。2018.3官方下载入口已打开但网页返回会话未建立，尚未取得安装包；未安装或替换库，原生PCPU7适配仍需独立门检。 [本批证据](../../tools/pose-v1/evidence/hdmi-jfm-compatibility-20261015-r1/REPORT.md)、[具体方案](VIVADO-VERSION-PLAN.md)。下述较早建议保留其当时范围，不再以继续寻找2019.1包为当前恢复任务。

2026-10-15。用户已允许实板、隔离同配置重建、16根IP修订白名单和有限衍生字段例外；旧DATA调查独立暂停。当前无后台构建，尚未下载候选或更换BOOT。

## 最新资料与隔离元数据核对

进一步按用户提示核对真实replace_7z030ai_file：严格限2018.3，先恢复多器件库再替换9项Vivado原语/器件文件；当前2019.1工程内只读入单文件仍报AI_IN端口不匹配，未改全局库或绕过版本检查。原理图确认AC14/100MHz、TMDS差分对，以及F8=1.5V/高有效PL_KEY2；IO直驱1080p60不可保证的限制保持。PS构建仍阻塞，未下载候选。 [JFM版本/影响与实际探针](JFM-COMPATIBILITY-REVIEW.md)、[Lite引脚/复位契约](PIN-CONTRACT.md)。单独原语读取的exit0只是空壳，实际PS包装仍展开失败；没有新硬件通过或下载。当前没有后台构建。

## 最新实际结果

实板只读身份和12寄存器核验通过，BOOT/六份SDK/内核保持。原r6 core/r7 pixel及Lite TMDS常量128周期结果保持，9份生产扫描RTL未改。纯输出OBUFDS→ODU_DS在实际引脚的兼容探针布线通过，但无有效STA端点，不是1080p60/1485Mb/s签核；双向IODU尝试因PLACE0854失败并已拒绝。

新r3有限契约门检通过，Vivado2019.1目标生成97.599574秒exit0；28项原有HDL参数、生成前后配置和四regslice生成端口核验通过。实际生成AXI3互联两入口各32 ID、64读/64写完整16拍burst，数据/地址/路由/背压通过，一次全局在途，仿真5.941891秒/90秒预算；Procise原生互联展开/综合16.416899秒exit0。

完整候选当前受阻：自定义PS生成包装直接原生展开时，PS7_inst端口超过PCPU7声明，ELAB-E-6/RTL-0902，8.417573秒exit1停止。没有改PS包/参数、AI_Mate或全局库，没有用黑盒替代。当前没有完整系统位流，显示器最近用户现场仍为“不支持当前时序”。

## 恢复入口与边界

先阅读[PS适配状态](PS-ADAPTATION-STATUS.md)，闭合30TAI扩展PS的正式映射/网表迁移依据；FMP100迁移流程不能直接套用。用户已完成2018.3安装；教程库替换仍未执行，用户随后取消完整工具副本，授权备份后就地030ai补丁，现已完成；2019.1、自定义PS及AI_Mate身份保持。已有板测授权持续有效，不重复申请；候选下载仍需真实完整实现产物、扫链及硬件停止/安全切换条件。

PS/DDR/HP2/GP所有权、CSR解码、原生PHY/规范复位、CDC及完整实现/时序/实屏仍待验。无FD owner不证明在途DDR读停止。BOOT/SDK/模型/RAW/正式CPU注册/NPU分配保持，不增加重启许可。失败目录和原门检不回写，不自动复跑失败负载。

[本批总报告](../../tools/pose-v1/evidence/hdmi-bringup-20261015-r1/REPORT.md)、[生成后检报告](../../tools/pose-v1/evidence/hdmi-ip-generation-20261015-r3/REPORT.md)、[已获批准的有限规则](IP-CONTRACT-REVIEW.md)、[集成契约](INTEGRATION.md)。历史分组结果见[前批报告](../../tools/pose-v1/evidence/hdmi-split-20261015-r1/REPORT.md)，原失败均保留。


## 最新暂停与恢复门禁（2026-10-16）

本轮只完成工作总结与文档同步，没有重新核验板端运行状态。后续先由用户确定项目架构，再明确指示恢复执行；恢复前先阅读[FPGA工作交接](../FPGA-WORK-SUMMARY-20261016.md)和[最新暂停记录](../../tools/pose-v1/evidence/hdmi-handoff-docs-20261016-r1/continuation-state.json)。旧封存continuation-state.json中的next及本文此前恢复步骤保留当时含义，均不能覆盖此次暂停。

本次实际源审查与首次setup失败完整原值：[独立源审查](../../tools/pose-v1/evidence/hdmi-live-20261017-r7/independent-source-review-r1/review.json)、[缓存失败保全](../../tools/pose-v1/evidence/hdmi-live-20261017-r7/setup-cache-failure-r1/review.json)。


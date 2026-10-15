# HDMI实机阶段恢复、原生IO及IP配套核验

2026-10-15，Windows执行位置与工作目录为D:/FPGACompetitionProject；板端192.168.126.49，采用既有固定主机密钥与内存认证。用户已允许板上实机验证，并先后批准现有Vivado2019.1隔离同配置重建、16个根IP白名单修订升级及IP-CONTRACT-REVIEW.md所列有限衍生字段例外。旧DATA调查保持暂停。此报告区分实际执行和后续门槛。

## 实际板端核验

- board_preflight.py：30秒外层/SSH20秒预算，实际3.2674497秒exit0；BOOT及六份SDK库匹配，FPGA operating，90个进程，无相关设备FD owner。此结果不证明PL在途读已排空。
- board_register_check.py：新/tmp/hdmi-bringup-20261015-r1目录传输既有只读探针，10秒探针预算，实际0.05630699秒exit0。仅正常SDK生命周期和12项白名单寄存器读取，无显式寄存器写、帧分配、Session、DMA或推理启动。子进程已回收。
- 设备版本25122301、icore FMSHZGV3TECH-AID-24160628、显示控制版本0x20230218；display地址寄存器为0x07e00000、disable=0，水平44/148/1920/88，垂直5/4/1080/36，input VTC=0。这些是寄存器原值，不能当像素时钟实测、内存所有权或当前BOOT内部所有行为证明。
- 前后BOOT、六份SDK、内核日志保持。最后用户现场结论仍为显示器“时序不支持”；未启动新画面或下载候选。

证据：board-preflight*.json/txt、register-transport.json、readonly-sdk-result.json及01–03完整传输/执行输出。BOARD-PLAN.md记录已批准顺序与安全切换条件。

## 原生差分输出验证

Procise2025.1.1temp/SVN32494，JFMQL30TAI676H，每步180秒安全预算，新目录独立执行，无位流生成或下载。

| 实验 | 实际结果 | 意义和限制 |
|---|---|---|
| IODU_DS_LIC_EN综合 | exit0，6.5863361秒 | 仅前端接受该双向原语，不能当物理通过 |
| diff_route r1/r2 | exit1，28.286/28.186秒 | PLACE0854拒绝双向宏使用TMDS33；r2改顶层为output仍失败，已拒绝此路径 |
| output_route r1 | exit0，36.3548132秒 | 参考纯输出OBUFDS被Procise映射为ODU_DS，AC14输入与AC17/AC16差分输出实际放置布线完成 |

通过的output_route只是100MHz输入经过组合输出的真实引脚/电平兼容探针，无有效STA端点，报告N/A，不能当742.5MHz串行、1485Mb/s、1080p60或完整HDMI物理签核。原生PHY/规范复位和时钟联合实现仍待完成。失败源码保留并标明拒绝，未接入候选。

完整证据见相邻hdmi-candidate-procise-diff-20261015-r1、diff_route-20261015-r1/r2和output_route-20261015-r1目录，包含输入SHA、工具退出码、returned-project原始EDIF/布线结果与日志。

## 系统IP状态、升级与门检

原参考297文件/163773137字节逐项SHA复制到新目录，原工程不回写；新建项目避免执行原XPR中8项缺失hook，未运行JFM hook或修改全局器件数据库。现有2019.1仅作参考IP前端，实际实现目标仍为Procise。

| 步骤 | 工具实际结果 | 门检及后续 |
|---|---|---|
| system r1状态查询 | exit0，63.4454551秒/180秒 | 28项含子核IP中23锁定；21根中16根需修订，不生成 |
| ip-revision r1白名单升级 | exit0，38.8977971秒/180秒 | 全28解锁；原始CONFIG门检拒绝，未生成目标；工具自动例化模板单列 |
| bd-validation r1传播校验 | exit0，14.8365213秒/180秒 | 64位/AXI3/ID及有效时钟恢复，字面门检仍拒绝；未生成 |
| 只读HDL/接口复核 | 脚本exit0 | 全28项原有MODELPARAM零差异；衍生名称/元数据逐项列明，不能宣称逻辑等价 |
| bd-metadata r1尝试恢复原标注 | exit1，11.6481016秒/180秒 | BD41-738拒绝改受管理内部只读在途标注；停止，未改厂商源码 |

原始失败不回写。有限例外已由用户明确批准：五个受管理角色名称、四处未启用CLK2X标注、四处复位低有效缺省、四个register_slice各17新增字段、一个M_AXI只读在途标注2→8；另仅移除不存在的gp0_monitor/gp1_monitor时钟关联。原有实际HDL参数、外部接口、地址、连线保持严格，负载不扩大。新建独立契约门检，不将旧字面门检改写通过。

有限门检与生成在独立hdmi-ip-generation-20261015-*目录执行；本报告不预写其结果。r1的Vivado校验exit0，核验驱动因新副本重新编号子核而找不到两个旧编号XCI，断言退出，未生成。修正为按已批准BD角色定位后在r2新副本执行。实际后续结果由对应execution.json、bounded-contract-gate.json及生成日志为准。

后续实际结果：r2误将加载旧BD时的警告计入修正后阶段，门检false停止、未生成，原记录保留；修正按阶段检查后，新r3有限契约门检通过，正式生成97.5995736秒exit0，生成前后配置及28原有HDL参数/四核实际端口后检通过。完整624文件树ZIP逐条SHA及CRC核验通过。实际生成AXI3互联的新r2仿真四阶段exit0，64读/64写完整16拍burst，两入口各ID0..31，一次全局在途和周期背压；r1缺头文件的前端失败另存。Procise原生互联综合16.4168988秒exit0；独立PS原生展开8.4175727秒exit1，PS7_inst扩展端口超过PCPU7声明，当前完整系统构建依赖在此停止。详见[生成、后检及失败报告](../hdmi-ip-generation-20261015-r3/REPORT.md)和[具体PS恢复入口](../../../../FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md)。

## 当前限制与停止条件

完整候选位流尚未具备，不下载旧发布bit冒充候选。PS/DDR/HP2/GP所有权、CSR解码、PHY复位、CDC、PLL与真实IO时序仍需完成；无FD owner不等于旧PL停止。正式生成失败、未知契约差异、锁定、超时即保存停止；不得自动复跑原负载或安装/升级工具。未改BOOT、SDK、模型/RAW、正式CPU注册/NPU分配；没有新重启。实际板测还需完整Procise实现、可下载候选、扫链和安全停止/临时切换条件。

## 收尾与证据身份

297项原参考复核全部SHA保持；九份生产扫描RTL与原r6/r7通过源相同，不重复无变更负载。Done/进度/难点/索引/讨论及候选状态已同步，前后文档与修订SHA另存documentation-revision，不回写历史清单。final-static-review.json记录18份Python语法检查和关键新文档链接通过。

所有已启动步骤已结束并保存实际返回；CIM进程接口权限拒绝另记，采用Get-Process按精确EDA进程名盘点，procise/vivado/xsim/xelab/xvlog/xvhdl为0。板端探针子进程和本批连接已结束，无后台续跑。最终源码、各目录SHA及completion-review.json为本批恢复依据；整体HDMI尚未验收。

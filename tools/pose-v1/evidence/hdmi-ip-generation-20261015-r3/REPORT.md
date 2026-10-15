# 有限例外下IP生成、后检及原生适配结果

2026-10-15，Windows D:/FPGACompetitionProject。源于用户“批准有限例外并继续生成验证”，新副本.local/hdmi-ip-generation-20261015-r3，现有Vivado2019.1，不执行JFM hook，不改原参考/全局数据库/BOOT/PS配置/AI_Mate。旧字面门检失败保留。

## 生成前门检与实际生成

- validate阶段：14.1234615秒exit0/180秒预算。只移除不存在的gp0_monitor/gp1_monitor关联，保留其它关联和全部连线；修正后的validate没有BD41-1287。加载旧BD时产生的原警告仍保留，不能通过扫描整份日志混淆修正前后阶段。
- bounded-contract-gate.json：passed=true；28项活动原始XCI，原有HDL模型参数/实际配置、外部接口、地址与连线保持；仅接受用户列明的15项既有字段差异和四核各17新增字段。名称按授权的五个固定BD角色核对，不绑定工具自动编号。
- generate阶段：97.5995736秒exit0/300秒预算，13独立XCI及1个BD目标完成，包括自定义PS核；保存后工程与实际文件清单。生成工具退出0不等于Procise或整机通过。
- post-generation-contract.json：通过；生成前后全部导出IP属性一致，全28项MODELPARAM同原参考；实际生成的四个regslice无新增活动REGION/USER/CLK2X端口，CLK2X接0，级数/流水参数匹配。新增字段没有静默当成新的板端功能。

第一次生成入口r1因脚本用旧自动编号定位子核而assert退出，未生成；r2的门检把加载旧BD时的警告误计为修正后警告，未生成。两份原日志及false/失败保留；修正按角色定位和按实际校验阶段判定后使用新r3，不覆盖失败目录。

## AXI ID位宽告警的实际验证

生成产生BD41-235：部分内部ID由5位接6位或返回时截取。原XCI已包含slave thread ID5、crossbar ID6、两来源BASE_ID=0/32；不能仅凭原参数相同就忽略。新增仿真直接使用未修改的生成BD模块、crossbar/register_slice及厂商模型。

hdmi-generated-axi-20261015-r1首次前端缺少axi_infrastructure头文件，compile exit1停止。补齐实际生成的全部相关.vh、Verilog/SV分开编译，另建r2；四阶段全部exit0，耗时1.416104/0.957925/10.099822/5.941891秒，各90秒预算。实际64读和64写完整16拍burst，读/写各1024拍，两入口各覆盖ID0..31，校验输出6位来源标签、返回5位ID及正确来源、地址、数据、LAST、WSTRB、响应，周期性背压，一次全局在途。

该有界路由场景通过；未验证多在途仲裁、系统PS/DDR响应或候选STOP集成。USER物理宽1/逻辑宽0警告对应未启用的占位通道，实际包装未暴露USER端口，原警告仍保存。

## Procise原生适配

- hdmi-native-axi-20261015-r1：同一生成互联的原生展开/综合exit0，16.4168988秒/180秒预算，JFMQL30TAI676H，实际EDIF已保存。未布局布线/时序签核或位流生成。
- hdmi-native-ps-20261015-r1：自定义PS生成包装和原包依赖直接原生展开失败，8.4175727秒exit1。ELAB-E-6：PS7_inst端口数量超过PCPU7声明，RTL-0902。停止，无自动重试、端口删除、黑盒替代、PS包升级或全局原语库修改。

这是当前完整候选构建的阻塞。原始PS和AI_Mate包保持；本机30TAI教程的JFM时序库/hook流程仍需在不改全局数据库边界内核对，FMP100迁移流程不能直接证明30TAI支持。细节和恢复前提见[PS适配状态](../../../../FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md)。

## 产物与通过边界

validate/generate完整stdout/stderr/log、Tcl、退出码、授权和输入/生成后SHA清单、bounded/post-generation门检均在本目录。generated-reference.zip保存实际生成参考树，按generated-manifest.json核验ZIP内容；后续文档修订另存于总批报告目录，不回写旧身份。

没有候选上板、BOOT替换、重启或新共享模型推理；先前只读实板核验和纯输出OBUFDS→ODU_DS引脚放置布线结果见[本批总报告](../hdmi-bringup-20261015-r1/REPORT.md)。当前显示器时序问题未验收。

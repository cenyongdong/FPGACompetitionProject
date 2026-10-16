# 参考位流定点豁免、发布与实际板端预检

2026-10-16，Windows工作目录D:/FPGACompetitionProject；新证据目录hdmi-board-reference-20261016-r1，工作目录.local/hdmi-board-reference-20261016-r1。前置为用户明确豁免并要求上板；当前BOOT/SDK必须匹配，身份变化或设备/逻辑错误停止依赖操作，不能用缺失设备强行下载。旧构建264项封存证据不回写。

## 已执行

- 两处原厂AI模型Min Period用户特批，解除该项HELD，发布实体已复制并SHA复核。请求标签为“已知原厂安全占位时钟”；安全/占位语义未独立证实，记录为用户接受的工程例外，原工具结果仍失败。
- 新原始bit与Procise后处理bit均为原厂参考RTL，尚未包含HDMI修复候选。发布与源SHA一致，见release-authorization.json。
- 原沙箱SSH因本机MSYS信号管道权限exit1，未连板；保留原日志。主机权限新目录只读身份审查3.673秒exit0（SSH预算30秒，外层40秒），BOOT和六份SDK库匹配；FPGA operating，无相关FD owner。没有寄存器写、推理、DMA、帧分配或配置写。
- Linux只见FMSH FMQL FPGA Manager，无fpga_bridge/fpga_region节点；这并不证明没有硬件隔离机制，只说明本次没有可用的已验证sysfs隔离入口。无FD owner也不证明PL排空。
- 回退bit重新与本地选择BOOT的PL分区做32位字节交换后完整载荷比较，全部载荷相同，余4字节分区填充；本地BOOT SHA与刚读板端相同。仅身份核验，不称热恢复验收。
- Procise实际版本2025.1.1temp/SVN32494；两次只读扫链预算各45秒，实际3.876/3.681秒、均exit1，第二次为主机权限，均0 cable/There are no FTDI chip found。Windows主机权限Get-PnpDevice未返回0403/10C4或JTAG/Digilent/FTDI设备。没有执行program_bit，目标序号未知。
- 首版扫链摘要expected_cable_present曾误匹配Tcl回显中的请求序列号；chain-review.json已按实际枚举结果纠正为false，原摘要保留，脚本已修正。未据此下载。

## 尚未执行

临时配置、实屏、实际像素频率、SDK新位流推理及并发实时性均未验证。以下是首次预检时状态，随后下载器已重连并扫链通过；现行结论见文末。在线停止/隔离尚未取得证明。不能改用未经核实的寄存器/FPGA Manager写入绕过。用户已被请求接好下载器；不再询问两处时序豁免。BOOT、模型、SDK、时序库、频率未改变，无重启。

## 原值和恢复

见release-authorization.json、host-permission-r2/board-audit.json、两份chain-scan*/stdout.log、chain-review.json、rollback-identity.json、released-reference-products/和rollback/。发布契约在项目FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md。核验实际链、在线切换条件后再做临时配置，不能把参考产物当修复候选。CDC及外部时序仍未完整签核，未新增其它豁免。


## 后续更新：物理重连和载荷相同

13:35:26 Windows枚举恢复VID0403/PID6014/210512180081。新目录r3实际Procise扫链4.029秒exit0，jfmql30 part0/0x9372c093、ps_dap part1/0x6ba00477，原两次设备缺失失败保持。枚举时另见既有ssh.exe PID28848（不属于本批已结束的传输，不擅自终止）；不称主机全部SSH为0。

离线重新封装对照BOOT实际0.618秒exit0，SHA与所选/当前板端BOOT完全相同。再换新参考bit构建试制BOOT实际0.627秒exit0，但非PL字节全同的后检失败、严格停止；离线复核发现PL分区0字节变化、只有9个映像名称字节变化。直接解析bit全载荷也证实新发布Procisebit与所选BOOT的PL载荷逐字节相同，均5980460字节/SHA657da80bb5eff97c917cf3a6c8c5b40a331b814dd840b5ac6a0bda44fb8a935d；Docs/BIT的Lite位流同载荷。这不是配置读回，不能证明任何未记录的外部加载未发生。

原试制result.json中的semantic_scope是拟核验的不变量描述，其实际布尔后检为false，不能引用该文字作为通过；reference-payload-review.json给出修正。离线控制r1默认GBK解码UTF-8失败在工具前发生，无BOOT产物；新utf8-r2目录修正后执行，不覆盖现场。

没有为同一配置载荷修改BOOT或重启，也未通过临时下载包装为新功能。两处定点豁免及参考产物发布保留，HDMI修复仍需先集成，不能把参考构建链复现记作HDMI修复或实时整机验收。用户要求的实板功能验证尚未完成。下一依赖是完整HDMI修复配置及明确的切换/CSR契约。

查询Linux FPGA Manager通用资料仅说明厂商细节属于底层驱动，不能替代FMQL驱动的隔离证据：https://cdn.kernel.org/doc/html/latest/driver-api/fpga/fpga-mgr.html 。本地原厂30TAI教程7–9页核对了BOOT封装/替换/重启路径，实际未改板端启动区。所有本批子进程均已等待结束；最后主机清理清单另存，不终止无关连接。

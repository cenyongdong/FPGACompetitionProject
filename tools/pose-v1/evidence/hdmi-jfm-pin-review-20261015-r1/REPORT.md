# JFM替换过程、Lite原理图及工程内原语读取核验

2026-10-15，Windows工作目录D:/FPGACompetitionProject。用户提示参考replace_7z030ai_file及Docs/开发板手册/JFMQL30TAI_LITE.pdf。本批只读审查和隔离元数据探针，未运行全局替换/恢复函数、hook，未安装/升级工具或PS核，未下载候选/更换BOOT/重启，旧DATA继续暂停。

## 原理图的完整相关页核验

读取原PDF共28页文本，保存来源SHA，使用本机Poppler渲染PDF第9/10/19/21/22页及BANK12放大图，均已目视检查。图纸Sheet标签为9/10/23/25/26，页脚沿用JFMQL100TAI标题，U1器件符号为JFMQL30TAI。引脚结论与原XDC及既有引脚探针核对，未据标题猜器件。

- BANK12供电3.3V。G1标称100MHz，PL_100MHz→AC14，MRCC；独立于SDI/MIG。TMDS CLK P/N=AC17/AC16，D0=AA15/AA14、D1=Y16/Y15、D2=W16/W15。
- HPD=AE16；DDC板侧FSCL=AA17、FSDA=AB17，分别经Q4/Q5接5V HDMI侧，需下拉/释放的双向控制；CEC=AB16。尚未增加任何HPD/DDC访问或执行EDID读取。
- F8是BANK34/1.5V的PL_KEY2，SW7松开下拉为低、按下为高，补齐此前仅从XDC知道F8而未确认极性的缺口。不是PS上电复位，规范复位/AXI协调仍待实现验证。
- HDMI采用IO直驱，PDF第19页明确不能保证1080p60，建议专用HDMI芯片；IO直驱支持720p及以下。现行批准目标1080p60没有自动改动，也没有将此前纯输出布线探针扩大为高速/实屏通过。

对应源文件和逐项机器记录见schematic-text.json、pin-contract.json及[可读引脚契约](../../../../FPGA/hdmi_candidate/PIN-CONTRACT.md)。

## replace_7z030ai_file的真实定义

r1首次Tcl查询因中文路径编码被旧工具截断，source_status1，未加载配套；主机输出又发生cp936编码错误，脚本exit1。原工具exit0仅表示查询脚本结束，不代表读取成功。inspect-driver-failure.json及全部原值保留。

修正为同SHA受保护文件的英文路径副本，在新r2使用现有Vivado2019.1的正常source加载器。加入文件写、外部命令、动态库及工程/配置变更拦截，只查询info body；未调用replace/reset/hook。实际3.141304秒exit0/60秒预算，source_status0，真实函数体读取成功，blocked-mutations.txt为空。未解密修改或重新打包厂商受保护文件。

函数入口严格要求2018.3。它先调用reset_database_to_default，该辅助函数涉及36个不同目标路径，再对030ai的9项Vivado安装库进行替换：Sitemap2.xml、两份unisim_comp、zynq.lib/rtd/xng/padr、xc7z030.paspd、unisim.btl。因此不只是修改像素时钟或少量时序参数。9个当前2019.1目标都存在，与030ai源SHA均不相同；这不证明能兼容覆盖。fast分支要求的xc7z030ai_fast.paspd当前不存在。

实际PS错误调用点为processing_system7_v5_5_atc.v:5420，PS7_inst具有4527个唯一命名端口；其中AI_IN2942、AI_OUT744，另有AI_CLK等扩展。原生PCPU7完整声明尚未取得，不能单凭端口数量推断准确映射，更不能删除端口绕过。

本函数修改Vivado的器件/原语库，不能据此证明它直接修复Procise的PCPU7。真实函数体/辅助函数在相邻hdmi-jfm-pin-review-20261015-r2，准确目标身份、恢复范围和源哈希在replacement-review.json。前批封存记录未改写。

## 保持全局库不变的工程内探针

| 新目录 | 实际工具结果 | 判断 |
|---|---|---|
| hdmi-jfm-primitive-20261015-r1 | 22.559951秒exit0，60秒预算 | 可读入本地原语声明，但单PS7顶层为空、端口0；metadata-review明确拒绝端口契约，不是硬件通过 |
| hdmi-jfm-ps-elaboration-20261015-r1 | 18.938109秒exit1，60秒预算 | 实际PS包装RTL展开报AI_IN1549等命名端口不匹配，Synth8-4456/总结104 Errors；停止，未继续硬件综合/实现 |

实际7份PS依赖及本地原语源SHA、Tcl、stdout/stderr/vivado.log完整保存。日志含在当前工程内覆盖同名原语的WARN，未将这些过程内声明写回全局库。各阶段结束后进程均返回，按精确EDA名盘点结果另存。本批没有实板动作。

## 结论、边界与恢复

用户给出的线索补齐了具体配套入口、版本条件、替换影响和板级引脚；当前PS构建仍阻塞。优先核对当前2019.1适用的正式30TAI JFM/Procise配套；如只能采用现有2018.3专用包，先讨论隔离工具环境及官方流程，不绕过版本判断、不自动安装或覆盖全局库。未修改当前PS包、AI_Mate、BOOT/SDK/模型/RAW。

[JFM版本与兼容核对](../../../../FPGA/hdmi_candidate/JFM-COMPATIBILITY-REVIEW.md)、[候选恢复入口](../../../../FPGA/hdmi_candidate/RESUME.md)。本批文档修订前后SHA另存，既有全局目标身份在新探针前后复核；原参考297文件身份及候选生产RTL复核保持，未重新跑已通过的无变更负载。

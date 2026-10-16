"""Record the bounded waiver, actual board audit and physically unavailable JTAG."""
from pathlib import Path
import json, hashlib, re, shutil
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1'
def read(rel):return (R/rel).read_text(encoding='utf-8-sig')
def write(rel,s):(R/rel).write_text(s,encoding='utf-8')
def replace_intro(rel,s):
 t=read(rel);parts=t.split('\n\n',2);assert len(parts)==3
 write(rel,parts[0]+'\n\n'+s+'\n\n'+parts[2])
summary='2026-10-16：用户特批两处原厂AI时钟模型最小周期例外，解除其HELD限制，发布为受控板测参考产物；原始WPWS−0.409ns及失败报告保留，不修改库/频率，不把“安全占位时钟”标签当独立验证结论。新参考位流与回退位流SHA已核验，回退载荷与当前BOOT的PL分区相符。实板SSH只读核验BOOT/六份SDK一致、FPGA operating；Procise两次只读扫链（第二次为主机权限）均0 cable/无FTDI，Windows也未枚举对应设备，尚未下载。HDMI修复候选未集成，CDC/外部时序未签核，在线停止/隔离条件待核实；BOOT未改、未重启，旧DATA保持暂停。'
replace_intro('PROJECT-PROGRESS.md','更新日期及最后实际验证日期：'+summary+' [本轮实际结果](tools/pose-v1/evidence/hdmi-board-reference-20261016-r1/REPORT.md)、[定点豁免与发布契约](FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md)。')
replace_intro('REFERENCES.md',summary+' [本轮证据](tools/pose-v1/evidence/hdmi-board-reference-20261016-r1/REPORT.md)、[当前板测入口](FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md)。此前32项库/四项GT处理成果保持，详见原封存构建报告。')
for rel in ['FPGA/hdmi_candidate/RESUME.md','FPGA/hdmi_candidate/INTEGRATION.md','FPGA/hdmi_candidate/BOARD-PLAN.md']:
 replace_intro(rel,summary+' [定点豁免、产物与实板恢复入口](BOARD-RELEASE-20261016.md)。下文保留此前依据，其HELD/未授权表述以本段为准。')
t=read('FPGA/hdmi_candidate/AI-CLOCK-GATE.md')
parts=t.split('\n\n',2)
write('FPGA/hdmi_candidate/AI-CLOCK-GATE.md',parts[0]+'\n\n2026-10-16更新：用户已明确特批下述两个Min Period检查，解除该项HELD，允许受控实板测试；原始时序失败及尚未验证的语义保留。[现行定点豁免与发布状态](BOARD-RELEASE-20261016.md)。下文为豁免前的门检事实及停止依据，其中“不得新增豁免／HELD”的旧决策已被本次用户定点授权更新，其余范围不扩展。\n\n'+parts[1]+'\n\n'+parts[2])
t=read('Agents.md');marker='## 平台、工具与环境约束'
authorization='- 用户已明确批准[定点AI时钟模型例外及受控板测范围](FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md)：仅解除该页列明的两个最小周期检查所致扣留，可执行该发布参考位流的临时上板验证；保留原报告，不扩展到其它时序检查、改库/频率、永久BOOT替换或再次重启。下载前仍须核对实际链目标、回退身份和运行中资源的安全停止/隔离；不把用户接受的例外标签写成独立安全验证结论。\n\n'
assert authorization not in t;write('Agents.md',t.replace(marker,authorization+marker,1))
t=read('DIFFICULTIES.md');lines=t.splitlines()
for i,line in enumerate(lines):
 if line.startswith('| D05 |'):
  lines[i]='| D05 | HDMI候选未集成；参考位流板测待接通下载链 | 两处AI最小周期用户定点豁免，参考产物解除该项HELD；BOOT/六SDK实板身份同，回退载荷已核验 | 2026-10-16主机权限扫链仍0 cable/无FTDI，在线隔离/排空未验证；CDC/外部时序未签核，未下载；[现行发布与恢复](FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md) |'
write('DIFFICULTIES.md','\n'.join(lines)+'\n')
t=read('Done.md');marker='### 工程内容总结\n\n';assert marker in t
addition='2026-10-16定点豁免与板测准备：'+summary+' 执行位置Windows D:/FPGACompetitionProject、只读SSH至Lite；SSH传输预算30秒/外层40秒，实际身份核验3.673秒exit0；原沙箱SSH本机管道错误保留，主机权限新目录成功，非板端故障。Procise2025.1.1temp/SVN32494扫链预算45秒，实际3.876/3.681秒均exit1、0 cable；没有执行program_bit。新发布/回退实体已建立，既有封存目录不改。[证据](tools/pose-v1/evidence/hdmi-board-reference-20261016-r1/REPORT.md)。\n\n'
t=t.replace(marker,marker+addition,1)
future='### 对后续开发的参考\n\n'
assert future in t
t=t.replace(future,future+'本次定点豁免仅改变受控板测放行决策，不改变原始时序结果；发布必须绑定SHA和RTL范围。下载器重连后重新扫链，不能沿用旧part序号；当前无bridge节点、无FD owner均不是AXI排空证明。参考实板结果也不能记为HDMI修复候选验收。[恢复入口](FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md)。\n\n',1)
write('Done.md',t)
report='''# 参考位流定点豁免、发布与实际板端预检

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

临时配置、实屏、实际像素频率、SDK新位流推理及并发实时性均未验证。当前直接阻塞是下载器未枚举；在线停止/隔离也尚未取得证明。不能改用未经核实的寄存器/FPGA Manager写入绕过。用户已被请求接好下载器；不再询问两处时序豁免。BOOT、模型、SDK、时序库、频率未改变，无重启。

## 原值和恢复

见release-authorization.json、host-permission-r2/board-audit.json、两份chain-scan*/stdout.log、chain-review.json、rollback-identity.json、released-reference-products/和rollback/。发布契约在项目FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md。核验实际链、在线切换条件后再做临时配置，不能把参考产物当修复候选。CDC及外部时序仍未完整签核，未新增其它豁免。
'''
(E/'REPORT.md').write_text(report,encoding='utf-8')
shutil.copyfile(Path(__file__),E/Path(__file__).name)
print(json.dumps({'current_documents_updated':9,'board_programmed':False,'reference_min_period_waiver':True}))

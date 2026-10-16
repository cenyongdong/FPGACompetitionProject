"""Publish actual integration checkpoint without turning reports into signoff."""
from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
def read(rel):return (R/rel).read_text(encoding='utf-8-sig')
def write(rel,s):(R/rel).write_text(s,encoding='utf-8')
def intro(rel,text):
 parts=read(rel).split('\n\n',2);write(rel,parts[0]+'\n\n'+text+'\n\n'+parts[2])
assert not (E/'documentation-checkpoint-revision.json').exists()
docs=['Agents.md','PROJECT-PROGRESS.md','REFERENCES.md','DIFFICULTIES.md','Done.md','ARCHITECTURE-DISCUSSION-20261015.md',
 'FPGA/hdmi_candidate/INTEGRATION.md','FPGA/hdmi_candidate/RESUME.md','FPGA/hdmi_candidate/BOARD-PLAN.md']
pre={}
for rel in docs:
 p=R/rel;s=read(rel);dest=E/'before-current-edit'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 if rel=='Agents.md':s=re.sub(r'密码：[^，。\r\n]+','密码：[REDACTED]',s)
 dest.write_text(s,encoding='utf-8');pre[rel]={'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'snapshot_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
summary='2026-10-16：用户已批准并在暂停后明确恢复HDMI整机接入及上板任务。隔离工程已完成新scanout/HP2读所有权、独立AC14时钟、显式CSR解码及规范SERDES复位接线。路由边界/背压仿真通过，真实2018.3模型验证256周期TMDS时钟及1920活动像素色条；九份原候选功能RTL未改，原PS/DDR/AI_Mate及SDK/模型保持。首版整机综合完成，但审查发现旧PHY资源仍被保留、混合时钟缓冲相位警告和Q端点路径截断，已保存原DCP/日志并修正源码；修正版BUFIO＋BUFR同源/5仿真通过，第二版底层综合及DCP完成。暂停中断外层收尾，当前正在从完整DCP恢复报告，已核验CRC、17份相关源及NEEDS_REFRESH=0，没有重跑综合。尚未完成新约束/DRC与布局布线、位流或实板验收；本轮没有下载、BOOT写入、重启或板端推理，旧DATA继续暂停。'
intro('PROJECT-PROGRESS.md','最后实际验证日期：'+summary+' [当前实施与恢复](FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md)、[本轮实际证据](tools/pose-v1/evidence/hdmi-integration-20261016-r1/REPORT.md)。')
intro('REFERENCES.md',summary+' [当前整机接入契约](FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md)。以下保留此前阶段资料及其当时范围。')
for rel in ['FPGA/hdmi_candidate/INTEGRATION.md','FPGA/hdmi_candidate/RESUME.md','FPGA/hdmi_candidate/BOARD-PLAN.md']:
 intro(rel,summary+' [现行接入、阶段与恢复契约](SYSTEM-INTEGRATION-PLAN.md)。下文为此前依据，原“尚未接线/地址未分配”等状态以本段和新契约为准；未通过项保持。')
t=read('FPGA/hdmi_candidate/INTEGRATION.md')
t=t.replace('**尚未分配/批准新板端基地址，不能向当前BOOT访问候选偏移。**','**本轮整机接入授权内，隔离候选已明确解码0x400b0000–0x400b00ff；原SDK低地址保留。该新地址仅在候选ABI实际确认后使用，不能向旧BOOT假定候选寄存器存在。**')
write('FPGA/hdmi_candidate/INTEGRATION.md',t)
for rel in ['PROJECT-PROGRESS.md','DIFFICULTIES.md']:
 lines=read(rel).splitlines()
 for i,line in enumerate(lines):
  if line.startswith('| HDMI |'):lines[i]='| HDMI | 整机接线、路由与真实时钟/色条仿真完成；首版综合审查后修正时钟拓扑，第二版底层综合完成 | 已按用户明确指令恢复，正在补齐中断的报告；新约束/DRC/布局布线与位流/板测仍待验证；[恢复契约](FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md) |'
  if line.startswith('| 当前恢复点 |'):lines[i]='| 当前恢复点 | **HDMI整机第二版综合已完成，恢复已有DCP报告，不重复综合**；随后复核新CDC和DRC，保持原AI两个Min Period特批，未授权额外违例；[当前契约](FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md)。旧DATA保持暂停 |'
  if line.startswith('| D05 |'):lines[i]='| D05 | HDMI整机已接线，修正版约束/实现/实屏仍待验 | 新路由/148.5MHz时钟/1920像素色条仿真通过；第一版整机综合完成，审查后移除旧PHY并改同源BUFIO/BUFR | 新版底层综合已完成、报告恢复中；旧路径截断和资源/相位警告不称通过，待新DRC及完整实现；未生成候选位流/上板；[实施与证据](FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md) |'
 write(rel,'\n'.join(lines)+'\n')
t=read('Agents.md');marker='## 平台、工具与环境约束'
authorization='- 用户已明确批准把修复后的HDMI模块接入隔离整机工程并进行上板验证，实施与最小接口契约见[HDMI整机接入执行包](FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md)。用户暂停后已明确恢复本任务；原旧DATA调查仍暂停。原AI时钟两个定点例外仅适用于原对象/模型保持的范围，新HDMI时序及DRC不得自行套用该例外；原BOOT/SDK/模型保护、下载前安全停止/隔离和新重启边界继续有效。\n\n'
assert authorization not in t;write('Agents.md',t.replace(marker,authorization+marker,1))
t=read('Done.md');marker='### 工程内容总结\n\n'
addition='本轮整机接入（恢复点，2026-10-16）：'+summary+' Windows/Vivado2018.3＋既有JFM，复制工程及配套2630489459字节/128.522秒；非工具目录复制。显式新CSR0x400b0000–0x400b00ff，原相机写及原低地址保留。router-r2四阶段通过，读6/写4及背压/响应持有；PHY-r3实际模型完整1920色条像素/256时钟周期通过，仿真71.414秒/90秒预算。首版整机综合277.159秒exit0；旧预检问题完整封存后改为同源BUFIO/BUFR。独立ARM静态探针完成、六库匹配，未板端执行；FPAI和本批启动的Docker Desktop均停止恢复原状态。[本轮报告](tools/pose-v1/evidence/hdmi-integration-20261016-r1/REPORT.md)。\n\n'
t=t.replace(marker,marker+addition,1)
future='### 对后续开发的参考\n\n';assert future in t
t=t.replace(future,future+'新综合DCP的生成与外层收尾是不同事件：本轮暂停中断了后者，恢复时按源SHA/CRC及工具Complete/NEEDS_REFRESH=0重用完整DCP，不伪造原外层exit0。Q引脚强制最大延迟起点会引发路径截断，现改用合法时钟起点；必须等新版实际绑定报告后才能称问题已消除。相位缓冲合法性、区域资源与实板IO速率不能由波形仿真代替。[当前实施包](FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md)。\n\n',1)
write('Done.md',t)
t=read('ARCHITECTURE-DISCUSSION-20261015.md')
t+='\n\n## 21. HDMI修复整机接入与暂停后恢复（2026-10-16）\n\n'+summary+'\n\n新接口0x400b0000–0x400b00ff由完整地址片选隔离，保留旧cam低地址；HP2新读主机与原相机写分属模块。静态色条为不启动DMA的首阶段，帧缓冲仍采用公开SDK持有实际块和stopped ID快照证明释放。新实现尚未完成，未改变PS/NPU任务划分或共享模型；原AI时钟定点例外不能扩展到新串行时钟。相关原厂适配及CDC/DDR身份门检保持。[本轮具体契约](FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md)。\n'
write('ARCHITECTURE-DISCUSSION-20261015.md',t)
report='''# HDMI修复整机接入：执行和恢复记录

2026-10-16，Windows D:/FPGACompetitionProject；工作.local/hdmi-integration-20261016-r1，证据本目录。用户已明确批准整机接入与板测，并在请求暂停后明确唤醒。保留旧DATA暂停；不扩大到BOOT修改或再次重启。Vivado2018.3/现有030ai＋JFM，后续仍以原厂Procise后处理及实板证据为准。

## 已完成及实际门检

- 复制已合格整机/IP/JFM配套4731文件/2630489459字节，128.522秒/180秒预算；仅54份项目/运行元数据路径重定位，无完整工具副本。
- 修改隔离工程5份参考RTL，新增12份模块文件；九份核心候选功能RTL不改。原始参考297文件核验保持，原PS/DDR/AI_Mate的XCI非运行时参数28项、DDR/BD/EDIF后检保持。HP2读为新scanout独占，原相机写保持；独立AC14时钟、合并写接口与完整地址片选、新SERDES复位已接线。
- 新CSR0x400b0000–0x400b00ff；旧SDK低地址不改，其余旧别名转旧桥。两处ABI实际核验前禁止写新端点。启动后黑色自由扫描、无显示DMA；静态色条仅安全空闲且首次START前允许启用。
- router-r2实际2018.3仿真读6/写4、端点背压和响应保持通过。r1把旧Verilog源码按SV编译，变量bit触发语法错误；识别语言模式后使用新目录分编译，不改厂商变量或覆盖失败。
- 真实2018.3 UNISIM MMCM/TMDS/CSR仿真：首版256时钟周期及50%转发时钟通过；r2、r3增加1920活动像素色条比对，模拟各71.998/71.414秒，均低于90秒。r3使用同源BUFIO/BUFR新拓扑；仅逻辑/模型证据，不是硅上IO验收。
- 整机语法及IP状态实际57.076秒exit0，无锁定IP。首版整机综合277.159秒exit0：180秒时日志新鲜/无ERROR且资源足，继续原进程到360秒门限内完成。新FIFO是1个RAMB36E1，8个OSERDESE2可见。
- 首版约束绑定145.076秒工具exit0，但审查不通过：Q端点导致Constraints18-515路径截断，打印达到100项上限；旧PHY仍在综合网表占资源（MMCM6/5），新BUFIO/BUFG混合时钟触发相位警告。完整DCP、报告、22份原综合run文件ZIP/逐项SHA保存，不写为签核通过。
- 修正：候选参数下generate掉旧时钟/发送器；新MMCM同一742.5MHz输出驱动BUFIO及BUFR/5；约束使用合法C起点。原NDRV预优化PS相关未驱动网没有被更改，仍待原厂opt后的DRC核验，不新增豁免。
- 第二版底层综合实际生成DCP且run日志成功退出；暂停时外层报告收集未完成，原execution.json缺失，退出状态不伪造。恢复前查无残留EDA进程；验证DCP ZIP CRC、17份相关源SHA，并由工具确认Complete/NEEDS_REFRESH=0。正在新恢复阶段读取既有DCP及报告，没有重跑综合。
- 独立ARM静态探针用既有FPAI交叉编译成功，六份SDK库匹配，AArch64及后端依赖核验通过；不分配内存/创建Session/启动DMA，未板端执行。初次构建因Docker引擎未运行而停止，原日志保留；启动已安装Desktop后新目录完成构建，FPAI及Desktop均已停止。没有安装/升级工具或SDK。

## 尚未执行或通过

新版CDC实际绑定、DRC、完整布局布线与时序、候选位流/Procise后处理、新配置载荷与参考的差异核验、实屏和实时性均未完成。本轮未连接板端执行新操作，没有JTAG下载、启动区写入、重启、模型推理或清缓存。原AI模型仅两处Min Period用户例外保持，新违例不能套用。

## 恢复入口和证据

当前从recover-synthesis-r2继续补齐元数据；成功后运行新版constraint-binding-r2并审查路径截断、资源和相位警告是否消除，再决定布局布线。不能重写原system-synthesis-r2缺失的外层结果，不能把计划当通过。授权/预算、复制、接线、每次仿真与EDA执行见对应JSON/Tcl/stdout/stderr及SYSTEM-INTEGRATION-PLAN.md。旧封存批次不回写。
'''
(E/'REPORT.md').write_text(report,encoding='utf-8')
plan=R/'FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md'
with plan.open('a',encoding='utf-8') as f:
 f.write('''

## 首版审查后的修正及恢复

首版综合网表仍保留旧PHY。已在CANDIDATE_SCANOUT=1时generate掉其时钟和发送器；原默认参数0路径保留。新时钟调整为MMCM单一742.5MHz输出→BUFIO快时钟及BUFR/5像素时钟，避免混合BUFFIO/BUFG两输出的相位警告，实际模型256周期及1920活动像素复验通过；新版DRC/布线尚待实际核验。区域时钟的布局资源和FMSH IO能力仍须由当前适配流程及硅上结果确认。

首版set_max_delay使用Q端点导致路径截断，工具提示改用合法时钟起点；现已改为C起点，保留Gray最大延迟/bus skew及第二级正常时序，等待新版实际约束报告。未通过更改严重级别或新增DRC关闭来解决。

用户请求暂停后又明确恢复。本次暂停发生在第二版底层综合完成、外层元数据收集期间，原stage没有退出记录；恢复时DCP CRC/17份源SHA及工具Complete/NEEDS_REFRESH=0均已核验，使用新恢复目录读原DCP，不重跑综合。当前新约束、实现、位流和板测仍未完成。[本批实际报告](../../tools/pose-v1/evidence/hdmi-integration-20261016-r1/REPORT.md)。

架构方法另核对AMD原始UG471/UG472的BUFIO/BUFR配对说明，仅作为2018.3前端拓扑依据，不把Xilinx速率数字当FMSH器件保证：[UG471](https://docs.amd.com/api/khub/documents/IbGcnPFe6eF19RHma_Y~IA/content)、[UG472](https://www.amd.com/content/dam/xilinx/support/documents/user_guides/ug472_7Series_Clocking.pdf)。本地原厂适配及实现检查保持优先。
''')
post={rel:{'before_edit':pre[rel],'after_original_sha256':hashlib.sha256((R/rel).read_bytes()).hexdigest()} for rel in docs}
(E/'documentation-checkpoint-revision.json').write_text(json.dumps(post,indent=2)+'\n')
print(json.dumps({'current_documents_updated':len(docs),'new_bitstream_or_board_acceptance_claimed':False}))

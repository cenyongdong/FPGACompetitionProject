"""Update current conclusions after physical reconnection and payload equality proof."""
from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1'
def read(rel):return (R/rel).read_text(encoding='utf-8-sig')
def write(rel,s):(R/rel).write_text(s,encoding='utf-8')
payload=json.loads((E/'reference-payload-review.json').read_text(encoding='utf-8'))
assert payload['rebuilt_Procise_equals_selected_BOOT_PL_payload']
chain=json.loads((E/'chain-scan-device-enumerated-r3/result.json').read_text())
assert chain['exit']==0 and chain['scan_completed']
summary='2026-10-16：用户特批两处原厂AI时钟模型Min Period例外，解除该项HELD，原始WPWS−0.409ns失败报告保留。参考位流已建立发布实体；重连后Procise扫链4.029秒exit0，确认jfmql30/0x9372c093/part 0、下载器210512180081。板端BOOT/六SDK只读身份同基线，FPGA operating。进一步核验发现新Procise参考位流的完整配置载荷与当前所选BOOT的PL分区逐字节一致；仅文件头等元数据不同，重下不会引入HDMI修复。原BOOT离线重建逐字节复现；试制BOOT只有9个映像名称字节变化、PL分区0字节变化，严格比较失败保留，不部署。未下载、未改启动分区、未重启；HDMI修复候选尚未集成，CDC/外部时序未签核，在线停止/隔离亦未验证，旧DATA继续暂停。'
for rel,prefix,link in [
 ('PROJECT-PROGRESS.md','更新及最后实际验证：','[当前发布与恢复](FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md)'),
 ('REFERENCES.md','','[当前发布与载荷复核](FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md)'),
 ('FPGA/hdmi_candidate/RESUME.md','','[发布与恢复](BOARD-RELEASE-20261016.md)'),
 ('FPGA/hdmi_candidate/INTEGRATION.md','','[发布与范围](BOARD-RELEASE-20261016.md)'),
 ('FPGA/hdmi_candidate/BOARD-PLAN.md','','[现行板测入口](BOARD-RELEASE-20261016.md)')]:
 t=read(rel).split('\n\n',2);write(rel,t[0]+'\n\n'+prefix+summary+' '+link+'。下文保留此前依据，以本段为现行状态。\n\n'+t[2])
t=read('PROJECT-PROGRESS.md');lines=t.splitlines()
for i,line in enumerate(lines):
 if line.startswith('| HDMI |'):lines[i]='| HDMI | 两处Min Period用户豁免，参考位流发布、实际JTAG链恢复；配置载荷与现BOOT相同 | 修复候选未集成，未下载；无需重复加载相同载荷，完整实时HDMI仍待验；[发布与恢复](FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md) |'
 if line.startswith('| 当前恢复点 |'):lines[i]='| 当前恢复点 | **两处最小周期豁免已生效、JTAG链正常，但参考配置载荷与现BOOT相同**；先接入HDMI修复候选后再形成有效新配置，在线停止/隔离待核实；[恢复](FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md)。旧DATA独立暂停 |'
write('PROJECT-PROGRESS.md','\n'.join(lines)+'\n')
t=read('DIFFICULTIES.md');lines=t.splitlines()
for i,line in enumerate(lines):
 if line.startswith('| D05 |'):lines[i]='| D05 | 参考重建载荷与现BOOT相同，HDMI修复尚未进入整机 | 两处Min Period用户豁免，JTAG链重连扫链通过；原BOOT离线逐字节复现 | 新参考PL载荷与现BOOT一致，重下不引入修复；修复候选/在线隔离/CDC及外部时序仍待闭合，未下载；[新证据与恢复](FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md) |'
write('DIFFICULTIES.md','\n'.join(lines)+'\n')
t=read('Done.md');marker='### 工程内容总结\n\n'
t=t.replace(marker,marker+'本阶段后续实际复核：'+summary+' 新下载器枚举是外部状态变化后的新批只读扫链，不是无依据重复失败负载。原BOOT控制构建0.618秒exit0且7023552字节/SHA全同；试制BOOT工具0.627秒exit0，但“非PL字节应相同”的后检失败，完整文件/日志保留；复核确认差异只在映像名字段，载荷与已选BOOT相同。最初离线脚本UTF-8默认GBK解码错误发生在工具调用前，原空目录和失败说明保留，修正编码后新目录执行。[载荷原值](tools/pose-v1/evidence/hdmi-board-reference-20261016-r1/reference-payload-review.json)。\n\n',1)
write('Done.md',t)
t=read('FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md')
t=t.replace('当前未下载，直接阻塞为本机未发现JTAG下载器。','当前未下载。下载器重连后扫链已恢复；新发现该发布参考位流的配置载荷与当前所选BOOT相同，重复加载不会引入HDMI修复。')
t=t.replace('Procise2025.1.1temp/SVN32494在主机权限下仍报告0 cable、There are no FTDI chip found；Windows只读设备枚举未发现对应下载器。必须物理接通后重新扫链，以实际part序号/IDCODE及下载器序列号决定目标，禁止沿用旧编号。','首次两次扫链均0 cable/无FTDI；随后用户接通下载器，Windows实际枚举USB VID0403/PID6014、210512180081。依据这一外部变化建立r3新目录，Procise实际扫链4.029秒exit0：jfmql30、IDCODE0x9372c093、part 0，ps_dap part 1、IDCODE0x6ba00477。未执行program_bit；以后下载前仍需新扫链，不永久假设编号。')
t+='''

## 载荷复核后的执行决定

新发布后处理bit与所选BOOT的回退bit，完整配置载荷均5980460字节，SHA-256均`657da80bb5eff97c917cf3a6c8c5b40a331b814dd840b5ac6a0bda44fb8a935d`，逐字节完全相同；Docs/BIT/30tai_lite_detpost提供的位流也相同。区别在.bit头部日期等元数据。原始未后处理bit载荷与后处理载荷不同，未把二者混用。

使用Procise实际create_boot_image及原厂BIF的-fmql、apu_x32等原参数，先用所选原bit及三份原PS文件生成对照BOOT；结果7023552字节、SHA与当前BOOT完全相同，验证了此封装路径。再只换入新发布bit得到离线试制BOOT，其PL分区仍0字节变化，只有偏移2388和2392–2399共9字节变化，对应32位交换后的映像名称。先前“应只改变PL、其余应相同”的严格断言失败原样保留，不把工具exit0当通过，也不部署此试制BOOT。没有必要为了这些名称字段修改启动文件或重启。

这证明**文件配置载荷相同**，不等于对运行中FPGA做了完整配置读回。当前板端BOOT哈希相符，FPGA operating；若要证明运行中配置的完整身份，还需合适的硬件读回或受控加载证据，不能仅用版本号替代。

因此本轮两处Min Period特批及发布有效，但不重复加载相同参考载荷来宣称完成新的HDMI修复验收。下一有效新配置必须先将已批准HDMI修复接入整机；沿用既有独立时钟、HP2读所有权、明确CSR和stop/drain集成契约。该集成尚未执行，新接口及在线切换条件未明确的依赖步骤保持待讨论。实时整机测量和实屏验证未执行，既有上板授权保持。

[完整载荷比较](../../tools/pose-v1/evidence/hdmi-board-reference-20261016-r1/reference-payload-review.json)、[原BOOT逐字节重建](../../tools/pose-v1/evidence/hdmi-board-reference-20261016-r1/boot-control-utf8-r2/result.json)、[试制BOOT原后检失败](../../tools/pose-v1/evidence/hdmi-board-reference-20261016-r1/boot-candidate/result.json)、[本次实际成功扫链](../../tools/pose-v1/evidence/hdmi-board-reference-20261016-r1/chain-scan-device-enumerated-r3/stdout.log)。本地30TAI教程第7–9页说明BOOT生成/替换/重启路线；本轮仅做离线封装，不据此扩展启动分区修改或再次重启许可。
'''
write('FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md',t)
t=(E/'REPORT.md').read_text(encoding='utf-8')
t=t.replace('当前直接阻塞是下载器未枚举；在线停止/隔离也尚未取得证明。','以下是首次预检时状态，随后下载器已重连并扫链通过；现行结论见文末。在线停止/隔离尚未取得证明。')
t+='''

## 后续更新：物理重连和载荷相同

13:35:26 Windows枚举恢复VID0403/PID6014/210512180081。新目录r3实际Procise扫链4.029秒exit0，jfmql30 part0/0x9372c093、ps_dap part1/0x6ba00477，原两次设备缺失失败保持。枚举时另见既有ssh.exe PID28848（不属于本批已结束的传输，不擅自终止）；不称主机全部SSH为0。

离线重新封装对照BOOT实际0.618秒exit0，SHA与所选/当前板端BOOT完全相同。再换新参考bit构建试制BOOT实际0.627秒exit0，但非PL字节全同的后检失败、严格停止；离线复核发现PL分区0字节变化、只有9个映像名称字节变化。直接解析bit全载荷也证实新发布Procisebit与所选BOOT的PL载荷逐字节相同，均5980460字节/SHA657da80bb5eff97c917cf3a6c8c5b40a331b814dd840b5ac6a0bda44fb8a935d；Docs/BIT的Lite位流同载荷。这不是配置读回，不能证明任何未记录的外部加载未发生。

原试制result.json中的semantic_scope是拟核验的不变量描述，其实际布尔后检为false，不能引用该文字作为通过；reference-payload-review.json给出修正。离线控制r1默认GBK解码UTF-8失败在工具前发生，无BOOT产物；新utf8-r2目录修正后执行，不覆盖现场。

没有为同一配置载荷修改BOOT或重启，也未通过临时下载包装为新功能。两处定点豁免及参考产物发布保留，HDMI修复仍需先集成，不能把参考构建链复现记作HDMI修复或实时整机验收。用户要求的实板功能验证尚未完成。下一依赖是完整HDMI修复配置及明确的切换/CSR契约。

查询Linux FPGA Manager通用资料仅说明厂商细节属于底层驱动，不能替代FMQL驱动的隔离证据：https://cdn.kernel.org/doc/html/latest/driver-api/fpga/fpga-mgr.html 。本地原厂30TAI教程7–9页核对了BOOT封装/替换/重启路径，实际未改板端启动区。所有本批子进程均已等待结束；最后主机清理清单另存，不终止无关连接。
'''
(E/'REPORT.md').write_text(t,encoding='utf-8')
(E/'boot-control/failure-before-tool.json').write_text(json.dumps({'reason':'UTF-8 JSON decoded with Windows default GBK','EDA_started':False,'board_access':False,'corrected_in_fresh_directory':'boot-control-utf8-r2'},indent=2)+'\n')
current={'status':'RELEASED_FOR_CONTROLLED_BOARD_TEST','two_min_period_checks_user_waived':True,
 'raw_timing_pass':False,'new_JTAG_chain_pass':True,'reference_payload_identical_to_selected_BOOT':True,
 'new_HDMI_candidate_integrated':False,'programmed':False,'BOOT_written':False,'rebooted':False,
 'live_HDMI_or_new_bitstream_realtime_acceptance':False,
 'reason_not_reloading_reference':'Identical payload does not add the approved HDMI fixes; full candidate and safe switching contract still needed'}
(E/'current-status.json').write_text(json.dumps(current,indent=2)+'\n')
shutil.copyfile(Path(__file__),E/Path(__file__).name)
print(json.dumps(current,indent=2))

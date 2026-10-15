from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[2]
E=R/'tools/pose-v1/evidence/hdmi-bringup-20261015-r1'
doc=E/'documentation-revision';doc.mkdir(exist_ok=False)
changes=[]
def update(name,fn):
 p=R/name;b=p.read_bytes();s=b.decode('utf-8-sig');nl='\r\n' if '\r\n' in s else '\n'
 s=s.replace('\r\n','\n');t=fn(s)
 assert t!=s,name
 (doc/'before'/name).parent.mkdir(parents=True,exist_ok=True);(doc/'before'/name).write_bytes(b)
 p.write_bytes(t.replace('\n',nl).encode('utf-8'))
 (doc/'after'/name).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,doc/'after'/name)
 changes.append({'path':name,'before_sha256':hashlib.sha256(b).hexdigest(),'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
summary=('2026-10-15 HDMI已获实板、隔离同配置重建、16根IP修订白名单及有限衍生字段例外授权。实板只读身份/12寄存器核验通过，BOOT/六份SDK/内核同；新r3有限契约门检、97.600秒IP生成及28项原有HDL参数/生成端口后检通过。实际生成AXI3互联两入口全32个ID、64读/64写完整16拍burst及背压通过，Procise原生互联综合16.417秒exit0；纯输出OBUFDS→ODU_DS真实引脚布线兼容探针通过。完整系统当前受阻于自定义PS7扩展端口与Procise PCPU7声明不匹配，PS门检8.418秒exit1，已停止。尚无完整候选位流，未下载、未改BOOT或重启，实屏仍待验；旧DATA继续暂停。')
link='[本批总报告](tools/pose-v1/evidence/hdmi-bringup-20261015-r1/REPORT.md)、[生成/后检](tools/pose-v1/evidence/hdmi-ip-generation-20261015-r3/REPORT.md)、[PS阻塞与恢复入口](FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md)。'
def progress(s):
 start=s.index('更新日期：');end=s.index('共享模型最近实际验证：',start)
 s=s[:start]+'更新日期：2026-10-15。最后实际验证日期同日。'+summary+' '+link+'\n\n'+s[end:]
 lines=s.splitlines()
 for i,line in enumerate(lines):
  if line.startswith('| HDMI |'):
   lines[i]='| HDMI | 分组扫描/TMDS常量、有限IP生成/端口后检、AXI3有界路由仿真及原生互联综合通过；纯输出引脚兼容探针通过 | 自定义PS7→PCPU7扩展端口不匹配，当前系统构建停止；原生PHY/CDC/完整实现与实屏仍待验。已允许板测但未下载候选，BOOT保持；[恢复入口](FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md) |'
 return '\n'.join(lines)+'\n' if not s.endswith('\n') else '\n'.join(lines)+'\n'
update('PROJECT-PROGRESS.md',progress)
update('REFERENCES.md',lambda s:s.replace('\n\n','\n\n'+summary+' '+link+'\n\n以下各日期/批次保留原执行范围，旧“暂不上板”不覆盖最新实板授权。\n\n',1))
def difficult(s):
 lines=s.splitlines()
 for i,line in enumerate(lines):
  if line.startswith('| D05 |'):
   lines[i]='| D05 | HDMI实屏时序不支持；完整候选受PS扩展原语兼容阻塞 | 扫描/TMDS常量通过；有限IP生成/端口后检通过，生成AXI3两入口全ID完整burst/背压通过，原生互联综合通过；纯输出引脚兼容探针通过 | PS7→PCPU7端口不匹配，原生PS展开exit1停止；未改PS包/AI_Mate/全局数据库，未下载候选/改BOOT。PHY/CDC/完整时序和实屏仍待验；[本批报告](tools/pose-v1/evidence/hdmi-bringup-20261015-r1/REPORT.md)、[具体阻塞](FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md) |'
 return '\n'.join(lines)+'\n'
update('DIFFICULTIES.md',difficult)
def done(s):
 point=s.index('### 工程内容总结')+len('### 工程内容总结')
 s=s[:point]+'\n\n本次实机阶段配套推进：'+summary+' '+link+' Windows/Vivado2019.1、XSim每阶段90秒；原生Procise2025.1.1temp/SVN32494、JFMQL30TAI676H。IP校验180秒/生成300秒、原生门检180秒。实际生成624文件树已ZIP归档并逐条SHA/CRC核验，297项原参考SHA保持；旧字面门检、驱动阶段误判与所有失败保留。当前无后台构建。\n\n以下为此前离线批次及其当时边界：'+s[point:]
 point=s.index('### 对后续开发的参考')+len('### 对后续开发的参考')
 return s[:point]+'\n\n本次补充：受管理IP按BD角色匹配，工具编号不作契约；CONFIG/实际MODELPARAM、生成端口、AXI路由及原生工具适配分别门检。校验前旧警告与修正后阶段区分；有限例外另立门检，旧false不回写。5位thread/6位来源ID需实际返回路由验证，不能把位宽WARN一律忽略。PS7扩展AI端口不能删掉或用普通PS/黑盒绕过；纯输出OBUFDS可映射ODU_DS，但双向IODU的TMDS物理失败保留；兼容探针布线无STA签核意义。\n'+s[point:]
update('Done.md',done)
update('ARCHITECTURE-DISCUSSION-20261015.md',lambda s:s+'\n## 十三、实机授权、IP有限例外与当前PS适配阻塞\n\n'+summary+' '+link+'\n\n用户先后明确批准隔离同配置重建、16个锁定根IP及子核修订升级，随后批准IP-CONTRACT-REVIEW.md所列有限衍生字段例外。两次原字面门检拒绝、只读标注恢复失败继续保留；新建契约门检通过后才实际生成。新增ID路由仿真和原生互联综合未提高在途负载，不能扩展为整机通过。PS包、AI_Mate及系统基线均保持；JFM全局时序库替换/工具安装仍不在范围内。\n')
resume='''# HDMI候选当前状态

2026-10-15。用户已允许实板、隔离同配置重建、16根IP修订白名单和有限衍生字段例外；旧DATA调查独立暂停。当前无后台构建，尚未下载候选或更换BOOT。

## 最新实际结果

实板只读身份和12寄存器核验通过，BOOT/六份SDK/内核保持。原r6 core/r7 pixel及Lite TMDS常量128周期结果保持，9份生产扫描RTL未改。纯输出OBUFDS→ODU_DS在实际引脚的兼容探针布线通过，但无有效STA端点，不是1080p60/1485Mb/s签核；双向IODU尝试因PLACE0854失败并已拒绝。

新r3有限契约门检通过，Vivado2019.1目标生成97.599574秒exit0；28项原有HDL参数、生成前后配置和四regslice生成端口核验通过。实际生成AXI3互联两入口各32 ID、64读/64写完整16拍burst，数据/地址/路由/背压通过，一次全局在途，仿真5.941891秒/90秒预算；Procise原生互联展开/综合16.416899秒exit0。

完整候选当前受阻：自定义PS生成包装直接原生展开时，PS7_inst端口超过PCPU7声明，ELAB-E-6/RTL-0902，8.417573秒exit1停止。没有改PS包/参数、AI_Mate或全局库，没有用黑盒替代。当前没有完整系统位流，显示器最近用户现场仍为“不支持当前时序”。

## 恢复入口与边界

先阅读[PS适配状态](PS-ADAPTATION-STATUS.md)，闭合30TAI扩展PS的正式映射/网表迁移依据；FMP100迁移流程不能直接套用。本机30TAI教程的全局库替换未执行，现有不改全局数据库/不安装升级/不升级自定义PS或AI_Mate边界保持。已有板测授权持续有效，不重复申请；候选下载仍需真实完整实现产物、扫链及硬件停止/安全切换条件。

PS/DDR/HP2/GP所有权、CSR解码、原生PHY/规范复位、CDC及完整实现/时序/实屏仍待验。无FD owner不证明在途DDR读停止。BOOT/SDK/模型/RAW/正式CPU注册/NPU分配保持，不增加重启许可。失败目录和原门检不回写，不自动复跑失败负载。

[本批总报告](../../tools/pose-v1/evidence/hdmi-bringup-20261015-r1/REPORT.md)、[生成后检报告](../../tools/pose-v1/evidence/hdmi-ip-generation-20261015-r3/REPORT.md)、[已获批准的有限规则](IP-CONTRACT-REVIEW.md)、[集成契约](INTEGRATION.md)。历史分组结果见[前批报告](../../tools/pose-v1/evidence/hdmi-split-20261015-r1/REPORT.md)，原失败均保留。
'''
update('FPGA/hdmi_candidate/RESUME.md',lambda s:resume)
update('FPGA/hdmi_candidate/README.md',lambda s:s.replace('**本批离线验证与TMDS常量修正已完成。**','**已允许实板；有限IP生成、参数/端口后检、AXI3仿真与原生互联综合通过；完整系统停在PS7→PCPU7扩展端口兼容门检。尚未下载候选。**',1))
update('FPGA/hdmi_candidate/INTEGRATION.md',lambda s:s.replace('\n\n','\n\n最新配套：隔离IP修订与有限例外已批准，生成/后检及AXI3有界路由仿真、原生互联综合通过；自定义PS7扩展端口与PCPU7声明不匹配，当前停止完整系统构建。纯输出OBUFDS→ODU_DS实际引脚布线兼容探针通过，无时序签核；双向IODU路径已拒绝。详见[PS适配状态](PS-ADAPTATION-STATUS.md)、[恢复入口](RESUME.md)。下文仍是尚未完成的系统契约，不能把局部门检当成集成完成。\n\n',1))
update('FPGA/hdmi_candidate/BOARD-PLAN.md',lambda s:s.replace('## 下一项需要明确的实现范围','## 已批准的隔离实现范围（以下保留提出时依据）',1).replace('## 已实际执行','## 最新配套执行状态\n\n用户已先后批准同配置重建、16根白名单修订升级和有限衍生字段例外。新r3生成/后检、AXI3全ID完整burst仿真和原生互联综合通过；当前阻塞为PS7扩展端口与PCPU7声明不兼容，PS原生门检exit1停止。详见[PS适配状态](PS-ADAPTATION-STATUS.md)。原参考/PS包/AI_Mate/全局数据库未改，候选未下载。下方建议中的审批请求是历史，已有批准不重复申请；全局库、BOOT及新重启边界保持。\n\n## 已实际执行',1))
update('FPGA/hdmi_candidate/IP-REVISION-PLAN.md',lambda s:s.replace('# 隔离工程IP修订升级的具体待确认范围','# 隔离工程IP修订升级的已批准范围与结果',1).replace('## 实际工具结果','用户已明确批准白名单修订升级与严格门检；实际升级38.897797秒exit0，但原字面门检拒绝。进一步审查后的有限例外另获批准，新r3生成/后检及AXI3原生互联综合通过，PS原生端口适配失败停止。旧门检false不回写；[生成报告](../../tools/pose-v1/evidence/hdmi-ip-generation-20261015-r3/REPORT.md)、[当前恢复入口](PS-ADAPTATION-STATUS.md)。以下保留升级前证据和当时提出的操作范围，不作为再次审批请求。\n\n## 实际工具结果',1))
update('FPGA/hdmi_candidate/IP-CONTRACT-REVIEW.md',lambda s:s.replace('当前尚未运行正式generate_target或综合/实现系统，升级工具自动产生的例化模板单独记录。','提出有限规则时尚未运行正式generate_target；用户批准后新r3已生成并通过参数/端口后检及AXI3有界路由/原生互联综合，完整系统当前受PS7→PCPU7扩展端口不匹配阻塞。升级工具自动产生的例化模板与后续正式生成分开记录。[实际报告](../../tools/pose-v1/evidence/hdmi-ip-generation-20261015-r3/REPORT.md)。',1))
(doc/'changes.json').write_text(json.dumps({'changes':changes,'historical_manifests_not_rewritten':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Updated',len(changes),'documents; before/after preserved')

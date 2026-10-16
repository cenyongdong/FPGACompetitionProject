"""Update one current status and preserve earlier records/credential-redacted snapshots."""
from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1'
assert json.loads((E/'result-review.json').read_text())['full_system_signoff'] is False
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return p.read_text(encoding='utf-8-sig')
def write(rel,text):(R/rel).write_text(text,encoding='utf-8')
# These entries were not edited earlier in this turn. Explicitly record late snapshot timing.
before_ids=json.loads(read(E/'documentation-before-identities.json'))
for rel in ['FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md','FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md']:
 p=R/rel;dest=E/'before'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 before_ids.append({'path':rel,'original_SHA':sha(p),'snapshot_SHA':sha(dest),'redacted':False,'captured':'after execution, before first edit this turn'})
(E/'documentation-before-identities.json').write_text(json.dumps(before_ids,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report='tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/REPORT.md';gate='FPGA/hdmi_candidate/AI-CLOCK-GATE.md'
summary=('原厂路径二已实际执行到完整参考位流及Procise ICAP输出：当前2018.3新增32项原厂IP库替换，独立备份/前后SHA通过；'
 '与既有030ai九项补丁合计41项预期变化，2019.1及Procise库保持。28项XCI参数、5份DDR配置及父BD后检保持；'
 '24项IP OOC和整机综合完成。首批完整链在1800秒监控上限处停止并封存，无ERROR；'
 '代理自主建立impl_r2复用综合，实际1173.647281秒exit0，原策略/约束/hook不变，未重跑IP综合。')
limits=('建立/保持裕量0.030/0.021ns，但AI时钟模型1GHz有2处最小周期违例（WPWS−0.409ns），总时序不通过；'
 'CDC及外部时序覆盖尚未签核。参考产物列为HELD，未接入HDMI候选、未下载、未改BOOT/SDK/模型/AI_Mate或NPU频率；旧DATA仍暂停。')
links=f' [完整证据]({report})、[AI时钟门检与恢复边界]({gate})。'
t=read(R/'PROJECT-PROGRESS.md');head,old,rest=t.split('\n\n',2)
t=head+'\n\n更新日期及最后实际验证日期：2026-10-16。'+summary+limits+links+'\n\n'+rest
line=next(x for x in t.splitlines() if x.startswith('| HDMI |'))
t=t.replace(line,'| HDMI | 原厂2018.3＋JFM整机综合/布局布线及Procise ICAP参考位流已生成；AXI2018实际模型64读/64写burst通过 | 完整时序因AI模型2处最小周期违例不通过，CDC/外部约束未签核；候选未集成、未上板；[门检]('+gate+') |')
t=t.replace('**原厂路径二审查、MIG同配置OOC及前置检查完成**；[审查与构建边界](FPGA/hdmi_candidate/ROUTE2-AUDIT.md)',
 '**原厂路径二参考位流已生成，AI最小周期/CDC门检未验收**；[实际停止点与恢复](FPGA/hdmi_candidate/AI-CLOCK-GATE.md)')
write('PROJECT-PROGRESS.md',t)
for rel in ['REFERENCES.md','FPGA/hdmi_candidate/RESUME.md','FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md','FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md']:
 t=read(R/rel);head,old,rest=t.split('\n\n',2);prefix='../../' if rel.startswith('FPGA/') else ''
 g='AI-CLOCK-GATE.md' if prefix else gate
 t=head+'\n\n2026-10-16最新状态：'+summary+limits+f' [本批实际结果]({prefix}{report})、[门检与恢复边界]({g})。此前32项库和四项GT处理范围已由用户授权自主决策并执行，不再等待重复批准；当前停在真实门检问题，不能按超时例外放行。\n\n'+rest
 if rel=='REFERENCES.md':
  line=next(x for x in t.splitlines() if x.startswith('| Vivado 辅助工具/MCP |'))
  t=t.replace(line,'| Vivado 辅助工具/MCP | D:/vivado18.3/Vivado/2018.3/bin/vivado.bat，64-bit Build2405991；2019.1保留 | 当前030ai九项＋32项原厂IP库补丁；参考位流/Procise ICAP已生成，完整时序未通过；[实际结果]('+report+') |')
 write(rel,t)
t=read(R/'DIFFICULTIES.md');line=next(x for x in t.splitlines() if x.startswith('| D05 |'))
t=t.replace(line,'| D05 | HDMI候选尚未集成，参考整机时序门检未通过 | 原厂混合链已生成真实参考位流及Procise ICAP产物；28项XCI、DDR及BD保持，AXI2018实际模型通过 | AI时钟模型1GHz的BUFG/PLL最小周期失败2处，WPWS−0.409ns；CDC/外部时序尚待解释，HELD未下载；[门检]('+gate+')／[完整证据]('+report+') |')
write('DIFFICULTIES.md',t)
t=read(R/'Done.md');h='### 工程内容总结\n\n'
t=t.replace(h,h+'2026-10-16原厂路径二实施：'+summary+limits+' Windows工作目录D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1；Vivado2018.3、Procise2025.1.1temp/SVN32494。只复制工程及JFM配套，不复制Vivado。实际根IP/父BD生成73.044秒，MIG前置综合261.136秒；XSim2018.3实际互联每阶段90秒内，两个入口各32 ID、64读/64写完整burst及背压通过。'+links+' 原始嵌套IP生成调用错误、生成注释严格字节断言失败及首批监控中断均保留；独立修正入口/分析，没有回写原失败。GT例外仅四项；原MIG CLK_REF例外在JFM hook前即存在。\n\n以下保留先前审查及其它批次实际结果：\n\n',1)
h='### 对后续开发的参考\n\n'
t=t.replace(h,h+'路径二实施参考：Generate Bitstream、Procise处理、setup/hold、最小周期和CDC必须分开报告；本次位流已生成但总时序明确不通过。报告复开DCP会恢复会话DRC默认状态，要保留原实现会话和复开默认报告的上下文。嵌套IP由父BD生成；实现可在超时后用新运行目录复用已完成综合，逐行核验实际命令，不能改门槛或覆盖旧日志。柜台式名字不证明IP类型，rindex/windex是FIFO，本轮已更正counter实例推断。原厂exec回传的Procise详细stdout未被其脚本打印，保留原命令、状态传播和位流身份，不伪称有该次独立stdout；下次候选应在执行前完善该层日志。\n\n',1)
write('Done.md',t)
t=read(R/'ARCHITECTURE-DISCUSSION-20261015.md')
t+='\n\n## 十九、授权自主配置、原厂整机链实际执行及门检停止\n\n2026-10-16用户同意方案，要求查看本地资料、自主决策并推进。已据此选择完整32项原厂IP库配套、独立备份后就地应用、保留change_speed=FALSE，按原厂030ai范围处理四项GT检查；保留BOOT/SDK/模型及AI_Mate。\n\n'+summary+limits+links+' 当前AI时钟链原网表已存在，实际可见BUFG只带锁定状态寄存器，硬核时钟适配语义未证；不据此自行豁免最小周期。setup/hold为正不能覆盖该失败。代理自主拆分超时作业并保留全部旧记录，不为超时再次请求批准；真实时序/CDC问题不因此放行。\n'
write('ARCHITECTURE-DISCUSSION-20261015.md',t)
t=read(R/'FPGA/hdmi_candidate/INTEGRATION.md');head,old,rest=t.split('\n\n',2)
t=head+'\n\n2026-10-16最新：原厂Vivado2018.3＋JFM／Procise路径已生成真实参考整机位流；原生PCPU7导入不是此路径前置条件。完整时序因AI模型2处最小周期违例未通过，CDC/外部约束未签核，参考产物HELD。HDMI扫描候选尚未接入该工程，以下资源、CSR、复位和CDC集成契约仍待实施。[当前门检](AI-CLOCK-GATE.md)。\n\n此前原生工具阶段结果保留：'+old+'\n\n'+rest
write('FPGA/hdmi_candidate/INTEGRATION.md',t)
t=read(R/'FPGA/hdmi_candidate/JFM-FLOW-REVIEW.md')
head,old,rest=t.split('\n\n',2)
t=head+'\n\n2026-10-16最新：用户已同意审查后的实施方案并授权自主决策。32项原厂IP库配套已执行，四项GT检查按原厂范围处理；参考整机实现与Procise ICAP位流生成完成。完整时序未通过（AI模型最小周期2处），产物HELD，候选未集成/未上板。[当前实际结果与恢复](AI-CLOCK-GATE.md)、[实施配置](ROUTE2-BUILD-PLAN.md)。\n\n以下为此前审查/路径选择依据：\n\n'+old+'\n\n'+rest
write('FPGA/hdmi_candidate/JFM-FLOW-REVIEW.md',t)
t=read(R/'FPGA/hdmi_candidate/ROUTE2-AUDIT.md')
t=t.replace('2026-10-16，用户批准审查路径二，并允许代理依据现场自主处理超时。','2026-10-16，用户随后已同意实施并授权自主决策，参考整机链实际结果及门检停止见[AI-CLOCK-GATE.md](AI-CLOCK-GATE.md)。以下保留路径二审查时的结果与边界；32项配套及GT范围已在后续实施，不再等待重复批准。原审查时，用户批准审查路径二，并允许代理依据现场自主处理超时。',1)
t=t.replace('缺省TRUE，会再替换paspd/fmsh/030ai/zynq.lib/padr等','缺省TRUE；实际xc7z030分支只复制paspd/fmsh/030ai下zynq.lib和zynq.padr（后续已证实均与现安装同SHA）')
write('FPGA/hdmi_candidate/ROUTE2-AUDIT.md',t)
t=read(R/'FPGA/hdmi_candidate/ROUTE2-BUILD-PLAN.md')
t+='\n\n## 本次实际执行与自主拆分\n\n'+summary+limits+' [门检与后续边界](AI-CLOCK-GATE.md)。32项原厂源已应用，32份独立原值SHA可回退；030ai默认速度分支两份源与现安装逐位相同，FALSE仅跳过重复写入。已证实MIG CLK_REF非专用路由例外先于JFM hook存在，不新增HDMI例外。\n\n首批完整链1800秒监控终止后，进程回收为0，原impl_1打包并逐项SHA核验；新impl_r2使用同一合格综合输入和相同实现命令，仅报告对象名称改变。新阶段仍初始180秒、依据真实进展延至1260秒，1173.647281秒完成；没有重复IP/顶层综合。该处理落实用户超时自主判断授权，原中断不是逻辑通过，也不阻断后续取证。真实AI最小周期及CDC门检保持，不以超时规则放行。\n'
write('FPGA/hdmi_candidate/ROUTE2-BUILD-PLAN.md',t)
print(json.dumps({'existing_current_documents_updated':13,'new_AI_clock_gate':True,'old_manifests_unchanged':True}))

from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent
assert not (E/'documentation-revision.json').exists()
names=['PROJECT-PROGRESS.md','Done.md','DIFFICULTIES.md','REFERENCES.md','ARCHITECTURE-DISCUSSION-20261015.md','FPGA/hdmi_validation/PROPOSAL.md','FPGA/hdmi_validation/README.md']
for n in names:
 p=E/'before'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/n,p)
checkpoint='tools/pose-v1/evidence/hdmi-candidate-pause-20261015-r1/CHECKPOINT.md'
resume='FPGA/hdmi_candidate/RESUME.md'
status='HDMI候选已按用户明确要求暂停，等待唤醒。隔离候选AXI10类/控制7类/CSR检查及完整1080p帧4,147,200字节背压验证通过，时钟与控制模块Procise原生展开/综合exit0；尚未原工程集成、布局布线/CDC时序或上板，不称整条HDMI通过。'
p=R/'PROJECT-PROGRESS.md';s=p.read_text(encoding='utf-8');a=s.index('更新日期：');b=s.index('共享模型最近实际验证：',a)
s=s[:a]+'更新日期：2026-10-15。'+status+' [暂停快照]('+checkpoint+')、[唤醒入口]('+resume+')。'+s[b:]
lines=s.splitlines();i=next(i for i,x in enumerate(lines) if x.startswith('| HDMI |'));lines[i]='| HDMI | **用户明确暂停**。候选模块行为与完整帧验证、Procise原生展开/综合完成；显示器仍报不支持时序 | 等待明确唤醒；先核身份和地址页边界，再原工程/FIFO/PHY/总线/时钟CDC集成。暂不上板、不换BOOT；[恢复]('+resume+') |'
i=next(i for i,x in enumerate(lines) if x.startswith('| 当前恢复点 |'));lines[i]='| 当前恢复点 | **HDMI候选暂停，等待用户唤醒**；[源码/证据/剩余边界]('+resume+')；本批工具已退出，旧DATA继续独立暂停 |'
p.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
p=R/'Done.md';s=p.read_text(encoding='utf-8');title='# 已完成工作记录\n\n';assert s.startswith(title)
entry='## 2026-10-15：HDMI隔离候选模块验证及用户要求暂停\n\n### 工程内容总结\n\n'+status+' 用户批准保持1080p60的独立时钟/AXI/停止换帧候选后，已实现7个独立RTL模块与有限测试/构建入口，原参考源码、BOOT、模型和SDK保持。候选r2行为门检exit0，整帧32,400 burst/518,400字逐地址与数据比较；Procise2025.1.1temp/SVN32494在JFMQL30TAI676H原生时钟/控制展开综合分别6.752/8.677秒exit0，真实EDIF保留。用户随后要求暂停，未再启动构建；所有已发工具返回，工具进程名盘点为空，较早板端/FPAI已回收。[暂停证据]('+checkpoint+')。\n\n### 对后续开发的参考\n\n候选分层保持SDK、PS/NPU边界；命令接收与地址采用/停止完成分开，缺失RLAST不得提前释放。原生综合和RTL验证不能替代FIFO/PHY/总线集成、PLL物理频率、CDC及布局布线；非128字节对齐帧址的4KiB burst拆分尚需审查。读[恢复入口]('+resume+')核对源码SHA及最新指令，保持当前BOOT、不上板；旧DATA单独暂停。文档前值及修订SHA另存，不覆盖原失败或历史完成清单。\n\n'
p.write_text(title+entry+s[len(title):],encoding='utf-8',newline='\n')
p=R/'DIFFICULTIES.md';lines=p.read_text(encoding='utf-8').splitlines();i=next(i for i,x in enumerate(lines) if x.startswith('| D05 |'));lines[i]='| D05 | HDMI实屏时序不支持，原参考AXI/停止缺陷 | 原行为缺陷已复现；新候选模块、完整帧背压及Procise原生展开/综合过，当前板端BOOT保持 | **用户要求暂停**，未原工程集成/布局布线/时序/实屏验收；非128字节对齐帧址页边界待查，等待唤醒；[恢复]('+resume+') |';p.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
p=R/'REFERENCES.md';s=p.read_text(encoding='utf-8');i=s.index('\n\n')+2;p.write_text(s[:i]+'2026-10-15 '+status+' [暂停与证据]('+checkpoint+')、[恢复]('+resume+')。旧DATA继续暂停。\n\n'+s[i:],encoding='utf-8',newline='\n')
p=R/'ARCHITECTURE-DISCUSSION-20261015.md';s=p.read_text(encoding='utf-8');s+='\n## 十、候选实现的实际进展与用户暂停\n\n'+status+' 已获授权为隔离副本候选修正与验证、暂不上板；最新暂停优先，只有用户明确唤醒后继续。原先误点稳定画面已由用户更正，当前显示器已接仍不支持时序。\n\n[停点、源码身份和后续边界]('+checkpoint+')、[恢复入口]('+resume+')。\n';p.write_text(s,encoding='utf-8',newline='\n')
p=R/'FPGA/hdmi_validation/PROPOSAL.md';s=p.read_text(encoding='utf-8');s=s.replace('# HDMI 候选修正方案（待架构确认）','# HDMI 候选修正方案（已批准候选阶段，现按用户要求暂停）',1);s+='\n## 状态更新\n\n用户已批准隔离候选修正与离线验证，暂不上板；第一轮模块行为/完整帧及Procise原生综合完成后，用户明确要求暂停。本文前述“待确认／未实施”为形成方案时的历史状态。当前以[恢复入口](../hdmi_candidate/RESUME.md)及暂停快照为准，不自动继续。\n';p.write_text(s,encoding='utf-8',newline='\n')
p=R/'FPGA/hdmi_validation/README.md';s=p.read_text(encoding='utf-8');s=s.replace('尚待架构确认。','用户已批准隔离候选阶段，现已明确要求暂停；恢复先读 `../hdmi_candidate/RESUME.md`。',1);p.write_text(s,encoding='utf-8',newline='\n')
shutil.copytree(R/'FPGA/hdmi_candidate',E/'candidate-source')
source={str(p.relative_to(R/'FPGA/hdmi_candidate')).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'FPGA/hdmi_candidate').rglob('*')) if p.is_file()}
(E/'source-manifest.json').write_text(json.dumps(source,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
revision=[{'path':n,'before_sha256':hashlib.sha256((E/'before'/n).read_bytes()).hexdigest(),'after_sha256':hashlib.sha256((R/n).read_bytes()).hexdigest(),'snapshot':'before/'+n} for n in names]
(E/'documentation-revision.json').write_text(json.dumps(revision,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(E/'state.json').write_text(json.dumps({'state':'paused_by_explicit_user_request','resume_requires_explicit_user_wakeup':True,'background_continuation':False,'latest_tool_calls_completed':True,'tool_process_name_inventory_empty':True,'CIM_commandline_inventory_denied':True,'BOOT_changed':False,'board_test_started_for_candidate':False,'candidate_full_system_integration':False},indent=2)+'\n',encoding='utf-8')
for pattern in ('hdmi-candidate-sim-20261015-r*','hdmi-candidate-procise-*-20261015-r*','hdmi-procise-api-20261015-r*'):
 for d in (R/'tools/pose-v1/evidence').glob(pattern):
  if (d/'files.sha256.json').exists():continue
  files={str(p.relative_to(d)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.rglob('*')) if p.is_file()}
  (d/'files.sha256.json').write_text(json.dumps(files,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
files={str(p.relative_to(E)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(E.rglob('*')) if p.is_file() and p.name!='files.sha256.json'}
(E/'files.sha256.json').write_text(json.dumps(files,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Paused checkpoint and source identities saved. No task execution resumed.')

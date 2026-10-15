from pathlib import Path
import ast,hashlib,json,shutil
R=Path('D:/FPGACompetitionProject')
E=R/'tools/pose-v1/evidence/hdmi-resume-20261015-r1'
C=R/'FPGA/hdmi_candidate'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save_json(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def replace_once(p,old,new):
 t=p.read_text(encoding='utf-8');assert old in t,(p,old);p.write_text(t.replace(old,new,1),encoding='utf-8')

# Never amend the old execution.json, manifests or prior source snapshots.
for rev in ('r3','r5'):
 W=R/('.local/hdmi-candidate-sim-20261015-'+rev)
 P=R/('tools/pose-v1/evidence/hdmi-candidate-sim-20261015-'+rev)
 shutil.copytree(W,P/'failure-work-copy',ignore=shutil.ignore_patterns('xsim.dir','*.pb','*.wdb'))
 X=P/'failure-work-copy/xsim-diagnostics';X.mkdir()
 for n in ('xsimkernel.log','xsimcrash.log','Compile_Options.txt','xsim_script.tcl'):
  src=W/'xsim.dir/candidate'/n
  if src.is_file():shutil.copyfile(src,X/n)
 if rev=='r5':
  raw=(W/'xsim.log').read_text(errors='replace')
  save_json(P/'timeout-review.json',{'driver_exit':1,'exception':'subprocess.TimeoutExpired',
    'stage':'simulate','outer_budget_seconds':90,'kernel_run_elapsed_seconds_from_log':88,
    'all_assertions_completed_in_raw_log':'HDMI_CANDIDATE_TEST_PASS' in raw,
    'overall_accepted':False,'automatic_retry':False,
    'explanation':'Outer deadline failure remains authoritative; raw kernel assertions and naturally completed child exit are separate evidence. Legacy launcher cleanup did not ensure process-tree termination; new runner correction is prepared but not executed.'})

resume='''# HDMI候选的当前状态与继续入口

2026-10-15用户明确唤醒后，已恢复离线候选。当前本轮仿真在90秒外层预算触发超时后停止，未自动重跑；新分组入口已准备，等待用户确认新批次。没有后台续跑。旧DATA坏读调查继续单独暂停。

## 授权范围

保持1080p60，在隔离目录修正独立显示时钟、AXI读握手、可观测停止/换帧接口，做RTL与Procise兼容/构建核验；暂不上板、不替换BOOT，不迁移/升级既有IP或工具。暂停时17项源码身份在本次恢复前全部核对一致；历史见[暂停检查点](../../tools/pose-v1/evidence/hdmi-candidate-pause-20261015-r1/CHECKPOINT.md)。

## 本次实际结果

- r3复现64字节对齐、页尾偏移4032时的4KiB burst越界拒绝；修正按页拆分后r4实际exit0。偏移0/64/4032三个完整1080p帧均518400个64位字/4147200字节，逐地址/数据通过；相应32400/32401/32401个burst。
- 新增双时钟FIFO、连续1080p扫描及scanout组合。停止保持HS/VS/DE，活动区输出黑色；欠载报faults位3并停止新请求、排空在途AXI。
- Procise scanout r1原生展开/综合exit0，10.620秒，真实EDIF中1个RAMH36E1；未布局布线、完整CDC/时序或电气签核。
- r5编译/展开exit0，原始xsim.log记录所有断言完成：完整2073600像素比对、2200×1125时序、欠载排空、像素时钟停止时STOP，以及原AXI/CSR/控制/三基址/FIFO用例。但外层simulate调用90秒TimeoutExpired、驱动exit1，**整体不验收**。原日志完整保留，不能只摘PASS掩盖超时。
- 原工程101项引用中93存在、8项JFM hook文件缺失，JFM_Kits中有6项同名；与旧索引一致。没有安装hook、修改数据库或自动迁移IP。PS/DDR/TMDS仍未完成集成。

## 已准备、未执行的新批次

`scripts/simulate.py`增加独立core/pixel展开根，避免长扫描期间继续驱动无关单元测试；FIFO测试完成后关闭自己的测试时钟。每阶段仍90秒，失败保存原始输出/源码；超时仅清理本次进程树，绝不自动重试。新入口仅做Python AST静态语法检查，未动态验证，原r5失败不回写。

如用户明确同意新批次，依次执行：

1. Windows，工作目录D:/FPGACompetitionProject；先确认r6/r7新目录不存在、工具版本和候选源码身份一致。`python FPGA/hdmi_candidate/scripts/simulate.py r6 core`：控制/AXI/CSR与三基址完整DMA帧组，每阶段90秒。
2. 第一组exit0且PASS/无Fatal后，再`python FPGA/hdmi_candidate/scripts/simulate.py r7 pixel`：FIFO与完整1080p扫描组，每阶段90秒。
3. 任一非零、超时、Fatal或缺少PASS，保存并停止，不启动下一组、不复用失败目录、不延长预算。结束盘点本批工具进程并归档最终SHA。

新批次不含板端运行、BOOT替换或IP迁移。两组通过也仅说明离线逻辑成立，不能跳过[集成与约束门槛](INTEGRATION.md)。

## 尚未完成

HP2读写所有权接入、GP总线适配及地址映射；真实PLL/像素/串行时钟与锁定观测；复位和Gray/邮箱CDC约束；原生TMDS序列器、电平/封装/BANK与1485Mb/s物理能力；PS/DDR/AI/IP配套构建、布局布线、setup/hold/未约束路径审查、位流和实屏。720p取舍须另议。

显示器现场仍是已接入但不支持时序，误点“稳定画面”无效。原始参考源码、当前BOOT/SDK/模型/RAW、CPU注册和NPU分配保持。完整执行、原值与前后身份见[本轮报告](../../tools/pose-v1/evidence/hdmi-resume-20261015-r1/REPORT.md)。
'''
(C/'RESUME.md').write_text(resume,encoding='utf-8')
short='HDMI候选已由用户明确唤醒，4KiB按页拆分修正经r4三基址完整帧验证通过；新增FIFO/连续1080p扫描的Procise原生综合exit0。r5全部断言完成，但外层90秒超时、驱动exit1，整体不验收；已停止且未重跑，新分组入口待确认。PS/DDR/TMDS、CDC及系统实现未完成，暂不上板、不换BOOT。'
reportlink='[本轮证据](tools/pose-v1/evidence/hdmi-resume-20261015-r1/REPORT.md)、[继续入口](FPGA/hdmi_candidate/RESUME.md)'
p=R/'PROJECT-PROGRESS.md';t=p.read_text(encoding='utf-8');a=t.index('更新日期：');b=t.index('共享模型最近实际验证：',a)
t=t[:a]+'更新日期：2026-10-15。'+short+' '+reportlink+'。'+t[b:]
lines=t.splitlines()
for i,line in enumerate(lines):
 if line.startswith('| HDMI |'):
  lines[i]='| HDMI | 4KiB修正r4通过；scanout原生综合exit0；r5断言完成但外层超时，整体未验收 | 本轮已停止，分组新批次待确认；PS/DDR/TMDS/CDC及物理实现待完成。暂不上板、不换BOOT；[继续入口](FPGA/hdmi_candidate/RESUME.md) |'
for i,line in enumerate(lines):
 if 'HDMI' in line and '恢复入口' in line and ('等待' in line or '先核' in line):
  lines[i]='HDMI当前继续入口为[候选状态](FPGA/hdmi_candidate/RESUME.md)：r4三基址通过、scanout原生综合完成，r5外层超时后停止；新分组批次等待用户确认。旧DATA仍暂停，暂不上板。'
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
p=R/'REFERENCES.md';t=p.read_text(encoding='utf-8');a=t.index('2026-10-15 HDMI候选');b=t.index('\n\n',a);p.write_text(t[:a]+'2026-10-15 '+short+' '+reportlink+'。旧DATA继续暂停。'+t[b:],encoding='utf-8')
p=R/'DIFFICULTIES.md';lines=p.read_text(encoding='utf-8').splitlines()
for i,line in enumerate(lines):
 if line.startswith('| D05 |'):
  lines[i]='| D05 | HDMI实屏时序不支持；原AXI/停止缺陷及候选集成风险 | r4三基址完整帧按4KiB拆分通过；新FIFO/扫描原生综合exit0，1个36Kb RAM；r5完整像素断言完成但外层90秒超时 | 本轮停止，整体不验收；分组新批次待确认，PS/DDR/TMDS/CDC及物理实现未完成。BOOT保持；[证据](tools/pose-v1/evidence/hdmi-resume-20261015-r1/REPORT.md) |'
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
p=R/'Done.md';replace_once(p,'## 2026-10-15：HDMI隔离候选模块验证及用户要求暂停','## 2026-10-15：HDMI隔离候选开发、暂停与恢复验证')
replace_once(p,'### 工程内容总结\n\n','### 工程内容总结\n\n恢复后实际结果：'+short+' Windows工作目录D:/FPGACompetitionProject，XSim2019.1每阶段90秒、Procise2025.1.1temp/SVN32494对JFMQL30TAI676H展开/综合预算180秒。新综合10.620秒exit0；r4每基址4147200字节完整地址/数据通过。r5原始日志完成2073600像素逐点比对、欠载排空、停像素时钟后STOP及全部旧用例，外层TimeoutExpired仍保留为失败。脚本已准备分组与失败证据/进程树清理修正，仅静态语法检查，无自动重跑。原参考/BOOT身份复核、本轮源码/日志与文档前后身份见'+reportlink+'。本次无板端连接。\n\n以下保留暂停时成果与当时状态：\n\n')
replace_once(p,'### 对后续开发的参考\n\n','### 对后续开发的参考\n\n恢复后补充：页拆分保留64字节帧址契约；原语综合不等于系统实现。保持像素扫描与内存停止两个责任边界，欠载停止不得伪造AXI完成。全像素断言PASS不能盖过外层超时；拆分独立展开根以降低无关测试事件，需新批次确认后实际验证。原工程hook/IP配套、HP2/GP映射和物理TMDS/CDC尚未闭合，详见[集成契约](FPGA/hdmi_candidate/INTEGRATION.md)。\n\n')
p=R/'ARCHITECTURE-DISCUSSION-20261015.md'
with p.open('a',encoding='utf-8') as f:f.write('\n\n## 十一、明确唤醒后的实际进展\n\n'+short+' '+reportlink+'。\n\n本次未连接板端。候选新分组验证方案已准备，每组每阶段仍90秒；按Agents.md失败停止与禁止自动重试规则，须明确确认新批次后执行。JFM hook/IP迁移和物理TMDS仍需闭合配套，不将模块综合推广为整机成功。原暂停记录保留历史，旧DATA暂停不解除。\n')

syntax={}
for p in (C/'scripts').glob('*.py'):
 ast.parse(p.read_text(encoding='utf-8'),filename=str(p));syntax[str(p.relative_to(R))]='AST parse passed; not dynamic validation'
save_json(E/'prepared-script-syntax.json',syntax)
previous=json.loads((R/'tools/pose-v1/evidence/hdmi-resource-audit-20261015-r1/sources.json').read_text(encoding='utf-8'))
check=[]
for f in previous:
 p=Path(f['path']);now=digest(p) if p.is_file() else None
 check.append({'path':str(p),'expected_sha256':f['sha256'],'actual_sha256':now,'equal':now==f['sha256']})
save_json(E/'protected-reference-identities.json',check)
assert all(v['equal'] for v in check),'Reference baseline changed; stop'
save_json(E/'clock-string-analysis.json',{'reference':'rtl/display/uihdmitx.v:92,136','original_unchanged':True,
 'string_value_low10':int.from_bytes(b'1111100000','big')&1023,'binary_value':int('1111100000',2),
 'current_BOOT_root_cause_proven':False})
assert not (R/'.local/hdmi-candidate-sim-20261015-r6').exists()
assert not (R/'.local/hdmi-candidate-sim-20261015-r7').exists()
print('Archived failure evidence; updated docs; protected references',len(check),'all unchanged; Python syntax passed; no simulation rerun')

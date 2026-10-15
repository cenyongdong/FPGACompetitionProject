from pathlib import Path
import ast,hashlib,json,shutil,re
R=Path('D:/FPGACompetitionProject');C=R/'FPGA/hdmi_candidate'
E=R/'tools/pose-v1/evidence/hdmi-split-20261015-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def put(p,t):
 old=p.read_bytes();newline='\r\n' if b'\r\n' in old else '\n'
 p.write_bytes(t.replace('\r\n','\n').replace('\n',newline).encode('utf-8'))
def replace_once(p,old,new):
 t=p.read_text(encoding='utf-8');assert old in t,(p,old);put(p,t.replace(old,new,1))
link='[本批报告](tools/pose-v1/evidence/hdmi-split-20261015-r1/REPORT.md)、[候选状态](FPGA/hdmi_candidate/RESUME.md)'
short='用户已认可r5像素内核结果及4KiB/FIFO成果；新r6 core/r7 pixel全阶段exit0，仿真分别11.540/30.102秒，均未超90秒。隔离uihdmitx.v两处时钟输入已改10\'b1111100000，Lite 7FAMILY新旧模型各128周期验证20%→50%占空比通过。原r5超时及非目标UFAMILY精确边沿诊断失败保留。PS/DDR/TMDS原生物理集成、CDC/实现时序及实屏待验，暂不上板、不换BOOT。'
p=R/'PROJECT-PROGRESS.md';t=p.read_text(encoding='utf-8');a=t.index('更新日期：');b=t.index('共享模型最近实际验证：',a)
t=t[:a]+'更新日期：2026-10-15。'+short+' '+link+'。'+t[b:]
lines=t.splitlines()
for i,l in enumerate(lines):
 if l.startswith('| HDMI |'):
  lines[i]='| HDMI | r6 core/r7 pixel通过，4KiB/FIFO成果认可；候选两处TMDS时钟常量修正，Lite 128周期20%→50%占空比通过 | 本批离线范围完成；PS/DDR/TMDS原生适配、CDC/实现时序及实屏待验。暂不上板、不换BOOT；[本批证据](tools/pose-v1/evidence/hdmi-split-20261015-r1/REPORT.md) |'
 if l.startswith('| 当前恢复点 |'):
  lines[i]='| 当前恢复点 | **本批HDMI离线分组验证及常量修正完成**；[结果/物理集成待办](FPGA/hdmi_candidate/RESUME.md)；无后台作业，旧DATA继续独立暂停 |'
put(p,'\n'.join(lines)+'\n')
p=R/'REFERENCES.md';t=p.read_text(encoding='utf-8');a=t.index('2026-10-15 HDMI候选');b=t.index('\n\n',a);put(p,t[:a]+'2026-10-15 HDMI：'+short+' '+link+'。旧DATA继续暂停。'+t[b:])
p=R/'DIFFICULTIES.md';lines=p.read_text(encoding='utf-8').splitlines()
for i,l in enumerate(lines):
 if l.startswith('| D05 |'):
  lines[i]='| D05 | HDMI实屏时序不支持；原AXI/停止缺陷、ASCII时钟常量及物理集成风险 | r6/r7分组全阶段通过；4KiB/FIFO成果认可；隔离发送层两处改10\'b1111100000，Lite目标128周期20%→50%占空比通过 | 离线局部修正通过，原r5超时和UFAMILY附加边沿失败保留；PS/DDR/TMDS原生适配/CDC/时序/实屏未验，BOOT保持；[证据](tools/pose-v1/evidence/hdmi-split-20261015-r1/REPORT.md) |'
put(p,'\n'.join(lines)+'\n')
p=R/'Done.md'
replace_once(p,'### 工程内容总结\n\n','### 工程内容总结\n\n新授权批次完成：'+short+' Windows/XSim2019.1在D:/FPGACompetitionProject，r6/r7与TMDS各阶段90秒。分组保留完整帧/像素/停止门检，未改9份生产扫描RTL；TMDS目标r4仿真6.419秒、五阶段exit0，真实参考包装与UNISIM/secureip行为模型、VCD保留。两处分支仅修正常量和说明注释，原参考字节不改；100MHz模型验证数字图案，非实板频率测量。所有授权任务均由代理实际执行，进程盘点/完整日志/源码/38项基线与文档修订SHA见'+link+'。\n\n以下为此前恢复阶段及当时停止状态：\n\n')
replace_once(p,'### 对后续开发的参考\n\n','### 对后续开发的参考\n\n新批次参考：数据字符常量应显式指定10位二进制；80位ASCII到10位截断可产生20%占空比，即使语法合法。模块/PASS与外层预算分别记录，前端编译模式/secureip依赖明确分开。附加非目标UFAMILY精确边沿差不能套到Lite，保留原失败；Lite目标门检不放宽。已有通过后不重复无变更的扫描综合/负载，后续集中原生物理适配与系统集成门槛。\n\n')
p=R/'ARCHITECTURE-DISCUSSION-20261015.md';t=p.read_text(encoding='utf-8')
t+='\n\n## 十二、分组新批次授权与TMDS时钟常量修正\n\n用户明确认可r5内核全部像素PASS以及4KiB/FIFO成果，将该轮超时归为外层监控限制；明确批准r6 core/r7 pixel新目录、90秒安全预算，并要求修正字符串时钟输入。\n\n'+short+' '+link+'。常量修正在隔离候选，原参考/BOOT保持，旧DATA仍暂停。未安装/迁移IP或更换工具；Lite分支数字波形通过不等于物理层整体风险清零。\n'
put(p,t)
p=C/'README.md';t=p.read_text(encoding='utf-8')
t=t.replace('**用户已明确唤醒，当前恢复离线候选工作。** 原暂停记录和恢复边界见 [RESUME.md](RESUME.md)。','**本批离线验证与TMDS常量修正已完成。** 当前结果、历史失败与物理集成边界见 [RESUME.md](RESUME.md)。')
a=t.index('三种基址完整帧背压r4通过；')
t=t[:a]+'''三种基址完整帧r6 core、完整2073600像素r7 pixel均全阶段exit0，未超90秒；scanout原生综合结果保持。`rtl/display/uihdmitx.v`为保留原厂商头的隔离发送层修正版，两个时钟输入改为10'b1111100000。Lite目标参考序列器模型新/旧各128周期严格检查通过，占空比20%→50%；附加UFAMILY精确边沿诊断仍未通过。该发送层尚未接入原生Procise物理顶层。

原r5外层超时exit1保留，用户已认可其内核像素结果；本批新目录正常通过。尚无布局布线、完整CDC/时序签核、PLL实测或实屏验收。[实际结果](RESUME.md)、[集成契约](INTEGRATION.md)、[本批报告](../../tools/pose-v1/evidence/hdmi-split-20261015-r1/REPORT.md)。
'''
put(p,t)
p=C/'INTEGRATION.md';t=p.read_text(encoding='utf-8')
t=t.replace('候选物理适配应显式二进制常量并用规范复位，随后验证位序/占空比/引脚/电气。','本批隔离`rtl/display/uihdmitx.v`两处均已改为显式10\'b1111100000，Lite目标参考序列器模型连续128周期恢复50%占空比；规范复位、原生PHY、引脚/电气仍待适配。')
a=t.index('4KiB边界红/绿验证r3/r4已完成，')
t=t[:a]+'''4KiB红/绿r3/r4保留历史，用户已认可4KiB/FIFO成果和r5内核像素结果，原r5外层超时exit1不回写。新增r6 core/r7 pixel全阶段exit0，分别11.540/30.102秒，完整帧/像素门检保持。原scanout综合结果1个RAMH36E1保持，9份生产逻辑未改，本批没有无理由重复综合。

发送层修正了UFAMILY/7FAMILY两个时钟txdata常量；本工程实际选择7FAMILY，独立Lite回归用真实参考包装和Xilinx UNISIM/secureip模型检查旧/新各128周期、20%→50%占空比通过。使用100MHz理想模型时钟，不是板端148.5MHz测量；当前Procise综合顶层仍是并行scanout，未集成该参考物理层。

附加UFAMILY联合探索的精确等宽断言因99ps级边沿差而失败，原r3门检/完整VCD保留，原因未闭合；只读VCD复核两分支实际常量和每字符位图正确，不将其当作双分支严格波形或本板电气通过。[本批完整结果](../../tools/pose-v1/evidence/hdmi-split-20261015-r1/REPORT.md)。
'''
put(p,t)
p=C/'RESUME.md'
put(p,'''# HDMI候选当前状态

2026-10-15本批授权的离线分组验证与TMDS常量修正已完成。无后台续跑，暂不上板、不替换BOOT；旧DATA调查继续独立暂停。

## 最新授权与实际结果

用户明确认可r5内核全部像素比对、4KiB修复与FIFO综合成果，并将该轮超时归为外层监控门限；原进程exit1和失败日志不回写。用户批准新r6 core/r7 pixel独立目录、每阶段90秒，要求修正uihdmitx.v时钟ASCII常量。

- r6 core全阶段exit0，外层仿真11.540083秒，无超时。AXI10类、控制7类、CSR及偏移0/64/4032完整帧均通过，各4147200字节；不越4KiB。
- r7 pixel全阶段exit0，外层仿真30.102087秒，无超时。完整2073600像素/2200×1125扫描、异步FIFO复用/部分字flush、欠载排空和像素停钟STOP通过。
- 隔离`rtl/display/uihdmitx.v`的UFAMILY/7FAMILY两处均改10'b1111100000，原参考保留。实际选择的Lite 7FAMILY模型新/旧各128周期严格波形通过：旧高2ns/低8ns，新高低各5ns，周期10ns，P/N互补。
- TMDS r1/r2前端配置失败、r3非目标UFAMILY精确边沿失败保留；r4独立Lite目标全阶段exit0，外层仿真6.418892秒。UFAMILY附加99ps级边沿差原因未闭合，不能写作双分支严格波形或实板验收通过。只读原VCD复核两分支常量/位图通过，不重跑r3联合负载。
- 9份生产扫描RTL与前轮r5和Procise scanout综合逐位一致；原生1个RAMH36E1结果保持。本次为100MHz参考序列器模型验证，不是148.5MHz实板测量或Procise物理时序签核。

## 已执行入口与证据

Windows，工作目录D:/FPGACompetitionProject。实际执行`python FPGA/hdmi_candidate/scripts/simulate.py r6 core`，通过后`... r7 pixel`，以及独立TMDS目标验证。均各阶段90秒、安全监控，不延长或复用失败目录。[本批报告](../../tools/pose-v1/evidence/hdmi-split-20261015-r1/REPORT.md)包含源/原值/VCD/前后文档SHA/退出码和停止条件；[前轮报告](../../tools/pose-v1/evidence/hdmi-resume-20261015-r1/REPORT.md)与[原暂停检查点](../../tools/pose-v1/evidence/hdmi-candidate-pause-20261015-r1/CHECKPOINT.md)保留历史。

## 下一步的技术门槛

PS/DDR/GP/HP2所有权和地址映射、厂商IP配套/JFM引用、原生TMDS/规范复位、实际PLL/像素/串行时钟观测、Gray/邮箱CDC约束、封装/BANK/电平与1485Mb/s能力，以及布局布线、setup/hold/未约束路径和实屏。详见[集成契约](INTEGRATION.md)。不能将并行scanout综合或参考序列器行为仿真扩展为完整系统构建成功；工具/IP迁移等重大影响需按已有范围讨论。

本批无板端SSH/Docker/新Procise构建，无位流生成/下载/BOOT替换。原始参考源码、当前BOOT/SDK/模型/RAW/CPU注册/NPU分配保持。显示器最近实际用户现场仍为已接但时序不支持，未以本机仿真改写现场结果。
''')
checks=[]
for f in json.loads((R/'tools/pose-v1/evidence/hdmi-resource-audit-20261015-r1/sources.json').read_text(encoding='utf-8')):
 p=Path(f['path']);checks.append({'path':str(p),'original_sha':f['sha256'],'current_sha':sha(p),'equal':f['sha256']==sha(p)})
assert all(v['equal'] for v in checks)
save(E/'protected-reference-identities.json',checks)
consistency=[]
native=json.loads((R/'tools/pose-v1/evidence/hdmi-candidate-procise-scanout-20261015-r1/execution.json').read_text())
for n,h in native['sources'].items():
 val={'source':n,'native_sha':h,'current_sha':sha(C/'rtl'/n)}
 for rev in ('r6','r7'):
  manifest=json.loads((R/('tools/pose-v1/evidence/hdmi-candidate-sim-20261015-'+rev)/'source-manifest.json').read_text())
  val[rev+'_sha']=manifest[n]
 assert len({val[k] for k in ('native_sha','current_sha','r6_sha','r7_sha')})==1
 consistency.append(val)
save(E/'scanout-RTL-identity-consistency.json',consistency)
candidate=(C/'rtl/display/uihdmitx.v').read_bytes()
assert candidate.count(b".txdata(10'b1111100000)")==2 and b'.txdata("1111100000")' not in candidate
for p in (C/'scripts').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
save(E/'completed.json',{'authorized_work_package_complete':True,'r6_core_passed':True,'r7_pixel_passed':True,
 'constant_replacements':2,'Lite_7FAMILY_exact_waveform_128_periods_passed':True,
 'UFAMILY_exact_waveform_passed':False,'UFAMILY_extra_diagnostic_preserved':True,
 'reference_and_BOOT_unchanged':True,'protected_files':len(checks),'scanout_RTL_unchanged':len(consistency),
 'silicon_display_validated':False,'native_physical_TMDS_integrated':False,'download':False,'old_DATA_paused':True})
print('Docs updated; 38 reference identities unchanged; 9 scanout RTL match native/r6/r7; both candidate constants fixed')

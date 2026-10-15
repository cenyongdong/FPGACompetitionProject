from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[2]
E=R/'tools/pose-v1/evidence/hdmi-contract-validation-20261015-r1'
assert not (E/'documentation-revision.json').exists()
names=('ARCHITECTURE-DISCUSSION-20261015.md','Done.md','DIFFICULTIES.md','PROJECT-PROGRESS.md','REFERENCES.md')
(E/'before').mkdir()
for n in names:shutil.copyfile(R/n,E/'before'/n)
report='tools/pose-v1/evidence/hdmi-contract-validation-20261015-r1/REPORT.md'
summary='HDMI新核验：本地Lite BOOT/bit与选用版相同；实板显示控制0x20230218及12寄存器读取过，BOOT/六份SDK库/内核前后一致。参考RTL行为仿真确认200MHz扫描80.81Hz、停消费可卡读帧及AXI在RREADY=0时提前完成缺陷；后者不代表当前BOOT故障已证。显示器已接仍报时序不支持，误点稳定画面作废。用户已批准隔离候选修正独立时钟/AXI/停止换帧，先仿真和Procise构建，暂不上板。'
p=R/'Done.md';s=p.read_text(encoding='utf-8');title='# 已完成工作记录\n\n';assert s.startswith(title)
entry='## 2026-10-15：HDMI寄存器实板核验与读握手／停止行为验证\n\n### 工程内容总结\n\n'+summary+' [完整阶段证据]('+report+')。Windows本机XSim2019.1行为验证r6通过，参考AXI仅仿真副本去10项重复端口声明，逻辑不改；原RTL/BOOT不写。FPAI/ARM探针新r3实际SDK生命周期+12读取exit0、0.083909秒；十秒预算，原值/前后日志完整，未启动DMA/推理/编码。所有进程连接结束，FPAI恢复停止。主机权限失败、链接剔除、仿真语法/timescale/watchdog失败分别保留；不把缺陷复现当DUT正确或实屏通过。\n\n### 对后续开发的参考\n\n完成标志必须绑定真实RVALID&&RREADY、在途读和请求停止；不能先关DE再固定延时释放。相同BOOT和寄存器特征提升对应证据，不能证明完整源码构建或现场像素频率。无设备FD不证明PL停止；板端时钟日期不作为主机执行日期。候选另目录实施，保持1080p60和模型/SDK/协议，下载与BOOT变更仍须另议；旧DATA暂停。文档修订另存SHA，不覆盖失败或旧完成清单。\n\n'
p.write_text(title+entry+s[len(title):],encoding='utf-8',newline='\n')
p=R/'PROJECT-PROGRESS.md';s=p.read_text(encoding='utf-8');start=s.index('更新日期：');end=s.index('共享模型最近实际验证：',start)
s=s[:start]+'更新日期：2026-10-15。'+summary+' [本轮证据]('+report+')。'+s[end:]
lines=s.splitlines();i=next(i for i,x in enumerate(lines) if x.startswith('| HDMI |'))
lines[i]='| HDMI | 12项实板读取与原RTL行为验证完成，实屏仍报时序；参考AXI背压提前完成已复现，现场时钟仍待测 | 已批准隔离候选修正独立时钟/AXI/停止换帧，保持1080p60，先仿真及Procise构建，暂不上板；[证据]('+report+') |'
s='\n'.join(lines)+'\n';s=s.replace('HDMI按已同意顺序推进，第一阶段只读身份/接口盘点完成，时钟与安全停止资料待补；','HDMI进入用户新批准的隔离候选修正阶段，寄存器与参考行为证据已完成；',1)
p.write_text(s,encoding='utf-8',newline='\n')
p=R/'DIFFICULTIES.md';lines=p.read_text(encoding='utf-8').splitlines();i=next(i for i,x in enumerate(lines) if x.startswith('| D05 |'))
lines[i]='| D05 | HDMI实屏时序不支持，参考扫描/AXI完成与停止缺陷 | 实板0x20230218/12读取与Lite BOOT配套身份过；参考行为确认200MHz为80.81Hz，FIFO背压和VS门控问题，AXI未接受末拍即RD_DONE；[新证据]('+report+') | 现场频率/当前BOOT完整构建对应未证，未做色条或释放扫描帧。用户已批准隔离候选修正独立时钟/AXI/停止换帧，1080p60，先RTL/Procise，暂不上板；旧DATA暂停 |'
p.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
p=R/'REFERENCES.md';s=p.read_text(encoding='utf-8');n=s.index('\n\n')+2;p.write_text(s[:n]+'2026-10-15 '+summary+' [执行、原值和限制]('+report+')。\n\n'+s[n:],encoding='utf-8',newline='\n')
p=R/'ARCHITECTURE-DISCUSSION-20261015.md';s=p.read_text(encoding='utf-8');s+='\n## 九、实板寄存器、行为验证与新候选授权\n\n'+summary+' 不将现场80.81Hz或当前BOOT内部缺陷写成已证明，参考RTL缺陷与当前实板区分。新候选只在独立副本进行，当前BOOT/SDK/模型保持，不含新重启许可。\n\n[实际原值、失败与新授权范围]('+report+')。\n';p.write_text(s,encoding='utf-8',newline='\n')
# Preserve each actual simulation copy, including pre-repair testbench versions.
for tag in ('r1','r2','r3','r4','r5','r6'):
    w=R/('.local/hdmi-contract-sim-20261015-'+tag);d=R/('tools/pose-v1/evidence/hdmi-contract-sim-20261015-'+tag)
    if not w.is_dir():continue
    out=d/'source-snapshots';out.mkdir(exist_ok=True)
    for p in w.iterdir():
        if p.is_file() and p.suffix in ('.v','.sv','.tcl'):shutil.copyfile(p,out/p.name)
for tag in ('r1','r2','r3'):
    w=R/('.local/hdmi-register-probe-20261015-'+tag);d=R/('tools/pose-v1/evidence/hdmi-register-probe-20261015-'+tag)
    if not w.is_dir():continue
    out=d/'source-snapshots';out.mkdir(exist_ok=True)
    for n in ('CMakeLists.txt','readonly_probe.cpp'):
        if (w/n).is_file():shutil.copyfile(w/n,out/n)
shutil.copytree(R/'FPGA/hdmi_validation',E/'validation-tools')
revision=[{'path':n,'before_sha256':hashlib.sha256((E/'before'/n).read_bytes()).hexdigest(),'after_sha256':hashlib.sha256((R/n).read_bytes()).hexdigest(),'before_snapshot':'before/'+n} for n in names]
(E/'documentation-revision.json').write_text(json.dumps(revision,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for d in [*sorted((R/'tools/pose-v1/evidence').glob('hdmi-contract-sim-20261015-r*')),*sorted((R/'tools/pose-v1/evidence').glob('hdmi-register-probe-20261015-r*')),E]:
    manifest={str(p.relative_to(d)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.rglob('*')) if p.is_file() and p.name!='files.sha256.json'}
    (d/'files.sha256.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('HDMI phase evidence and explicit candidate authorization recorded.')

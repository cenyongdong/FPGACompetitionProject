"""Bind read-only evidence, source identities and narrowly scoped documentation updates."""
from pathlib import Path
import hashlib
import json
import shutil

R = Path(__file__).resolve().parents[2]
E = R/'tools/pose-v1/evidence/hdmi-stage1-20261015-r2'
assert not (E/'documentation-revision.json').exists()
r=json.loads((E/'review.json').read_text(encoding='utf-8'))
assert r['boot_identity_matches'] and r['SDK_libraries_match']
sources=[
 'rtl/ai7030_edif_top.v','rtl/ps_ai_peripheral.sv','rtl/utils/demo_clkrst_wrapper.v',
 'rtl/sdi/rx_sdi.v','rtl/display/frame_to_ps_largebuf.v','rtl/display/video_rect_read_data.v',
 'rtl/display/frame_fifo_read.v','rtl/display/frame_ctrl.v','rtl/display/video_define.v',
 'rtl/ip/cmos_clkgen_742_5/cmos_clkgen_742_5.xci','constrs_1/impl_constraints.xdc']
source_root=R/'Docs/26嵌赛开发/fpai_demo_fpga'
identities=[]
for rel in sources:
    p=source_root/rel
    b=p.read_bytes()
    dest=E/'source-snapshots'/rel
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(b)
    identities.append({'source':str(p),'snapshot':str(dest.relative_to(E)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
for name in ('hdmi_stage1_prepare.py','hdmi_stage1_run.py','hdmi_stage1_finish.py'):
    shutil.copyfile(R/'tools/pose-v1'/name,E/name)
(E/'sources.json').write_text(json.dumps(identities,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

report='tools/pose-v1/evidence/hdmi-stage1-20261015-r2/REPORT.md'
discussion='ARCHITECTURE-DISCUSSION-20261015.md'
done='''## 2026-10-15：架构讨论归档与 HDMI 板端只读核验

### 工程内容总结

按用户要求先创建根目录 [架构讨论记录](ARCHITECTURE-DISCUSSION-20261015.md)，汇总共享模型、模块所有权、PS/NPU/PL候选、CSI心率及HDMI讨论，区分决策、建议、验证与范围。随后在Windows工作目录D:/FPGACompetitionProject，以既有Python/OpenSSH和固定主机密钥执行一次Lite只读盘点，r2退出0、3.124318秒：BOOT与原记录相同、三份SDK核心库相同、icraft/customop3.39.0、FPGA operating。未见DRM/fb/I²C适配器，Linux时钟树不提供已识别HDMI像素/PLL节点。[完整返回、边界与报告](REPORT_LINK)。r1本机signal pipe权限失败尚未连接板端，完整保留；限制外ssh -V通过后才以新r2执行，无硬件负载失败重试。

### 对后续开发的参考

参考RTL关闭display_en会停止DE/FIFO消费，读帧可能停留等FIFO空间，且关闭VS可能形成读请求，故不能凭“等待一帧”证明扫描结束。read_finish未接出，当前位流时钟/PLL及安全停止契约仍缺；本轮未读写MMIO、初始化SDK、分配DMA或运行显示/推理/编码，未改BOOT、SDK、模型或重启。色条、翻帧、安全停止和骨架均待验，先补当前25122301发布版本配套。全部连接结束，无本批后台；旧DATA继续暂停。文档前后快照/身份和11份源码快照保存在本批，不改历史完成清单。

'''.replace('REPORT_LINK',report)
p=R/'Done.md';s=p.read_text(encoding='utf-8');title='# 已完成工作记录\n\n';assert s.startswith(title);p.write_text(title+done+s[len(title):],encoding='utf-8',newline='\n')

p=R/'PROJECT-PROGRESS.md';s=p.read_text(encoding='utf-8')
prefix='更新日期：2026-10-15。最近实际验证：'
assert prefix in s
s=s.replace(prefix,'更新日期：2026-10-15。最近实际验证另包括HDMI只读盘点：当前BOOT/三份SDK核心库身份相同、FPGA operating；未发现Linux显示或HDMI时钟观测接口，像素时钟/PLL与安全停止尚缺依据，色条未启动。用户已批准先核配套再静态图、翻帧/停止、骨架的有条件顺序；[讨论记录]('+discussion+')、[本次证据]('+report+')。共享模型最近实际验证：',1)
old='| HDMI | 目标1920×1080/60Hz，已有资料/授权历史，当前demo未接入 | 配套、scanout、换帧及实屏独立门检，不以720p编码替代显示时序；[ADR_00](ADR/ADR_00.md) |'
new='| HDMI | 目标1080p60；15日只读盘点BOOT/SDK同、FPGA operating，未找到Linux显示/HDMI时钟节点；当前demo未接入 | 保持BOOT，先补当前版本无SDI时钟/PLL及安全停止契约，再色条/换帧/骨架；[本轮报告]('+report+') |'
assert old in s;s=s.replace(old,new)
old='| 当前恢复点 | [重构完成检查点](tools/pose-v1/evidence/core-refactor-20261013-r1/next-checkpoint.json)；CPU107/三窗口完成无后台项目工作，等待用户后续任务 |'
new='| 当前恢复点 | HDMI按已同意顺序推进，第一阶段只读身份/接口盘点完成，时钟与安全停止资料待补；[门槛与证据]('+report+')。共享图稳定性及正式旧图重构分别保持原范围，无本批后台 |'
assert old in s;s=s.replace(old,new)
p.write_text(s,encoding='utf-8',newline='\n')

p=R/'DIFFICULTIES.md';s=p.read_text(encoding='utf-8');lines=s.splitlines()
idx=next(i for i,line in enumerate(lines) if line.startswith('| D05 |'))
lines[idx]='| D05 | HDMI输入时序不支持，scanout/安全停止映射未闭合 | 指定BOOT/配对bit本机身份已核；15日新板端只读盘点BOOT/SDK同、FPGA operating，无DRM/fb/I²C适配器或已识别HDMI时钟节点；参考门控可能令FIFO读帧停滞；[静态资源](tools/pose-v1/evidence/hdmi-resource-audit-20261015-r1/REPORT.md)、[实板只读结果]('+report+') | **待验**：未证当前BOOT无SDI像素/PLL或RTL对应关系，无安全停止完成契约；色条未执行、demo排除HDMI。先补当前25122301配套，再按用户已同意顺序继续；不以关闭显示或固定延时释放DMA |'
p.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')

p=R/'REFERENCES.md';s=p.read_text(encoding='utf-8');title=s.splitlines()[0]+'\n\n';assert s.startswith(title)
entry='2026-10-15 HDMI已按用户要求先归档[完整讨论]('+discussion+')，再一次板端只读核验：BOOT/三份SDK核心库同、FPGA operating；无DRM/fb/I²C适配器，clk_summary不能观测HDMI像素/PLL。参考RTL显示门控可能令读FIFO不再消费，不能等一帧即释放；当前发布位流时钟与停止契约待补，色条未启动。[执行/原值/停止门槛]('+report+')。未改BOOT/SDK/模型，无MMIO、设备初始化或后台，旧DATA暂停。\n\n'
p.write_text(title+entry+s[len(title):],encoding='utf-8',newline='\n')

p=R/discussion;s=p.read_text(encoding='utf-8')
s+='''
## 七、记录创建后的第一阶段实际结果

本文件创建后，已执行一次新的板端只读核验（r2 exit0，3.124318秒）：BOOT及三份SDK核心库与原身份相同，FPGA operating；无DRM、framebuffer和I²C适配器，Linux时钟树未提供已识别的HDMI像素时钟／PLL锁定节点。此前r1因本机Git SSH信号管道权限失败，尚未连接板端，原失败保留。

补充参考源码分析：display_en关闭后DE消费停止，FIFO可能填满并令读状态机停留，故“关显示并等一帧”不能证明读完；read_finish未接出。当前发布位流的独立时钟、PLL观测与安全停止契约仍待补齐，因此未进入静态色条。BOOT／SDK／模型保持，无MMIO、设备初始化、重启或后台任务；旧DATA调查继续暂停。

实际返回、源码快照、身份与后续门槛见 [HDMI第一阶段报告](REPORT_LINK)。这次完成的是只读盘点，不是HDMI显示验收。
'''.replace('REPORT_LINK',report)
p.write_text(s,encoding='utf-8',newline='\n')

revision=[]
for name in ('Done.md','DIFFICULTIES.md','PROJECT-PROGRESS.md','REFERENCES.md',discussion):
    before=E/'before'/name;after=R/name
    revision.append({'path':name,'before_snapshot':str(before.relative_to(E)),'before_sha256':hashlib.sha256(before.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(after.read_bytes()).hexdigest(),'historical_manifests_rewritten':False})
(E/'documentation-revision.json').write_text(json.dumps(revision,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for directory in (R/'tools/pose-v1/evidence/hdmi-stage1-20261015-r1',E):
    files={str(p.relative_to(directory)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.rglob('*')) if p.is_file() and p.name!='files.sha256.json'}
    (directory/'files.sha256.json').write_text(json.dumps(files,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Source snapshots, discussion, current-state docs and evidence manifests recorded.')

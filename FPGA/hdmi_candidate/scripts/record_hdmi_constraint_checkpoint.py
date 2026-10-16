"""Record actual constraint recovery and the start of route, preserving revisions."""
from pathlib import Path
import json, hashlib

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
assert json.loads((E / 'constraint-binding-r4/review.json').read_text())['route_prerequisite_pass']
assert (E / 'system-route-r2/owned-process.json').exists()
revision = E / 'documentation-constraint-r4-revision.json'
assert not revision.exists()
docs = ['PROJECT-PROGRESS.md', 'REFERENCES.md', 'DIFFICULTIES.md', 'Done.md',
        'FPGA/hdmi_candidate/INTEGRATION.md', 'FPGA/hdmi_candidate/RESUME.md',
        'FPGA/hdmi_candidate/BOARD-PLAN.md', 'FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md']
before = {}
for rel in docs:
    p = R / rel
    before[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    snap = E / 'before-constraint-r4-doc-edit' / rel
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_bytes(p.read_bytes())

summary = ('2026-10-16：HDMI整机任务已按用户指令恢复。第二版综合检查点的报告恢复完成，'
           '266.248秒exit0，未重跑综合；MMCM已由6降至5，旧PHY移除，148.5MHz像素时钟识别正确。'
           'r2约束绑定133.068秒exit0，已消除Q起点截断、资源超额及快慢时钟相位警告，'
           '但原工程整域false-path覆盖新邮箱上限，故未放行实现。r3因2018.3不支持独立reset_path命令停止，原日志保留；'
           'r4按本机手册用同对象set_max_delay -reset_path替换，再恢复所有旧逻辑起点的原cut，'
           '157.126秒exit0，真实邮箱路径5ns/10ns和Gray三组约束已核验。'
           '整机布局布线impl_hdmi_r2现已启动，原策略/JFM hook保持，尚无新候选位流或实板验收。'
           '板端只读复核BOOT/六份SDK保持、FPGA operating、无设备FD owner；仍无公开排空/隔离证明。'
           '本轮未下载、修改BOOT、重启或推理，旧DATA继续暂停。')
for rel in ['PROJECT-PROGRESS.md', 'REFERENCES.md', 'FPGA/hdmi_candidate/INTEGRATION.md',
            'FPGA/hdmi_candidate/RESUME.md', 'FPGA/hdmi_candidate/BOARD-PLAN.md']:
    p = R / rel
    parts = p.read_text(encoding='utf-8-sig').split('\n\n', 2)
    link = (' [本轮实施与恢复](FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md)。' if '/' not in rel
            else ' [本轮实施与恢复](SYSTEM-INTEGRATION-PLAN.md)。以下保留此前阶段依据。')
    p.write_text(parts[0] + '\n\n' + summary + link + '\n\n' + parts[2], encoding='utf-8')
for rel in ['PROJECT-PROGRESS.md', 'DIFFICULTIES.md']:
    p = R / rel
    lines = p.read_text(encoding='utf-8-sig').splitlines()
    for i, line in enumerate(lines):
        if line.startswith('| HDMI |'):
            lines[i] = '| HDMI | 整机接线、路由/真实时钟色条仿真、第二版综合和r4有效约束门检完成 | impl_hdmi_r2布局布线进行中；新反馈缓冲提示/物理时序/CDC与位流、实屏待验；[当前入口](FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md) |'
        if line.startswith('| 当前恢复点 |'):
            lines[i] = '| 当前恢复点 | **HDMI整机impl_hdmi_r2布局布线中**；监控原进程，不重复启动；完成后审查新时序/DRC/CDC，保留原AI两个定点例外。旧DATA暂停；[执行契约](FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md) |'
        if line.startswith('| D05 |'):
            lines[i] = '| D05 | HDMI有效约束已绑定，整机实现与实屏待验 | r2 MMCM5/5及相位/截断修正可见；原clock false-path覆盖新邮箱，经r4限定旧起点后5ns/10ns路径有效，157.126秒exit0 | 新MMCM反馈缓冲REQP-1577仍需实际物理时序核验；impl_hdmi_r2进行中，未出新位流/上板；[本轮证据](tools/pose-v1/evidence/hdmi-integration-20261016-r1/REPORT.md) |'
    p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
p = R / 'Done.md'
t = p.read_text(encoding='utf-8-sig')
t = t.replace('### 工程内容总结\n\n', '### 工程内容总结\n\n' + summary +
    ' [实际报告](tools/pose-v1/evidence/hdmi-integration-20261016-r1/REPORT.md)。\n\n', 1)
t = t.replace('### 对后续开发的参考\n\n', '### 对后续开发的参考\n\n'
    '时序约束需验证实际路径而非只看命令成功：整域false-path优先于pin级max-delay。'
    '本轮按原对象使用受支持的-reset_path选项，再从全部原逻辑时钟引脚恢复旧cut，仅新HDMI起点受有限上限；'
    'all_registers包括DSP/BRAM，真实邮箱路径REQUIREMENT已逐条检查。原r2/r3结果不回写。'
    '反馈缓冲提示、CDC条目和实际布线签核仍须分别审查。\n\n', 1)
p.write_text(t, encoding='utf-8')
p = R / 'FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md'
t = p.read_text(encoding='utf-8-sig').replace('MMCME2_BASE/BUFG/BUFIO，目标', 'MMCME2_BASE（BUFG反馈）/BUFIO及BUFR除5，目标')
t += ('\n\n## 有效约束门检与实现启动\n\n' + summary + '\n\n'
      'r4仅替换clk_out1_clk_wiz_0与clk_pll_i两向的原整域cut：新时钟对max-delay先用完全相同对象及-reset_path替换；'
      '随后全部旧起始时钟引脚（5879/53610）恢复对原目标时钟的false-path，新HDMI起点627/490排除。'
      '三组Gray仍是10/10/32位max-delay与skew约束，邮箱真实路径可计时且REQUIREMENT为5/10ns。'
      '预优化两个原NDRV不被豁免，需原厂opt后复核。新MMCM剩余REQP-1577指向BUFG反馈与区域输出的差异，'
      '两只SERDES时钟已同源并无REQP-1580；必须继续检查实际布线/保持与脉宽，不改严重级别放行。\n')
p.write_text(t, encoding='utf-8')
p = E / 'REPORT.md'
t = p.read_text(encoding='utf-8')
t += ('\n\n## 恢复后实际进展（有效约束r4）\n\n' + summary + '\n\n'
      'recover-synthesis-r2报告完整，原system-synthesis-r2外层结果仍未知。'
      'constraint-binding-r2的exit0不是签核；r3的API错误68.118秒exit1原样保留；'
      'r4实际157.126秒/180秒预算完成，review.json仅允许开始route，不是实板或完整CDC通过。'
      'system-route-r2只执行到route_design，未授权自动跳过报告审查写位流。'
      'board-resume-readonly实际4.73秒完成，只读后连接关闭，六库/BOOT身份保持；无FD不替代AXI排空。\n')
p.write_text(t, encoding='utf-8')
result = {rel: {'before': before[rel], 'after': hashlib.sha256((R / rel).read_bytes()).hexdigest()} for rel in docs}
revision.write_text(json.dumps(result, indent=2) + '\n')
print('Recorded constraint-r4 checkpoint and document hashes; implementation not claimed complete')

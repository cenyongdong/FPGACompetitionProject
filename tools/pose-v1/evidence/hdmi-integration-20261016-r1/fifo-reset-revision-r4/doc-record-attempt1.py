"""Publish the diagnosed reset fault, actual pixel pass and current rebuild."""
from pathlib import Path
import json, hashlib

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
assert json.loads((R / 'tools/pose-v1/evidence/hdmi-candidate-sim-20261015-r8/result.json').read_text())['passed']
out = E / 'documentation-fifo-r4-revision.json'
assert not out.exists()
docs = ['PROJECT-PROGRESS.md', 'REFERENCES.md', 'DIFFICULTIES.md', 'Done.md',
        'FPGA/hdmi_candidate/INTEGRATION.md', 'FPGA/hdmi_candidate/RESUME.md',
        'FPGA/hdmi_candidate/BOARD-PLAN.md', 'FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md']
records = {}
summary = ('2026-10-16：HDMI整机接入已恢复。时钟/色条及router仿真、第二版综合、邮箱5ns/10ns有效约束及实际Tcl hook加载已核验。'
           'r3实现因布局后优化异常耗时主动停止，未完成布线；79.069秒的优化DCP诊断定位FIFO跨域复位恢复−6.337ns、移除−3.367ns。'
           '已修正为每域状态由本域三级同步链释放复位；只对9个真正异步复位链CLR输入约束，不切功能状态复位。'
           '新r8像素仿真42.244秒/90秒通过：2073600像素、部分字刷新、欠载排空及像素时钟停转STOP。'
           '九份核心功能模块中仅FIFO本次修改，另八份及PS/DDR/AI_Mate/时钟配置保持。第四版顶层综合进行中，后续新约束/物理时序/位流和实板仍待验证。'
           '板端只读BOOT/六SDK身份保持；本轮没有下载、BOOT写入、重启或推理，旧DATA继续暂停。')
for rel in docs:
    p = R / rel
    before = p.read_bytes()
    snap = E / 'before-fifo-r4-doc-edit' / rel
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_bytes(before)
    text = before.decode('utf-8-sig')
    if rel in ['PROJECT-PROGRESS.md', 'REFERENCES.md', 'FPGA/hdmi_candidate/INTEGRATION.md',
               'FPGA/hdmi_candidate/RESUME.md', 'FPGA/hdmi_candidate/BOARD-PLAN.md']:
        parts = text.split('\n\n', 2)
        link = ('FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md' if '/' not in rel else 'SYSTEM-INTEGRATION-PLAN.md')
        text = parts[0] + '\n\n' + summary + ' [实施、证据及恢复](' + link + ')。\n\n' + parts[2]
    if rel in ['PROJECT-PROGRESS.md', 'DIFFICULTIES.md']:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith('| HDMI |'):
                lines[i] = '| HDMI | 已集成；新FIFO本域同步复位及r8完整像素/STOP验证通过 | system-synthesis-r4进行中；后续约束r5、物理实现/位流与实屏待验；[证据](tools/pose-v1/evidence/hdmi-integration-20261016-r1/REPORT.md) |'
            if line.startswith('| 当前恢复点 |'):
                lines[i] = '| 当前恢复点 | **HDMI复位修正后的system-synthesis-r4**；r8完整像素42.244秒通过，原r3实现停止及−6.337/−3.367ns原报告保留。综合后绑定r5约束并证明FIFO状态复位来源与目标同域，再实施新run；旧DATA暂停 |'
            if line.startswith('| D05 |'):
                lines[i] = '| D05 | HDMI整机新跨域复位问题已定位/修正，物理结果待验 | 约束加载已修正；优化DCP恢复−6.337ns、移除−3.367ns定位到FIFO状态原异步复位。各域状态改用本域三级同步释放，r8完整2073600像素及故障/STOP排空通过 | 新综合进行中，随后实际复位来源/时序门检；不套用原AI例外，无新位流/板测；[证据](tools/pose-v1/evidence/hdmi-integration-20261016-r1/REPORT.md) |'
        text = '\n'.join(lines) + '\n'
    if rel == 'Done.md':
        marker = '### 工程内容总结\n\n'
        start = text.index(marker) + len(marker)
        stop = text.index('本阶段后续实际复核：', start)
        text = text[:start] + summary + '\n\n' + (
            '工程内容：Windows隔离整机、Vivado2018.3＋既有JFM，HP2读所有权/CSR0x400b0000/独立AC14时钟已接线；'
            '原router-r2、真实模型PHY-r3及首版/第二版综合结果保留。整域false-path覆盖邮箱与过程式XDC未加载的问题已分别修正，'
            '实际实现子进程5ns/10ns约束断言通过。r2/r3不完整实现和原外层失败均封存，不写成布局布线通过；'
            'r3优化DCP的CRC/SHA和原−6.337/−3.367ns报告完整保留。当前仅FIFO复位变动，新r8编译/展开/仿真各5.418/11.401/42.244秒exit0。'
            '八份其余功能RTL与原IP/模型/SDK保持。[本轮执行与证据](tools/pose-v1/evidence/hdmi-integration-20261016-r1/REPORT.md)。\n\n') + text[stop:]
        text = text.replace('### 对后续开发的参考\n\n', '### 对后续开发的参考\n\n'
            'FIFO出口等待三级释放不等于状态寄存器的复位已同步：本轮实际Recovery/Removal路径证实仍会跨域。'
            '修正应把异步释放链与功能状态always分开，状态复位由各域链末级驱动；仅对真正异步链的CLR输入明确约束，'
            '保持功能状态恢复/移除检查，并在真实综合网表核对复位唯一来源与同域时钟。'
            '本轮完整像素、随机回绕/刷新和停像素时钟排空可复用；通过这些逻辑测试仍需新的综合与物理门检。\n\n', 1)
    if rel.endswith('SYSTEM-INTEGRATION-PLAN.md'):
        text += '\n\n## FIFO复位物理诊断与修正r4\n\n' + summary + '\n\n'
        text += ('优化DCP最差Recovery来源waiting_reg/C、目的lane/rd_bin等CLR；Removal来源pixel_release_reg[2]/C、目的内存域Gray同步器CLR。'
                 '这是新HDMI结构问题，不属于原AI两个定点例外。三级wr/rd_release独立always仅接收原组合异步复位，'
                 '状态分别以wr_release[2]/rd_release[2]作为本域释放后的复位。后续约束只切三组真实异步复位链的CLR，'
                 '状态复位仍计时，并追溯综合后的唯一来源及源/目标时钟相同。原FIFO容量、AXI/帧协议与时钟目标不变。\n')
    p.write_text(text, encoding='utf-8')
    records[rel] = {'before': hashlib.sha256(before).hexdigest(), 'after': hashlib.sha256(p.read_bytes()).hexdigest()}
out.write_text(json.dumps(records, indent=2) + '\n')
p = E / 'REPORT.md'
t = p.read_text(encoding='utf-8')
parts = t.split('\n\n', 2)
t = parts[0] + '\n\n当前检查点：' + summary + '\n\n以下按实际发生顺序保留此前阶段记录。\n\n' + parts[1] + '\n\n' + parts[2]
t += ('\n\n## FIFO复位诊断、修正与r8实际验证\n\n' + summary + '\n\n'
      'r3实现759.734秒主动结束exit1，初始180秒、当时预算900秒、绝对上限1800秒；不是工具完成或超时逻辑通过。'
      '独立诊断79.069秒exit0，优化DCP完整保存CRC/SHA；最差新恢复/移除原值不抹除。'
      '修正前synth_1和impl_hdmi_r3共53份文件ZIP逐项SHA/CRC核验。'
      '综合前两次源清单预检因未使用独立物理适配器而失败，均未启动EDA；完整核对12份根候选和9份整机功能文件后修正，原SHA保护保持，FIFO单项新SHA明确列明。\n')
p.write_text(t, encoding='utf-8')
print('Recorded actual FIFO diagnosis/pixel pass and current synthesis; prior document revisions preserved')

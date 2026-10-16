"""Publish actual r5 products after offline BOOT verification; preserve revisions."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
boot = json.loads((E / 'boot-offline-r5/review.json').read_text())
bit = json.loads((E / 'candidate-bit-r5/review.json').read_text())
assert boot['all_bytes_outside_PL_identical'] and boot['PL_payload_matches_candidate_after_word_swap']
assert bit['payload_differs_from_original_BOOT']
assert json.loads((E / 'uart-marker-r2/review.json').read_text())['marker_received']
record = E / 'documentation-completed-r5-revision.json'
assert not record.exists()
summary = ('2026-10-16：HDMI整机r5实现和离线候选已完成，待受控启动与实屏验证。'
           'FIFO本域同步复位修正后，r8完整2073600像素/欠载/STOP仿真通过；综合259.732秒、约束167.171秒、整机实现1299.938秒均exit0。'
           '布线后WNS+0.030ns、WHS+0.029ns，TNS/THS均0；仅保留已批准的两处AI Min Period原失败，不新增豁免。'
           '三组Gray偏斜及邮箱5ns/10ns、96条CE路径均通过，完整CDC/剩余告警与实屏限制保留。'
           '新位流配置载荷已确认不同于现BOOT；离线BOOT仅PL分区改变，三份PS文件及全部非PL字节相同。'
           'COM7/115200 8N1已收到板端ttyPS0标记。没有可验证的在线全PL停止/隔离通道，临时启动切换方案待具体确认；'
           '本轮未下载、写板端BOOT、重启、DMA或推理，旧DATA继续暂停。')
docs = ['PROJECT-PROGRESS.md', 'REFERENCES.md', 'DIFFICULTIES.md', 'Done.md',
        'FPGA/hdmi_candidate/INTEGRATION.md', 'FPGA/hdmi_candidate/RESUME.md',
        'FPGA/hdmi_candidate/BOARD-PLAN.md', 'FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md']
revisions = {}
for rel in docs:
    p = R / rel
    before = p.read_bytes()
    snap = E / 'before-completed-r5-doc-edit' / rel
    snap.parent.mkdir(parents=True, exist_ok=True)
    assert not snap.exists()
    snap.write_bytes(before)
    text = before.decode('utf-8-sig').replace('\r\n', '\n')
    if rel in docs[:2] + docs[4:7]:
        parts = text.split('\n\n', 2)
        link = 'FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md' if '/' not in rel else 'SYSTEM-INTEGRATION-PLAN.md'
        text = parts[0] + '\n\n' + summary + ' [证据与恢复](' + link + ')。\n\n' + parts[2]
    if rel in ['PROJECT-PROGRESS.md', 'DIFFICULTIES.md']:
        rows = text.splitlines()
        for i, row in enumerate(rows):
            if row.startswith('| HDMI |'):
                rows[i] = '| HDMI | r5整机时序/Gray/邮箱数据与CE门检及新位流/离线BOOT通过 | 待受控启动范围确认与实屏，未下载/改启动区/重启；[恢复](FPGA/hdmi_candidate/CANDIDATE-BOARD-TEST-R5.md) |'
            if row.startswith('| 当前恢复点 |'):
                rows[i] = '| 当前恢复点 | **HDMI整机新候选已离线生成**；COM7接收确认，现BOOT/SDK保持，待具体临时启动切换范围确认；[执行包](FPGA/hdmi_candidate/CANDIDATE-BOARD-TEST-R5.md)。旧DATA暂停 |'
            if row.startswith('| D05 |'):
                rows[i] = '| D05 | HDMI整机复位及物理时序修正通过，实屏待验 | r5 WNS+0.030/WHS+0.029ns，Gray/邮箱D及96CE路径过；新位流载荷不同且离线BOOT仅PL改变 | 在线全PL隔离未取得证据，待受控启动范围确认；原两个AI脉宽例外/全部告警保留，未下载；[执行包](FPGA/hdmi_candidate/CANDIDATE-BOARD-TEST-R5.md) |'
        text = '\n'.join(rows) + '\n'
    if rel == 'Done.md':
        marker = '### 工程内容总结\n\n'
        start = text.index(marker) + len(marker)
        stop = text.index('\n\n', start)
        text = text[:start] + summary + text[stop:]
        ref = '### 对后续开发的参考\n\n'
        text = text.replace(ref, ref + '本轮将完整实现与报告收集拆分，分别1299.938/212.546秒完成，67.041秒补查96条跨域CE；布局后优化长时间无日志时，以所属进程CPU和资源判断进展，保留r4误中断及无检查点事实。原始全局时序仍因两个AI Min Period检查失败；只能按既有两点例外生成候选，不能称全部原始时序通过。新bit必须比较配置载荷，BOOT保持原bit映像名才能避免无关名称字节变化。UART可通过SSH写ttyPS0标记、主机只收不发来核验接收链路；不必重启。\n\n', 1)
    if rel.endswith('SYSTEM-INTEGRATION-PLAN.md'):
        text += '\n\n## r5布线及离线交付的实际结果\n\n' + summary + '\n\n'
        text += ('执行位置Windows，工作目录D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1，Vivado2018.3＋既有JFM、Procise2025.1.1temp/SVN32494。'
                 'r4布局已完成但在写检查点时被代理误中断，未留placed DCP；42文件另存，r5保持同源码/约束/策略完成。'
                 '原始脉宽WPWS−0.409ns/TPWS−0.479ns及两原厂端点保持，非独立安全验证。'
                 '新HDMI物理报告50条建立/保持最小+0.105/+0.079ns，Gray偏斜裕量3.820/5.731/5.580ns；'
                 '邮箱数据/响应裕量1.534/8.779ns、96CE最小0.856ns。REQP-1577及O5等告警未降级，默认重开DCP的GT52/56与实现原厂四项处理分开保留。'
                 '报告解析首试因默认摘要只列一个脉宽最差路径而失败，改为同时核验实际实现十路径报告，两处原值不改。'
                 '[原值及完整报告](../../tools/pose-v1/evidence/hdmi-integration-20261016-r1/REPORT.md)、[下一受控启动执行包](CANDIDATE-BOARD-TEST-R5.md)。\n')
    p.write_text(text, encoding='utf-8')
    revisions[rel] = {'before': hashlib.sha256(before).hexdigest(), 'after': hashlib.sha256(p.read_bytes()).hexdigest()}
record.write_text(json.dumps(revisions, indent=2) + '\n')
report = E / 'REPORT.md'
before = report.read_bytes()
(E / 'REPORT-before-completed-r5.md').write_bytes(before)
parts = before.decode('utf-8-sig').replace('\r\n', '\n').split('\n\n', 2)
report.write_text(parts[0] + '\n\n当前检查点：' + summary + '\n\n' + parts[2] +
                 '\n\n## r5整机时序、位流及离线BOOT\n\n' + summary + '\n\n' +
                 '实际产物：candidate-bit-r5/review.json、boot-offline-r5/review.json。仅本地文件；板端启动配置保持。'
                 '原r4误中断、报告解析失败及所有原时序告警保留。\n', encoding='utf-8')
state = json.loads((E / 'continuation-state.json').read_text(encoding='utf-8'))
state.update(updated_local=datetime.datetime.now().isoformat(), active_stage='offline candidate complete; awaiting specific controlled startup scope',
             execution_session=None, next='CANDIDATE-BOARD-TEST-R5.md; no background execution or board startup changes while awaiting specific scope',
             offline_BOOT=boot, new_bit_payload_SHA256=bit['new_payload_sha256'])
(E / 'continuation-state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
shutil.copyfile(Path(__file__), E / Path(__file__).name)
print('Updated actual r5 results and waiting boundary; historical document hashes preserved separately')

"""Documentation-only handoff and explicit user pause; no EDA or board calls."""
from pathlib import Path
import datetime
import hashlib
import json
import re

R = Path('D:/FPGACompetitionProject')
E = R / 'tools/pose-v1/evidence/hdmi-handoff-docs-20261016-r1'
assert not (E / 'document-revisions.json').exists()
SUMMARY = 'FPGA/FPGA-WORK-SUMMARY-20261016.md'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


sealed = [R / 'tools/pose-v1/evidence' / name for name in
          ['hdmi-integration-20261016-r1', 'hdmi-board-candidate-20261016-r1']]
seal_before = {p.name: sha((p / 'files.sha256.json').read_bytes()) for p in sealed}

pause = ('2026-10-16：**下一阶段实施按用户要求暂停，等待后续项目架构确定及明确恢复指令。** '
         '本轮仅完成FPGA工作总结和文档交接，未连接板卡或执行构建。最近实际验证为同日HDMI双ABI／PLL／约148.5MHz像素计数及稳定八色条实屏通过。'
         '原BOOT已恢复、运行中候选为上次封存确认状态，本轮没有重新核验实板。DDR读帧／翻帧／在途STOP和整机实时性尚未验收；'
         'FAT脏标志及未引用链来源未明、未修复，旧DATA继续暂停。')
paths = ['Agents.md', 'PROJECT-PROGRESS.md', 'REFERENCES.md', 'Done.md', 'DIFFICULTIES.md',
         'ARCHITECTURE-DISCUSSION-20261015.md', 'FPGA/hdmi_candidate/RESUME.md',
         'FPGA/hdmi_candidate/INTEGRATION.md', 'FPGA/hdmi_candidate/BOARD-PLAN.md',
         'FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md', 'FPGA/hdmi_candidate/CANDIDATE-BOARD-TEST-R5.md']
changes = {}
for rel in paths:
    p = R / rel
    before = p.read_bytes()
    text = before.decode('utf-8-sig').replace('\r\n', '\n')
    if rel == 'Agents.md':
        needle = '- 用户暂停的任务不得自主恢复或启动后台续跑；恢复须由用户明确唤醒。当前旧DATA首次坏读定位在用户明确恢复前保持暂停，文档整理不解除此约束。'
        assert text.count(needle) == 1
        text = text.replace(needle, needle + '\n- 用户最新明确要求：本轮仅整理FPGA模块负责范围、完成内容及原厂位流操作，并更新相关文档。文档完成后暂停下一阶段项目实施，包括FPGA/HDMI开发、仿真、综合实现、板测、部署、文件系统修复及后台续作；须待用户确定后续项目架构并明确要求执行后恢复。架构讨论可按用户要求进行，历史计划和既有执行授权不解除此暂停。')
        needle = '用户暂停后已明确恢复本任务；原旧DATA调查仍暂停。'
        assert text.count(needle) == 1
        text = text.replace(needle, '本项实施授权当前受最新架构讨论暂停约束，恢复须待用户明确指示；旧DATA调查仍暂停。')
    if rel in ['PROJECT-PROGRESS.md', 'REFERENCES.md', 'FPGA/hdmi_candidate/RESUME.md',
               'FPGA/hdmi_candidate/INTEGRATION.md', 'FPGA/hdmi_candidate/BOARD-PLAN.md']:
        parts = text.split('\n\n', 2)
        target = SUMMARY if '/' not in rel else '../FPGA-WORK-SUMMARY-20261016.md'
        text = parts[0] + '\n\n' + pause + ' [负责范围、原厂位流操作及交接](' + target + ')。\n\n' + parts[2]
    if rel == 'PROJECT-PROGRESS.md':
        rows = text.splitlines()
        for i, row in enumerate(rows):
            if row.startswith('| HDMI |'):
                rows[i] = '| HDMI | 整机候选构建与静态八色条实屏通过；原BOOT已恢复 | **下一阶段暂停待架构确定及明确恢复**；DDR读帧／翻帧／STOP和推理双路未验，FAT另列D43；[交接](FPGA/FPGA-WORK-SUMMARY-20261016.md) |'
            if row.startswith('| 当前恢复点 |'):
                rows[i] = '| 当前恢复点 | **文档交接完成，下一阶段暂停待用户确定架构**；上次实际状态为运行中候选色条、启动BOOT原版。无新板端核验，旧DATA暂停；[交接与边界](FPGA/FPGA-WORK-SUMMARY-20261016.md)、[最新暂停记录](tools/pose-v1/evidence/hdmi-handoff-docs-20261016-r1/continuation-state.json) |'
        text = '\n'.join(rows) + '\n'
    if rel == 'DIFFICULTIES.md':
        parts = text.split('\n\n', 2)
        text = parts[0] + '\n\n2026-10-16交接更新：D05静态色条已通过，D42暂存恢复路径已修正，D43文件系统来源问题未解。下一阶段实施按用户要求暂停，待架构确定及明确恢复；[FPGA工作总结](FPGA/FPGA-WORK-SUMMARY-20261016.md)。原D01–D43稳定编号和失败证据保留。\n\n' + parts[2]
        text = text.replace('- **D05 HDMI及D29严格性能/长期：待验。** 编码和主机GUI通过不等于HDMI、严格5Hz或30分钟通过。',
                            '- **D05 HDMI静态色条通过；动态帧及D29整机实时性／长期待验。** DDR读帧、翻帧和在途STOP尚未执行；下一阶段暂停待架构确定。共享图独立串行30分钟与整机并发长期验收分别报告。')
        rows = text.splitlines()
        for i, row in enumerate(rows):
            if row.startswith('| D05 |'):
                rows[i] = row.replace('DDR帧、换帧/STOP与整机实时仍待验；', 'DDR帧、换帧/STOP与整机实时仍待验；下一阶段暂停待架构确定及明确恢复；')
        text = '\n'.join(rows) + '\n'
    if rel == 'Done.md':
        parts = text.split('\n\n', 1)
        entry = '''## 2026-10-16：FPGA模块总结归档与架构讨论前暂停

### 工程内容总结

按用户要求新增[FPGA／HDMI工作总结](FPGA/FPGA-WORK-SUMMARY-20261016.md)及[FPGA索引](FPGA/README.md)，梳理代理负责范围、模块和资源所有权、已完成逻辑／物理／实屏验证、原厂工程复现与新bit重生成的区别、Procise后处理、仅换PL的BOOT封装、临时启动及原BOOT还原。明确JTAG只扫链、实际经FSBL加载候选，运行中配置与启动文件分别记录；DDR读帧、STOP和整机实时性仍未验，FAT问题来源未证。

执行位置Windows D:/FPGACompetitionProject，仅本地文件读取、SHA核验及Markdown／暂停记录维护。本轮未运行EDA、SSH／UART／JTAG、下载、重启、DMA、推理或文件系统修复。进度、资料索引、难点、现行恢复入口和Agents暂停约束同步更新；原封存证据与旧哈希清单不回写，文档前后SHA及历史快照另存[交接证据](tools/pose-v1/evidence/hdmi-handoff-docs-20261016-r1)。

### 对后续开发的参考

讨论新架构时先区分“候选代码已实现／仿真通过”“已构建和时序受限放行”“静态实屏通过”与“真实DDR帧／STOP／整机验收”，不从一层通过推导其它层通过。原厂bit文件头变化不等于载荷变化；BOOT还原不等于运行中PL回退。文档完成后按用户要求暂停下一阶段实施，等待架构确定及明确恢复指令；历史下一步、剩余回退许可和未验项目均不触发自动执行。

'''
        text = parts[0] + '\n\n' + entry + parts[1]
    if rel == 'ARCHITECTURE-DISCUSSION-20261015.md':
        assert '## 23. FPGA工作交接与架构确定前暂停' not in text
        text += '\n\n## 23. FPGA工作交接与架构确定前暂停（2026-10-16）\n\n用户要求先总结代理在FPGA模块的负责范围、完成内容及对原厂位流的操作，在FPGA子目录记录并同步文档，随后不启动下一阶段，待用户确定后续架构后再执行。现已形成[工作总结](FPGA/FPGA-WORK-SUMMARY-20261016.md)，区分原厂链路复现、新HDMI候选重生成、Procise后处理与临时BOOT启动／还原。\n\n最近实板结果为稳定八色条，DDR读帧／翻帧／在途STOP及整机并发尚未验收；当前板端描述沿用封存现场，本轮没有重新核验。PS／NPU／PL新分工未在本文档整理中决定；心率功能亦未实现。下一阶段项目实施与后台续作暂停，旧DATA独立暂停；后续先讨论架构，待用户明确恢复再执行。\n'
    if rel.endswith('SYSTEM-INTEGRATION-PLAN.md'):
        parts = text.split('\n\n', 1)
        text = parts[0] + '\n\n**当前执行状态：用户要求文档交接后暂停下一阶段，待架构确定及明确恢复指令。** [FPGA工作总结](../FPGA-WORK-SUMMARY-20261016.md)为交接入口；下文保留此前集成范围、计划及实际结果，不能作为自动继续构建或板测的授权。\n\n' + parts[1]
    if rel.endswith('CANDIDATE-BOARD-TEST-R5.md'):
        parts = text.split('\n\n', 2)
        text = parts[0] + '\n\n状态：上次实际完成一次候选启动、原BOOT文件还原和稳定八色条确认；本次仅文档交接。**下一阶段实施现按用户要求暂停，待架构确定及明确恢复，历史回退许可不自动触发重启。** [负责范围与位流操作总结](../FPGA-WORK-SUMMARY-20261016.md)。下文原计划与实际记录保留，FAT问题尚未修复。\n\n' + parts[2]
    if rel.endswith('RESUME.md'):
        text += '\n\n## 最新暂停与恢复门禁（2026-10-16）\n\n本轮只完成工作总结与文档同步，没有重新核验板端运行状态。后续先由用户确定项目架构，再明确指示恢复执行；恢复前先阅读[FPGA工作交接](../FPGA-WORK-SUMMARY-20261016.md)和[最新暂停记录](../../tools/pose-v1/evidence/hdmi-handoff-docs-20261016-r1/continuation-state.json)。旧封存continuation-state.json中的next及本文此前恢复步骤保留当时含义，均不能覆盖此次暂停。\n'
    assert text != before.decode('utf-8-sig').replace('\r\n', '\n'), rel
    changes[rel] = (before, text)

# Snapshot documents and original fragments before any mutation. Do not duplicate
# the credentials elsewhere in Agents.md into a new documentation archive.
records = {}
for rel, (before, after) in changes.items():
    if rel == 'Agents.md':
        fragments = [line for line in before.decode('utf-8-sig').splitlines()
                     if line.startswith('- 用户暂停的任务') or '用户暂停后已明确恢复本任务；' in line]
        dump(E / 'Agents-replaced-fragments.json', {'before_file_sha256': sha(before), 'replaced_fragments': fragments})
    else:
        p = E / 'before-document-edit' / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        assert not p.exists()
        p.write_bytes(before)
    records[rel] = {'before_sha256': sha(before)}
for rel, (_, after) in changes.items():
    p = R / rel
    p.write_text(after, encoding='utf-8')
    records[rel]['after_sha256'] = sha(p.read_bytes())
for rel in [SUMMARY, 'FPGA/README.md']:
    p = R / rel
    assert p.is_file()
    records[rel] = {'new_document': True, 'after_sha256': sha(p.read_bytes())}
dump(E / 'document-revisions.json', records)
for rel in [SUMMARY, 'FPGA/README.md']:
    p = E / 'new-documents' / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes((R / rel).read_bytes())

dump(E / 'continuation-state.json', {
    'date_Asia_Shanghai': '2026-10-16', 'status': 'paused_by_explicit_user_request',
    'reason': 'Complete FPGA responsibility/work/bitstream documentation, then wait for user architecture decision before further execution',
    'allowed_current_scope': 'requested local documentation handoff only; completed',
    'next_stage_execution_allowed': False, 'background_continuation_allowed': False,
    'resume_requires': 'user determines next project architecture and explicitly instructs execution',
    'last_actual_board_validation_date': '2026-10-16', 'board_rechecked_this_turn': False,
    'last_confirmed_snapshot': {'runtime': 'HDMI candidate static eight bars', 'startup_BOOT': 'original restored',
                                'display_DMA_or_inference': 'not performed', 'FAT': 'unresolved; no new startup-volume writes'},
    'last_board_evidence': '../hdmi-board-candidate-20261016-r1/REPORT.md',
    'old_DATA_investigation': 'remains paused', 'summary': '../../../../FPGA/FPGA-WORK-SUMMARY-20261016.md',
    'no_new_EDA_SSH_UART_JTAG_boot_DMA_or_filesystem_repair': True,
})

integrity = {}
for base in sealed:
    m = json.loads((base / 'files.sha256.json').read_text(encoding='utf-8'))['files']
    for rel, expected in m.items():
        p = base / rel
        assert p.is_file() and p.stat().st_size == expected['bytes'] and sha(p.read_bytes()) == expected['sha256'], str(p)
    assert sha((base / 'files.sha256.json').read_bytes()) == seal_before[base.name]
    integrity[base.name] = {'files_verified': len(m), 'all_pass': True, 'manifest_sha256': seal_before[base.name]}
dump(E / 'prior-sealed-evidence-integrity.json', integrity)

link_records = []
for rel in [SUMMARY, 'FPGA/README.md']:
    p = R / rel
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', p.read_text(encoding='utf-8')):
        if target.startswith(('https:', 'http:')):
            continue
        target = target.split('#', 1)[0]
        assert (p.parent / target).resolve().exists(), (rel, target)
        link_records.append({'document': rel, 'target': target, 'exists': True})
dump(E / 'new-document-link-check.json', link_records)
print('Updated', len(records), 'documents; sealed historical evidence checked:',
      sum(v['files_verified'] for v in integrity.values()), 'files PASS; new local links:', len(link_records))

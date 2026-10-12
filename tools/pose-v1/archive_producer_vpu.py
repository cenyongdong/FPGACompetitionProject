"""Archive exact finite results and preserve timing failure without rerunning hardware."""
from pathlib import Path
import ast, hashlib, json, shutil

R = Path(__file__).resolve().parents[2]
E = R / 'tools/pose-v1/evidence/producer-vpu-20261011-r2'
B = R / '.local/pose-v1-build/producer-vpu-20261011-r2'
assert not (E / 'completion-review.json').exists()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text())
build = load(B / 'build-result.json')
for name, h in build['sources'].items():
    assert sha(R / name) == h
assert sha(B / 'pose_producer_vpu_check') == build['program_sha256']
base = load(R / '.local/pose-v1-read-phase/package-20261011-r3/manifest.json')
frozen = {p: x['sha256'] for p, x in base['build_files'].items() if p.startswith('software/')}
assert len(frozen) == 152
for name, h in frozen.items():
    assert sha(R / name) == h
off, on, video = (load(E / name) for name in ('off.data-review.json', 'on.failure-review.json', 'on.video-review.json'))
final = load(E / 'final-r2-return/final-r2/review.json')
assert off['calls'] == 100 and off['FP32_values'] == 1176000
assert on['completed'] == 82 and on['FP32_values_verified'] == 964320 and on['stage_exit'] == 1
assert video['decoded_images'] == 270 and video['copy_spans_with_submitted_capture_overlap'] == 162
assert final['kernel_unchanged'] and final['pose_processes'] == 0 and final['test_ports_clear']
assert (E / 'on-return/run-on/after.dmesg.txt').read_bytes() == (E / 'final-r2-return/final-r2/dmesg.txt').read_bytes()
resource = load(E / 'resources-return/resources-on/review.json')
assert resource['writes'] == 1 and resource['elapsed_ns'] == 161296680
for name in ('build-result.json', 'symbols.txt', 'encoder-symbols.txt'):
    shutil.copyfile(B / name, E / name)
shutil.copyfile(B / 'build.log', E / 'build.txt')
old = R / '.local/pose-v1-build/producer-vpu-20261011-r1'
assert '5.05Hz arithmetic differs' in (old / 'build.log').read_text()
shutil.copyfile(old / 'build.log', E / 'r1-build-failure.txt')
old_sources = {str(p.relative_to(old)): sha(p) for p in (old / 'source').iterdir() if p.is_file()}
shutil.copyfile(old / 'source/producer_schedule_selftest.cpp', E / 'r1-producer_schedule_selftest.cpp')
assert (old / 'source/producer_schedule.hpp').read_bytes() == (R / 'software/pose_v1/include/producer_schedule.hpp').read_bytes()

def insert(path, body):
    p = R / path
    a, b = p.read_text(encoding='utf-8').split('\n', 1)
    p.write_text(a + '\n\n' + body.strip() + '\n' + b, encoding='utf-8', newline='\n')

insert('Agents.md', '''- 独立生产者／VPU对照本批结束（2026-10-11）：用户批准PRODUCER-GROUP-NEXT。r2 5dde91e1…32b0a同身份18来源／152冻结软件，Native／ARM载荷9拒绝、时隙及ioctl透传合同过。无VPU100调用1176000FP32全逐位／有限／0→11／时隙过；有VPU先实际capture后主线程Session及真实往返，82调用964320FP32全正确，inv81保存比较后因Call exhausted slot退出1、无call82，不记100通过。合182／2140320值，正式192坏读未复现未修。inv81 reset前1763.68731ms空档，随后forward460.98μs／copy91.12及109.15μs；空档含目录／输入身份写盘、SDK Host输入校验分配写入和调度，未拆分，不归因已证IO或NPU。当前仅调用开始检查时隙，准备结束无二次门检，迟到仍完成该一次前向后停止、无追帧。VPU Q/DQ间1655.39453ms空档，最长ioctl1.6711ms；阶段allocstall/reclaim/OOM/compact0、pgmajfault17未定位。1628公开记录／单VPU线程／fd6／NV12type10及H264type9／各2buffer，164copy中162交叠提交capture跨度非fence；271ownedpacket47878字节含参数头，270解码ID0–269正确，272raw提交／271归还，尾两未解码，全部NoInput不计新姿态吞吐。两abort STREAMOFF0／join后SDK毁块0，正常drain-LAST未过；冻结summary0计数字段因abort未返回不能当无工作。一次自主规整161.29668ms、普通512单位7→34，无清缓存／重启／CMABOOTSDK模型变化；阶段及最终内核同，FPGA operating／全部本批程序管理器端口连接结束。最终694568/106916KiB仅快照。Native r1期望+1ns错误／只读收尾r1 Host清单KeyError与新r2修正保留，无失败硬件重跑。ADR_40、PRODUCER-VPU-RESULTS/NEXT、producer-vpu-20261011-r2 completion/next-checkpoint当前；下一reset前应用与SDK分段单钟／准备后绝对截止检查仅准备，原异常读取／745／CPU分工保持，83/100／完整103／严格整机5Hz／长期／HDMI待。以下当前为历史。''')
insert('Done.md', '''## 2026-10-11：独立生产者无视频100通过，有视频82正确后时隙失败

### 工程内容总结

新增SDK无关时隙和公开VPU ioctl观察模块及隔离编排，复用原producer SDK和冻结VPU源；18来源／152冻结软件、模型／RAW／SDK／BOOT保持。r2程序5dde91e1…32b0a，Native／ARM载荷9拒绝、时隙及透传返回／errno／EINTR／EAGAIN／容量合同通过。无VPU100次1176000 FP32逐位独立参考／有限／0→11和时隙通过；有VPU取得实际capture后再创建主线程Session及内存往返，实际82次964320值全部正确，inv81完整保存和比较后时隙失败exit1，未call82，合182次2140320值正确，不称有VPU100通过。

inv81 reset前1763.68731ms未拆分空档，随后forward460.98μs及两copy91.12／109.15μs；空档包括应用保存、SDK Host输入准备和调度，根因尚未确认。1628公开ioctl，164次复制中162与提交capture跨度交叠；271 owned packet／47878字节包括参数头，270图像ID0–269解码正确，272raw提交／271归还，尾270／271未解码。全部NoInput不计姿态吞吐；两abort STREAMOFF成功，join后SDK毁／块0，正常drain／LAST未过。

### 对后续开发的参考

新身份下一先拆分reset前应用保存及SDK校验／分配／写入，补准备后按原绝对截止时间检查，不调频／追帧／延时猜修复。同期VPU调用外空档、阶段pgmajfault17未定位，不能认定文件I/O／NPU／DMA原因；正式192坏读未复现未修，原异常读取保留，83/100保持。自主规整一次161.29668ms、普通512KiB单位7→34，无清缓存／重启／CMABOOT变化。Native r1期望1ns错误及只读收尾Host清单错误保留，新修订修正未硬件重跑。BOOT／SDK／内核同，全部程序／管理器／测试端口和代理连接结束，最终MemAvailable694568／CmaFree106916KiB仅快照。[结果](tools/pose-v1/PRODUCER-VPU-RESULTS-20261011.md)／[ADR_40](ADR/ADR_40.md)／[下一](tools/pose-v1/PRODUCER-VPU-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-vpu-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
insert('PROJECT-PROGRESS.md', '''## 当前：无视频100通过，有视频82次数据正确但时隙失败

同身份独立19成员off100／on82共2140320 FP32逐位参考、0→11正确，on inv81 reset前1763.68731ms空档导致时隙退出1，不能认定文件I/O或NPU根因。实际并发覆盖162/164复制跨度，270 NoInput图像解码正确；正常drain-LAST未验。原正式192坏值未复现未修、异常读取保持，当前仍处首版闭环后的并发可靠性定位，主观管理83/100不变（非通过率或工期），完整103／严格整机5Hz／长期／HDMI待。一次有记录规整，原模型SDKBOOT/CMA和152软件保持，程序／连接全结束。下一分段观察及准备后绝对截止检查仅准备。

[结果](tools/pose-v1/PRODUCER-VPU-RESULTS-20261011.md)／[ADR_40](ADR/ADR_40.md)／[下一](tools/pose-v1/PRODUCER-VPU-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-vpu-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
for path in ('DIFFICULTIES.md', 'REFERENCES.md', 'ToDoLists.md'):
    insert(path, '2026-10-11最新：[ADR_40](ADR/ADR_40.md)记录同身份off100通过、on82数值正确后时隙失败及reset前1.764秒空档，正式根因未修。271packet／270 NoInput图像／162复制交叠、异常清理通过，正常drain-LAST未过；[结果](tools/pose-v1/PRODUCER-VPU-RESULTS-20261011.md)／[下一分段观察](tools/pose-v1/PRODUCER-VPU-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-vpu-20261011-r2/next-checkpoint.json)。原异常读取保留，下一未执行，全部程序连接结束，以下当前为历史。')
insert('ADR/README.md', '最新：[ADR_40](ADR_40.md)独立生产者／VPU对照：off100通过，on82次数据正确后时隙失败，reset前1.764秒空档待分解；正式坏读未修。[结果](../tools/pose-v1/PRODUCER-VPU-RESULTS-20261011.md)／[下一](../tools/pose-v1/PRODUCER-VPU-NEXT-20261011.md)。以下当前为历史。')
insert('tools/pose-v1/README.md', '> 2026-10-11最新：[独立生产者／VPU结果](PRODUCER-VPU-RESULTS-20261011.md)：off100通过，on82次数据正确后时隙失败；reset前1.764秒空档未分解，正式根因未修。271packet／270 NoInput图像前缀正确、162/164复制交叠，abort清理通过但正常drain-LAST未过；原异常读取保留。[ADR_40](../../ADR/ADR_40.md)／[下一](PRODUCER-VPU-NEXT-20261011.md)／[恢复](evidence/producer-vpu-20261011-r2/next-checkpoint.json)。全部程序连接结束，以下当前为历史。')
checkpoint = {'active_work': False, 'user_paused': False, 'services_running': False,
              'all_agent_programs_connections_closed': True, 'root_cause_resolved': False,
              'current_stage': 'off100_passed_on82_correct_pacing_failed_archived',
              'next_entry': 'tools/pose-v1/PRODUCER-VPU-NEXT-20261011.md',
              'next_implemented': False, 'no_failed_hardware_retry': True,
              'preserve_original_failure_and_reads': True, 'original_final_count': 745,
              'independent_count': 11, 'management_estimate': 83,
              'next': 'separate pre-reset save/SDK Host preparation/scheduling; add absolute deadline recheck after preparation'}
(E / 'next-checkpoint.json').write_text(json.dumps(checkpoint, indent=2) + '\n', encoding='utf-8', newline='\n')
names = ('build_producer_vpu.py', 'build_producer_vpu_r2.py', 'board_producer_vpu_run.py', 'execute_producer_vpu.py',
         'producer_vpu_resources.py', 'prepare_producer_vpu_resources.py', 'review_producer_vpu_outputs.py',
         'review_producer_vpu_failure.py', 'review_producer_vpu_video.py', 'board_producer_vpu_final.py',
         'collect_producer_vpu_final.py', 'board_producer_vpu_final_r2.py', 'collect_producer_vpu_final_r2.py',
         'archive_producer_vpu.py', 'ssh_memory_transport.py', 'archive_bytes.py')
tools = ['tools/pose-v1/' + n for n in names]
for name in tools:
    ast.parse((R / name).read_text(encoding='utf-8-sig'))
docs = ['Agents.md', 'Done.md', 'PROJECT-PROGRESS.md', 'DIFFICULTIES.md', 'REFERENCES.md', 'ToDoLists.md',
        'ADR/ADR_40.md', 'ADR/README.md', 'tools/pose-v1/README.md',
        'tools/pose-v1/PRODUCER-VPU-RESULTS-20261011.md', 'tools/pose-v1/PRODUCER-VPU-NEXT-20261011.md', '.gitignore']
reviews = ('host.review.json', 'off.data-review.json', 'off.exit-review.json', 'on.failure-review.json',
           'on.exit-review.json', 'on.video-review.json', 'off-deployment.review.json', 'on-deployment.review.json',
           'resources-return/resources-on/review.json', 'final-r2-return/final-r2/review.json')
report = {'status': checkpoint['current_stage'], 'program_sha256': build['program_sha256'],
          'build_source_hashes': build['sources'], 'frozen_software_hashes': frozen,
          'frozen_software_sources_unchanged': len(frozen), 'tool_hashes': {p: sha(R / p) for p in tools},
          'off_completed': 100, 'on_completed': 82, 'on_exit': 1, 'FP32_values_verified': 2140320,
          'full_model_calls': 0, 'new_Host107_runs': 0, 'frame_reset1_calls': 182,
          'VPU_packets': 271, 'decoded_NoInput_images': 270, 'normal_drain_LAST_pass': False,
          'copy_overlap_spans': 162, 'copy_spans_total': 164, 'ioctl_records': 1628,
          'compactions': 1, 'compaction_elapsed_ns': resource['elapsed_ns'],
          'BOOT_SDK_model_kernel_unchanged': True, 'root_cause_resolved': False,
          'agent_programs_connections_closed': True, 'management_estimate': 83,
          'reviews': {n: sha(E / n) for n in reviews},
          'archives': {p.name: sha(p) for p in E.glob('*.tar')},
          'r1_native_failure_source_hashes': old_sources, 'r1_native_failure_log_sha256': sha(E / 'r1-build-failure.txt'),
          'retained_final_audit_keyerror_log_sha256': sha(E / 'final-operation.txt'),
          'documents': {n: sha(R / n) for n in docs}, 'checkpoint_sha256': sha(E / 'next-checkpoint.json')}
(E / 'completion-review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
print('Archived off100/on82 failure; frozen152 verified; SHA256', sha(E / 'completion-review.json'))

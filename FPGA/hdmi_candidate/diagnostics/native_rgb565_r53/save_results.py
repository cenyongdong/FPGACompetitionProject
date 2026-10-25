from pathlib import Path
import shutil
o=Path('D:/FPGACompetitionProject');c=Path('C:/Users/cenyongdong/.codex/worktrees/hdmi-s01-isolation/FPGACompetitionProject')
rel=Path('tools/pose-v1/evidence/hdmi-pipeline-20261024-r53')
shutil.copytree(o/rel,c/rel,dirs_exist_ok=True)
src=c/'FPGA/hdmi_candidate/diagnostics/native_rgb565_r53'
for name in ('start_long.py','finalize_local.py','save_results.py'):
    shutil.copyfile(Path(__file__).with_name(name),src/name)
p=c/'PROJECT-PROGRESS.md';lines=p.read_text(encoding='utf-8-sig').splitlines()
lines[2]='2026-10-24：r53单SDK线程推理/HDMI流水调度编译及64项SDK无关检查通过；本次健康启动（消费0），短样本29.521Hz、采纳187帧后，第189次op192首读索引1568字混入同帧姿态内容而停止，未重试。用户仍只看到瞬间骨架，长期未通过。已回原BOOT运行，1候选/1SDK/1回退包关闭，主机/隧道/UART均结束；无新板测许可。[r53事实、原始数据与恢复](tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/RESULTS.md)。'
p.write_bytes(('\n'.join(lines)+'\n').encode())
p=c/'DIFFICULTIES.md';lines=p.read_text(encoding='utf-8-sig').splitlines()
lines[2]='更新：2026-10-24，r53流水调度短样本29.521Hz、187次采纳后遇到首读索引内容混合；本次健康启动、无消费，长期及实屏均未通过，已回原BOOT。启动根因与本轮数值异常均未解决；无新板测许可。[r53实测](tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/RESULTS.md)。'
for i,line in enumerate(lines):
    if line.startswith('- **D29严格实时、D41长尾与HDMI长期：'):
        lines[i]='- **D29严格实时、D41长尾与HDMI长期：未验收或未解决。** r53单SDK线程流水调度将短样本输出提升至29.521Hz，第189次op192首读内容混合触发停止；187采纳、188原值、187最终确认分别保留，实屏只瞬间可见。两轮SDK晚读正确不能修补首读错误；已回原BOOT、无新板测许可，见[r53](tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/RESULTS.md)。'
p.write_bytes(('\n'.join(lines)+'\n').encode())
p=c/'Done.md';text=p.read_text(encoding='utf-8-sig')
marker='见[r52结果](tools/pose-v1/evidence/hdmi-long-git-20261024-r52/RESULTS.md)。'
text=text.replace(marker,marker+' r53完成单SDK线程流水调度和离线边界测试，短样本29.521Hz；第189次首读索引内容混合，已停止并回原BOOT，不作稳定性通过；见[r53结果](tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/RESULTS.md)。',1)
p.write_bytes(text.encode())
print('Saved r53 actual numeric failure, source bytes, physical-screen feedback and original recovery; main workspace unrelated changes untouched.')

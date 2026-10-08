"""Collapse obsolete status notices; keep original history and evidence intact."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'PROJECT-PROGRESS.md';text=p.read_text(encoding='utf-8')
heading='# 项目进度总览（2026-10-08）\n\n';assert text.startswith(heading)
anchor='用户确认当前异构方案完成首版全流程'
cut=text.index(anchor);preface=text[len(heading):cut]
latest,past=preface.split('\n\n',1)
text=heading+latest+'\n\n当前审阅入口：[本次进度与后续方案](tools/pose-v1/PROJECT-STATUS-AND-NEXT-20261008.md)。本轮仅文档核对，未启动新板测。\n\n<details>\n<summary>历次阶段更新（历史，旧入口不作当前待办）</summary>\n\n'+past+'\n</details>\n\n'+text[cut:]
replacements={
'**尚未通过的验收：** guarded正式入口固化、TCP窗口与此真实串联目标合并、HDMI、整机吞吐及30分钟闭环。固定本地CSI的实际VPU/RTSP串联已通过；2Hz带全量证据运行不等于整机5Hz。CPU绘图/单NV12转换的争用仍需计量，lazy-r4的5.24655Hz仍是独立短期核心基线。':
'**尚未通过的验收：** 整机吞吐/P95、启动与长期内存可靠性、完整混合链路慢客户端清理、HDMI及30分钟闭环。guarded和TCP完整窗口已接入并有限三/27通过；2Hz带保存运行不等于整机5Hz。CPU绘图/单NV12争用仍需计量，5.24655Hz仅独立短期核心基线。',
'| E1/F0应用输出 | 生产接口/TCP/绘图已分别通过；固定CSI真实推理→VPU→RTSP三/27窗通过，32来源完整 | guarded候选固化/TCP前端整体联调及最终性能/双路/长期未完成；有限CLI不是长期服务 |':
'| E1/F0应用输出 | TCP完整窗口→主线程Engine→骨架→VPU→guarded RTSP三/27有限门检通过，32来源/保存值完整 | 整机性能/HDMI/长期未过；旧失配未复现原因未知，规整恢复不是永久内存方案 |',
'下一批按[真实在线结果接续](tools/pose-v1/LIVE-RESULTS-20261008.md)固化guarded、接入已验TCP完整窗口，再计量整机关键路径/过载及长期。HDMI配套未明不写，目标1080p60与用户允许测试保持；深度优化后置。':
'下一批建议按[当前后续方案](tools/pose-v1/PROJECT-STATUS-AND-NEXT-20261008.md)先独立低日志整机计量：单时钟分段→2Hz基线→有限5Hz负载，再据瓶颈讨论最小修正。CMA/HDMI先核验匹配接口，深度优化仍后置。当前仅整理，尚未实施该批。',
'新恢复点：[当前检查点](tools/pose-v1/evidence/live-20261008-completion/next-checkpoint.json)。旧检查点保留，不重跑历史失败或用模块门检替代最终整机验收。':
'新恢复点：[当前检查点](tools/pose-v1/evidence/tcp-presaved-20261008-r1/next-checkpoint.json)。一次规整授权已使用，当前无后台；旧检查点保留，不重跑历史失败或用模块门检替代整机验收。',
'| [最新检查点](tools/pose-v1/evidence/render-20261007-r1/next-checkpoint.json) | CPU骨架画面完成、V0查询与后续编码/HDMI配套边界，旧入口保留 |':
'| [最新检查点](tools/pose-v1/evidence/tcp-presaved-20261008-r1/next-checkpoint.json) | 保存优先/一次规整下有限全链通过，接续独立低日志计量；旧错误原因与长期可靠性保留 |'
}
for before,after in replacements.items():assert text.count(before)==1,before;text=text.replace(before,after)
p.write_bytes(text.encode())
p=root/'ToDoLists.md';text=p.read_text(encoding='utf-8');cut=text.index('2026-10-08当前：[guarded/TCP结果]')
text=text[:cut]+'下一批具体建议见[当前进度与后续方案](tools/pose-v1/PROJECT-STATUS-AND-NEXT-20261008.md)。本輪仅整理，未新板测。\n\n<details>\n<summary>历史清单与停止记录（不作当前任务指令）</summary>\n\n'+text[cut:]+'\n</details>\n'
text=text.replace('本輪','本轮');p.write_bytes(text.encode())
print('Current overview corrected; historical notices preserved and collapsed.')

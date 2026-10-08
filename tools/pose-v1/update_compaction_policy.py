"""Apply the user's current policy while retaining historical observations."""
from pathlib import Path
p=Path(__file__).resolve().parents[2]/'Agents.md'
s=p.read_text(encoding='utf-8')
replacements={
'不自动再规整/清缓存/重启/CMA改变':'不自动清缓存/重启/CMA改变',
'不得自动再次规整/清缓存/重启或盲改CMA/HDMI':'不得自动清缓存/重启或盲改CMA/HDMI',
'一次授权已消耗，不自动循环规整/复位':'该批单次规整已记录，不自动复位',
'代理可执行该一次恢复，不清缓存、不循环规整/重试、不重启或改CMA/BOOT/SDK/模型':'该批执行恢复的历史证据保留，不清缓存、不自动重试、不重启或改CMA/BOOT/SDK/模型',
'不自动重试/规整/reset或BOOT/CMA变化':'不自动重试/reset或BOOT/CMA变化',
'不自动规整/重试':'不自动重试',
'用户选择恢复首启动条件后新目录三窗→27失败取证':'恢复首启动条件后新目录三窗→27失败取证',
}
for a,b in replacements.items():s=s.replace(a,b)
policy='- 内存规整执行权限（2026-10-08，用户最新要求）：代理可根据当前页分配、碎片化和测试资源状态，自主决定是否执行内存规整，无须逐次征求用户批准或按单次授权计数。每次在独立证据目录记录原因、前后 buddyinfo/pagetypeinfo/meminfo/vmstat、内核日志、耗时及结果；不以规整成功代替首次启动可靠性验收。历史条目中的单次授权、已消耗及实际次数仅说明当时情况，旧审批限制已删除。此授权不涉及清缓存、重启、修改 CMA/内核/BOOT/模型/SDK，也不取消异常保存和停止条件。\n\n'
assert '内存规整执行权限（2026-10-08' not in s
s=s.replace('# 项目执行规范\n\n','# 项目执行规范\n\n'+policy,1)
p.write_text(s,encoding='utf-8',newline='\n')

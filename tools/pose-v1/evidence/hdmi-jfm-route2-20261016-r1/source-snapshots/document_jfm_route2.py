"""Document this audit without changing earlier sealed evidence or credentials."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1'
def read(rel):return (R/rel).read_text(encoding='utf-8-sig')
def write(rel,text):
 assert (E/'before'/rel).exists(),rel
 (R/rel).write_text(text,encoding='utf-8')
audit='FPGA/hdmi_candidate/ROUTE2-AUDIT.md';report='tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/REPORT.md'
summary=('用户批准原厂Vivado＋JFM／Procise路径二审查。隔离原始2018.3工程297份身份通过，28项IP全部未锁定且未升级；'
 'HARC与原厂源同SHA，预览时跳过复制。本批未增加安装写入。六项hook配置已独立重开确认；'
 '首次配置驱动save_project用法错误exit1保留，未重跑add_hook。原厂门检先检出MIG无OOC；'
 '同配置MIG综合262.133509秒exit0，XCI非运行时参数及DDR .prj字节不变，随后原厂pre_patch_check通过。'
 '180秒门限时依据日志进展自主将预算延至360秒并等待原进程，没有重启作业。'
 '已确认30TAI独立ICAP后处理的Procise目标JFMQL30TAI676H，未执行.bit处理。')
limits=('当前无完整候选位流、实屏或DDR硬件验收；正式构建尚需确定32项全局IP库替换与四项GT专用DRC处理范围。'
 '原生PCPU7导入旧失败保留，不再作为路径二前置条件。BOOT/SDK/模型/PS/AI_Mate及原扫描RTL保持，旧DATA继续暂停。')
t=read('PROJECT-PROGRESS.md');head,old,rest=t.split('\n\n',2)
t=head+'\n\n更新日期及最后实际验证日期：2026-10-16。'+summary+limits+f' [审查与后续范围]({audit})、[完整证据]({report})。\n\n'+rest
line=next(x for x in t.splitlines() if x.startswith('| HDMI |'))
t=t.replace(line,'| HDMI | 原厂混合路径审查完成；原始28项IP未锁定，MIG同配置OOC及原厂前置检查通过 | 全局IP库/GT DRC范围待确定；无顶层完整位流或实屏验收；[流程审查]('+audit+') |')
t=t.replace('**本批HDMI离线分组验证及常量修正完成**；[结果/物理集成待办](FPGA/hdmi_candidate/RESUME.md)','**原厂路径二审查、MIG同配置OOC及前置检查完成**；[审查与构建边界]('+audit+')')
write('PROJECT-PROGRESS.md',t)
for rel in ['REFERENCES.md','FPGA/hdmi_candidate/RESUME.md','FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md','FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md']:
 t=read(rel);head,old,rest=t.split('\n\n',2);prefix='../../' if rel.startswith('FPGA/') else ''
 link='ROUTE2-AUDIT.md' if prefix else audit
 t=head+'\n\n2026-10-16最新状态：'+summary+limits+f' [审查与参数/写入范围]({link})、[本批证据]({prefix}{report})。用户已更新超时规则：依据现场自主判断、记录预算调整和清理，无需因超时逐次确认；非超时故障及重大变更边界继续保持。\n\n## 此前阶段资料（保留当时结果，当前入口见上）\n\n'+old+'\n\n'+rest
 if rel=='REFERENCES.md':
  line=next(x for x in t.splitlines() if x.startswith('| Vivado 辅助工具/MCP |'))
  t=t.replace(line,'| Vivado 辅助工具/MCP | D:/vivado18.3/Vivado/2018.3/bin/vivado.bat，64-bit Build2405991；2019.1保留 | 用户安装且已就地030ai补丁；本批原厂路径审查、MIG同配置OOC/前置检查通过；[实际职责与边界]('+audit+') |')
 write(rel,t)
t=read('DIFFICULTIES.md');line=next(x for x in t.splitlines() if x.startswith('| D05 |'))
t=t.replace(line,'| D05 | HDMI完整候选尚未实现或实屏验收 | 原厂Vivado＋JFM／Procise路径审查完成，28项原始IP未锁定；MIG同配置OOC/原厂前置检查通过 | 通用EDIF旧失败保留；路径二需确定32项全局IP库及4项GT DRC范围；ICAP只预览无实际处理；[审查]('+audit+')／[原值]('+report+') |')
write('DIFFICULTIES.md',t)
t=read('Done.md');h='### 工程内容总结\n\n'
t=t.replace(h,h+'2026-10-16路径二审查：'+summary+limits+' 执行位置Windows，工作目录D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1；Vivado2018.3、Procise2025.1.1temp/SVN32494。只复制工程及必要JFM文件，不复制工具。'+f' [完整原值和通过标准]({report})、[参数/后续范围]({audit})。32项默认IP库覆盖对象逐项只读盘点，源/目标均存在且全部不同；四项DRC定义实际查询，未执行关闭。所有配置预览失败及MIG前置失败保留，无板端连接。\n\n以下为此前r2及更早阶段实际结果：\n\n',1)
h='### 对后续开发的参考\n\n'
t=t.replace(h,h+'路径二审查参考：预览生成脚本、配置落盘、原厂前置检查、实际位流处理和BOOT打包逐项取证。原厂按mtime选bit，后续一目录一输入并显式保存SHA；K325通用配置不能替代30TAI独立ICAP分支。-xfft_modify实际覆盖32项库，工程存在counter，不凭无FFT跳过。超时先辨识日志进度与进程祖先链，再有界调整原进程预算；直接命令行路径匹配不足以判断相对路径子进程归属。此前“超时须另次确认”仅为当时规则，现以Agents最新授权为准。\n\n',1)
write('Done.md',t)
t=read('ARCHITECTURE-DISCUSSION-20261015.md')
t+='\n\n## 十八、路径二审查及超时自主判断规则\n\n2026-10-16，用户同意审查原厂Vivado＋JFM、Procise后处理流程，同时明确要求超时由代理根据现况决定后续操作，不再必须逐次询问。Agents相应修改：保存现场、核对作业归属，允许有界续等、清理、拆分或新目录重执行；不扩大架构、负载、启动配置或门禁，非超时严重故障仍保存停止。\n\n'+summary+limits+f' [完整审查]({audit})、[本批证据]({report})。此授权落实为审查与既有同配置IP重建，不将默认全局库替换、速度改变、DRC豁免或BOOT修改自动当作同意。\n'
write('ARCHITECTURE-DISCUSSION-20261015.md',t)
t='''# 原厂流程审查与当前实现入口

2026-10-16，用户已选定路径二进行审查。最新结果、参数读写清单及正式构建边界统一见[ROUTE2-AUDIT.md](ROUTE2-AUDIT.md)，本页保留此前路径选择的依据。

2018.3已按明确授权就地完成030ai补丁，真实扩展PS展开及综合通过。之后通用EDIF原语名称转换成功，但Procise原生PCPU7导入失败；失败证据、端口原值与未重试状态保留于[上一批报告](../../tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/REPORT.md)。这不能推导原厂Vivado＋JFM位流链路也必须经过PCPU7导入。

本轮在隔离原始工程上审查六项hook、真实DRC定义和默认库操作，补齐同配置MIG OOC后原厂前置检查通过。Procise后处理包含30TAI独立ICAP分支，并非仅有K325示例增量配置。已确认调用目标，但没有执行位流处理或完整顶层实现；32项全局IP库替换和四项GT DRC处理仍需确定范围。BOOT及旧DATA暂停保持。

本轮发生的save_project驱动错误与初次MIG前置检查失败均保留，不将独立核验改写成原运行通过。超时处理遵循最新Agents授权，自主取证并有界决策；MIG实际以180→360秒继续原作业，在262.133509秒完成。

[本批完整原值](../../tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/REPORT.md)。此前本页全文保存在该批before文档快照；历史报告及其清单未回写。
'''
write('FPGA/hdmi_candidate/JFM-FLOW-REVIEW.md',t)
print(json.dumps({'existing_documents_updated':9,'new_audit':audit,'Agents_changed_separately':True}))

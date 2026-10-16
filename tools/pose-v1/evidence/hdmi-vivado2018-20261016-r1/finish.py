from pathlib import Path
import ast, hashlib, json, re, shutil
R=Path(__file__).resolve().parents[2]
E=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r1'
def read(p):return p.read_text(encoding='utf-8-sig')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
out=E/'installed-preflight'
log=read(out/'stdout.txt')
assert 'Vivado v2018.3 (64-bit)' in log and 'SW Build 2405991' in log
assert 'INSTALLED_PREFLIGHT_COMPLETE' in log
pins=[x.split('|')[0].split('/')[-1] for x in read(out/'builtin-PS7-pins.txt').splitlines()]
assert len(pins)==len(set(pins))==3305
assert not any(p.startswith('AI_') for p in pins)
dump(out/'execution.json',{'result_origin':'recovered from outer exec result because v1 driver raised before saving execution.json',
 'driver_exit':1,'tool_exit':None,'timeout':True,'budget_seconds':60,
 'cleanup_command_return':'Access denied','cleanup_wait_timeout_seconds':15,
 'kernel_synth_design_elapsed_seconds_reported':61,'kernel_completion_marker_present':True,
 'runtime_PS7_pins_written':3305,'overall_pass':False,'failed_load_rerun':False,
 'natural_tool_exit_logged':True,'final_process_inventory_required':True})
dump(E/'installed-tree-inventory.json',{'source':'read-only Python directory inventory, outer exec exit0',
 'root':'D:/vivado18.3/Vivado/2018.3','files':99661,'bytes':28560628023,
 'metadata_inventory_only_not_full_content_hash':True,'tool_copied':False,
 'inventory_process_naturally_finished':True})
targets=json.loads(read(E/'installed-targets-before.json'))
for x in targets:
 x['after_sha256']=sha(Path(x['path']));x['equal']=x['after_sha256']==x['sha256'];assert x['equal']
dump(E/'installed-targets-after.json',targets)
prior=json.loads(read(R/'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/replacement-review.json'))
for x in prior['replacement_pairs']:assert sha(Path(x['installed_target']['path']))==x['installed_target']['sha256']
original=json.loads(read(R/'tools/pose-v1/evidence/hdmi-system-20261015-r1/original-manifest.json'))
for n,h in original.items():assert sha(R/'Docs/26嵌赛开发/fpai_demo_fpga'/n)==h,n
rtl=json.loads(read(R/'tools/pose-v1/evidence/hdmi-split-20261015-r1/scanout-RTL-identity-consistency.json'))
for x in rtl:assert sha(R/'FPGA/hdmi_candidate/rtl'/x['source'])==x['current_sha']
dump(E/'baseline-review.json',{'original_reference_files_unchanged':len(original),
 'accepted_scanout_RTL_unchanged':len(rtl),'installed_2018_3_database_targets_unchanged':9,
 'old_2019_1_database_targets_unchanged':9,'replace_reset_hook_invoked':False,
 'whole_installation_tree_byte_identity_not_claimed':True,'board_not_connected_this_batch':True})
destination=R/'.local/hdmi-vivado2018-20261016-r2/tool/Vivado/2018.3'
dump(E/'proposed-private-target-map.json',{'not_executed':True,'root':str(destination),
 'replacement_pairs':[{'source':x['patch']['path'],'source_sha256':x['patch']['sha256'],
 'target':str(destination/Path(x['installed_target']['path']).relative_to(Path('D:/Xilinx/Vivado/2019.1')))} for x in prior['replacement_pairs']],
 'reset_static_targets':[str(destination/n) for n in prior['reset_helper_target_paths_static']],
 'reset_target_count':len(prior['reset_helper_target_paths_static']),
 'write_guard_allow_root':'D:/FPGACompetitionProject/.local/hdmi-vivado2018-20261016-r2',
 'user_installation_write_forbidden':True,'full_backup_before_patch_required':True})

summary=('用户已自行安装Vivado2018.3于D:/vivado18.3/Vivado/2018.3；实际启动确认64-bit、SW Build2405991/IP Build2404404。'
 '首次60秒预检外层超时，随后内核完成小锚点展开及PS7/3305位引脚查询；驱动exit1，整轮不验收。'
 'taskkill权限拒绝及15秒等待超时保留，工具最终自行退出，未重跑；Common17-741的TclStore路径告警待核对。'
 '未复制或修改工具库，九项2018.3和旧2019.1目标SHA同；扩展PS仍待私有副本验证。')
link='tools/pose-v1/evidence/hdmi-vivado2018-20261016-r1/REPORT.md'
plan='FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md'
changes=[]
def write_doc(rel,text):
 before=E/'before'/rel;assert before.exists()
 (R/rel).write_text(text,encoding='utf-8')
 changes.append({'path':rel,'before_sha256':sha(before),'after_sha256':sha(R/rel)})

p=R/'PROJECT-PROGRESS.md';t=read(p);first,_,rest=t.split('\n\n',2)
overview=('更新日期及最后实际验证日期：2026-10-16。'+summary+
 ' 新批次私有工具/专用库及PS验证方案待用户确认；完整候选仍受PS7→PCPU7绑定阻塞，无完整位流或实屏验收。'
 '原扫描RTL、IP生成、AXI3与原生互联综合成果保持；无板端操作/BOOT修改/重启，旧DATA继续暂停。'
 f' [安装与预检证据]({link})、[新批次具体方案]({plan})。')
t=first+'\n\n'+overview+'\n\n'+rest
line=next(x for x in t.splitlines() if x.startswith('| HDMI |'))
t=t.replace(line,'| HDMI | 2018.3由用户安装并实际启动；首次预检外层60秒超时停止，库未修改 | 运行库仍缺AI扩展，私有工具/30TAI库/PS新批次待确认；已有扫描/IP/AXI成果保持，完整实现与实屏待验；[恢复方案]('+plan+') |')
line=next(x for x in t.splitlines() if x.startswith('| 工具链 |'))
t=t.replace(line,line.replace('Vivado2019.1辅助','Vivado2018.3（D:/vivado18.3/Vivado/2018.3）专用前端待验证，Vivado2019.1保留'))
write_doc('PROJECT-PROGRESS.md',t)

for rel in ['REFERENCES.md','FPGA/hdmi_candidate/RESUME.md','FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md']:
 t=read(R/rel);header,rest=t.split('\n\n',1)
 # Move the former current status into an explicitly historical paragraph.
 rest=rest.replace('2026-10-15最新版本路线：','2026-10-15历史版本路线：',1)
 prefix='../../' if rel.startswith('FPGA/') else ''
 t=header+'\n\n2026-10-16当前安装与恢复状态：'+summary+f' [实际日志]({prefix}{link})、[新批次方案]('+('VIVADO-VERSION-PLAN.md' if prefix else plan)+')。安装/下载由用户完成，不再等待AMD登录；以下较早结果保留当时范围。\n\n'+rest
 if rel=='REFERENCES.md':
  line=next(x for x in t.splitlines() if x.startswith('| Vivado 辅助工具/MCP |'))
  t=t.replace(line,'| Vivado 辅助工具/MCP | 2018.3实际入口D:/vivado18.3/Vivado/2018.3/bin/vivado.bat；2019.1原环境保留 | 2018.3由用户安装，16日实际启动确认Build2405991；首次60秒预检超时，不当整轮通过，专用库/PS/Procise交接未验；[证据]('+link+') |')
 if rel.endswith('RESUME.md'):
  t=t.replace('本机30TAI教程的全局库替换未执行，现有不改全局数据库/不安装升级/不升级自定义PS或AI_Mate边界保持。',
   '用户已完成2018.3安装；教程库替换仍未执行，新批次拟只作用于完整私有工具副本。保留用户安装、2019.1、自定义PS及AI_Mate身份，超时后未自动恢复。')
 write_doc(rel,t)

t=read(R/'Done.md');t=t.replace('## 2026-10-15：HDMI隔离候选开发、暂停与恢复验证','## 2026-10-15—16：HDMI隔离候选开发、暂停与恢复验证',1)
head='### 工程内容总结\n\n'
t=t.replace(head,head+'2026-10-16安装说明与实际继续：'+summary+f' 工作目录D:/FPGACompetitionProject，元数据预算60秒；[证据]({link})。原参考297文件、九份扫描RTL和两版安装九项数据库目标均另行SHA核验同；本轮没有板端连接。驱动异常路径已修正为先记录超时/清理状态再停止，仅静态检查，未再次运行EDA。新批次完整私有复制/补丁/扩展PS方案已准备，待确认后执行。\n\n',1)
head='### 对后续开发的参考\n\n'
t=t.replace(head,head+'16日补充：首次启动与热启动不可混同；内核稍后完成不能覆盖已触发的监控超时。监控清理失败仍须先落盘状态并核对实际进程，不能在第二次wait异常时丢失execution.json。工具启动时本地TclStore回退告警应单独定位；全树盘点和EDA同时进行可能影响I/O，未验证前不下归因结论。工具副本应完整隔离，不能用硬链接修改原安装。\n\n',1)
write_doc('Done.md',t)
t=read(R/'DIFFICULTIES.md');line=next(x for x in t.splitlines() if x.startswith('| D05 |'))
t=t.replace(line,'| D05 | HDMI完整候选受扩展PS兼容阻塞；2018.3首次预检外层超时 | 用户安装2018.3并实际确认版本；内核稍后输出3305位PS7引脚，但整轮60秒超时/驱动exit1，清理权限错误保留 | 未重跑、未补丁；TclStore告警及PS/Procise绑定待验，新私有副本批次待确认；BOOT/SDK/模型保持；[实际证据]('+link+')／[新方案]('+plan+') |')
write_doc('DIFFICULTIES.md',t)
t=read(R/'ARCHITECTURE-DISCUSSION-20261015.md')
t+='\n\n## 十六、用户安装2018.3后的继续及预检停止\n\n2026-10-16，用户明确安装由其进行，现告知安装完毕、路径D:/vivado18.3/Vivado/2018.3，要求记录并继续原任务。\n\n'+summary+f' [新证据]({link})。本轮已实际继续到首次预检；依照Agents的超时停止规则保存现场，不自动延长失败预算或重跑。拟新目录完整工具复制、写入守卫、原版speed=0库替换及扩展PS门检的具体对象和预算已写入[方案]({plan})并请求确认，不能把请求当已获批准。\n'
write_doc('ARCHITECTURE-DISCUSSION-20261015.md',t)
t=read(R/'FPGA/hdmi_candidate/JFM-COMPATIBILITY-REVIEW.md')
t+='\n\n## 2026-10-16实际2018.3安装及预检状态\n\n'+summary+' 此运行库仍是普通PS7，不能仅因版本匹配即宣称具备AI扩展。完整私有工具副本及原版030ai库替换尚未执行；新批次元数据90秒、PS综合180秒为拟议范围，未重写本轮60秒超时。[新证据](../../'+link+')、[恢复方案](VIVADO-VERSION-PLAN.md)。\n'
write_doc('FPGA/hdmi_candidate/JFM-COMPATIBILITY-REVIEW.md',t)
rel=plan;changes.append({'path':rel,'before_sha256':sha(E/'before'/rel),'after_sha256':sha(R/rel)})
dump(E/'documentation-revision.json',{'changes':changes,'prior_sealed_manifests_not_modified':True})
for item in changes:
 p=E/'after'/item['path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/item['path'],p)

(E/'REPORT.md').write_text('''# 用户安装Vivado2018.3后的登记与首次实际预检

2026-10-16（Asia/Shanghai），Windows，工作目录D:/FPGACompetitionProject。用户自行完成安装并要求登记后继续任务；没有由代理下载、安装或修改系统工具配置。

## 实际已验证事实与限制

- 安装入口D:/vivado18.3/Vivado/2018.3/bin/vivado.bat存在；实际启动输出Vivado v2018.3 64-bit、SW Build2405991/IP Build2404404，入口身份见installed-launcher-identity.json。
- 新目录installed-preflight进行小锚点RTL展开/普通PS7库读取，预算60秒。内核随后实际完成，synth_design报告elapsed61秒；PS7输出3305个位引脚、无AI_命名引脚，并打印INSTALLED_PREFLIGHT_COMPLETE。这不是实际扩展PS综合或HDMI验收。
- 外层60秒触发TimeoutExpired，taskkill返回Access denied，驱动又等待15秒超时后exit1，未取得工具进程返回码，整轮明确不通过。工具最后自行退出，不将完成标志回写为通过。驱动v1未能在第二次异常前写execution.json，现记录从外层工具结果恢复的状态并明确来源；原始Tcl、stdout/stderr、Vivado完整log、cleanup.txt及实际引脚文件全部保留。
- 启动Common17-741报告本地TclStore路径'C'无写权限并回退安装目录。原因尚未核实；没有据此断言许可证、逻辑或磁盘故障。并行全树盘点可能增加I/O耗时，未经受控验证不作归因。CIM进程查询曾被系统权限拒绝，之后限制外核对时目标已结束，没有停止其他Python进程；最终EDA进程另盘点。

[本次执行与失败状态](installed-preflight/execution.json)、[完整stdout](installed-preflight/stdout.txt)、[Vivado日志](installed-preflight/vivado.log)、[引脚原值](installed-preflight/builtin-PS7-pins.txt)。没有自动重跑或延长原预算。

## 安装说明、保护及恢复准备

只读目录盘点实际99661文件、28,560,628,023字节，任务自然结束；这是容量盘点，不是全安装字节身份验收。本轮对2018.3九项潜在数据库目标、旧2019.1对应目标、原参考297文件及九份已通过扫描RTL另行SHA核对一致。没有执行replace/reset/hook、完整复制工具、补丁或真实PS综合；不声称整个安装树逐字不变。

已更新PROJECT-PROGRESS、REFERENCES、Done、DIFFICULTIES、讨论记录和候选恢复文档。用户安装的路径取代此前备用下载/代理安装设想；15日原证据及失败不改。文档原值、修订后快照及SHA清单保留。

下一阶段具体对象已准备：[版本及新批次方案](../../../../FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md)、[私有目标与36个静态恢复路径](proposed-private-target-map.json)。拟完整复制工具至新的r2私有目录，不用硬链接；只在该副本运行原版speed=0，保护用户安装和2019.1。拟复制900秒/总45GiB、元数据90秒、PS综合180秒、RTL90秒；尚未启动，需按超时停止/新预算规则确认后执行。即使2018.3前端通过，Procise的扩展PS绑定仍需独立证明。

监控驱动已修复超时清理异常路径，确保未来先记录状态再停止；当前仅AST静态检查，未运行修复后的EDA阶段。没有板端连接、候选下载、BOOT/SDK/模型/RAW/PS/AI_Mate修改或重启；旧DATA调查仍独立暂停。无完整候选位流或实屏通过结论。
''',encoding='utf-8')
source=E/'source-snapshots';source.mkdir(exist_ok=False)
for name in ('preflight_vivado2018.py','vivado2018_support.py'):shutil.copyfile(R/'FPGA/hdmi_candidate/scripts'/name,source/name)
shutil.copyfile(Path(__file__),E/'finish.py')
print(json.dumps({'documents':len(changes),'installed_version_verified':'2018.3','overall_preflight_pass':False,'database_targets_unchanged':18,'reference_files_unchanged':len(original)}))

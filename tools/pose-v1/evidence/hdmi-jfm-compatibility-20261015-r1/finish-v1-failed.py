from pathlib import Path
import ast, hashlib, html, json, re, shutil

R = Path(__file__).resolve().parents[2]
E = R / 'tools/pose-v1/evidence/hdmi-jfm-compatibility-20261015-r1'
V = R / 'tools/pose-v1/evidence/hdmi-vivado2019-library-20261015-r1'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read(p):return p.read_text(encoding='utf-8-sig')
report_link='tools/pose-v1/evidence/hdmi-jfm-compatibility-20261015-r1/REPORT.md'
plan='FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md'
summary=('用户确认官方资料已全部本地保存且无2019.1配套，要求先评估迁移、不可行再下载2018.3。'
 '实际2019.1运行库PS7的3305个位引脚与安装Liberty一致；030ai配套有7213个位引脚，'
 '工程使用的3868个AI_端口在现运行库全部缺失、在配套Liberty全部存在。'
 '九项替换源有八项受保护，现有资料不能形成可验证的完整2019.1迁移；普通RTL/IP成果保持。'
 '2018.3官方下载入口已打开但网页返回会话未建立，尚未取得安装包；未安装或替换库，原生PCPU7适配仍需独立门检。')
changes=[]
def write_doc(rel,text):
 p=R/rel;before=E/'before'/rel
 if p.exists():assert before.exists(),rel
 p.write_text(text,encoding='utf-8')
 changes.append({'path':rel,'before_sha256':sha(before) if before.exists() else None,'after_sha256':sha(p)})

# Replace the single current overview, keeping historical stage records below it.
p=R/'PROJECT-PROGRESS.md';t=read(p);parts=t.split('\n\n',2)
overview=('更新日期：2026-10-15，最后实际验证日期同日。HDMI隔离扫描RTL、有限IP生成、AXI3路由仿真/原生综合与纯输出实际引脚兼容探针成果保持；完整系统仍受扩展PS7→PCPU7绑定阻塞，无完整候选位流或实屏验收。'
 +summary+' 当前无后台构建，未下载候选/改BOOT/重启，旧DATA继续暂停。'
 f' [最新版本评估与证据]({report_link})、[备用环境与恢复步骤]({plan})、[已完成构建结果](tools/pose-v1/evidence/hdmi-bringup-20261015-r1/REPORT.md)。')
t=parts[0]+'\n\n'+overview+'\n\n'+parts[2]
line=next(x for x in t.splitlines() if x.startswith('| HDMI |'))
t=t.replace(line,'| HDMI | 扫描、有限IP/AXI3和原生互联综合通过；完整PS与实屏仍阻塞 | 已逐端口确认2019.1缺全部3868个所需AI扩展端口；现有资料不能完成可靠整机迁移，2018.3备用下载等待账户会话，未安装/换库/下载候选；[版本方案]('+plan+') |')
write_doc('PROJECT-PROGRESS.md',t)

for rel in ['REFERENCES.md','FPGA/hdmi_candidate/RESUME.md','FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md']:
 t=read(R/rel);first,rest=t.split('\n\n',1)
 prefix=('../../' if rel.startswith('FPGA/') else '')
 write_doc(rel,first+'\n\n2026-10-15最新版本路线：'+summary+f' [本批证据]({prefix}{report_link})、[具体方案]('+('VIVADO-VERSION-PLAN.md' if prefix else plan)+')。下述较早建议保留其当时范围，不再以继续寻找2019.1包为当前恢复任务。\n\n'+rest)

t=read(R/'FPGA/hdmi_candidate/JFM-COMPATIBILITY-REVIEW.md')
t += ('\n\n## 最新用户补充后的2019.1迁移评估\n\n'+summary+
 '\n\n运行库查询28.899712秒/60秒、exit0，只证明读到当前库契约，不是迁移通过。运行时BIDIR和Liberty inout规范化后逐项一致；不能将命名实参数和标量位引脚数量直接相减。两份Liberty公共同名引脚方向无差异，AI缺失由逐项集合比较确认。八项Xlx文件头只作为格式证据，不据此宣称跨版本理论上绝对不可加载；缺少可重建源及正式映射，故没有验证依据去做二进制库移植。\n\n'
 '此前“优先寻找2019.1配套”的建议被用户提供的资料完整性事实和最新执行顺序更新。备用下载已获允许；安装、隔离库替换尚未执行，具体范围与门槛见[VIVADO-VERSION-PLAN.md](VIVADO-VERSION-PLAN.md)。\n')
write_doc('FPGA/hdmi_candidate/JFM-COMPATIBILITY-REVIEW.md',t)

t=read(R/'DIFFICULTIES.md');line=next(x for x in t.splitlines() if x.startswith('| D05 |'))
t=t.replace(line,'| D05 | HDMI实屏时序不支持；完整候选受扩展PS兼容阻塞 | 已确认2019.1缺全部3868个所需AI端口，030ai配套Liberty齐全；普通RTL/IP成果保持 | 八项专有库/器件文件与原生PCPU7绑定仍无完整迁移依据。按用户备用顺序准备2018.3下载，官方入口会话未建立；未安装/改库/PS/AI_Mate/BOOT，完整实现与实屏未验；[版本方案]('+plan+')／[证据]('+report_link+') |')
write_doc('DIFFICULTIES.md',t)

t=read(R/'Done.md');heading='### 工程内容总结\n\n'
t=t.replace(heading,heading+'最新版本兼容评估：'+summary+f' [方案]({plan})、[证据]({report_link})。Windows工作目录D:/FPGACompetitionProject，现有Vivado2019.1，正常库查询28.899712秒/60秒exit0。JFM_Kits原归档1,239,868,855字节/3829条目和关键脚本SHA已核验；公共目录读取与用户确认分别记录。分析脚本的BIDIR/inout规范化和源文件名假设两次失败均保留，仅修正分析器，未重跑失败PS或硬件负载。\n\n',1)
heading='### 对后续开发的参考\n\n'
t=t.replace(heading,heading+'本次补充：可移植RTL/IP、运行时原语契约、专有器件数据库和目标工具绑定分别验证；文件扩展名.v不保证是普通源码，.lib也不保证均为可读Liberty。缺失端口必须按名核对，标量位引脚与向量实参不能直接比总数。下载许可、账户会话、取得安装包、安装和库变更分别记录；迁移尚未通过就保持原系统，不以准备方案代替执行。\n\n',1)
write_doc('Done.md',t)

t=read(R/'ARCHITECTURE-DISCUSSION-20261015.md')
t += ('\n\n## 十五、用户确认资料范围与工具版本优先顺序\n\n'
 '用户确认“官方提供的所有资料已经保存到本地，没有19.1版本的”，随后要求“考虑能否迁移到19.1版本的，实在不行再下载18.3版本的vivado”。停止继续搜索不存在的已提供版本；改为核对现有配套迁移条件，再执行有条件的备用下载。此要求允许备用下载，不将其扩大为已同意安装新工具、全局替库或更改PS/AI_Mate。\n\n'
 +summary+f' 具体可审查方案见[版本方案]({plan})，原始事实与查询见[本批报告]({report_link})。2018.3即使前端成功，仍需独立证明Procise中的扩展PS实际绑定；保持已有板测授权、1080p60目标和旧DATA暂停。\n')
write_doc('ARCHITECTURE-DISCUSSION-20261015.md',t)
new=R/plan;changes.append({'path':plan,'before_sha256':None,'after_sha256':sha(new)})
dump(E/'documentation-revision.json',{'changes':changes,'historical_manifests_not_rewritten':True})
for item in changes:
 dest=E/'after'/item['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/item['path'],dest)

links=[];results=[]
for name in ('indexes','details','reference','install-metadata','implementation'):
 records=json.loads((E/name/'results.json').read_text(encoding='utf-8'));results.extend(records)
 for item in records:
  p=E/name/(str(item['index'])+'.html')
  for href,title in re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>([^<]*)',read(p)):
   links.append({'stage':name,'index':item['index'],'href':html.unescape(href),'title':html.unescape(title)})
dump(E/'all-observed-portal-links.json',links)
dump(E/'portal-read-summary.json',{'successful_index_requests':sum(i.get('status')==200 for i in results),
 'root_read_separate':'portal-fetch-elevated.json','failed_initial_network_read_preserved':'portal-fetch.json',
 'browser_body_reads_timed_out':True,'subsequent_bounded_HTTPS_reads_succeeded':True,
 'user_confirmed_all_provided_material_local':True,'no_further_package_search_after_confirmation':True,
 'third_party_tutorial_links_not_used_as_technical_authority':True,
 'software_binaries_downloaded':False,'outbound_messages_or_account_form_submissions':False})
dump(E/'download-status.json',{'source':'https://www.amd.com/en/support/downloads/adaptive-socs-and-fpgas/development-tools/2018-3.html',
 'official_filename':'Xilinx_Vivado_SDK_2018.3_1207_2324.tar.gz','official_display_size':'18.97 GB',
 'download_form':'https://account.amd.com/en/forms/downloads/xef-vivado.html?filename=Xilinx_Vivado_SDK_2018.3_1207_2324.tar.gz',
 'web_result':'BIG-IP session could not be established; redirected to my.logout.php3?errorcode=19',
 'Codex_browser_open_result':'queued','user_login_or_local_installer_path_requested':True,
 'installer_bytes_acquired':0,'installer_launched':False,'license_or_account_terms_submitted':False,
 'all_local_installer_locations_exhaustively_searched':False,'known_project_material_roots_no_2018_3_installer_found':True,
 'D_free_bytes_last_inventory':309699170304,'installation_disk_or_OS_compatibility_verified':False})

# Verify protected original inputs and the previously accepted RTL; no reruns of passed loads.
original=json.loads((R/'tools/pose-v1/evidence/hdmi-system-20261015-r1/original-manifest.json').read_text())
ref=R/'Docs/26嵌赛开发/fpai_demo_fpga'
bad=[n for n,h in original.items() if sha(ref/n)!=h];assert not bad,bad
old=json.loads((R/'tools/pose-v1/evidence/hdmi-split-20261015-r1/scanout-RTL-identity-consistency.json').read_text())
for item in old:assert sha(R/'FPGA/hdmi_candidate/rtl'/item['source'])==item['current_sha'],item['source']
pairs=json.loads((R/'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/replacement-review.json').read_text())['replacement_pairs']
targets=[]
for pair in pairs:
 p=Path(pair['installed_target']['path']);actual=sha(p);expected=pair['installed_target']['sha256']
 assert actual==expected,str(p)
 targets.append({'path':str(p),'before_sha256':expected,'after_sha256':actual,'equal':True})
dump(E/'baseline-review.json',{'all_297_reference_files_equal':len(original)==297,'nine_scanout_RTL_unchanged':len(old)==9,
 'all_nine_installed_targets_unchanged':True,'installed_targets':targets,
 'board_not_connected_this_batch':True,'BOOT_SDK_model_not_rechecked_on_board_this_batch':True})

(E/'REPORT.md').write_text('''# 30TAI配套迁移到Vivado2019.1的评估与备用下载状态

2026-10-15，Windows，工作目录D:/FPGACompetitionProject。按用户顺序先评估2019.1；用户另确认全部官方资料已本地保存且没有该版本配套。实际结论：常规RTL/IP已有成果保持，但用现有资料不能完成可验证的完整2019.1迁移。不是理论上不可移植的证明，未逆向受保护数据库。

## 已执行与通过标准

现有Vivado2019.1在新目录中只展开输入直连输出的小锚点模块，使标准器件库可查询，未加载或重跑已失败的实际PS。get_lib_cells/get_lib_pins读取到PS7，28.899712秒/60秒预算、exit0；[完整执行](../hdmi-vivado2019-library-20261015-r1/execution.json)、[原始位引脚](../hdmi-vivado2019-library-20261015-r1/builtin-PS7-pins.txt)。通过标准仅为真实库元数据读取并与安装Liberty逐项核对，不是PS综合、迁移、时序或硬件通过。

| 比较项 | 实际结果 |
|---|---|
| 2019.1运行库PS7 | 3305个位引脚，规范化方向后与安装zynq.lib逐项一致 |
| 030ai配套PS7 | 7213个位引脚，公共同名引脚方向无差异 |
| 原PS调用的AI_端口 | 3868个，在运行库全部缺失，在030ai Liberty全部存在 |
| 九项030ai替换源 | 八项Xlx受保护文件头；zynq.lib为可读文本 |
| 原生Procise PCPU7 | 此前实际PS展开失败保持，换前端不能直接证明已解决 |

[逐项名称、方向与格式证据](migration-contract-review.json)。命名实参4527项与位引脚数不是同一计数口径，不能直接比大小；本结论按AI_名称逐项核对。单份Liberty或伪造同名黑盒不能补齐物理资源/时序/位流契约。全库二进制移植无2019.1重建源与正式验证依据，未作为修复执行。此前工程内单文件读取的实际PS失败保留，未自动重跑。

## 本地/官方资料核对及范围修正

原始JFM_Kits.zip实际1,239,868,855字节、3829条目，[归档SHA](local-kit-archive-identity.json)；关键脚本与已解压目录一致，[ZIP关键条目](local-kit-archive-review.json)。本地默认rg会忽略部分归档，本次用明确路径读取，不能因默认检索遗漏就说没有原包。

用户补充之前，已只读获取官方公共索引：Procise目录列出的32494工具与本机相同，索引将完整FPGA教程/源码获取指向企业方；Icraft参考入口亦已读取。索引/搜索看不到兼容包不是全球不存在的证明。用户确认资料完整后停止继续寻找该版本，改为迁移评估。浏览器正文读取超时与初次网络连接失败原样保留；后续在获准限制外执行的正常TLS、固定主机、限时/限大小HTTPS读取成功。原始HTML与[全部链接](all-observed-portal-links.json)保留，未联系企业、登录或提交信息，未将第三方教程作为兼容性技术依据。

## 备用下载及待执行范围

用户已允许无法可靠迁移时下载2018.3。核对[AMD官方归档](https://www.amd.com/en/support/downloads/adaptive-socs-and-fpgas/development-tools/2018-3.html)的完整HLx包18.97 GB；Lab Edition仅编程/调试，不能替代本次前端。官方账户下载入口网页实际返回会话未建立，Codex打开浏览器返回queued；已请求用户登录或告知已有本机安装包路径。[下载状态](download-status.json)。没有取得安装包，没有安装/启动下载器，也未提交账户或许可证表单。

具体下载落点、独立2018.3安装及库修改范围、原2018.3工程恢复、每步通过/停止条件见[版本方案](../../../../..//FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md)。安装/库替换仍是待确认阶段；目前没有工具环境变更。即使2018.3前端通过，仍须闭合30TAI专用网表到Procise的真实PS绑定，FMP100通用迁移脚本不能直接套用。

## 证据保护与停止

本次分析器两次失败分别因BIDIR/inout术语未规范化、误以为补丁源名等于安装目标名，原失败版本和说明保存；修复分析器后仅重新分析已有文本，没有重跑PS或板端负载。生产扫描RTL九份、原参考297文件、2019.1九项安装目标SHA重新核对一致；源码/文档前后值、静态检查与新证据清单另存，不回写旧封存清单。

没有板端连接、候选下载、BOOT/模型/SDK/AI_Mate/PS变更或重启。无完整候选位流；旧DATA仍独立暂停。查询超时/异常则保存并结束进程树，未自动重试；本次实际查询未超时。最终进程盘点与封存结果见completion-review.json。
'''.replace('../../../../..//FPGA','../../../../../FPGA'),encoding='utf-8')

sources=E/'source-snapshots';sources.mkdir(exist_ok=False)
for name in ['read_vendor_portal.py','fetch_vendor_index.py','inspect_2019_ps_library.py','review_2019_migration.py']:
 shutil.copyfile(R/'FPGA/hdmi_candidate/scripts'/name,sources/name)
shutil.copyfile(Path(__file__),E/'finish.py')
print(json.dumps({'documents_updated':len(changes),'baseline_files':len(original),'scanout_RTL':len(old),'global_targets_unchanged':len(targets)},ensure_ascii=True))

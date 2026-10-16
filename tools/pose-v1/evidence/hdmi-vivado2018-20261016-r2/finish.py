from pathlib import Path
import ast,hashlib,json,re,shutil
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2'
def read(p):return p.read_text(encoding='utf-8-sig')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
link='tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/REPORT.md'
flow='FPGA/hdmi_candidate/JFM-FLOW-REVIEW.md'
summary=('用户安装的D:/vivado18.3/Vivado/2018.3已按新授权就地打原版030ai补丁；未复制完整工具。'
 '34文件/63,130,403字节备份SHA通过，九项最终目标匹配厂商源，其余备份文件未变。'
 '真实扩展PS的RTL展开29.826517秒、综合22.396529秒，工具均exit0；全部4527个命名连接/3868个AI连接可绑定，实际EDIF/DCP已生成。'
 'Liberty总数断言失败保留，独立核对证实运行库/实例7212位引脚一致，仅调试元数据表示差异及未调用DEBUGDATA160。'
 '通用转换后Procise导入3.833887秒exit1，PCPU7端口不匹配，已停止未重跑。'
 '本地JFM确有Vivado实现hook＋可选Procise位流后处理，尚未采用；其HARC、速度和DRC影响需讨论。')
changes=[]
def write(rel,t):
 p=R/rel;b=E/'before'/rel
 if p.exists() and rel!=flow:assert b.exists()
 p.write_text(t,encoding='utf-8');changes.append({'path':rel,'before_sha256':sha(b) if b.exists() else None,'after_sha256':sha(p)})
p=R/'PROJECT-PROGRESS.md';head,_,rest=read(p).split('\n\n',2)
t=head+'\n\n更新日期及最后实际验证日期：2026-10-16。'+summary+' 当前无完整候选位流或实屏验收；实现停在原生PS导入失败处，下一步讨论正确实现路径。2019.1/Procise库、BOOT/SDK/模型/PS/AI_Mate及原扫描RTL保持，旧DATA继续暂停。'+f' [完整结果]({link})、[原厂流程与路径取舍]({flow})。\n\n'+rest
line=next(x for x in t.splitlines() if x.startswith('| HDMI |'));t=t.replace(line,'| HDMI | 2018.3已就地030ai补丁，真实PS前端展开/综合通过；原扫描/IP/AXI成果保持 | Procise通用EDIF导入仍失败，原厂混合流程需另议；无完整位流/实屏；[恢复与取舍]('+flow+') |')
t=t.replace('专用前端待验证','已就地030ai补丁、PS前端综合通过')
write('PROJECT-PROGRESS.md',t)
for rel in ['REFERENCES.md','FPGA/hdmi_candidate/RESUME.md','FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md']:
 head,_,rest=read(R/rel).split('\n\n',2);prefix='../../' if rel.startswith('FPGA/') else ''
 t=head+'\n\n2026-10-16当前结果：'+summary+f' [本批证据]({prefix}{link})、[后续实现路径]('+('JFM-FLOW-REVIEW.md' if prefix else flow)+')。当前180秒阶段授权已实际执行，取消完整工具副本方案；原生导入失败后停止实现。以下较早状态保留当时范围。\n\n'+rest
 t=t.replace('新批次拟只作用于完整私有工具副本。保留用户安装、2019.1、自定义PS及AI_Mate身份，超时后未自动恢复。','用户随后取消完整工具副本，授权备份后就地030ai补丁，现已完成；2019.1、自定义PS及AI_Mate身份保持。')
 if rel=='REFERENCES.md':
  line=next(x for x in t.splitlines() if x.startswith('| Vivado 辅助工具/MCP |'));t=t.replace(line,'| Vivado 辅助工具/MCP | D:/vivado18.3/Vivado/2018.3/bin/vivado.bat，64-bit Build2405991；2019.1保留 | 用户安装，16日按授权就地030ai补丁；34文件备份/九目标SHA通过，扩展PS综合通过，Procise导入仍失败；[结果]('+link+') |')
 write(rel,t)
t=read(R/'Done.md');h='### 工程内容总结\n\n'
t=t.replace(h,h+'2026-10-16新授权r2实际结果：'+summary+f' Windows工作目录D:/FPGACompetitionProject，各EDA/转换阶段预算180秒；[完整证据]({link})。先读取原厂过程3.580671秒，再就地补丁6.924940秒；转换0.977310秒且3572处差异仅七类原语名称，随后原生导入失败保存停止。只读hook复核2.767676秒，未调用hook或另改HARC。源码/实际端口/原值/失败/备份及文档修订保留，无板端动作。\n\n以下为此前r1首次安装预检及当时的私有副本提案，已被新授权更新：\n\n',1)
h='### 对后续开发的参考\n\n';t=t.replace(h,h+'r2参考：编译器实际原语/连接契约、Liberty元数据和原生目标宏分开核验；DEBUGDATA命名归一及无连接元数据不应变成修改RTL。cell重命名工具不等同完整SoC网表适配；Procise后处理.bit和原生PCPU7导入是不同职责。厂商hook还可能写额外库文件或改速度/DRC，需读实际函数体及默认配置，不能从工具包名称推断已验证支持。\n\n',1);write('Done.md',t)
t=read(R/'DIFFICULTIES.md');line=next(x for x in t.splitlines() if x.startswith('| D05 |'));t=t.replace(line,'| D05 | HDMI完整候选受Procise扩展PS接入阻塞 | 2018.3就地030ai补丁及真实PS前端展开/综合通过，原始备份与产物齐全 | 通用EDIF导入仍报PCPU7端口不匹配，未重跑；本地原厂混合流程涉及HARC/速度/DRC及工具职责，需另议，无位流或实屏通过；[结果]('+link+')／[流程取舍]('+flow+') |');write('DIFFICULTIES.md',t)
t=read(R/'ARCHITECTURE-DISCUSSION-20261015.md');t+='\n\n## 十七、取消工具复制、授权就地补丁及新结果\n\n2026-10-16用户明确：“不要复制副本，批准放宽超时预算至180秒……直接在当前2018.3中备份关键文件后就地打补丁继续”；随后确认已关闭2018.3 GUI。此授权取代完整工具副本提案，并允许对所给安装就地执行已审查的030ai补丁，不改变BOOT/SDK/PS/AI_Mate。\n\n'+summary+f' [完整证据]({link})。工具目标仍以项目要求为准，未将Vivado前端通过扩展为完整实现或实板通过；原厂混合实现/后处理的采用仍需讨论，见[路径取舍]({flow})。\n';write('ARCHITECTURE-DISCUSSION-20261015.md',t)
t=read(R/'FPGA/hdmi_candidate/JFM-COMPATIBILITY-REVIEW.md');t+='\n\n## 2026-10-16就地补丁及真实PS前端结果\n\n'+summary+' 用户新授权取代完整工具副本提案；目前该2018.3安装处于030ai专用补丁状态，原文件备份可核验。前端已解决原先AI端口不识别，但原生工具接入尚未解决。[结果](../../'+link+')、[完整原厂流程复核](JFM-FLOW-REVIEW.md)。\n';write('FPGA/hdmi_candidate/JFM-COMPATIBILITY-REVIEW.md',t)
p=R/'FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md';head,_,rest=read(p).split('\n\n',2)
t=head+'\n\n2026-10-16最新授权与实际结果：'+summary+' 用户明确取消完整工具复制，允许在现安装备份后就地补丁，各本批阶段180秒。此前“待确认私有副本/不修改安装”及900秒复制提案均已被此新要求取代，不执行。当前应从[JFM-FLOW-REVIEW.md](JFM-FLOW-REVIEW.md)讨论原生导入阻塞与实现职责，而非重跑失败网表。以下首次预检和15日方案仅为历史依据。\n\n'+rest
write('FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md',t)
changes.append({'path':flow,'before_sha256':None,'after_sha256':sha(R/flow)})
dump(E/'documentation-revision.json',{'changes':changes,'old_manifests_not_rewritten':True})
for x in changes:
 p=E/'after'/x['path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/x['path'],p)

# Protect all original inputs and verify the intended installation changes exactly.
old=json.loads(read(R/'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/replacement-review.json'))
for pair in old['replacement_pairs']:assert sha(Path(pair['installed_target']['path']))==pair['installed_target']['sha256']
patch=json.loads(read(E/'patch-review.json'));assert patch['all_nine_equal_vendor_patch'] and len(patch['changed_backed_up_files'])==9
backup=json.loads(read(E/'backup-manifest.json'))
expected={x['relative']:x['after'] for x in patch['changed_backed_up_files']}
for x in backup['targets']:
 if 'sha256' in x:
  assert sha(E/'backup'/x['relative'])==x['sha256']
  assert sha(Path(backup['root'])/x['relative'])==expected.get(x['relative'],x['sha256'])
orig=json.loads(read(R/'tools/pose-v1/evidence/hdmi-system-20261015-r1/original-manifest.json'))
for n,h in orig.items():assert sha(R/'Docs/26嵌赛开发/fpai_demo_fpga'/n)==h
rtl=json.loads(read(R/'tools/pose-v1/evidence/hdmi-split-20261015-r1/scanout-RTL-identity-consistency.json'))
for x in rtl:assert sha(R/'FPGA/hdmi_candidate/rtl'/x['source'])==x['current_sha']
dump(E/'baseline-review.json',{'original_reference_unchanged':297,'scanout_RTL_unchanged':9,
 '2019_1_targets_unchanged':9,'2018_3_changed_files':9,'remaining_backup_files_unchanged':25,
 'backup_bytes':63130403,'board_not_connected':True,'HARC_and_hooks_not_changed_or_invoked':True})
dump(E/'rollback-plan.json',{'not_executed':True,'installation_root':backup['root'],
 'restore_only_after_verifying_current_post_patch_identity':True,
 'changed_files':[{'relative':x['relative'],'current_sha256':x['after'],
 'backup':str(E/'backup'/x['relative']),'restore_sha256':x['before']} for x in patch['changed_backed_up_files']]})
dump(E/'postprocessor-count-failure.json',{'script':'validate_vivado2018_ps.v1.py','driver_exit':1,'EDA_exit':0,
 'assertion':'runtime pin count == 7213','actual':7212,'earlier_failure_preserved':True,
 'resolved_by_offline_actual_connection_and_direction_review':True,'RTL_not_rerun':True})

(E/'REPORT.md').write_text('''# Vivado2018.3就地030ai补丁、扩展PS前端与Procise接入

2026-10-16，Windows，工作目录D:/FPGACompetitionProject。用户明确取消完整工具复制，批准180秒新批次，并授权当前2018.3备份后就地补丁；用户关闭GUI后核对无占用。旧r1的60秒超时保持，不回写为通过。

## 实际结果

| 阶段 | 实际耗时 | 结果与范围 |
|---|---:|---|
| 备份/原厂过程读取 | 过程3.580671秒 | 34文件63,130,403字节，备份SHA一致 |
| 原版replace_7z030ai_file 0 | 6.924940秒 | exit0；精确文件写入守卫，最终九目标全部等于030ai源 |
| 真实扩展PS RTL展开 | 29.826517秒 | 工具exit0；旧后处理总数断言exit1另保留 |
| 连接契约独立复核 | 仅读原输出 | 全4527命名连接/3868 AI存在，实际实例/运行库7212位引脚名称方向一致 |
| 真实扩展PS综合 | 22.396529秒 | exit0，实际EDIF/DCP及利用率报告生成；PS7硬原语1，不是人工黑盒 |
| 现有translate_file转换 | 0.977310秒 | exit0，3572处差异仅7组原语名称替换，所有端口/连接/参数保持 |
| Procise转换网表导入 | 3.833887秒 | exit1，PCPU7接口不匹配，保存停止未重跑 |
| 原厂hook定义读取 | 2.767676秒 | 只读exit0，未调用hook/后处理 |

所有实际EDA/转换阶段上限180秒，本批无超时。已批准的RTL仿真预算保持，未新增像素负载。当前2018.3为030ai专用补丁环境，原版关键文件在[备份清单](backup-manifest.json)，[实际九项变化](patch-review.json)、[回退对象](rollback-plan.json)可核验；未复制完整工具，未自动回退。原参考297文件、九扫描RTL与2019.1九项库文件SHA保持。

真实PS沿用原已保存七份包装/依赖的SHA，不升级自定义PS，不改变AI_Mate。原代码读入后识别一个真实PS7硬原语并综合出[EDIF](actual-ps-synth/actual_ps.edf)与[DCP](actual-ps-synth/actual_ps.dcp)。后处理最初把Liberty7213总数当运行库总数，断言失败保留；独立检查实际连接后闭合：39处DEBUGDATA命名形式差异及Liberty独有、未被调用的DEBUGDATA160，IN/OUT/INOUT与input/output/bidir按语义规范化。没有为此改RTL或厂商源，也没有重跑RTL。[实际连接复核](actual-ps-rtl/connected-contract-review.json)。

## Procise的真实停止点

通用转换工具只完成PS7→PCPU7等名称替换。转换前后100387行，3572处差异全部为cell/cellref名；[完整线性对照](translate-ps/linear-diff.json)、[语义审查](translate-ps/conversion-contract-review.json)保留。全文difflib后处理较慢但最终自然完成，没有重跑转换。

新网表送入Procise2025.1.1temp/SVN32494、JFMQL30TAI676H的post-elaborate，实际报3981条IO-0134、63个不同的PCPU7缺失端口及DM-0047/IO-0168，含DDRARB和AXI接口；[全部错误与命名](procise-ps-import/failure-analysis.json)、[原stdout](procise-ps-import/stdout.txt)。内部错误数不是缺失AI端口数，不能推断硬件没有AI。此失败没有重跑，也没有删端口或伪造普通PS/黑盒。无完整实现/时序/位流或板端下载。

## 本地流程已查到的新依据

原厂包确有Vivado综合/实现/位流hook及可选Procise increment_bit_cfg_v3后处理，并非只有通用EDIF迁移。只读[真实函数体](flow-reading/hook-definitions.txt)和原process_control脚本已核对：add_hook还会覆盖HARC.cfg，change_speed默认TRUE，030AI分支会禁用若干REQP检查；随包位流配置却默认JFM7K325T8/sw_ctrl_led，不能直接套30TAI。它改变实现工具职责及额外配置，尚未调用或采用。

后续需要讨论原生Procise PS宏接入与原厂混合流程的选择，详见[具体依据/影响](../../../../FPGA/hdmi_candidate/JFM-FLOW-REVIEW.md)。不把前端通过推广为完整系统验收，不自动替换实现后端或复制默认配置；BOOT/SDK/模型/RAW/PS/AI_Mate保持，旧DATA调查仍暂停。

Common17-741本地TclStore路径告警、补丁恢复过程的fmsh-2023提示和独立PS无完整约束的WARN均保留，未静默删除。前端综合只做接口/资源门检，不作STA签核。修复监控的清理异常落盘路径已静态检查，本批实际无清理超时；所有源码、命令、输入身份、原始结果、文档前后值及清单保留。最终进程盘点/封存见completion-review.json。
''',encoding='utf-8')
snap=E/'source-snapshots';snap.mkdir(exist_ok=False)
for n in ['vivado2018_support.py','prepare_vivado2018_inplace.py','patch_vivado2018_inplace.py','validate_vivado2018_ps.py','review_vivado2018_ps_contract.py','probe_translate_file.py','translate_vivado2018_ps.py','import_vivado2018_ps_procise.py','inspect_jfm_flow.py']:
 shutil.copyfile(R/'FPGA/hdmi_candidate/scripts'/n,snap/n)
inputs=E/'frozen-PS-inputs';inputs.mkdir()
for p in (R/'.local/hdmi-native-ps-20261015-r1').glob('*.v'):shutil.copyfile(p,inputs/p.name)
hooks=E/'vendor-flow-sources';hooks.mkdir()
kit=R/'Docs/26嵌赛开发/JFM_Kits/JFM_Kits/ip_patch'
shutil.copytree(kit/'process_control',hooks/'process_control')
shutil.copyfile(kit/'procise_incr_cfg.txt',hooks/'procise_incr_cfg.txt')
shutil.copyfile(kit/'all_src_files.tcl',hooks/'all_src_files.tcl')
shutil.copyfile(Path(__file__),E/'finish.py')
print(json.dumps({'documents':len(changes),'backups':34,'patch_targets':9,'PS_frontend_synth_pass':True,'Procise_import_pass':False}))

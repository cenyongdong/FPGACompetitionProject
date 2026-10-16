from pathlib import Path
import ast,hashlib,json,re,shutil,struct
R=Path('D:/FPGACompetitionProject');E=R/'tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1';W=R/'.local/hdmi-jfm-route2-20261016-r1'
assert not (E/'files.sha256.json').exists(),'Already sealed'
def read(p):return p.read_text(encoding='utf-8-sig')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def redact(text):return re.sub(r'(密码\s*[:：]\s*)[^，。\s]+',r'\1<REDACTED>',text)

# Protect all frozen inputs; never repair an old SHA or completion file.
orig=json.loads(read(R/'tools/pose-v1/evidence/hdmi-system-20261015-r1/original-manifest.json'))
for n,h in orig.items():assert sha(R/'Docs/26嵌赛开发/fpai_demo_fpga'/n)==h,n
rtl=json.loads(read(R/'tools/pose-v1/evidence/hdmi-split-20261015-r1/scanout-RTL-identity-consistency.json'))
for x in rtl:assert sha(R/'FPGA/hdmi_candidate/rtl'/x['source'])==x['current_sha']
prior=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2'
patch=json.loads(read(prior/'patch-review.json'));expected={x['relative']:x['actual_sha256'] for x in patch['targets']}
backup=json.loads(read(prior/'backup-manifest.json'))
for x in backup['targets']:
 if 'sha256' in x:assert sha(Path(backup['root'])/x['relative'])==expected.get(x['relative'],x['sha256'])
old=json.loads(read(R/'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/replacement-review.json'))
for x in old['replacement_pairs']:assert sha(Path(x['installed_target']['path']))==x['installed_target']['sha256']
harc=json.loads(read(E/'HARC-readonly-review.json'))
assert sha(Path(harc['target']))==harc['target_sha256']==sha(Path(harc['source']))
lib=json.loads(read(E/'IP-library-readonly-inventory.json'))
for x in lib['targets']:
 assert sha(Path('D:/vivado18.3/Vivado/2018.3')/x['relative'])==x['target_sha256']
 assert sha(Path(x['source']))==x['source_sha256']
dump(E/'baseline-review.json',{'original_reference_unchanged':len(orig),'scanout_RTL_unchanged':len(rtl),
 '2019_targets_unchanged':len(old['replacement_pairs']),'2018_prior_34_target_states_unchanged':True,
 'HARC_same_as_vendor_and_before':True,'32_extra_IP_library_targets_not_written':True,
 'board_not_connected':True,'BOOT_not_written':True,'old_DATA_not_resumed':True})

# Snapshot executable inputs separately from generated future hook text.
snaps=E/'source-snapshots';snaps.mkdir(exist_ok=False)
names=['vivado2018_support.py','audit_jfm_route2.py','prepare_jfm_route2_project.py','preview_jfm_route2_hooks.py',
 'verify_jfm_route2_preview.py','query_route2_procise.py','validate_jfm_route2_mig_ooc.py',
 'check_jfm_route2_after_mig.py','inventory_jfm_route2_library.py','document_jfm_route2.py']
for name in names:shutil.copyfile(R/'FPGA/hdmi_candidate/scripts'/name,snaps/name)
hooks=E/'generated-future-hooks-NOT-executed';shutil.copytree(W/'reference/ip_patch/process_control',hooks)
config=E/'configured-project';config.mkdir()
shutil.copyfile(W/'reference/fpai_demo_vivado.xpr',config/'fpai_demo_vivado.xpr')
shutil.copyfile(W/'reference/ip_patch/all_src_files.tcl',config/'all_src_files.tcl')
dump(config/'identity.json',{'factory_protected_script_SHA':sha(config/'all_src_files.tcl'),
 'six_hook_files':{p.name:sha(p) for p in hooks.glob('*.tcl')},'hook_execution':False,
 'hook_profile':'xfft_modify FALSE; change_speed FALSE; disable_icap TRUE; device 0',
 'formal_build_profile_accepted':False})

# Independently parse only the factory reference bit header; no bit modification.
p=R/'Docs/26嵌赛开发/BOOT_Gen/ai7030_edif_top.bit';data=p.read_bytes();pos=0
def short():
 global pos
 n=struct.unpack_from('>H',data,pos)[0];pos+=2;return n
n=short();pos+=n;assert short()==1
fields={}
for key in b'abcd':
 assert data[pos]==key;pos+=1;n=short();fields[chr(key)]=data[pos:pos+n].rstrip(b'\0').decode('ascii');pos+=n
assert data[pos]==ord('e');pos+=1;payload=struct.unpack_from('>I',data,pos)[0];pos+=4
assert pos+payload==len(data)
dump(E/'factory-reference-bit-header.json',{'source':str(p),'sha256':sha(p),'header_fields':fields,
 'payload_bytes':payload,'total_bytes':len(data),'factory_reference_only':True,'new_candidate':False,'current_BOOT_partition_identity_proven':False})

dump(E/'scope.json',{'date':'2026-10-16','host':'Windows','work':str(W),
 'tool':'D:/vivado18.3/Vivado/2018.3','Procise':'C:/FudanMicro/Procise',
 'authorized':'Route 2 audit plus existing same-configuration IP rebuild; autonomous bounded timeout decisions',
 'initial_stage_seconds':180,'MIG_actual_adjustment_seconds':[180,360],
 'no_tool_directory_clone':True,'no_new_installation_write':True,
 'not_executed':['top synthesis/implementation hooks','extra IP library patch','speed replacement','DRC waiver','real bit postprocess','BOOT build/change','download/reboot','old DATA investigation']})

report='''# 原厂 Vivado＋JFM／Procise 路径二审查结果

2026-10-16，Windows，工作目录D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1。用户批准审查原厂混合路径并更新超时规则；同配置IP重建授权继续有效。原参考工程297份逐项SHA恢复到隔离目录；只复制工程和必要JFM资料，没有复制Vivado工具目录。本机2018.3沿用上一批030ai九项补丁，本批无新增安装写入。

## 实际执行与通过标准

| 阶段 | 实际用时/退出 | 结果与范围 |
|---|---|---|
| 原厂参数/DRC定义查询 | 10.400216秒/0 | 正常加载原厂受保护过程，只读查询四项DRC |
| 原始工程状态 | 16.263756秒/0 | 28项IP未锁定，无修订升级；缓存/OOC属性分别核对 |
| 隔离hook配置预览 | 13.030318秒/1 | add_hook已返回；驱动错误调用save_project导致17-163，原失败保留 |
| 独立重开/后处理预览 | 9.376277秒/0 | 六项hook实际落盘；29份XCI/BD SHA当时不变；exec被拦截，无输出bit |
| Procise命令查询 | 0.290259秒/0 | 存在increment_bit_cfg_v3及BOOT命令；无实际输入位流处理 |
| 同配置MIG OOC | 262.133509秒/0 | 实际DCP、完整日志和资源报告生成；XCI非运行时配置/DDR PRJ字节通过 |
| MIG后原厂前置检查 | 9.815504秒/0 | pre_patch_check返回0，没有执行顶层hook或位流生成 |

阶段原始结果与命令分别在对应目录的execution.json、stage.tcl/build.tcl、stdout/stderr/vivado.log；MIG完整子运行日志、utilization及实际DCP均已保存。通过依据为真实退出码、产物及配置契约，脚本准备或工具stdout提示不替代执行。

## 保留的错误和自主超时判断

[配置驱动首次原值](hook-preview/)的save_project错误不是超时。原add_hook未重跑；修正未来驱动后仅独立重开确认绑定，修正版本并未重新执行。首次[前置检查](post-command-preview/post-command-preview.txt)报告MIG缺少OOC，随后单独完成原配置MIG综合，[再次原厂门检](precheck-after-mig/precheck.txt)通过；不回写首次失败。

MIG初始180秒门限到达时仍有新日志、未见ERROR，按用户新规则有界延至360秒，继续原进程至262.133509秒成功，没有重启或重复负载。[预算判断](mig-ooc/timeout-decisions.json)、[进程祖先链](process-ancestry-snapshot.json)、[资源快照](runtime-resource-snapshot.json)保留。资源快照的direct-path owned_by_this_batch布尔值只是初筛，不能识别相对路径子进程；后续祖先链证实四个Vivado进程均属本批。MIG最终exit0，未触发最终超时终止；历史超时记录不改。

前提及停止条件：只运行同配置MIG OOC，maxThreads=2、jobs=1；门限到达依据进展决定继续，预算上界540秒，实际只调整一次至360秒。无进展、错误或资源问题停止并取证；确认的参数/身份变化、OOM/逻辑故障不因新超时授权而放行。最终EDA进程盘点为空，无板端连接或后台工作。

## 实现职责与尚待确定的构建配置

实际链路为原始2018.3 IP/OOC→Vivado＋JFM实现/bit→30TAI专用ICAP的Procise后处理→核对后的BOOT打包。通用PS7→PCPU7导入旧失败不再作为该链路必经步骤，但保留其全部证据。

[32项全局IP库只读清单](IP-library-readonly-inventory.json)的源/目标均存在且32项全部不同。-xfft_modify默认TRUE并非只改FFT，还含本工程确有的counter，故审查用FALSE不代表已证明可省略。HARC安装与原厂源同SHA并跳过复制；-change_speed审查用FALSE。REQP-44/46/52/56实际均启用、Error级，针对GTHE2/GTXE2的GTGREFCLK；生成的未来脚本有关闭分支，但本批未执行，不是HDMI时序/CDC豁免。

实际ICAP分支device=0按xc7z030推导JFMQL30TAI676H；[原厂生成命令](post-command-preview/procise_run_disable_icap.tcl)保留，exec在[预览日志](post-command-preview/post-command-preview.txt)中明确SUPPRESSED。没有生成_disable_icap.bit，厂商“runs success”不能算真实后处理通过。原工程根不存在procise_incr_cfg.txt，不套包中的K325流水灯示例。

原脚本引擎5.3.1.8与包标签5.3.2.1_100AI_LV分别记录；没有据此擅自换包。BOOT_Gen五份输入[SHA/ELF身份](BOOT-Gen-input-identities.json)及[参考bit头](factory-reference-bit-header.json)已保存，不等同现用BOOT分区身份，原BIF旧路径与apu_x32文本未自行改动。

## 交付、限制与恢复

[参数、影响及正式构建范围](../../../../FPGA/hdmi_candidate/ROUTE2-AUDIT.md)已明确。32项全局IP库替换及4项GT规则处理需要确定具体范围后才能采用正式配置；本批不将审查授权扩展为额外库替换或DRC豁免。尚无顶层完整位流、STA/CDC或实屏验收；BOOT/SDK/模型/PS/AI_Mate不改，旧DATA继续暂停，无下载或重启。

原始297份参考、9份扫描RTL、2019九项目标、既有2018补丁及其余备份目标状态复核通过，见baseline-review.json。Agents已落实超时自主判断，保留取证、原值、范围控制和其它故障停止要求。文档修改前后SHA独立记录，Agents快照隐去认证口令，原文SHA与脱敏快照SHA分开；历史完成清单不回写。所有新证据另作SHA封存。
'''
(E/'REPORT.md').write_text(report,encoding='utf-8')

# Before/after identities describe working files; credential-redacted snapshots are explicit.
after=E/'after';after.mkdir(exist_ok=False);changes=[]
for before in sorted((E/'before').rglob('*')):
 if not before.is_file():continue
 rel=before.relative_to(E/'before');p=R/rel;dest=after/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 special=rel.as_posix()=='Agents.md'
 if special:dest.write_text(redact(read(p)),encoding='utf-8')
 else:shutil.copyfile(p,dest)
 bsha=json.loads(read(E/'Agents-before-snapshot-identity.json'))['original_before_sha256'] if special else sha(before)
 changes.append({'path':rel.as_posix(),'before_working_sha256':bsha,'after_working_sha256':sha(p),
  'before_snapshot_sha256':sha(before),'after_snapshot_sha256':sha(dest),'snapshots_redacted':special})
rel='FPGA/hdmi_candidate/ROUTE2-AUDIT.md';dest=after/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/rel,dest)
changes.append({'path':rel,'before_working_sha256':None,'after_working_sha256':sha(R/rel),'after_snapshot_sha256':sha(dest),'snapshots_redacted':False})
dump(E/'documentation-revision.json',{'changes':changes,'earlier_manifests_not_rewritten':True,'Agents_original_and_redacted_SHA_distinguished':True})

def links(t):return {a or b for a,b in re.findall(r'\]\((?:<([^>]+)>|([^\n)]+))\)',t)}
new=[];inherited=[]
for x in changes:
 p=R/x['path'];assert sha(p)==x['after_working_sha256']
 oldp=E/'before'/x['path'];old=links(read(oldp)) if oldp.exists() else set()
 for target in links(read(p)):
  if '://' in target or target.startswith('#'):continue
  if not (p.parent/target.split('#')[0]).exists():
   (inherited if target in old else new).append({'path':x['path'],'target':target})
for target in links(report):
 if '://' not in target and not target.startswith('#') and not (E/target.split('#')[0]).exists():new.append({'path':'REPORT.md','target':target})
assert not new,new
scripts=list((R/'FPGA/hdmi_candidate/scripts').glob('*.py'))
for p in scripts+[Path(__file__)]:ast.parse(read(p),filename=str(p))
for name in ['parameters-drc','project-status','post-command-preview','procise-command-review','mig-ooc','precheck-after-mig']:
 x=json.loads(read(E/name/'execution.json'));assert x['exit']==0 and not x.get('timeout',False),name
assert json.loads(read(E/'hook-preview/execution.json'))['exit']==1
assert json.loads(read(E/'final-process-inventory.json'))['count']==0
dump(E/'static-review.json',{'Python_AST_pass':True,'script_count':len(scripts),'new_broken_links':new,
 'historical_broken_links_preserved':inherited,'working_document_SHA_verified':True,
 'original_hook_wrapper_failure_preserved':True,'first_MIG_precheck_failure_preserved':True})
dump(E/'completion-review.json',{'route2_audit_completed':True,'28_original_IPs_unlocked':True,'MIG_OOC_exit':0,
 'MIG_seconds':262.13350860000355,'MIG_initial_budget':180,'MIG_final_budget':360,
 'autonomous_timeout_continued_original_process':True,'MIG_configuration_contract_pass':True,
 'factory_precheck_after_MIG_pass':True,'hook_configuration_wrapper_original_exit':1,
 'independent_hook_persistence_review_pass':True,'library_extra_writes':False,'DRC_waiver_executed':False,
 'bit_postprocess_executed':False,'complete_candidate_or_hardware_pass':False,'BOOT_changed':False,
 'old_DATA_resumed':False,'EDA_processes_remaining':0,'documents':len(changes),
 'next_configuration_scope':'32 global IP library files and four factory GT DRC checks, per ROUTE2-AUDIT.md'})
manifest={p.relative_to(E).as_posix():sha(p) for p in E.rglob('*') if p.is_file()}
dump(E/'files.sha256.json',manifest)
for n,h in manifest.items():assert sha(E/n)==h,n
print(json.dumps({'sealed_files':len(manifest),'all_SHA_verified':True,'documents':len(changes),
 'AST_scripts':len(scripts),'new_broken_links':len(new),'historical_broken_links':len(inherited),'EDA_processes_remaining':0}))

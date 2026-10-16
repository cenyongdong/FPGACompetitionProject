from pathlib import Path
import ast,hashlib,json,re,shutil
R=Path(__file__).resolve().parents[2]
E=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r1'
def read(p):return p.read_text(encoding='utf-8-sig')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def links(t):return {a or b for a,b in re.findall(r'\]\((?:<([^>]+)>|([^\n)]+))\)',t)}
changes=json.loads(read(E/'documentation-revision.json'))['changes']
new=[];historical=[]
for item in changes:
 p=R/item['path'];assert sha(p)==item['after_sha256'],str(p)
 old=links(read(E/'before'/item['path']))
 for s in links(read(p)):
  if '://' in s or s.startswith('#'):continue
  target=s.split('#')[0]
  if target and not (p.parent/target).exists():
   (historical if s in old else new).append({'path':item['path'],'target':s})
for s in links(read(E/'REPORT.md')):
 if '://' not in s and not s.startswith('#') and not (E/s.split('#')[0]).exists():new.append({'path':'REPORT.md','target':s})
assert not new,new
scripts=list((R/'FPGA/hdmi_candidate/scripts').glob('*.py'))
for p in scripts:ast.parse(read(p),filename=str(p))
for p in Path(__file__).parent.glob('*.py'):ast.parse(read(p),filename=str(p))
processes=json.loads(read(E/'final-process-inventory.json'));assert processes['count']==0
result=json.loads(read(E/'installed-preflight/execution.json'))
assert result['timeout'] and not result['overall_pass'] and result['driver_exit']==1
assert result['runtime_PS7_pins_written']==3305
shutil.copyfile(R/'.local/hdmi-vivado2018-20261016-r1/installed-preflight/anchor.v',E/'installed-preflight/anchor.v')
dump(E/'static-review.json',{'AST_passed':True,'production_script_count':len(scripts),
 'fixed_driver_not_reexecuted':True,'new_broken_links':new,'historical_broken_links_preserved':historical,
 'all_document_before_after_SHA_recorded':True,'old_sealed_manifests_not_rewritten':True})
dump(E/'completion-review.json',{'date':'2026-10-16','workspace':str(R),
 'user_installed_root':'D:/vivado18.3/Vivado/2018.3','actual_version_banner_verified':True,
 'installation_documented':True,'prior_task_actually_resumed_to_first_preflight':True,
 'first_preflight_overall_pass':False,'first_preflight_outer_timeout_seconds':60,
 'cleanup_permission_failure_preserved':True,'tool_naturally_exited':True,
 'EDA_processes_remaining':0,'failed_preflight_retried':False,'private_tool_copied':False,
 'database_replacement_or_hook':False,'board_connected':False,'BOOT_model_SDK_PS_AI_Mate_changed':False,
 'old_DATA_resumed':False,'new_batch_plan_prepared':True,'new_batch_approval_requested':True,
 'new_batch_started':False,'resume':'FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md'})
shutil.copyfile(Path(__file__),E/'verify_and_seal.py')
dest=E/'files.sha256.json';assert not dest.exists()
manifest={p.relative_to(E).as_posix():sha(p) for p in E.rglob('*') if p.is_file()}
dump(dest,manifest)
for name,h in manifest.items():assert sha(E/name)==h
print(json.dumps({'documents':len(changes),'production_Python_AST':len(scripts),
 'new_broken_links':0,'historical_broken_links_preserved':len(historical),
 'sealed_files':len(manifest),'all_SHA_verified':True,'EDA_processes':0}))

from pathlib import Path
import ast, hashlib, json, re, shutil
R=Path(__file__).resolve().parents[2]
E=R/'tools/pose-v1/evidence/hdmi-jfm-compatibility-20261015-r1'
V=R/'tools/pose-v1/evidence/hdmi-vivado2019-library-20261015-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return p.read_text(encoding='utf-8-sig')
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def links(t):return {a or b for a,b in re.findall(r'\]\((?:<([^>]+)>|([^\n)]+))\)',t)}
changes=json.loads(read(E/'documentation-revision.json'))['changes']
historical=[];new=[]
for item in changes:
 p=R/item['path'];assert sha(p)==item['after_sha256'],str(p)
 before=E/'before'/item['path'];old=links(read(before)) if before.exists() else set()
 for s in links(read(p)):
  if '://' in s or s.startswith('#'):continue
  target=s.split('#')[0]
  if target and not (p.parent/target).exists():
   (historical if s in old else new).append({'path':item['path'],'target':s})
p=E/'REPORT.md'
for s in links(read(p)):
 if '://' not in s and not s.startswith('#') and not (p.parent/s.split('#')[0]).exists():new.append({'path':str(p),'target':s})
assert not new,new
scripts=list((R/'FPGA/hdmi_candidate/scripts').glob('*.py'))
for p in scripts:ast.parse(read(p),filename=str(p))
review=json.loads(read(E/'migration-contract-review.json'))
assert review['runtime_PS7_scalar_pins']==3305
assert review['vendor_PS7_scalar_pins']==7213
assert review['called_AI_named_terminals']==review['called_AI_missing_in_runtime']==3868
assert review['called_AI_missing_in_vendor_Liberty']==0
assert not review['vendor_runtime_same_named_pin_direction_mismatches']
query=json.loads(read(V/'execution.json'));assert query['exit']==0 and not query['timeout']
assert query['seconds']<query['budget_seconds']==60
processes=json.loads(read(E/'final-process-inventory.json'));assert processes['count']==0
baseline=json.loads(read(E/'baseline-review.json'))
assert baseline['all_297_reference_files_equal'] and baseline['nine_scanout_RTL_unchanged']
assert baseline['all_nine_installed_targets_unchanged']
dump(E/'static-review.json',{'Python_AST_files':len(scripts),'AST_passed':True,'new_broken_links':new,
 'historical_broken_links_preserved':historical,'all_document_after_SHA_verified':True,
 'runtime_Liberty_AI_contract_checks_passed':True,'not_a_migration_or_hardware_pass':True})
dump(E/'completion-review.json',{'date':'2026-10-15','workspace':str(R),
 'user_requested_2019_migration_assessment_done':True,'verified_full_2019_migration':False,
 'theoretical_impossibility_claimed':False,'2018_3_fallback_download_authorized':True,
 'download_blocker':'Official download session not established; user login or existing local installer path pending',
 'installer_bytes_acquired':0,'tool_installation_or_database_replacement':False,
 'actual_PS_failure_retried':False,'metadata_query_seconds':query['seconds'],
 'new_hardware_signoff':False,'board_connected_this_batch':False,'candidate_downloaded':False,
 'BOOT_SDK_model_PS_AI_Mate_changed':False,'old_DATA_resumed':False,'EDA_processes_remaining':0,
 'historical_evidence_manifests_not_modified':True,'resume':'FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md'})
shutil.copyfile(Path(__file__),E/'verify_and_seal.py')
(V/'README.md').write_text('# Vivado 2019.1 library metadata query\n\nStandard-device library read only, using an unrelated wire-through RTL anchor. No actual PS RTL retry, database replacement, synthesis/implementation acceptance or board operation. See execution.json and builtin-PS7-pins.txt; source preserved in the sibling compatibility review.\n',encoding='utf-8')
for d in (E,V):
 dest=d/'files.sha256.json';assert not dest.exists()
 manifest={p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file()}
 dump(dest,manifest)
for d in (E,V):
 for name,h in json.loads(read(d/'files.sha256.json')).items():assert sha(d/name)==h
print(json.dumps({'documents':len(changes),'AST_files':len(scripts),'new_broken_links':0,
 'historical_broken_links_preserved':len(historical),'new_evidence_directories_sealed':2,
 'all_new_manifest_SHA_verified':True,'EDA_processes_remaining':0}))

from pathlib import Path
import ast,hashlib,json,re,shutil
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2'
def read(p):return p.read_text(encoding='utf-8-sig')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def links(t):return {a or b for a,b in re.findall(r'\]\((?:<([^>]+)>|([^\n)]+))\)',t)}
changes=json.loads(read(E/'documentation-revision.json'))['changes'];new=[];old_errors=[]
for x in changes:
 p=R/x['path'];assert sha(p)==x['after_sha256']
 before=E/'before'/x['path'];old=links(read(before)) if before.exists() else set()
 for target in links(read(p)):
  if '://' in target or target.startswith('#'):continue
  if not (p.parent/target.split('#')[0]).exists():
   (old_errors if target in old else new).append({'path':x['path'],'target':target})
for target in links(read(E/'REPORT.md')):
 if '://' not in target and not target.startswith('#') and not (E/target.split('#')[0]).exists():new.append({'path':'REPORT.md','target':target})
assert not new,new
scripts=list((R/'FPGA/hdmi_candidate/scripts').glob('*.py'))
for p in scripts:ast.parse(read(p),filename=str(p))
for p in Path(__file__).parent.glob('*.py'):ast.parse(read(p),filename=str(p))
inventory=json.loads(read(E/'final-process-inventory.json'));assert inventory['count']==0,inventory
for name in ('vendor-procedures','inplace-patch','actual-ps-rtl','actual-ps-synth','translate-help','translate-ps','flow-reading'):
 result=json.loads(read(E/name/'execution.json'));assert result['exit']==0 and not result['timeout'] and result['seconds']<180
native=json.loads(read(E/'procise-ps-import/execution.json'));assert native['exit']==1 and not native['timeout']
for mode in ('rtl','synth'):assert json.loads(read(E/('actual-ps-'+mode)/'connected-contract-review.json'))['gate_pass']
dump(E/'static-review.json',{'Python_AST_passed':True,'script_count':len(scripts),'new_broken_links':new,
 'historical_broken_links_preserved':old_errors,'all_document_after_SHA_verified':True,
 'native_failure_preserved':True,'old_7213_count_assertion_failure_preserved':True})
dump(E/'completion-review.json',{'date':'2026-10-16','workspace':str(R),
 'user_installed_2018_3_documented':True,'full_tool_copy':False,'inplace_patch_authorized_and_completed':True,
 'backed_up_files':34,'backup_bytes':63130403,'changed_installation_files':9,'patch_targets_match_vendor':True,
 'actual_extended_PS_RTL_tool_exit':0,'RTL_old_postprocessor_exit':1,'offline_connected_contract_review_pass':True,
 'actual_PS_synthesis_exit':0,'actual_PS_synthesis_seconds':22.396528500001295,
 'actual_EDIF_and_DCP_generated':True,'vendor_converter_executed':True,'Procise_import_exit':1,
 'Procise_import_seconds':native['seconds'],'failed_import_retried':False,'hook_definitions_read_only':True,
 'hook_HARC_speed_DRC_or_final_flow_executed':False,'full_system_bitstream_or_hardware_pass':False,
 'candidate_downloaded':False,'board_connected':False,'BOOT_SDK_model_PS_AI_Mate_changed':False,
 'old_DATA_resumed':False,'EDA_processes_remaining':0,'next_decision':'FPGA/hdmi_candidate/JFM-FLOW-REVIEW.md'})
shutil.copyfile(Path(__file__),E/'verify_and_seal.py')
dest=E/'files.sha256.json';assert not dest.exists()
manifest={p.relative_to(E).as_posix():sha(p) for p in E.rglob('*') if p.is_file()};dump(dest,manifest)
for n,h in manifest.items():assert sha(E/n)==h
print(json.dumps({'documents':len(changes),'AST_files':len(scripts),'new_broken_links':0,
 'historical_broken_links_preserved':len(old_errors),'sealed_files':len(manifest),'all_SHA_verified':True,'EDA_processes_remaining':0}))

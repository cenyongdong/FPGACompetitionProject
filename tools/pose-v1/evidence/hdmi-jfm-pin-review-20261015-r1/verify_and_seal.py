from pathlib import Path
import ast,hashlib,json,re,shutil
R=Path(__file__).resolve().parents[2]
V=R/'tools/pose-v1/evidence';E=V/'hdmi-jfm-pin-review-20261015-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changes=json.loads((E/'documentation-revision.json').read_text(encoding='utf-8'))['changes']
def links(text):
 return {a or b for a,b in re.findall(r'\]\((?:<([^>]+)>|([^\n)]+))\)',text)}
new_errors=[];historical=[]
for item in changes:
 p=R/item['path'];assert sha(p)==item['after_sha256']
 before=E/'before'/item['path']
 old=links(before.read_text(encoding='utf-8-sig')) if before.exists() else set()
 for target in links(p.read_text(encoding='utf-8')):
  if '://' in target or target.startswith('#'):continue
  t=target.split('#')[0]
  if t and not (p.parent/t).exists():
   (historical if target in old else new_errors).append({'path':item['path'],'target':target})
# Check every new report link independently.
p=E/'REPORT.md'
for target in links(p.read_text(encoding='utf-8')):
 if '://' not in target and not target.startswith('#') and not (p.parent/target).exists():
  new_errors.append({'path':str(p.relative_to(R)),'target':target})
assert not new_errors,new_errors
scripts=list((R/'FPGA/hdmi_candidate/scripts').glob('*.py'))
for p in scripts:ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
(E/'final-static-review.json').write_text(json.dumps({'Python_AST_files':len(scripts),'AST_passed':True,
 'new_broken_links':new_errors,'historical_broken_links_preserved':historical,
 'first_checker_failed_on_angle_brackets_and_historical_links':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(E/'documentation-checker-failure.json').write_text(json.dumps({'script':'finish_review.py','exit':1,
 'document_updates_completed':True,'stage':'naive link parser scanned all historical links',
 'corrected_by':'read-only verification with CommonMark angle targets and before/after comparison',
 'documents_not_rewritten_or_duplicated':True},indent=2)+'\n')
for name in ('finish_review.py','verify_and_seal.py'):
 shutil.copyfile(Path(__file__).with_name(name),E/name)
source=E/'source-snapshots';source.mkdir(exist_ok=False)
for name in ('inspect_jfm_replace.py','review_jfm_pin_contract.py','probe_jfm_primitive_read.py','probe_jfm_ps_elaboration.py'):
 shutil.copyfile(R/'FPGA/hdmi_candidate/scripts'/name,source/name)
for name,query in [('hdmi-jfm-pin-review-20261015-r2','inspect.tcl'),
                   ('hdmi-jfm-primitive-20261015-r1','read.tcl'),
                   ('hdmi-jfm-ps-elaboration-20261015-r1','elaborate.tcl')]:
 shutil.copyfile(R/'.local'/name/query,V/name/query) if not (V/name/query).exists() else None
(V/'hdmi-jfm-pin-review-20261015-r2/README.md').write_text(
 '# Procedure inspection only\n\nReal bodies read via normal vendor Tcl loader under mutation guards. '
 'replace/reset/hook never invoked. dependency-procedures.tcl is an inspection listing: info args omits '
 'default values, so it must not be sourced as a reconstructed implementation. Use the original protected '
 'vendor source for any separately approved future execution.\n',encoding='utf-8')
completion={'date':'2026-10-15','workspace':str(R),'user_resource_hints_reviewed':True,
 'PDF_pages_visually_reviewed':[9,10,19,21,22],'F8_key2_polarity_closed_from_schematic':True,
 'real_replace_body_read':True,'full_replace_requires_Vivado_2018_3':True,
 'all_9_installed_targets_before_after_equal':True,'all_297_reference_files_equal':True,
 'PS_primitive_standalone_exit0_was_empty_and_not_accepted':True,
 'actual_PS_RTL_metadata_probe_passed':False,'actual_PS_failure':'Synth 8-4456 named AI_IN ports mismatch',
 'global_replace_or_reset_or_hook_invoked':False,'tools_installed_or_upgraded':False,
 'PS_or_AI_Mate_changed':False,'board_operation':False,'candidate_downloaded':False,'BOOT_changed':False,
 'old_DATA_resumed':False,'full_HDMI_accepted':False,'failed_logs_preserved':True,
 'EDA_process_inventory':json.loads((E/'final-process-inventory.json').read_text(encoding='utf-8-sig')),
 'recovery':'FPGA/hdmi_candidate/JFM-COMPATIBILITY-REVIEW.md'}
(E/'completion-review.json').write_text(json.dumps(completion,indent=2)+'\n')
folders=[E,V/'hdmi-jfm-pin-review-20261015-r2',V/'hdmi-jfm-primitive-20261015-r1',V/'hdmi-jfm-ps-elaboration-20261015-r1']
for d in folders:
 dest=d/'files.sha256.json';assert not dest.exists()
 manifest={p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file()}
 dest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for d in folders:
 for n,h in json.loads((d/'files.sha256.json').read_text(encoding='utf-8')).items():assert sha(d/n)==h
print(json.dumps({'documents':len(changes),'AST_files':len(scripts),'new_broken_links':0,
 'historical_broken_links_preserved':len(historical),'sealed_evidence_directories':len(folders),'all_SHA_verified':True}))

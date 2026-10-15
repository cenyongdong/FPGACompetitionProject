from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[2]
V=R/'tools/pose-v1/evidence'
E=V/'hdmi-bringup-20261015-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copytree(R/'FPGA/hdmi_candidate',E/'final-candidate-source',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for name in ('update_documentation.py','seal_evidence.py'):
 shutil.copyfile(Path(__file__).with_name(name),E/name)
for rev in ('r3','r4'):
 name='hdmi-procise-api-20261015-'+rev
 shutil.copyfile(R/'.local'/name/'query.tcl',V/name/'query.tcl')
folders=[
'hdmi-system-20261015-r1','hdmi-ip-revision-20261015-r1',
'hdmi-bd-validation-20261015-r1','hdmi-bd-metadata-20261015-r1',
'hdmi-ip-generation-20261015-r1','hdmi-ip-generation-20261015-r2','hdmi-ip-generation-20261015-r3',
'hdmi-generated-axi-20261015-r1','hdmi-generated-axi-20261015-r2',
'hdmi-native-axi-20261015-r1','hdmi-native-ps-20261015-r1',
'hdmi-candidate-procise-diff-20261015-r1','hdmi-candidate-procise-diff_route-20261015-r1',
'hdmi-candidate-procise-diff_route-20261015-r2','hdmi-candidate-procise-output_route-20261015-r1',
'hdmi-procise-api-20261015-r3','hdmi-procise-api-20261015-r4']
sealed=[]
for name in folders:
 d=V/name;target=d/'files.sha256.json'
 assert not target.exists(),name
 hashes={p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file()}
 target.write_text(json.dumps(hashes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 sealed.append({'directory':name,'files':len(hashes),'manifest_sha256':sha(target)})
completion={'actual_execution_date':'2026-10-15','workspace':str(R),
 'user_authorized_board_validation':True,'user_authorized_whitelist_revision_upgrade':True,
 'user_authorized_finite_contract_exceptions':True,
 'read_only_board_identity_and_register_check_passed':True,
 'finite_IP_contract_and_generation_and_postcheck_passed':True,
 'actual_generated_AXI3_simulation_passed':True,'actual_generated_AXI_native_synthesis_passed':True,
 'PS_native_gate_passed':False,'PS_stop_reason':'ELAB-E-6: extended PS7_inst terminals exceed native PCPU7 declaration',
 'native_IO_pin_compatibility_probe_routed':True,'native_IO_timing_signoff':False,
 'whole_HDMI_complete':False,'candidate_bitstream_generated':False,'candidate_downloaded':False,
 'BOOT_replaced':False,'new_reboot':False,'global_database_patch':False,
 'PS_custom_IP_or_AI_Mate_upgrade':False,'old_DATA_investigation_resumed':False,
 'original_reference_297_files_equal':True,'nine_scanout_RTL_equal_r6':True,
 'tool_processes_by_exact_name':json.loads((E/'final-process-inventory.json').read_text(encoding='utf-8-sig')),
 'failed_evidence_preserved':True,'stage_complete_not_system_acceptance':True,
 'recovery_document':'FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md','sealed_directories':sealed}
(E/'completion-review.json').write_text(json.dumps(completion,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
target=E/'files.sha256.json';assert not target.exists()
hashes={p.relative_to(E).as_posix():sha(p) for p in E.rglob('*') if p.is_file()}
target.write_text(json.dumps(hashes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Read-only verification of every just-written manifest; never rewrite historical ones.
for d in [V/name for name in folders]+[E]:
 for name,h in json.loads((d/'files.sha256.json').read_text(encoding='utf-8')).items():
  assert sha(d/name)==h,(d,name)
print(json.dumps({'sealed_directories':len(folders)+1,'all_manifest_entries_verified':True,'system_complete':False}))

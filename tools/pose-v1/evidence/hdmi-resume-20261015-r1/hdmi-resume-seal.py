from pathlib import Path
import hashlib,json,shutil,ast,re
R=Path('D:/FPGACompetitionProject');C=R/'FPGA/hdmi_candidate'
E=R/'tools/pose-v1/evidence/hdmi-resume-20261015-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
# The native synthesis and r5 kernel used exactly the current production RTL.
native=json.loads((R/'tools/pose-v1/evidence/hdmi-candidate-procise-scanout-20261015-r1/execution.json').read_text())
sim=json.loads((R/'tools/pose-v1/evidence/hdmi-candidate-sim-20261015-r5/source-manifest.json').read_text())
consistency=[]
for n,h in native['sources'].items():
 actual=sha(C/'rtl'/n);row={'source':n,'native_sha':h,'r5_sha':sim[n],'current_sha':actual,'equal':h==sim[n]==actual};consistency.append(row)
assert all(r['equal'] for r in consistency)
save(E/'rtl-identity-consistency.json',consistency)
for p in (C/'scripts').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
for rev in ('r6','r7'):
 assert not (R/('.local/hdmi-candidate-sim-20261015-'+rev)).exists()
 assert not (R/('tools/pose-v1/evidence/hdmi-candidate-sim-20261015-'+rev)).exists()
save(E/'prepared-validation.json',{'executed':False,'needs_new_batch_confirmation':True,
 'location':'Windows; D:/FPGACompetitionProject','tools':'Vivado XSim 2019.1, existing installation',
 'stage_budget_seconds':90,'new_batch_order':[
 {'command':'python FPGA/hdmi_candidate/scripts/simulate.py r6 core','condition':'explicit new-batch confirmation and fresh evidence/work paths'},
 {'command':'python FPGA/hdmi_candidate/scripts/simulate.py r7 pixel','condition':'first batch all stages exit0, marker PASS and no Fatal'}],
 'stop_on':['timeout','nonzero exit','Fatal','missing PASS','source identity change'],
 'hardware_activity':False,'IP_migration':False,'automatic_retry':False})
revision={}
for before in (E/'before').rglob('*.md'):
 rel=before.relative_to(E/'before');p=R/rel
 revision[rel.as_posix()]={'before_sha256':sha(before),'after_sha256':sha(p),'changed':sha(before)!=sha(p)}
save(E/'documentation-revision.json',revision)
shutil.copytree(C,E/'candidate-source',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for n in ('hdmi-resume-finalize.py','hdmi-resume-seal.py'):shutil.copyfile(R/'.local'/n,E/n)
state={'date':'2026-10-15','user_resumed_HDMI':True,'old_DATA_still_paused':True,
 'r4_complete_frame_three_bases_passed':True,'native_scanout_synthesis_exit':native['exit'],
 'r5_kernel_assertions_completed':True,'r5_driver_exit':1,'r5_overall_accepted':False,'r5_timeout_seconds':90,
 'simulation_retry_after_timeout':False,'new_split_entry_prepared_not_run':True,'current_RTL_matches_r5_and_native':True,
 'PS_AI_system_integrated':False,'TMDS_physical_integrated':False,'implementation_timing_signoff':False,
 'bitstream_generated':False,'download':False,'board_connection_this_turn':False,
 'protected_reference_files_unchanged':38,'project_task_complete':False,'awaiting':'explicit confirmation of new split simulation batch',
 'tool_process_inventory':json.loads((E/'process-inventory.json').read_text(encoding='utf-8-sig'))}
save(E/'final-state.json',state)
for rev in ('r3','r4','r5'):
 d=R/('tools/pose-v1/evidence/hdmi-candidate-sim-20261015-'+rev)
 assert not (d/'files.sha256.json').exists()
 save(d/'files.sha256.json',{p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file()})
d=R/'tools/pose-v1/evidence/hdmi-candidate-procise-scanout-20261015-r1'
save(d/'files.sha256.json',{p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file()})
# Verify only relevant Markdown references created by this turn.
for p in (C/'README.md',C/'RESUME.md',C/'INTEGRATION.md',E/'REPORT.md'):
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  assert (p.parent/target.split('#')[0]).exists(),(p,target)
save(E/'files.sha256.json',{p.relative_to(E).as_posix():sha(p) for p in E.rglob('*') if p.is_file()})
print(json.dumps({'sealed':True,'documentation_revisions':len(revision),'matched_native_and_simulation_RTL':len(consistency),
 'current_source_files':sum(p.is_file() for p in (E/'candidate-source').rglob('*')),'new_batch_executed':False,
 'local_links_checked':True,'background_tools':state['tool_process_inventory']['processes']},ensure_ascii=False))

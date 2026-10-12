"""Bind offline/official logs without converting a failed exit into a pass."""
from pathlib import Path
import json,hashlib,re,shutil,tarfile
from archive_bytes import extract_bytes
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-contract-20261011-r2';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if not (E/'final-return').exists():extract_bytes(E/'final.tar',E/'final-return')
with tarfile.open(E/'final.tar') as archive:
    for member in archive.getmembers():
        if member.isfile():assert archive.extractfile(member).read()==(E/'final-return'/member.name).read_bytes()
final=E/'final-return/final'
reports={};baseline=None
for name,expected in [('apply-return',0),('apply-r3-return',1)]:
    d=E/name/'run-apply'
    for line in (d/'files.sha256').read_text().splitlines():h,n=line.split('  ',1);assert sha(d/n)==h
    assert int((d/'exit.txt').read_text())==expected
    before=(d/'dmesg.before.log').read_bytes();assert before==(d/'dmesg.after.log').read_bytes()
    if baseline is None:baseline=before
    else:assert before==baseline
    assert not any(line.split()[1].startswith('pose_') for line in (d/'processes.txt').read_text().splitlines()[1:] if len(line.split())>1)
    assert ':39001 ' not in (d/'ports.txt').read_text() and ':8554 ' not in (d/'ports.txt').read_text()
    rows=[json.loads(x) for x in (d/'results/registry.jsonl').read_text().splitlines()];assert len(rows)==12
    assert all(x['supported'] and x['init'] and x['forward'] for x in rows if x['phase']=='after')
    maps=[json.loads(x) for x in (d/'results/after-apply.zg-hardop-map.jsonl').read_text().splitlines()]
    group=next(x for x in maps if x['op_id']==9186);assert group['sync_index']==223 and group['layer_count']==11 and len(group['merge_from'])==19
    logs=list((d/'work/.icraft/logs/piw24').glob('*.log'));assert len(logs)==2
    reports[name]={'program_exit':expected,'official_log_files':len(logs),'full_model_forward':False,'registry_rows':12,'group':group,'kernel_unchanged':True,'status':'metadata_captured_application_log_count_gate_failed' if expected else 'apply_and_official_log_pair_captured'}
assert (final/'dmesg.log').read_bytes()==baseline
assert not any(line.split()[1].startswith('pose_') for line in (final/'processes.txt').read_text().splitlines()[1:] if len(line.split())>1)
logdir=E/'apply-r3-return/run-apply/work/.icraft/logs/piw24'
main=logdir/'piw24_zg330backend_0.log';opt=logdir/'piw24_zg330backend_0_memopt.log'
assert main.stat().st_size>0 and opt.stat().st_size>0;json.loads(opt.read_text())
shutil.copyfile(main,E/'official-deployment-main.txt');shutil.copyfile(opt,E/'official-deployment-memopt.json')
pattern=re.compile(r'ftmp_id: (\d+), is_ocm: (true|false), ftmp_physical_addr: (\d+), ftmp_logic_addr: (\d+), ftmp_size: (\d+)')
selected={};parent=None
for line in main.read_text().splitlines():
    m=pattern.search(line)
    if not m:continue
    ident=int(m[1]);alias='|--' in line
    if not alias:parent=ident
    if ident in (4386,4390,8467,8479):selected[ident]={'is_ocm':m[2]=='true','physical_address':int(m[3]),'logical_address':int(m[4]),'bytes':int(m[5]),'parent':parent,'alias_line':alias,'original_line':line}
assert set(selected)=={4386,4390,8467,8479}
for alias,owner,address,size in ((4386,8467,109232128,30240),(4390,8479,109285376,16800)):
    assert selected[alias]['parent']==owner and selected[alias]['physical_address']==selected[owner]['physical_address']==address
    assert selected[alias]['bytes']==size and not selected[alias]['is_ocm'] and not selected[owner]['is_ocm']
modelpath=R/'.local/pose-v1-axi-pair/package-20261011-r4/graph/piw24_ZG.json';model=json.loads(modelpath.read_text());ops={x['op_id']:x for x in model['ops']}
fusion=json.loads((R/'tools/pose-v1/mixed-fusion-baseline.json').read_text());group=next(x for x in fusion['groups'] if x['effective_op_id']==9186)
details=[]
for ident in group['members']:
    op=ops[ident];details.append({'op_id':ident,'name':op['name'],'layer_count':op['layer_count'],'instruction_bytes':sum(x['dtype']['shape'][0]*8 for x in op['instr']),'parameter_count':len(op['params'])})
for ident in (8629,8631):assert ops[ident]['layer_count']==0 and all(x['dtype']['shape']==[0] for x in ops[ident]['instr'])
assert sum(x['layer_count'] for x in details)==11
parent=json.loads((E/'apply-r3-return/run-apply/results/log-parent-contract.json').read_text());assert parent=={'missing_parent_opened':False,'prepared_parent_opened':True,'Device_opened_during_contract':False}
failed=R/'.local/pose-v1-build/producer-deployment-20261011-r3';future=R/'.local/pose-v1-build/producer-deployment-20261011-r4';b=json.loads((failed/'build-result.json').read_text());assert sha(failed/'entry.failed-r3.cpp')==b['entry_sha256']
future_result=json.loads((future/'build-result.json').read_text());assert sha(R/'software/pose_v1/src/producer_deployment_log.cpp')==future_result['entry_sha256']
report={'status':'producer_contract_paths_and_official_maps_reviewed_root_unresolved','offline_review_sha256':sha(E/'offline.review.json'),'matching_audit_sha256':sha(E/'audit.identity.json'),'model_sha256':sha(modelpath),'apply_stages':reports,'selected_value_maps':selected,'group_members':details,'single_cast_has_no_compute_instructions':True,'preserved_group_inputs':[486,478],'preserved_group_layers':11,'preserved_group_end':234,'ready_checker_has_conditional_region_copy':True,'conditional_copy_triggered_for_current_values_proven':False,'DDR_completion_contract_proven':False,'root_fixed':False,'SDK_log_parent_contract_passed':True,'SDK_parent_creation_fault_proven':False,'initial_missing_log_claim_retracted_gitignore_search_error':True,'r3_application_exit_preserved':1,'future_corrected_gate_program_sha256':future_result['program_sha256'],'future_corrected_gate_compiled_not_executed':True,'all_programs_ports_connections_closed':True,'compactions':0,'NPU_forward':False,'VPU_streaming':False,'strace_available':bool((final/'strace-path.txt').read_text().strip()),'final_MemAvailable_KiB':int(re.search(r'MemAvailable:\s+(\d+)',(final/'meminfo').read_text())[1]),'final_CmaFree_KiB':int(re.search(r'CmaFree:\s+(\d+)',(final/'meminfo').read_text())[1]),'archives_sha256':{p.name:sha(p) for p in E.glob('*.tar')},'official_log_sha256':{'main':sha(main),'memopt':sha(opt)},'evidence_sha256':{p.relative_to(E).as_posix():sha(p) for p in E.iterdir() if p.is_file() and p.suffix in ('.stdout','.txt','.json')},'failed_r3_source_sha256':sha(failed/'entry.failed-r3.cpp')}
(E/'data-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:report[k] for k in ('selected_value_maps','strace_available','final_MemAvailable_KiB','final_CmaFree_KiB','root_fixed')},indent=2))

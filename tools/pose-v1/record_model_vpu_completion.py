"""Bind the approved finite contrast; an unobserved fault is not a repair."""
import collections,json,re
from pathlib import Path
import mixed_validation_gate as g

e=g.ROOT/'tools/pose-v1/evidence/model-vpu-20261010-r2'
stages=('model-three','vpu-three','model-103','vpu-103')
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def put(name,value):
    p=e/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def snapshot(label,p,prefix):
    units=0
    for line in (p/(prefix+'.pagetypeinfo')).read_text().splitlines():
        match=re.search(r'type\s+(Unmovable|Movable|Reclaimable|HighAtomic)\s+([\d\s]+)$',line)
        if match:
            counts=list(map(int,match[2].split()));assert len(counts)==11
            units+=sum(counts[i]*2**(i-7) for i in range(7,11))
    mem={m[1]:int(m[2]) for m in re.finditer(r'^(\w+):\s+(\d+) kB$',(p/(prefix+'.meminfo')).read_text(),re.M)}
    return dict(label=label,ordinary_512KiB_units=units,MemAvailable_KiB=mem['MemAvailable'],CmaFree_KiB=mem['CmaFree'],sha256={n:g.sha(p/(prefix+'.'+n)) for n in ('buddyinfo','pagetypeinfo','meminfo','vmstat')})

base=g.load(e/'baseline.acceptance.json');contracts=g.load(e/'contracts.acceptance.json')
assert not base['Host107_new_run'] and base['Host107_reused']==107
assert contracts['ARM_refusals']==9 and contracts['ARM_load_refusals']==6
assert g.sha(g.ROOT/'.local/pose-v1-model-vpu/transfer-20261010-r2.tar')=='9226b6826360721e417bcbdd5db8e4d81fced027e79f7bfc3aa1df81e626f82c'
archives={'contracts.tar':'946a73bd280cdaa5d6651366b36d93718fd92cbbde10ee80e51a53c15dec2d9c','model-three.tar':'2f950d613fc65c29f4d6d9dfad0e46dd93e5fe56a528eb8fea859e4f675bd56e','vpu-three.tar':'b6ffba0959167d3a912ca2f174a792b0114bacbe6b17615c5c547de51694e0c5','model-103.tar':'dc17646f8e0dc8e4f886d010fd272dba177080b0c6854d8cd6afe75e92dcc19b'}
archives['vpu-103.tar']='123093cf8d6f95e9b426b0d4dda015106daea6647d7c52b7d783eb0391cc290c'
for name,digest in archives.items():assert g.sha(e/name)==digest
facts=[];snapshots=[];kernels=[];refs=['build.acceptance.json','baseline.acceptance.json','contracts.acceptance.json'];compactions=[]
for stage in ('contracts',)+stages:
    r=e/(stage+'-return')/('run-'+stage);g.verify(r)
    if stage=='vpu-103':
        failed=g.load(e/'vpu-103.failed-review.json');assert failed['status']=='model_vpu_startup_failed_preserved_not_acceptance' and not failed['Engine_created'] and failed['attempted']==0 and failed['both_abort_STREAMOFF_succeeded']
        assert (r/'exit.txt').read_text().strip()=='1' and (r/'dmesg.after.log').read_bytes().startswith((r/'dmesg.before.log').read_bytes())
        refs.append('vpu-103.failed-review.json')
    else:
        assert (r/'exit.txt').read_text().strip()=='0' and (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
        kernels.append((r/'dmesg.after.log').read_bytes())
    assert not any(line.split(maxsplit=2)[1].startswith('pose_') for line in (r/'final.processes').read_text().splitlines()[1:])
    assert all(port not in (r/'final.ports').read_text() for port in (':39001 ',':8554 '))
    for prefix in ('before','after'):snapshots.append(snapshot(stage+'.'+prefix,r,prefix))
    if stage in ('contracts','vpu-103'):continue
    a=g.load(e/(stage+'.acceptance.json'));assert a['status']=='model_vpu_stage_passed' and a['model_vpu_binary_sha256']==base['model_vpu_binary_sha256'] and a['correct']==(4 if stage.endswith('three') else 103)
    for suffix in ('acceptance','objects','counts'):refs.append(stage+'.'+suffix+'.json')
    obj=g.load(e/(stage+'.objects.json'));count=g.load(e/(stage+'.counts.json'));assert not obj['object_changed_across_copy'] and not count['below234'] and not count['query_errors']
    out=r/'results';life=rows(out/'lifecycle.jsonl');timing=rows(out/'timing.jsonl');oo=rows(out/'tensor-identities/objects.jsonl');mm=rows(out/'copy-observations/metadata.jsonl')
    pairs=collections.defaultdict(list);align=set()
    for x in oo:
        if x['op_id']==192 and x['point']=='after_copy':pairs[x['invocation']].append(x['source']['address_identity']);align.add(x['destination']['address_identity']%64)
    assert all(p==[109232128,109285376] for p in pairs.values())
    completion=[x for x in mm if x['kind']!='post_copy_Host_shadow'];assert all(x['op_id']==582 and x['initial']==x['final']==638 and x['polls']==1 for x in completion)
    f=dict(stage=stage,calls=a['correct'],FP32=a['FP32_compared'],returned_files=a['returned_files'],object_rows=obj['rows'],copied_inputs=obj['copied_inputs'],producer192_queries=count['query_rows'],copy_metadata=count['metadata_rows'],source_addresses=[109232128,109285376],Host_destination_mod64=sorted(align),init_ms=life[1 if a['video'] else 0]['init_ms'],actual_begin_span_ms=(timing[-1]['process_begin_ns']-timing[0]['process_begin_ns'])/1e6)
    if a['video']:
        v=g.load(e/(stage+'.video.json'));assert v['status']=='synthetic_scratch_VPU_content_and_actual_PTS_passed' and v['actual_PTS_match'] and v['model_inference_frames']==0
        refs.append(stage+'.video.json');f.update(synthetic_images=v['decoded_frames'],stream_bytes=v['stream_bytes'],NoInput_only=True)
    facts.append(f)
assert all(k==kernels[0] for k in kernels),'New kernel events between stages'
for stage,name in [('model-three','resources-common'),('vpu-three','resources-vpu-three'),('vpu-103','resources-vpu-103')]:
    p=e/(stage+'-return')/name;d=g.load(p/'decision.json');assert d['kernel_unchanged'] and not any(d[k] for k in ('drop_caches','reboot','CMA_changed','numerical_fault_fixed'))
    assert (p/'before.dmesg').read_bytes()==(p/'after.dmesg').read_bytes()
    compactions.append(dict(stage=stage,decision=d,sha256=g.sha(p/'decision.json')))
    for prefix in ('before','after'):snapshots.append(snapshot(name+'.'+prefix,p,prefix))
put('resource-review.json',dict(status='paired_resources_cleanup_checked_with_final_startup_failure',snapshots=snapshots,decisions=compactions,agent_compactions=sum(x['decision']['compaction_writes'] for x in compactions),between_groups_preparation_difference=True,kernel_raw_successful_stages_identical=True,kernel_raw_all_stages_identical=False,final_new_kernel_allocation_failure=True,programs_remaining=0,ports_released=True,not_leak_or_permanent_startup_proof=True))
refs.append('resource-review.json')
report=dict(status='same_ELF_contrast_three_stages_passed_final_VPU_startup_failed',program_SHA256=base['model_vpu_binary_sha256'],original_main_SHA256=base['binary_sha256'],manifest_SHA256=base['package_manifest_sha256'],payloads=403,build_sources=102,Host107_new_run=False,Host107_reused=107,Native_ARM_Run_refusals_each=9,Native_ARM_load_refusals_each=6,correct_calls=sum(f['calls'] for f in facts),FP32_compared=sum(f['FP32'] for f in facts),synthetic_VPU_images=sum(f.get('synthetic_images',0) for f in facts),object_rows=sum(f['object_rows'] for f in facts),copied_inputs=sum(f['copied_inputs'] for f in facts),producer192_queries=sum(f['producer192_queries'] for f in facts),copy_metadata=sum(f['copy_metadata'] for f in facts),stages=facts,failed_stage=failed,archives_SHA256=archives,agent_compactions=sum(x['decision']['compaction_writes'] for x in compactions),normal_source_reads_added=0,failure_late_source_reads_triggered=0,old_failure_reads_retained=True,root_cause_fixed=False,VPU_cause_proven=False,performance_accepted=False,stable_long_term_accepted=False,render_display_network_HDMI=False,active_tests=False,services_running=False,SSH_SCP_closed=True,evidence_SHA256={n:g.sha(e/n) for n in refs})
assert report['correct_calls']==111 and report['FP32_compared']==1676100
put('completion-review.json',report)
checkpoint=dict(status=report['status'],user_paused=False,active_tests=False,services_running=False,SSH_SCP_closed=True,program_SHA256=report['program_SHA256'],manifest_SHA256=report['manifest_SHA256'],passed_stages=['contracts']+list(stages[:3]),failed_stage='vpu-103',failed_stage_Engine_created=False,compactions=report['agent_compactions'],completion_review_SHA256=g.sha(e/'completion-review.json'),resume='Read MODEL-VPU-RESULTS/NEXT-20261010.md and ADR_27/ADR_02. Last stage stopped on pre-Engine VPU512KiB ordinary-page firmware allocation failure despite recorded compaction; no model forward occurred, no192 fault reproduction. Do not retry failed directory or compact in a loop. Next prepare resource-lifetime/first-context acquisition feasibility, not CMA/BOOT/cache guesses; explicit review before new hardware. Keep original exception/two late reads. Stable concurrent103/5Hz/long-term/HDMI/zero-copy pending.')
put('next-checkpoint.json',checkpoint);(e/'active-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ('status','correct_calls','FP32_compared','synthetic_VPU_images','agent_compactions')}))

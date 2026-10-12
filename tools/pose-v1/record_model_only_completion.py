"""Bind completed no-video runs and distinguish negative diagnosis from repair."""
import json,re,collections
import mixed_validation_gate as g
root=g.ROOT;e=root/'tools/pose-v1/evidence/model-only-20261010-r1'
def load(n):return g.load(e/n)
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def put(n,v):p=e/n;assert not p.exists();p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
archives=load('archive-identities.json')['return_archives'];assert g.sha(root/'.local/pose-v1-model-only/transfer-20261010-r1.tar')==load('archive-identities.json')['transfer_SHA256']
for n,digest in archives.items():assert g.sha(e/n)==digest
base=load('baseline.acceptance.json');contracts=load('contracts.acceptance.json');three=load('three.acceptance.json');long=load('load.acceptance.json')
assert base['Native_refusals']==contracts['ARM_refusals']==9 and not base['Host107_new_run'] and three['correct']==4 and long['correct']==103 and three['FP32_compared']+long['FP32_compared']==1615700
snapshots=[];kernels=[];meta=[];counts=[];objects=[];stageFacts=[]
for label,mode in [('contracts','contracts'),('three','three'),('load','load-103')]:
    r=e/(label+'-return')/('run-'+mode);g.verify(r);assert (r/'exit.txt').read_text().strip()=='0' and (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes();kernels.append((r/'dmesg.after.log').read_bytes())
    assert not any(line.split(maxsplit=2)[1].startswith('pose_') for line in (r/'final.processes').read_text().splitlines()[1:]);assert all(p not in (r/'final.ports').read_text() for p in (':39001 ',':8554 '))
    for prefix in ('before','after'):
        units=0
        for line in (r/(prefix+'.pagetypeinfo')).read_text().splitlines():
            match=re.search(r'type\s+(Unmovable|Movable|Reclaimable|HighAtomic)\s+([\d\s]+)$',line)
            if match:
                ns=list(map(int,match[2].split()));assert len(ns)==11;units+=sum(ns[i]*2**(i-7) for i in range(7,11))
        mem={m[1]:int(m[2]) for m in re.finditer(r'^(\w+):\s+(\d+) kB$',(r/(prefix+'.meminfo')).read_text(),re.M)}
        snapshots.append(dict(label=label+'.'+prefix,MemAvailable_KiB=mem['MemAvailable'],CmaFree_KiB=mem['CmaFree'],ordinary_512KiB_units=units,sha256={n:g.sha(r/(prefix+'.'+n)) for n in ['meminfo','buddyinfo','pagetypeinfo','vmstat']}))
    if label!='contracts':
        out=r/'results';cc=rows(out/'producer-counts/counts.jsonl');mm=rows(out/'copy-observations/metadata.jsonl');oo=rows(out/'tensor-identities/objects.jsonl');counts.extend(cc);meta.extend(mm);objects.extend(oo)
        assert all(x['count']==234 and not x['error'] for x in cc)
        completion=[x for x in mm if x['kind']!='post_copy_Host_shadow'];assert all(x['op_id']==582 and x['initial']==638 and x['final']==638 and x['polls']==1 for x in completion)
        sourcePairs=collections.defaultdict(list);align=set()
        for x in oo:
            if x['op_id']==192 and x['point']=='after_copy':sourcePairs[x['invocation']].append(x['source']['address_identity']);align.add(x['destination']['address_identity']%64)
        assert all(pair==[109232128,109285376] for pair in sourcePairs.values())
        timing=rows(out/'timing.jsonl');life=rows(out/'lifecycle.jsonl');assert len(life)==2
        stageFacts.append(dict(stage=mode,calls=len(timing),init_ms=life[0]['init_ms'],source_addresses=[109232128,109285376],Host_destination_mod64=sorted(align),actual_begin_span_ms=(timing[-1]['process_begin_ns']-timing[0]['process_begin_ns'])/1e6,normal_source_reads_added=0,all192_counts=234,completion582_no_extra_poll=True))
assert all(k==kernels[0] for k in kernels)
put('resource-review.json',dict(status='model_only_resources_and_cleanup_checked',snapshots=snapshots,agent_compactions=0,kernel_raw_all_stages_identical=True,program_processes_remaining=0,input_RTSP_ports_released=True,drop_caches=False,reboot=False,CMA_changed=False,not_leak_or_permanent_startup_proof=True))
refs=['build.acceptance.json','baseline.acceptance.json','contracts.acceptance.json','three.acceptance.json','three.objects.json','three.counts.json','load.acceptance.json','load.objects.json','load.counts.json','resource-review.json']
tools=['prepare_model_only_r1.py','Build-ModelOnly.ps1','review_model_only_build_base.py','review_model_only.py','review_model_only_objects.py','review_model_only_counts.py','run_model_only_native.py','run-model-only.sh','model_only_transfer.py','record_model_only_completion.py']
report=dict(status='real_mixed_model_without_video_three_and103_passed_fault_unresolved',program_sha256=long['model_only_binary_sha256'],original_main_sha256=base['binary_sha256'],manifest_sha256=base['package_manifest_sha256'],payloads=403,build_sources=98,Native_ARM_refusals_each=9,Host107_new_run=False,Host107_reused=107,registry_reused=12,Host_FP32_reused=59600,three_calls=4,load_calls=103,correct_calls=107,FP32_compared=1615700,all_raw_windows_and_complete_outputs_saved=True,all_outputs_bitwise_old_board_reference=True,stage_facts=stageFacts,shadow_records=sum(x['kind']=='post_copy_Host_shadow' for x in meta),copy_metadata_rows=len(meta),object_rows=len(objects),producer192_queries=len(counts),source_addresses=[109232128,109285376],all192_counts234=True,completion582_no_extra_poll=True,independent_persistence_tasks_per_run=7,single_main_Engine=True,full_model_Session=True,NPU_forward=True,VPU=False,display=False,network=False,HDMI=False,profiling=False,normal_device_source_reads_added=0,hardware_error_source_reads_triggered=0,model_fault_reproduced=False,root_cause_fixed=False,VPU_proven_cause=False,DMA_cache_fence_proven=False,zero_copy_verified=False,performance_accepted=False,long_term_accepted=False,agent_compactions=0,BOOT_SDK_model_math_changed=False,all_agent_sessions_closed=True,final_MemAvailable_KiB=snapshots[-1]['MemAvailable_KiB'],final_CmaFree_KiB=snapshots[-1]['CmaFree_KiB'],final_ordinary_512KiB_units=snapshots[-1]['ordinary_512KiB_units'],evidence_sha256={n:g.sha(e/n) for n in refs},review_tools_sha256={n:g.sha(root/'tools/pose-v1'/n) for n in tools},archive_sha256=archives,limitations=['No video/display/network; one103 sequence is not permanent concurrency reliability.','Saved output IO, wrapper heap, and no VPU-first initialization alter conditions; no causal proof from non-reproduction.','Correct FP32-aligned Host destinations include nonzero mod64 values; not a64byte alignment fix.','Old failed Host bytes and both late reads remain archived; no new device exception this batch.'])
put('completion-review.json',report)
checkpoint=dict(status=report['status'],user_paused=False,active_tests=False,services_running=False,SSH_SCP_closed=True,package='.local/pose-v1-model-only/package-20261010-r1',build='.local/pose-v1-build/mixed-20261010-model-only-r1',board='/tmp/pose-model-only-20261010-r1',completion_sha256=g.sha(e/'completion-review.json'),next='Read MODEL-ONLY-RESULTS-20261010, ADR_26 and MODEL-ONLY-NEXT-20261010. No-video original Engine4+103 passed107 complete outputs1615700FP32, actual192sources109232128/109285376,856queries234. No compaction and all agents closed. Fault not reproduced/fixed; noVPU causal conclusion. Next prepare one same-binary model-only versus synthetic-VPU contrast, keeping original observers and stop/source reads, separate approval. No private mapping/cache/BOOT/CMA guess; stable concurrent103/long-term/HDMI/zero-copy pending.')
put('next-checkpoint.json',checkpoint);(e/'active-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['status','correct_calls','FP32_compared','object_rows','producer192_queries','agent_compactions','final_ordinary_512KiB_units']}))

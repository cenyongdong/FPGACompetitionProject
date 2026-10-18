"""Bounded checkpoint-only continuation of the preserved r7 native physopt result.

Default inspect is filesystem-only. Explicit bootstrap/route/reports never
launch or reset a managed run, repeat placement, program hardware or write BOOT.
The original r7 parent exit1 remains failed. New receipts describe new stages.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import re
import sys
import time
import types
import zipfile

sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[3]
SCRIPT=Path(__file__).resolve()
START_BYTES=SCRIPT.read_bytes()
SCRIPTS=SCRIPT.parent
E3=ROOT/'tools/pose-v1/evidence/hdmi-live-20261017-r3'
E7=ROOT/'tools/pose-v1/evidence/hdmi-live-20261017-r7'
E=ROOT/'tools/pose-v1/evidence/hdmi-live-20261018-r8'
W=ROOT/'.local/hdmi-live-20261017-r7'
REF=W/'reference'
ORIGINAL=REF/'fpai_demo_vivado.runs/impl_read_v3r7'
NATIVE=REF/'fpai_demo_vivado.runs/route_read_v3r8b'
PHYS=ORIGINAL/'ai7030_edif_top_physopt.dcp'
PHYS_SHA='453a031b1bf820a3e5aae96d3a73a29665304d3855f35fb85327117544dc6f68'
ROUTED=NATIVE/'ai7030_edif_top_routed.dcp'
GATE=E7/'read-v3r7-constraints/review.json'
AUDIT=E/'native-input-audit-r2'
PREFIX='read-v3r8b-'
PINNED={
    'continue_ai_read_checkpoint.py':'ee11b66896bb84886b186a4667fd4d5c871ec7c404bcc034e56637bacd01504b',
    'ai_read_r7_contract.py':'fa28b01f12baf593788d554fae942564ff69753caf1310cd034a48d08178fdc8',
    'eda_owned_stage.py':'3a098b066127c53d26bfb5829c253055fc796e7078888edb0a9ce21acdd2b672',
    'continue_ai_read_candidate.py':'a100884326b044a6c054e8331255135a4e1231a53ad5d86def5ecf208100b55d',
    'continue_hdmi_reader_idle_candidate.py':'aa175d681abc632625df8e7ec7a74cf332fa59a1dd3e0ab39066074c1696f2a6',
    'review_ai_read_route.py':'48a1506553804c2b033bbe41d527eca41a9f8b610bed6b32999f6cc89e60053c',
    'review_ai_read_constraints.py':'5b0ab899a632d0d732ab9192d559335c9f3fcca4695a146f449f3ff70e9644ae',
    'ai_read_postroute_contract.py':'37f1f50aa55f866d59260a350b25dc0cf9de0e423597bbeb9d65b2e96853fb6b'}

def need(ok, message):
    if not ok: raise ValueError(message)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(path,obj):
    with path.open('x',encoding='utf-8') as f: f.write(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def record(path):
    st=path.stat()
    need(not path.is_symlink() and not getattr(st,'st_file_attributes',0)&0x400,'Nonordinary input: '+str(path))
    return dict(bytes=st.st_size,SHA256=sha(path),mtime_ns=st.st_mtime_ns)
def inventory(base):
    return {p.relative_to(base).as_posix():record(p) for p in sorted(base.rglob('*')) if p.is_file()}
def frozen(name):
    path=SCRIPTS/name
    raw=path.read_bytes()
    need(hashlib.sha256(raw).hexdigest()==PINNED[name],'Frozen implementation changed: '+name)
    mod=types.ModuleType('r8_'+name.replace('.','_'));mod.__file__=str(path)
    exec(compile(raw,str(path),'exec'),mod.__dict__)
    return mod

def source_guard():
    need(SCRIPT.read_bytes()==START_BYTES,'Controller changed after process start')
    for name,expected in PINNED.items(): need(sha(SCRIPTS/name)==expected,'Protected algorithm changed: '+name)
    s=load(E3/'continuation-state.json')
    need(s['status']=='active_offline_r7_checkpoint_continuation'
         and s['whole_task_pause']['paused'] is False and s['offline_work_continues'] is True,
         'Task not explicitly resumed for this continuation')
    need(s['old_DATA']=='paused' and s['onsite_observation_work']['paused'] is True
         and not s['BOOT_writes_authorized'] and s['remaining_previous_package_reboots']==0,
         'Existing board/DATA protection boundary changed')

def preflight():
    source_guard()
    contract=frozen('ai_read_r7_contract.py')
    # Reuse one verified input snapshot within this read-only preflight. A new
    # module and full fresh scan are still made before AND after every EDA job.
    preparation=contract.preparation_identity()
    contract.preparation_identity=lambda:preparation
    installed=contract.installed_identity(preparation)
    contract.installed_identity=lambda proof=None:installed
    sources=contract.stable_sources()
    contract.stable_sources=lambda:sources
    original_completed=contract.completed
    completion_cache={}
    def completed_snapshot(mode):
        if mode not in completion_cache: completion_cache[mode]=original_completed(mode)
        return completion_cache[mode]
    contract.completed=completed_snapshot
    synthesis=contract.verify_synthesis()
    gate=load(GATE)
    need(gate['route_prerequisite_pass'] is True and gate['source_sha256']==sources
         and gate['read_bits']==2768,'Actual r7 full constraints gate changed')
    contract.completed('constraints')
    baseline=load(E7/'place-parent-failure-r1/native-inventory-after.json')
    current=inventory(ORIGINAL)
    need(set(current)==set(baseline),'Original native file set changed')
    for p,row in current.items():
        need(all(row[k]==baseline[p][k] for k in row),'Original native artifact changed: '+p)
    need(PHYS.stat().st_size==44437238 and sha(PHYS)==PHYS_SHA,'r7 physopt checkpoint changed')
    for step in ['init_design','opt_design','place_design','phys_opt_design']:
        need((ORIGINAL/f'.{step}.begin.rst').is_file()
             and (ORIGINAL/f'.{step}.end.rst').is_file()
             and (ORIGINAL/f'.{step}.end.rst').stat().st_size==0
             and not (ORIGINAL/f'.{step}.error.rst').exists(),'Native step incomplete: '+step)
    need((ORIGINAL/'.vivado.end.rst').is_file()
         and not any(p.name.endswith(('.error.rst','.fail')) for p in ORIGINAL.iterdir()),'Native failure marker exists')
    need(not (ORIGINAL/'.route_design.begin.rst').exists(),'Original native route unexpectedly started')
    log=(ORIGINAL/'runme.log').read_text()
    need('place_design completed successfully' in log and 'phys_opt_design completed successfully' in log
         and not re.search(r'^ERROR:',log,re.M),'Native physical steps failed')
    native=(ORIGINAL/'ai7030_edif_top.tcl').read_text()
    synth_path=REF/'fpai_demo_vivado.runs/synth_read_v3r7/ai7030_edif_top.dcp'
    need(native.count('add_files -quiet '+synth_path.as_posix())==1
         and synthesis['synthesis_checkpoint']['SHA256']==sha(synth_path),'Physical synthesis lineage changed')
    failed=load(E7/'read-v3r7-place/execution.json')
    need(failed['exit']==1 and not failed['stopped_by_monitor'],'Original parent failure was changed')
    parent=(E7/'read-v3r7-place/stdout.txt').read_text()
    need('HDMI_READER_R7_STAGE_FAILED Fresh place/physopt incomplete/stale' in parent
         and not (E7/'read-v3r7-place/phase-review.json').exists(),'Original parent guard failure not preserved')
    query=load(E7/'place-run-state-query-r1/review.json')
    need(query['query_completed_only'] is True and query['changes']=={}
         and query['protected_before_after_equal'] is True,'Independent current-state query incomplete')
    qfiles=load(E7/'place-run-state-query-r1/after.json')['REF7_all']
    need(record(REF/'fpai_demo_vivado.xpr')==qfiles['fpai_demo_vivado.xpr'],'Frozen actual XPR changed')
    query_text=(E7/'read-v3r7-current-run-query-r1/current-run-properties.txt').read_text()
    need('CURRENT_RUN impl_read_v3r7 STATUS {Not started route_design} NEEDS_REFRESH 0 PROGRESS 80%' in query_text,
         'Recorded current-state query differs')
    profile=(E7/'read-v3r7-place/implementation-profile.txt').read_text()
    values=dict(row.split('|',1) for row in profile.splitlines())
    need(all(values.get(k)==v for k,v in {
        'STRATEGY':'Performance_NetDelay_high','PART':'xc7z030ffg676-2',
        'STEPS.PLACE_DESIGN.ARGS.DIRECTIVE':'ExtraNetDelay_high',
        'STEPS.PHYS_OPT_DESIGN.ARGS.DIRECTIVE':'AggressiveExplore',
        'STEPS.ROUTE_DESIGN.ARGS.DIRECTIVE':'NoTimingRelaxation',
        'STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED':'0'}.items()),'Original profile differs')
    prep=load(E7/'preparation/review.json')
    cache={}
    for name in prep['OOC_cached_run_names']:
        cache.update({'fpai_demo_vivado.runs/'+name+'/'+p:row for p,row in inventory(REF/'fpai_demo_vivado.runs'/name).items()})
    need(len(cache)==451,'Cached OOC file count changed')
    bindings={p:sha(E7/p) for p in [
        'place-parent-failure-r1/review.json','place-parent-failure-r1/native-inventory-after.json',
        'read-v3r7-place/execution.json','read-v3r7-place/stage.tcl','read-v3r7-place/stdout.txt',
        'read-v3r7-place/implementation-profile.txt','read-v3r7-constraints/review.json',
        'place-run-state-query-r1/review.json','place-run-state-query-r1/before.json',
        'place-run-state-query-r1/after.json','read-v3r7-current-run-query-r1/execution.json',
        'read-v3r7-current-run-query-r1/current-run-properties.txt']}
    return dict(schema='r8-native-physopt-consumption-v1',source_sha256=sources,
        installed_sha256=prep['installed_sha256'],source_preparation_SHA256=sha(E7/'preparation/review.json'),
        constraints_gate_SHA256=sha(GATE),synthesis_checkpoint=synthesis['synthesis_checkpoint'],
        native_physopt=record(PHYS),original_native=current,OOC_cache=cache,
        XPR=record(REF/'fpai_demo_vivado.xpr'),prior_evidence_SHA256=bindings,
        controller_SHA256=hashlib.sha256(START_BYTES).hexdigest(),runtime_source_SHA256=PINNED,
        original_parent_exit=1,original_parent_phase_passed=False,historical_STATUS_or_refresh=None,
        supplemental_native_completion=True,final_timing_or_release_pass=False,
        no_place_physopt_repeat=True,new_BOOT_or_reboot_permission=False,MCP_integrated=False)

def configured_base():
    base=frozen('continue_ai_read_checkpoint.py')
    original_pieces=base.pieces
    header,route,endpoints,reports=original_pieces()
    old_ref=(ROOT/'.local/hdmi-live-20261017-r3/reference').as_posix()
    old_header,old_route=header,route
    header=header.replace(old_ref,REF.as_posix()).replace('route_read_v3r5','route_read_v3r8b')
    route=route.replace(old_ref,REF.as_posix()).replace('route_read_v3r5','route_read_v3r8b')
    need(header.replace(REF.as_posix(),old_ref).replace('route_read_v3r8b','route_read_v3r5')==old_header
         and route.replace(REF.as_posix(),old_ref).replace('route_read_v3r8b','route_read_v3r5')==old_route,
         'Original factory continuation inverse differs')
    need(route.count('route_design -directive NoTimingRelaxation')==1
         and len(re.findall(r'^\s*source\s+[^\n]*implementation_route_post\.tcl[^\n]*$',route,re.M))==1
         and not re.search(r'^\s*(?:opt_design|place_design|phys_opt_design|write_bitstream)\b',route,re.M),
         'Route-only scope/full factory hook differs')
    # The two comparison sources are historical managed-PS receipts, not new
    # outputs. Expand their source root before the base substitutes output E.
    need(endpoints.count('@@EVIDENCE@@/managed-PS-observer-r2/')==2,'PS receipt placeholders changed')
    endpoints=endpoints.replace('@@EVIDENCE@@',E3.as_posix())
    for actual,expected in [
        (REF/'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/synth/ps_ai.v',E3/'managed-PS-observer-r2/ps_ai.v.after'),
        (REF/'rtl/ps_ai_wrapper.sv',E3/'managed-PS-observer-r2/ps_ai_wrapper.sv.after')]:
        need(actual.is_file() and expected.is_file() and actual.read_bytes()==expected.read_bytes(),
             'Actual/expected PS input unavailable or mismatched: '+str(expected))
    base.E,base.W,base.REF,base.NATIVE=E,W,REF,NATIVE
    base.CHECKPOINT,base.CHECKPOINT_SHA,base.ROUTED=PHYS,PHYS_SHA,ROUTED
    base.pieces=lambda:(header,route,endpoints,reports)
    proof=dict(base_source_SHA256=PINNED['continue_ai_read_checkpoint.py'],
        original_native_SHA256=base.OLD_NATIVE_SHA,route_block_SHA256=hashlib.sha256(route.encode()).hexdigest(),
        only_reference_and_run_names_changed=True,inverse_complete_text_equal=True,
        no_implementation_step_repeated=True,original_full_factory_hook_once=True,
        historical_managed_PS_receipt_root=str(E3),actual_PS_reference_bytes_checked=True)
    return base,proof

def stage_name(mode): return PREFIX+mode
def completed(mode,proof):
    out=E/stage_name(mode)
    need(load(out/'execution.json')['exit']==0 and not load(out/'execution.json')['stopped_by_monitor']
         and load(out/'phase-review.json')['passed'] is True,'Prior stage incomplete: '+mode)
    need(load(out/'input-proof.json')==proof,'Prior stage physical/source inputs changed')
    return out

def evaluate_phase(mode,out):
    contract=frozen('ai_read_r7_contract.py')
    helper,_=contract.constraints_algorithms()
    gate=load(GATE)
    indices=helper.parse_indices((out/'checkpoint-binding.txt').read_text(),'source','capture')
    need(indices==gate['read_indices'],'Physical checkpoint snapshot bit identities changed')
    filename='read-snapshot-endpoints.txt' if mode=='reports' else 'checkpoint-endpoints.txt'
    endpoints=helper.snapshot_endpoints(out/filename,indices)
    clocks=helper.clock_taps(out/'clock-taps.txt',indices)
    need(clocks['source_period_ns']==5. and clocks['csr_period_ns']==10.,'Restored clock periods changed')
    return dict(passed=True,mode=mode,scope='This new checkpoint-only stage; not original r7 parent acceptance or board acceptance.',
        source_identity_unchanged=True,read_bits=len(indices),restored_snapshot_endpoint_bound=endpoints,
        actual_clocks=clocks,no_managed_run_status_used_or_fabricated=True,
        original_parent_exit=1,new_BOOT_or_reboot_permission=False)

def formal_review(proof):
    out=completed('reports',proof)
    contract=frozen('ai_read_r7_contract.py')
    evaluate,algorithm=contract.routed_report_algorithm()
    helper,_=contract.constraints_algorithms()
    phases={mode:{name:sha(completed(mode,proof)/name) for name in ['execution.json','phase-review.json','input-proof.json']}
            for mode in ['bootstrap','route','reports']}
    gate=load(GATE)
    installed_path=contract.INSTALLED
    review=evaluate(out,NATIVE,gate,helper,proof['source_sha256'],installed_path,load(installed_path),phases,
                    SCRIPTS/'review_ai_read_constraints.py')
    review.update(candidate_run='route_read_v3r8b',managed_run=False,
        checkpoint_continuation=dict(source_physical_SHA256=PHYS_SHA,routed_checkpoint=load(E/(PREFIX+'route')/'routed-checkpoint.json'),
            source_synthesis_checkpoint=proof['synthesis_checkpoint'],original_r7_parent_exit_remains=1,
            source_native_completion_audit_SHA256=sha(AUDIT/'review.json')),
        original_r7_parent_phase_passed=False,retained_routed_algorithm=algorithm,
        actual_review_producer_SHA256=hashlib.sha256(START_BYTES).hexdigest())
    save(out/'review.json',review)
    print(json.dumps({k:review[k] for k in ['bit_generation_prerequisite_pass','global_setup_WNS_ns','global_hold_WHS_ns','read_bits']}))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',nargs='?',default='inspect',choices=['inspect','audit','bootstrap','route','reports','review'])
    args=parser.parse_args();started=time.monotonic()
    proof=preflight();base,transform=configured_base()
    if args.mode=='inspect':
        for mode in ['bootstrap','route','reports']:
            text=base.build_tcl(mode)
            need(not re.search(r'^\s*(?:launch_runs|reset_run|place_design|phys_opt_design|opt_design|write_bitstream)\b',text,re.M),
                 'Unexpected implementation command in new stage: '+mode)
        print(json.dumps(dict(read_only=True,source_count=937,cache_files=451,installed_count=41,
            native_checkpoint_SHA256=PHYS_SHA,original_parent_exit=1,route_transform=transform,
            seconds=time.monotonic()-started),ensure_ascii=False));return
    if args.mode=='audit':
        need(not AUDIT.exists(),'Preserve previous native input audit')
        with zipfile.ZipFile(PHYS) as archive: need(archive.testzip() is None,'Physical DCP CRC failed')
        AUDIT.mkdir()
        save(AUDIT/'input-proof.json',proof);save(AUDIT/'route-transform.json',transform)
        save(AUDIT/'review.json',dict(native_physopt_consumption_accepted=True,
            original_parent_phase_passed=False,original_parent_exit=1,historical_properties_not_reconstructed=True,
            input_proof_SHA256=sha(AUDIT/'input-proof.json'),route_transform_SHA256=sha(AUDIT/'route-transform.json'),
            checkpoint_archive_CRC_pass=True,actual_open_checkpoint_context_not_yet_verified=True,
            no_new_EDA_or_board=True,seconds=time.monotonic()-started))
        print(json.dumps(load(AUDIT/'review.json')));return
    need(load(AUDIT/'input-proof.json')==proof and load(AUDIT/'route-transform.json')==transform
         and load(AUDIT/'review.json')['native_physopt_consumption_accepted'] is True,'Native input audit changed')
    if args.mode=='review': formal_review(proof);return
    stage=stage_name(args.mode);out=E/stage
    need(not out.exists() and not (W/stage).exists(),'Preserve previous stage/output')
    if args.mode=='bootstrap':
        need(not NATIVE.exists(),'Preserve existing continuation directory')
        NATIVE.mkdir();save(NATIVE/'bootstrap-owner.json',dict(checkpoint_SHA256=PHYS_SHA,producer_SHA256=proof['controller_SHA256']))
    else:
        prior=completed('bootstrap' if args.mode=='route' else 'route',proof)
        need(inventory(NATIVE)==load(prior/'native-after.json'),'Native outputs changed since previous stage')
        if args.mode=='reports': need(sha(ROUTED)==load(E/(PREFIX+'route')/'routed-checkpoint.json')['SHA256'],'Routed DCP changed')
    text=base.build_tcl(args.mode)
    owner=frozen('eda_owned_stage.py');owner.E,owner.W=E,W
    try:
        owner.stage(stage,text,ceiling=360 if args.mode=='bootstrap' else 1800 if args.mode=='route' else 540,
                    run_names=['route_read_v3r8b'])
    finally:
        if out.exists():
            (out/'actual-driver.py').write_bytes(START_BYTES)
            save(out/'input-proof.json',proof);save(out/'route-transform.json',transform)
            save(out/'native-after.json',inventory(NATIVE))
    need(preflight()==proof,'Source, cache, toolchain or original checkpoint changed during stage')
    review=evaluate_phase(args.mode,out)
    if args.mode=='route':
        need(ROUTED.is_file() and (NATIVE/'.route_design.end.rst').is_file()
             and not any(p.name.endswith(('.error.rst','.fail')) for p in NATIVE.iterdir()),'Native routing/report failure')
        save(out/'routed-checkpoint.json',dict(path=str(ROUTED),bytes=ROUTED.stat().st_size,SHA256=sha(ROUTED),
            source_physical_checkpoint_SHA256=PHYS_SHA,route_pass_not_final_acceptance=True))
    save(out/'phase-review.json',review)
    print(json.dumps(dict(phase=stage,passed=True,seconds=time.monotonic()-started,scope='new phase only')))

if __name__=='__main__': main()

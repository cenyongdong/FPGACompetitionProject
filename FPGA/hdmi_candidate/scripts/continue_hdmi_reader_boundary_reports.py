"""Independent consumption of completed R9 native route; retain failed parent.

Explicit audit/reports/review only. No implementation, bit or device operation.
"""
from pathlib import Path
import argparse,hashlib,json,re,sys,types,zipfile
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[3];S=Path(__file__).parent
START=Path(__file__).read_bytes()
E=R/'tools/pose-v1/evidence/hdmi-live-20261018-r9'
E3=R/'tools/pose-v1/evidence/hdmi-live-20261017-r3'
W=R/'.local/hdmi-live-20261018-r9';REF=W/'reference'
NATIVE=REF/'fpai_demo_vivado.runs/impl_read_v3r9'
AUX=REF/'fpai_demo_vivado.runs/report_read_v3r9_r2'
PHYS=NATIVE/'ai7030_edif_top_physopt.dcp';ROUTED=NATIVE/'ai7030_edif_top_routed.dcp'
AUDIT=E/'native-route-consumption-r2'
STAGE='read-v3r9-independent-reports-r1';OUT=E/STAGE
PINS={'ai_read_r9_contract.py':'d4212dfa4f917a1e44327442e25421a771773448be358fa84f6ecf96e96b4dc1',
 'continue_hdmi_reader_boundary_candidate.py':'3e65b5154282f5c714576bde337f01cb34cdf1a4197a7e0a4f072557d86991c5',
 'continue_ai_read_checkpoint.py':'ee11b66896bb84886b186a4667fd4d5c871ec7c404bcc034e56637bacd01504b',
 'eda_owned_stage.py':'3a098b066127c53d26bfb5829c253055fc796e7078888edb0a9ce21acdd2b672',
 'continue_ai_read_candidate.py':'a100884326b044a6c054e8331255135a4e1231a53ad5d86def5ecf208100b55d',
 'continue_ai_monitor_candidate.py':'e30ffbe3fb4231096ab19f6423daaf39994c2427ed52a73086ca07da8cc06941'}
def need(x,msg):
 if not x:raise ValueError(msg)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def frozen(name):
 p=S/name;raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==PINS[name],'Source changed: '+name)
 m=types.ModuleType('r9_independent_'+name.replace('.','_'));m.__file__=str(p)
 exec(compile(raw,str(p),'exec'),m.__dict__);return m
def inventory():
 return {p.relative_to(NATIVE).as_posix():dict(bytes=p.stat().st_size,SHA256=sha(p),mtime_ns=p.stat().st_mtime_ns)
         for p in sorted(NATIVE.rglob('*')) if p.is_file()}
def inputs():
 need(Path(__file__).read_bytes()==START,'Dispatcher changed after start')
 state=load(E3/'continuation-state.json')
 need(not state['whole_task_pause']['paused'] and state['offline_work_continues'],'Task paused')
 need(state['onsite_observation_work']['paused'] and state['old_DATA']=='paused'
      and not state['BOOT_writes_authorized'] and state['remaining_previous_package_reboots']==0,'Board/DATA boundary changed')
 for name,value in PINS.items():need(sha(S/name)==value,'Frozen source changed: '+name)
 h=frozen('ai_read_r9_contract.py')
 prep=h.preparation_identity();h.preparation_identity=lambda:prep
 installed=h.installed_identity(prep);h.installed_identity=lambda proof=None:installed
 sources=h.stable_sources();h.stable_sources=lambda:sources
 original_completed=h.completed;cache={}
 def completed(mode):
  if mode not in cache:cache[mode]=original_completed(mode)
  return cache[mode]
 h.completed=completed
 synthesis=h.verify_synthesis();place=h.completed('place')
 gate=load(E/'read-v3r9-constraints/review.json')
 need(gate['route_prerequisite_pass'] is True and gate['source_sha256']==sources and gate['read_bits']==2768
      and gate['r9_contract_SHA256']==PINS['ai_read_r9_contract.py'],'Actual constraints changed')
 h.completed('constraints')
 physical=h.checkpoint_identity(PHYS)
 need(physical['SHA256']=='b948f0e4b2d90c0ac67cfd82e50bba980a5b80dea494e7ac6ac9f31808955b21'
      and load(E/'place-native-completion-r1/review.json')['physical_checkpoint']==physical,'Physical lineage changed')
 failed=E/'read-v3r9-route';execution=load(failed/'execution.json')
 need(execution['exit']==1 and not execution['stopped_by_monitor']
      and not (failed/'phase-review.json').exists(),'Original parent failure changed')
 wrapper=load(E/'route-wrapper-final-result.json')
 need(wrapper['exit_code']==1 and 'EDA failed/stopped' in wrapper['output'],'Actual wrapper failure not preserved')
 need('HDMI_READER_R9_STAGE_FAILED Fresh route incomplete/stale' in (failed/'stdout.txt').read_text(),
      'Not the known combined STATUS/NEEDS_REFRESH postcondition')
 source_proof=load(failed/'input-proof.json')
 need(source_proof['source_sha256']==sources and source_proof['driver_SHA256']==PINS['continue_hdmi_reader_boundary_candidate.py']
      and source_proof['parent_checkpoint']==physical,'Actual route input lineage changed')
 d=frozen('continue_hdmi_reader_boundary_candidate.py');d.preflight()
 before,after=load(failed/'OOC-cache-before.json'),load(failed/'OOC-cache-after.json')
 metadata=source_proof['OOC_metadata_expected_paths']
 need(before==source_proof['OOC_cached_files_before'],'Actual cache-before differs')
 comparison=d.compare_ooc_cache(before,after,metadata)
 need(comparison==load(failed/'OOC-cache-comparison.json') and comparison['passed'],'Original cache comparison changed')
 d.compare_ooc_cache(after,d.cached_ooc_inventory(),metadata)
 for name in ['.route_design.end.rst','.vivado.end.rst']:
  need((NATIVE/name).is_file() and (NATIVE/name).stat().st_size==0,'Native completion absent: '+name)
 need(not any(p.name.endswith(('.error.rst','.fail')) for p in NATIVE.iterdir()),'Native failure marker exists')
 text=(NATIVE/'runme.log').read_text()
 need('route_design completed successfully' in text and not re.search(r'^ERROR:',text,re.M),'Native route failed')
 native=(NATIVE/'ai7030_edif_top.tcl').read_text()
 commands=[x.strip() for x in native.splitlines() if re.match(r'^\s*(?:route_design|place_design|phys_opt_design|opt_design|write_bitstream)\b',x)]
 need(commands==['route_design -directive NoTimingRelaxation'] and native.count('open_checkpoint ai7030_edif_top_physopt.dcp')==1,
      'Actual continuation is not route-only from its physical checkpoint')
 need(len(re.findall(r'^\s*source\s+'+re.escape(REF.as_posix())+r'/ip_patch/process_control/implementation_route_post\.tcl\s*$',native,re.M))==1,
      'Complete original route-post hook differs')
 route_status=(NATIVE/'ai7030_edif_top_route_status.rpt').read_text()
 counts=[]
 for key in ['routable nets','fully routed nets','nets with routing errors']:
  found=re.findall(r'# of '+key+r'\.*\s*:\s*(\d+)\s*:',route_status);need(len(found)==1,'Route status field differs');counts.append(int(found[0]))
 need(counts[0]>0 and counts[0]==counts[1] and counts[2]==0,'Native is not fully routed/error-free')
 proof=dict(dispatcher_SHA256=hashlib.sha256(START).hexdigest(),source_sha256=sources,
  installed_identity_ledger_SHA256=h.sha(h.INSTALLED),installed_sha256=installed['actual'],
  synthesis_checkpoint=synthesis['synthesis_checkpoint'],physical_checkpoint=physical,
  routed_checkpoint=h.checkpoint_identity(ROUTED),native_inventory=inventory(),
  original_route_execution_SHA256=sha(failed/'execution.json'),original_route_wrapper_SHA256=sha(E/'route-wrapper-final-result.json'),
  original_parent_exit=1,historical_STATUS_and_NEEDS_REFRESH='unknown; never reconstructed',
  constraints_review_SHA256=sha(E/'read-v3r9-constraints/review.json'),actual_source_pins=PINS,
  upstream_phase_evidence={mode:h.completed(mode) for mode in ['setup','synthesis','constraints','place']},
  route_counts=counts,new_timing_or_DRC_waiver=False,new_BOOT_or_reboot_permission=False)
 return proof,h,gate

def report_tcl():
 b=frozen('continue_ai_read_checkpoint.py')
 header,route,endpoints,reports=b.pieces()
 need(endpoints.count('@@EVIDENCE@@/managed-PS-observer-r2/')==2,'Historical PS receipt bindings differ')
 endpoints=endpoints.replace('@@EVIDENCE@@',E3.as_posix())
 b.E,b.W,b.REF,b.NATIVE=E,W,REF,AUX
 b.CHECKPOINT,b.CHECKPOINT_SHA,b.ROUTED=PHYS,'b948f0e4b2d90c0ac67cfd82e50bba980a5b80dea494e7ac6ac9f31808955b21',ROUTED
 b.pieces=lambda:(header,route,endpoints,reports)
 text=b.build_tcl('reports')
 anchor='open_checkpoint {'+ROUTED.as_posix()+'}'
 query='''open_project {@@REF@@/fpai_demo_vivado.xpr}
set f [open {@@OUT@@/current-managed-route-properties.txt} {WRONLY CREAT EXCL}]
set r [get_runs impl_read_v3r9]
foreach p {STATUS NEEDS_REFRESH PROGRESS} {puts $f "$p|[get_property $p $r]"}
close $f
close_project
'''
 need(text.count(anchor)==1,'Actual routed checkpoint opening differs')
 text=text.replace(anchor,query+anchor)
 need(not re.search(r'^\s*(?:route_design|place_design|phys_opt_design|opt_design|write_bitstream|launch_runs|reset_run)\b',text,re.M),
      'Independent reports contain an implementation command')
 return text

def report_phase(h,gate):
 result=load(OUT/'execution.json')
 need(result['exit']==0 and not result['stopped_by_monitor'],'Independent report tool failed')
 helper,_=h.constraints_algorithms()
 indices=helper.parse_indices((OUT/'checkpoint-binding.txt').read_text(),'source','capture')
 need(indices==gate['read_indices'],'Restored read bit identity differs')
 endpoints=helper.snapshot_endpoints(OUT/'read-snapshot-endpoints.txt',indices)
 clocks=helper.clock_taps(OUT/'clock-taps.txt',indices)
 need(clocks['source_period_ns']==5. and clocks['csr_period_ns']==10.,'Restored clocks differ')
 return dict(passed=True,mode='independent_reports',scope='new report stage only; original route parent exit1 remains',
             read_bits=len(indices),actual_endpoints=endpoints,actual_clocks=clocks,
             original_route_parent_phase_passed=False,board_executed=False)

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['audit','reports','review'],nargs='?',default='audit')
 mode=parser.parse_args().mode
 proof,h,gate=inputs()
 if mode=='audit':
  AUDIT.mkdir()
  with zipfile.ZipFile(ROUTED) as archive:need(archive.testzip() is None,'Routed DCP archive CRC failed')
  save(AUDIT/'input-proof.json',proof)
  for path in NATIVE.iterdir():
   if path.is_file() and path.suffix in ['.tcl','.log','.rpt','.rst']:(AUDIT/path.name).write_bytes(path.read_bytes())
  (AUDIT/'actual-dispatcher.py').write_bytes(START)
  save(AUDIT/'review.json',dict(native_routed_checkpoint_consumption_accepted=True,
       scope='completed native route and immutable source lineage; no original parent phase or final STA acceptance',
       original_route_parent_exit=1,original_route_parent_phase_passed=False,
       actual_native_scope='route-only from b948 physical checkpoint; one complete original JFM hook',
       historical_STATUS_and_NEEDS_REFRESH_unknown=True,input_proof_SHA256=sha(AUDIT/'input-proof.json'),
       routed_checkpoint=proof['routed_checkpoint'],new_BOOT_or_reboot_permission=False))
  print(json.dumps(dict(native_consumption_accepted=True,routed_checkpoint=proof['routed_checkpoint'])));return
 need(load(AUDIT/'input-proof.json')==proof and load(AUDIT/'review.json')['native_routed_checkpoint_consumption_accepted'],
      'Native input audit changed')
 if mode=='reports':
  need(not OUT.exists() and not (W/STAGE).exists() and not AUX.exists(),'Preserve previous independent report session')
  AUX.mkdir();save(AUX/'report-owner.json',dict(source_routed_checkpoint=proof['routed_checkpoint'],dispatcher_SHA256=proof['dispatcher_SHA256']))
  owner=frozen('eda_owned_stage.py');owner.E,owner.W=E,W
  try:owner.stage(STAGE,report_tcl(),ceiling=540,run_names=[AUX.name])
  finally:
   if OUT.exists():
    (OUT/'actual-dispatcher.py').write_bytes(START);save(OUT/'input-proof.json',proof)
    for name in PINS:(OUT/('frozen-'+name)).write_bytes((S/name).read_bytes())
  need(inputs()[0]==proof,'Actual report process changed protected inputs/native products')
  save(OUT/'phase-review.json',report_phase(h,gate));print('R9_INDEPENDENT_REPORT_PHASE_PASS');return
 need(load(OUT/'input-proof.json')==proof and load(OUT/'phase-review.json')==report_phase(h,gate),'Report receipt/input changed')
 evaluate,algorithm=h.routed_report_algorithm();helper,_=h.constraints_algorithms()
 phases=dict(proof['upstream_phase_evidence'])
 phases['native_route_consumption']={name:sha(AUDIT/name) for name in ['review.json','input-proof.json']}
 phases['independent_reports']={name:sha(OUT/name) for name in ['execution.json','phase-review.json','input-proof.json']}
 review=evaluate(OUT,NATIVE,gate,helper,proof['source_sha256'],h.INSTALLED,load(h.INSTALLED),phases,h.CONSTRAINTS)
 review.update(candidate_run='impl_read_v3r9',managed_run=True,actual_review_producer_SHA256=proof['dispatcher_SHA256'],
     original_route_parent_phase_passed=False,original_route_parent_exit=1,
     native_route_consumption_review_SHA256=sha(AUDIT/'review.json'),retained_routed_algorithm=algorithm,
     checkpoint_continuation=dict(source_physical_checkpoint=proof['physical_checkpoint'],routed_checkpoint=proof['routed_checkpoint']),
     current_properties_are_later_observations_not_historical_values=True)
 save(OUT/'review.json',review)
 print(json.dumps({key:review[key] for key in ['bit_generation_prerequisite_pass','global_setup_WNS_ns','global_hold_WHS_ns','read_bits']}))

if __name__=='__main__':main()

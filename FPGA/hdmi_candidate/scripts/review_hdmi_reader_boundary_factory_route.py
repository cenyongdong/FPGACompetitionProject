"""Pure R9 final gate: unchanged report decisions, explicit actual factory DRC input."""
from pathlib import Path
import hashlib,json,re,types
R=Path(__file__).resolve().parents[3];S=Path(__file__).parent
START=Path(__file__).read_bytes()
E=R/'tools/pose-v1/evidence/hdmi-live-20261018-r9'
REPORTS=E/'read-v3r9-independent-reports-r1'
DRC=E/'read-v3r9-factory-drc-r2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def code_identity(code):
 def value(x):
  if isinstance(x,types.CodeType):return code_identity(x)
  if isinstance(x,bytes):return {'bytes':x.hex()}
  if isinstance(x,tuple):return {'tuple':[value(y) for y in x]}
  if isinstance(x,frozenset):return {'frozenset':sorted((value(y) for y in x),key=lambda y:json.dumps(y,sort_keys=True))}
  return {'type':type(x).__name__,'repr':repr(x)}
 return {key:value(getattr(code,key)) for key in dir(code) if key.startswith('co_') and not callable(getattr(code,key))}
def code_sha(code):return hashlib.sha256(json.dumps(code_identity(code),sort_keys=True,separators=(',',':')).encode()).hexdigest()
def module(name,digest):
 p=S/name;raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
 m=types.ModuleType('final_r9_'+name.replace('.','_'));m.__file__=str(p)
 exec(compile(raw,str(p),'exec'),m.__dict__);return m

def fresh_review():
 assert Path(__file__).read_bytes()==START
 c=module('continue_hdmi_reader_boundary_reports.py','528fa208e01a3de18f3f312ce929458ea5c94dc59845dae2e4f036bf79f00967')
 proof,h,gate=c.inputs()
 assert load(c.AUDIT/'input-proof.json')==load(REPORTS/'input-proof.json')==load(DRC/'input-proof.json')==proof
 assert load(REPORTS/'phase-review.json')==c.report_phase(h,gate)
 execution,profile=load(DRC/'execution.json'),load(DRC/'phase-review.json')
 assert execution['exit']==0 and not execution['stopped_by_monitor'] and profile['passed'] is True
 assert profile['source_routed_checkpoint']==proof['routed_checkpoint'] and profile['new_timing_or_DRC_waiver'] is False
 assert profile['restored_existing_disabled_rules']==['REQP-44','REQP-46','REQP-52','REQP-56']
 assert profile['actual_dispatcher_SHA256']==sha(S/'check_hdmi_reader_boundary_factory_drc.py')=='e145581d66ee31f66420a3b19338d49184711e3dfa367a66202f9bc844dd30fc'
 assert (DRC/'actual-dispatcher.py').read_bytes()==(S/'check_hdmi_reader_boundary_factory_drc.py').read_bytes()
 factory=DRC/'factory-DRC.rpt'
 assert profile['factory_DRC_SHA256']==sha(factory) and Path(profile['factory_DRC_path']).resolve()==factory.resolve()
 native_drc=c.NATIVE/'ai7030_edif_top_drc_routed.rpt'
 assert sha(native_drc)==profile['original_native_default_DRC_SHA256']
 assert re.findall(r'^(\S+#\d+) Error$',native_drc.read_text(),re.M)==['REQP-52#1','REQP-56#1']
 for name,digest in profile['original_factory_hook_SHA256'].items():assert sha(c.REF/'ip_patch/process_control'/name)==digest
 original,algorithm=h.routed_report_algorithm()
 code=original.__code__;literal='ai7030_edif_top_drc_routed.rpt'
 indices=[i for i,x in enumerate(code.co_consts) if type(x) is str and x==literal]
 assert len(indices)==1
 position=indices[0];values=list(code.co_consts);values[position]=factory.as_posix()
 # Windows Path's absolute right operand points to the recorded actual report.
 assert (c.NATIVE/values[position]).resolve()==factory.resolve()
 changed=code.replace(co_consts=tuple(values))
 assert changed.co_code==code.co_code
 inverse=list(changed.co_consts);inverse[position]=code.co_consts[position]
 assert code_identity(changed.replace(co_consts=tuple(inverse)))==code_identity(code)
 evaluate=types.FunctionType(changed,original.__globals__,original.__name__,original.__defaults__,original.__closure__)
 helper,_=h.constraints_algorithms()
 phases=dict(proof['upstream_phase_evidence'])
 phases['native_route_consumption']={name:sha(c.AUDIT/name) for name in ['review.json','input-proof.json']}
 phases['independent_reports']={name:sha(REPORTS/name) for name in ['execution.json','phase-review.json','input-proof.json']}
 phases['restored_factory_DRC']={name:sha(DRC/name) for name in ['execution.json','phase-review.json','factory-DRC.rpt']}
 review=evaluate(REPORTS,c.NATIVE,gate,helper,proof['source_sha256'],h.INSTALLED,load(h.INSTALLED),phases,h.CONSTRAINTS)
 review.update(candidate_run='impl_read_v3r9',managed_run=True,
   actual_review_producer_SHA256=hashlib.sha256(START).hexdigest(),report_producer_SHA256=proof['dispatcher_SHA256'],
   original_route_parent_phase_passed=False,original_route_parent_exit=1,
   native_route_consumption_review_SHA256=sha(c.AUDIT/'review.json'),retained_routed_algorithm=algorithm,
   factory_DRC_profile_reinstatement=profile,
   explicit_factory_DRC_reader_adaptation=dict(constant_index=position,old_filename=literal,actual_report_path=str(factory),
       actual_report_SHA256=sha(factory),Python_decision_bytecode_unchanged=True,inverse_all_public_code_fields_equal=True,
       original_code_SHA256=code_sha(code),adapted_code_SHA256=code_sha(changed)),
   checkpoint_continuation=dict(source_physical_checkpoint=proof['physical_checkpoint'],routed_checkpoint=proof['routed_checkpoint']),
   current_properties_are_later_observations_not_historical_values=True)
 return review

def main():
 review=fresh_review();p=REPORTS/'review.json'
 with p.open('x',encoding='utf-8') as f:json.dump(review,f,indent=2,ensure_ascii=False,allow_nan=False)
 print(json.dumps({key:review[key] for key in ['bit_generation_prerequisite_pass','global_setup_WNS_ns','global_hold_WHS_ns','read_bits']}))

if __name__=='__main__':main()

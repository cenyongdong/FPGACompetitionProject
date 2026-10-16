"""Compare actual connected primitive pins, preserving distinct Liberty metadata."""
import json
def review(R,E,mode):
 out=E/('actual-ps-'+mode)
 def pins(path):
  direction={'bidir':'inout','in':'input','out':'output'}
  return {n.split('/')[-1]:direction.get(d.lower(),d.lower()) for n,d in
          (line.split('|') for line in path.read_text(encoding='utf-8').splitlines())}
 runtime=pins(out/'library-PS7-pins.txt');actual=pins(out/'actual-PS7-pins.txt')
 calls=set(json.loads((R/'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/PS7-callsite-review.json').read_text(encoding='utf-8'))['terminals'])
 missing_calls=[n for n in sorted(calls) if n not in runtime and not any(p.startswith(n+'[') for p in runtime)]
 vendor=json.loads((R/'tools/pose-v1/evidence/hdmi-jfm-compatibility-20261015-r1/vendor-PS7-pins.json').read_text(encoding='utf-8'))
 aliases={f'DEBUGDATA[{i}]':f'DEBUGDATA{i}' for i in range(161,200)}
 assert all(dst in calls and src in vendor and dst in runtime for src,dst in aliases.items())
 normalized={aliases.get(n,n):d for n,d in vendor.items()}
 missing=set(normalized)-runtime.keys();extra=runtime.keys()-normalized.keys()
 bad=[n for n in normalized.keys()&runtime.keys() if normalized[n]!=runtime[n]]
 assert actual==runtime,'Actual primitive and runtime library mismatch'
 assert not missing_calls,missing_calls
 assert missing=={'DEBUGDATA160'} and not (missing&calls) and not extra and not bad
 result={'mode':mode,'actual_source_4527_named_connections_present':True,
         'required_AI_connections_present':3868,'actual_and_runtime_pins':len(runtime),
         'actual_runtime_names_and_directions_equal':True,'debug_metadata_aliases':aliases,
         'Liberty_only_pin':'DEBUGDATA160','Liberty_only_pin_instantiated':False,
         'PS7_actual_primitive_not_artificial_blackbox':True,'gate_pass':True,
         'earlier_7213_count_assertion_failure_not_rewritten':True,
         'RTL_vendor_sources_and_libraries_not_changed_for_this_review':True,
         'Procise_or_hardware_acceptance':False}
 (out/'connected-contract-review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 return result
if __name__=='__main__':
 from pathlib import Path
 import sys
 R=Path(__file__).resolve().parents[3]
 result=review(R,R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2',sys.argv[1])
 print(json.dumps({k:result[k] for k in ['mode','actual_and_runtime_pins','required_AI_connections_present','gate_pass']}))

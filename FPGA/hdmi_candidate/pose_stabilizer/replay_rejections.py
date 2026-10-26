"""Read-only regression of original r8/r9 evidence; never translates it into lean admission."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'software/pose180_pipeline/resident'))
from test_witness import read_run,load
old=ROOT/'FPGA/hdmi_candidate/diagnostics/deferred_consume_r45'
sys.modules['consume_gate']=load(old/'gates/consume_gate.py','consume_gate')
gate=load(old/'before_seed_gate.py','seed')
result={}
for name,run in [('r8','pose180-resident-phase-20261025-r8'),('r9','pose180-resident-witness-20261025-r9')]:
 before,trace,protocol=read_run(ROOT/'.local'/run/'evidence/startup')
 decision=gate.evaluate(before,trace,protocol)
 if decision['eligible'] or decision['continue_allowed']:raise RuntimeError('Historical rejection unexpectedly admitted')
 result[name]=dict(original_gate=decision,lean_profile='not_applicable_legacy_evidence',lean_admitted=False)
out=ROOT/'.local/pose-postprocess-offline/legacy-rejections.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(out)

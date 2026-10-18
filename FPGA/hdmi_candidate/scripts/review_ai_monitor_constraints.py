"""Fail-closed gate for the observer's new CDC; retains generic tool warnings."""
from pathlib import Path
import json,re,collections,hashlib
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r2';P=E/'monitor-v2-constraints'
W=R/'.local/hdmi-live-20261017-r1/reference'
assert not (P/'review.json').exists()
assert json.loads((P/'execution.json').read_text())['exit']==0
binding=(P/'binding.txt').read_text()
bits=[int(x) for x in re.search(r'source_bits=(\d+) capture_bits=(\d+)',binding).groups()]
assert bits[0]==bits[1] and 700<=bits[0]<=768
assert 'stable_bus_requirement=10.000' in binding
rows=[line for line in (P/'observer-CDC.rpt').read_text().splitlines() if re.match(r'^\s*\d+\s+CDC-\d+\s',line)]
counts=dict(collections.Counter(re.search(r'CDC-\d+',line)[0] for line in rows))
assert counts=={'CDC-3':2,'CDC-15':bits[0],'CDC-9':2},counts
assert not any('Critical' in line for line in rows)
for line in rows:
 if 'CDC-15' in line:
  assert 'Max Delay Datapath Only' in line and 'source_snapshot_reg[' in line and 'csr_snapshot_reg[' in line
 elif 'CDC-3' in line:
  assert 'Depth' not in line and 'False Path' in line
  assert ('request_toggle_reg/C' in line and 'request_sync_reg[0]/D' in line) or ('ack_toggle_reg/C' in line and 'ack_sync_reg[0]/D' in line)
 else:
  assert 'release_reg[0]/CLR' in line and 'False Path' in line
timing=(P/'observer-snapshot-path.rpt').read_text()
assert 'Requirement:            10.000ns' in timing and 'VIOLATED' not in timing
preparation=json.loads((R/'tools/pose-v1/evidence/hdmi-live-20261017-r1/monitor-candidate-preparation.json').read_text())
sources={}
for rel,expected in preparation['RTL_before'].items():
 p=W/'rtl'/rel;actual=hashlib.sha256(p.read_bytes()).hexdigest()
 if rel!='ps_ai_peripheral.sv':assert actual==expected,rel
 sources['rtl/'+rel]=actual
for rel in ['rtl/hdmi_candidate/ai_event_monitor.sv','constrs_1/ai7030.xdc','constrs_1/hdmi_cdc.tcl','constrs_1/hdmi_cdc.xdc','constrs_1/ai_monitor_cdc.tcl','ip_patch/process_control/implementation_opt_pre_hdmi.tcl']:
 sources[rel]=hashlib.sha256((W/rel).read_bytes()).hexdigest()
assert (W/'constrs_1/hdmi_cdc.tcl').read_bytes()==(W/'constrs_1/hdmi_cdc.xdc').read_bytes()
review={'route_prerequisite_pass':True,'scope':'local route only; not routed timing or board acceptance',
 'stable_bus_ns':10,'bits':bits[0],'CDC_row_counts':counts,'manual_review':'held snapshot until next accepted request; two-stage synchronized ack; both-domain coordinated hard reset and three-stage local release; only reset-chain CLR and first synchronizer D cut',
 'source_sha256':sources,'raw_reset_metadata_bits_14_13':'reserved zero, no new exception',
 'original_failed_gate':'../monitor-constraints/review.json','new_BOOT_or_reboot_authorized':False}
(P/'review.json').write_text(json.dumps(review,indent=2))
print(json.dumps({k:v for k,v in review.items() if k!='source_sha256'}))

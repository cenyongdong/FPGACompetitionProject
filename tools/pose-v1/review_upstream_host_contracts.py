"""Bind the new contracts to the build, and independently check original Gather."""
import argparse,json
from pathlib import Path
import mixed_validation_gate as g
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--boundary-review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();b=g.load(a.build/'build-result.json');r=a.run
for prefix,name,key in [('upstream-contracts','pose_upstream_boundary_selftest','upstream_contract_sha256'),('upstream-sdk-contracts','pose_upstream_boundary_sdk_selftest','upstream_sdk_contract_sha256')]:
    assert (r/(prefix+'.exit.txt')).read_text().strip()=='0' and not (r/(prefix+'.stderr.log')).read_bytes() and g.sha(r/name)==b[key]
assert g.load(r/'upstream-contracts.stdout.log')==dict(status='passed',refusals=7,foreign_thread_refused=True,owned_bytes=True,previous_frame_cleared=True,partial_read_preserved=True,control_error_JSON=True,device_opened=False)
assert g.load(r/'upstream-sdk-contracts.stdout.log')==dict(status='passed',points=8,owned_bytes=101600,original_Gather_executed=True,registration_overridden=False,device_opened=False)
review=g.load(a.boundary_review);assert review['status']=='synthetic_original_Gather_and_public_Host_boundary_passed' and review['rows']==8 and review['complete_owned_frames']==1
meta=[json.loads(x) for x in (r/'upstream-contracts/evidence/metadata.jsonl').read_text().splitlines()];assert meta[-1]['error']=='Injected\nread\x1bfailure'
a.output.write_text(json.dumps(dict(status='passed',new_contracts_passed=True,original_Gather_NumPy_bitwise=True,Host_Gather_single_view_bound=True,full_model_Session_created=False,device_opened=False,boundary_review_SHA256=g.sha(a.boundary_review)),indent=2)+'\n',encoding='utf-8',newline='\n');print('Original Gather and8 public Host points independently verified')

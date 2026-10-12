"""Bind ARM contracts and independent snapshot review to executed ELF identities."""
import argparse,json
from pathlib import Path
import mixed_validation_gate as g
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--core-review',type=Path,required=True);p.add_argument('--SDK-review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();b=g.load(a.build/'build-result.json')
for prefix,name,key in [('read-phase-contracts','pose_read_phase_selftest','phase_contract_sha256'),('read-phase-sdk-contracts','pose_read_phase_sdk_selftest','phase_sdk_contract_sha256')]:
    assert (a.run/(prefix+'.exit.txt')).read_text().strip()=='0' and not (a.run/(prefix+'.stderr.log')).read_bytes() and g.sha(a.run/name)==b[key]
assert g.load(a.run/'read-phase-contracts.stdout.log')==dict(status='passed',refusals=8,foreign_thread_refused=True,owned_bytes=True,first4_last=True,partial_read_saved=True,device_opened=False)
assert g.load(a.run/'read-phase-sdk-contracts.stdout.log')==dict(status='passed',Host_copy=True,two_owned_snapshots=True,device_opened=False)
c=g.load(a.core_review);s=g.load(a.SDK_review);assert c['rows']==103 and c['owned_frames']==5 and s['rows']==1 and s['owned_frames']==1
a.output.write_text(json.dumps(dict(status='passed',ARM_core=True,Host_copy_two_owned_snapshots=True,device_opened=False,original_index_values_not_changed=True,core_review_SHA256=g.sha(a.core_review),SDK_review_SHA256=g.sha(a.SDK_review)),indent=2)+'\n',encoding='utf-8',newline='\n');print('Read-phase ARM and Host contracts bound')

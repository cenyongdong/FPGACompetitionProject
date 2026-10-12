"""Additional exact contract audit; does not mutate the prepared manifest."""
import argparse,json
from pathlib import Path
import mixed_validation_gate as g
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
b=g.load(a.build/'build-result.json');r=a.run
for prefix,name,key in [('final-contracts','pose_final_source_selftest','final_contract_sha256'),('final-sdk-contracts','pose_final_source_sdk_selftest','final_sdk_contract_sha256')]:
    assert (r/(prefix+'.exit.txt')).read_text().strip()=='0' and not (r/(prefix+'.stderr.log')).read_bytes() and g.sha(r/name)==b[key]
contract=g.load(r/'final-contracts.stdout.log');assert contract==dict(status='passed',refusals=7,foreign_thread_refused=True,owned_bytes=True,two_rounds=True,partial_read_saved=True,bad_result_saved=True,previous_frame_cleared=True,device_opened=False)
sdk=g.load(r/'final-sdk-contracts.stdout.log');assert sdk==dict(status='passed',public_Host_reads=8,source_bytes=67200,CPU_output_bytes=17600,device_opened=False)
root=r/'final-sdk-contracts';idx=g.load(root/'index.json');assert len(idx['sources'])==4 and len(idx['cpu_outputs'])==3 and len(idx['reads'])==8 and all(x['complete'] and x['end_ns']>=x['begin_ns']>0 for x in idx['reads'])
for op in [582,649]:
    for slot in [0,1]:
        blob=(root/f'host.{op}.{slot}.f32').read_bytes();assert len(blob)==16800 and blob==(root/f'round0.{op}.{slot}.f32').read_bytes()==(root/f'round1.{op}.{slot}.f32').read_bytes()
assert sum(x['bytes'] for x in idx['cpu_outputs'])==17600
a.output.write_text(json.dumps(dict(status='passed',contract=contract,SDK_contract=sdk,public_Host_bytes_two_rounds=134400,device_opened=False),indent=2)+'\n',encoding='utf-8',newline='\n');print('Final recorder and save-only ARM contracts independently passed')

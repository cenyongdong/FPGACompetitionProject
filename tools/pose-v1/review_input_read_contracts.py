"""New SDK Host-read and actual new-bridge Host107 gate, no hardware call."""
import argparse,json
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
from review_input_read_build_base import identities
p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
m,b,n=identities(a.package,a.build);r=a.results;g.verify(r);assert (r/'exit.txt').read_text().strip()=='0'
tests=[('pose_input_read_selftest','read_selftest_sha256',dict(status='passed',refusals=8,guard_bytes=16,original_error_preserved=True,SDK_device=False)),('pose_input_read_sdk_selftest','read_sdk_selftest_sha256',dict(status='passed',refusals=3,Host_read_bytes=47040,types_from_op=192,device_opened=False))]
for name,key,expected in tests:
    assert g.sha(r/name)==b[key] and g.load(r/(name+'.stdout.json'))==expected
for name,key in [(x[0],x[1]) for x in tests]+[('pose_input_read_host_check','read_host_binary_sha256')]:
    assert g.sha(r/name)==b[key] and (r/(name+'.exit.txt')).read_text().strip()=='0' and not (r/(name+'.stderr.log')).read_bytes()
host=r/'host';rows=[json.loads(x) for x in (host/'cases.jsonl').read_text().splitlines()];wanted=g.load(a.package/'cpu-fixture-manifest.json')['cases'];assert len(rows)==len(wanted)==107;g.registry(host/'registry.jsonl');total=0;outputs=0
for actual,case in zip(rows,wanted):
    assert actual['passed'] and all(actual[k]==case[k] for k in ('case_id','op_id','expected')) and actual['rejection']==('' if case['expected']=='PASS' else case['expected'])
    for i in range(case['outputs']):
        blob=(host/case['case_id']/f'output{i}.f32').read_bytes();assert blob==(a.package/'fixtures'/case['case_id']/f'expected{i}.f32').read_bytes() and np.isfinite(np.frombuffer(blob,'<f4')).all();total+=len(blob)//4;outputs+=1
assert total==59600 and outputs==22 and (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
report=dict(status='input_read_Host_contracts_passed',Host107_new_run=True,Host_cases=107,registry_records=12,outputs=22,CPU_FP32=total,SDK_Host_read_bytes=47040,read_refusals=11,read_picture_binary_sha256=b['read_picture_binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],device_opened=False)
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(report)

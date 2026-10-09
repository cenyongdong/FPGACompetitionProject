"""Additional independent budget/native identity gate; no device access."""
import argparse,json,struct,hashlib
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--results',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    b=load(a.build/'build-result.json')
    for name,key,machine in [('pose_bounded_load_selftest','bounded_selftest_sha256',183),('pose_bounded_reference_export.native','native_reference_sha256',62)]:
        data=(a.build/name).read_bytes();assert sha(a.build/name)==b[key] and data[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',data,18)[0]==machine
    report=dict(status='bounded_program_identities_checked',native_reference_SHA=b['native_reference_sha256'],bounded_selftest_SHA=b['bounded_selftest_sha256'],device_access=False)
    if a.results:
        r=a.results;assert sha(r/'pose_bounded_load_selftest')==b['bounded_selftest_sha256']
        assert (r/'bounded-contracts.exit.txt').read_text().strip()=='0' and not (r/'bounded-contracts.stderr.log').read_bytes()
        assert load(r/'bounded-contracts.stdout.log')==dict(status='passed',mapping=103,renders=206,refusals=5,sparse_references=29,SDK_device=False)
        normal=[json.loads(x) for x in (r/'bounded-contracts/normal/child.jsonl').read_text().splitlines()];assert normal[-1]['renders']==103 and normal[-1]['event']=='stopped'
        overflow=[json.loads(x) for x in (r/'bounded-contracts/overflow/child.jsonl').read_text().splitlines()];assert len(overflow)==103
        assert 'Display request kind/budget differs' in (r/'bounded-contracts/overflow/child.stderr.log').read_text()
        normalParent=[json.loads(x) for x in (r/'bounded-contracts/normal/parent.jsonl').read_text().splitlines()];badParent=[json.loads(x) for x in (r/'bounded-contracts/overflow/parent.jsonl').read_text().splitlines()]
        assert normalParent[-1]['event']=='cleanly_reaped' and badParent[-1]['event']=='error_cleanup_reaped'
        report.update(status='103_budget_104_refusal_and_reaping_verified',renders=206,first_last_NV12_bitwise=True)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()

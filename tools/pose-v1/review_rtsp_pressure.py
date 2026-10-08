"""Audit intentional transport rejection without model/codec initialization."""
import argparse,hashlib,json
from pathlib import Path
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);a=p.parse_args()
out=a.evidence/'completion-review.json';assert not out.exists();r=a.evidence/'board';m=load(a.package/'manifest.json');b=load(a.build/'build-result.json');root=Path(__file__).resolve().parents[2]
for rel,h in b['sources'].items():assert sha(root/rel)==h==sha(a.build/Path(rel).name)
assert sha(r/'pose_rtsp_pressure_check')==m['program_sha256']==b['programs']['pose_rtsp_pressure_check']
count=0
for line in (r/'files.sha256').read_text().splitlines():
    h,name=line.split('  ',1);assert name.startswith('run-pressure/');path=r/name[len('run-pressure/'):];assert r.resolve() in path.resolve().parents and sha(path)==h;count+=1
assert (r/'exit.txt').read_text().strip()=='1' and (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
assert ':8554' not in (r/'listeners.after.txt').read_text()
base=load(root/'tools/pose-v1/evidence/resident-20261008-r6/resident-three/preflight.json');pre=load(r/'preflight.json')
assert all(pre[k]==base[k] for k in ('boot_files','libraries','SDK_packages','fpga_state'))
events=[json.loads(line) for line in (r/'results/network/events.jsonl').read_text().splitlines()]
bounds=[e for e in events if e['event']=='TCP_buffer_bound'];assert len(bounds)==1 and bounds[0]['requested']==65536 and bounds[0]['actual']==131072
errors=[i for i,e in enumerate(events) if e['event']=='rtp_send_error'];assert errors and all(e['event'] not in ('au_received','nal_delivered') for e in events[errors[0]+1:])
assert events[-1]['event']=='completed' and events[-1]['failed'] and events[-1]['sources_live']==0
summary=load(r/'results/summary.json');assert summary['rejected'] and not summary['VPU_NPU'] and summary['AU_high_water']<=8
stderr=(r/'stderr.log').read_text();assert 'EXPECTED STOP: RTP transport send failed; stop reference chain' in stderr and 'capacity exceeded' not in stderr
peer=load(a.evidence/'client/review.json');assert peer['no_reads_after_PLAY'] and peer['actual_receive_buffer']==4096 and 3<=peer['held_seconds']<=9 and peer['send_error']
result=dict(status='SDK_free_slow_reader_guarded_module_rejected_correctly',program_sha256=m['program_sha256'],returned_hashed_files=count,expected_exit=1,RTP_send_error_propagated=True,TCP_send_buffer_actual=131072,AU_high_water=summary['AU_high_water'],produced=summary['produced'],sources_live=0,port_released=True,kernel_unchanged=True,VPU_NPU=False,guarded_module_integrated_into_r2=False)
out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result,indent=2))

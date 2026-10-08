"""Normal-client control of the exact same guarded module as the slow-reader gate."""
import argparse,hashlib,json,re
from pathlib import Path
import cv2
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[2]
r=a.evidence/'board';m=load(a.package/'manifest.json');b=load(a.build/'build-result.json');out=a.evidence/'completion-review.json';assert not out.exists()
for rel,h in b['sources'].items():assert sha(root/rel)==h==sha(a.build/Path(rel).name)
negative=load(root/'.local/pose-v1-build/rtsp-pressure-20261008-r1/build-result.json')
for rel in b['sources']:
    if rel.endswith(('guarded_rtsp.cpp','guarded_rtsp.hpp','access_unit_channel.cpp','h264_access_unit.cpp')):assert b['sources'][rel]==negative['sources'][rel]
assert sha(r/'pose_rtsp_guarded_normal_check')==m['program_sha256']==b['programs']['pose_rtsp_guarded_normal_check']
count=0
for line in (r/'files.sha256').read_text().splitlines():
    h,name=line.split('  ',1);assert name.startswith('run-normal/');f=r/name[len('run-normal/'):];assert r.resolve() in f.resolve().parents and sha(f)==h;count+=1
assert (r/'exit.txt').read_text().strip()=='0' and (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes() and ':8554' not in (r/'listeners.after.txt').read_text()
base=load(root/'tools/pose-v1/evidence/resident-20261008-r6/resident-three/preflight.json');pre=load(r/'preflight.json');assert all(pre[k]==base[k] for k in ('boot_files','libraries','SDK_packages','fpga_state'))
events=[json.loads(line) for line in (r/'results/network/events.jsonl').read_text().splitlines()];received=[e for e in events if e['event']=='au_received'];sent=[e for e in events if e['event']=='nal_delivered' and e['type']==5]
assert len(received)==300 and not any(e['event']=='rtp_send_error' for e in events)
assert events[-1]['event']=='completed' and not events[-1]['failed'] and events[-1]['sources_live']==0
bounds=[e for e in events if e['event']=='TCP_buffer_bound'];assert len(bounds)==1 and bounds[0]['actual']==131072
summary=load(r/'results/summary.json');assert summary['produced']==300 and not summary['rejected'] and not summary['VPU_NPU'] and summary['AU_high_water']<=8
data=(a.package/'video.h264').read_bytes();index=(a.package/'packets.tsv').read_text().splitlines();size=int(index[0].split()[1]);n=int(index[1].split()[1]);chunk=data[size:size+n];start=re.match(b'\x00\x00(?:\x00)?\x01',chunk);assert start;seed_digest=hashlib.sha256(chunk[start.end():]).hexdigest()
client=load(a.evidence/'client/review.json');frames=client['frames'];assert client['status']=='live_received_pending_board_content_review' and client['server_closed'] and len(frames)==len(sent)>=100
reference=load(root/'tools/pose-v1/evidence/resident-20261008-r6/three-video-review/review.json')['records'][0]['decoded_bgr_sha256']
cap=cv2.VideoCapture(str(a.evidence/'client/received.h264'),cv2.CAP_FFMPEG);assert cap.isOpened();decoded=0
try:
    for i,frame in enumerate(frames):
        assert frame['vcl_sha256']==seed_digest and frame['idr'] and sent[i]['encoded_id']==sent[0]['encoded_id']+i
        ticks=(frame['timestamp']-frames[0]['timestamp'])&0xffffffff;assert abs(ticks-(sent[i]['pts_us']-sent[0]['pts_us'])*0.09)<=1.1
        ok,image=cap.read();assert ok and image.shape==(720,1280,3) and hashlib.sha256(image.tobytes()).hexdigest()==reference;decoded+=1
    assert not cap.read()[0]
finally:cap.release()
assert sent[-1]['encoded_id']==299
result=dict(status='SDK_free_guarded_normal_reader_control_passed',program_sha256=m['program_sha256'],returned_hashed_files=count,producer_frames=300,decoded_network_frames=decoded,TCP_send_buffer_actual=131072,guarded_module_same_negative=True,send_errors=0,exact_seed_pixels=True,actual_producer_RTP_PTS=True,port_released=True,kernel_unchanged=True,VPU_NPU=False,guarded_module_integrated_into_r2=False)
out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result,indent=2))

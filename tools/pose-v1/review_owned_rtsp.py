"""Independent adapter-gate review; recorded packets are not online VPU proof."""
import argparse,hashlib,json,re
from pathlib import Path
import cv2

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def rows(path):return [json.loads(x) for x in path.read_text().splitlines()]
def main():
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--frames',type=int,choices=(54,100),default=100);p.add_argument('--require-active',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parents[2];board=a.evidence/'board';clients=a.evidence/'clients';output=a.output
    assert not output.exists();output.mkdir()
    manifest=load(a.package/'manifest.json');build=load(a.build/'build-result.json')
    for rel,digest in build['sources'].items():assert sha(root/rel)==digest==sha(a.build/Path(rel).name)
    count=0
    for row in (board/'files.sha256').read_text().splitlines():
        digest,name=row.split('  ',1);assert name.startswith('run-owned/')
        target=board/name[len('run-owned/'):];assert board.resolve() in target.resolve().parents and sha(target)==digest;count+=1
    assert (board/'exit.txt').read_text().strip()==(board/'host.exit.txt').read_text().strip()=='0'
    assert not (board/'host.stderr.log').read_bytes()
    assert load(board/'host.stdout.log')==dict(status='passed',rejections=17,threaded_units=2000,capacity=8,no_device=True)
    assert (board/'dmesg.before.log').read_bytes()==(board/'dmesg.after.log').read_bytes()
    assert ':8554' not in (board/'listeners.after.txt').read_text()
    for name,digest in manifest['programs'].items():assert sha(board/name)==digest==build['programs'][name]
    actual=load(board/'preflight.json');baseline=load(a.package/'baseline-preflight.json')
    assert all(actual[k]==baseline[k] for k in ('boot_files','libraries','SDK_packages','fpga_state'))
    events=rows(board/'results/events.jsonl');received=[e for e in events if e['event']=='au_received']
    expected=load(a.package/'expected.json')['frames'];assert len(received)==len(expected)==493
    assert all(all(e[k]==r[k] for k in ('encoded_id','pts_us','idr')) for e,r in zip(received,expected))
    final=events[-1];assert final==dict(event='completed',pictures=493,sources_created=3,sources_live=0,failed=False)
    created=[e['source'] for e in events if e['event']=='source_created'];closed=[e['source'] for e in events if e['event']=='source_closed']
    delivered={e['source'] for e in events if e['event']=='nal_delivered'}
    assert created==closed==[0,1,2] and delivered=={1,2} # SDP probe0 carries no AU.
    stderr=(board/'stderr.log').read_text();assert all('CJN-Trace>>' in line and 'maxRTCPPacketSize' in line for line in stderr.splitlines())
    reference=load(root/'tools/pose-v1/evidence/resident-20261008-r6/three-video-review/review.json')['records']
    reports=[]
    for number in (1,2):
        directory=clients/f'client{number}';review=load(directory/'review.json');assert review['actual_capture_PTS'] and len(review['frames'])==a.frames
        assert len(review['keepalives'])>=a.frames//30-1 and review['sequence_gaps']==0 and review['status']=='finite_RTSP_RTP_verified'
        cap=cv2.VideoCapture(str(directory/'received.h264'),cv2.CAP_FFMPEG);assert cap.isOpened();decoded=[]
        try:
            while True:
                ok,frame=cap.read()
                if not ok:break
                i=len(decoded);assert i<a.frames and frame.shape==(720,1280,3)
                record=review['frames'][i];wanted=record['encoded_id']
                level=[float(frame[604:628,44+b*64:84+b*64].mean()) for b in range(10)]
                actual=sum((v>128)<<b for b,v in enumerate(level));assert actual==wanted
                digest=hashlib.sha256(frame.tobytes()).hexdigest();assert digest==reference[wanted]['decoded_bgr_sha256']
                decoded.append(dict(encoded_id=wanted,source_frame_id=reference[wanted]['source_frame_id'],invocation=reference[wanted]['invocation'],decoded_bgr_sha256=digest))
                if i in (0,30,60,a.frames-1):assert cv2.imwrite(str(output/f'client{number}-frame{i:03d}.png'),frame)
        finally:cap.release()
        assert len(decoded)==a.frames;reports.append(dict(client=number,records=decoded))
    invocations={r['invocation'] for client in reports for r in client['records'] if r['invocation'] is not None}
    if a.require_active:assert invocations=={0,1,2,3},'Network subset missed an active source'
    result=dict(status='owned_AU_adapter_native_ARM_network_gate_passed',programs=manifest['programs'],manifest_sha256=sha(a.package/'manifest.json'),returned_hashed_files=count,host_rejections=17,concurrent_units_per_Host=2000,capture_AUs=493,network_frames=2*a.frames,actual_RTP_PTS=True,decoded_pixels_equal_resident=True,kernel_unchanged=True,port_released=True,stderr_vendor_diagnostic_lines=len(stderr.splitlines()),clients=reports,active_invocations=sorted(invocations),new_VPU_NPU=False,online_pipeline_verified=False)
    (output/'review.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    (a.evidence/'completion-review.json').write_bytes((json.dumps({k:v for k,v in result.items() if k!='clients'},indent=2)+'\n').encode())
    print(result['status'])
if __name__=='__main__':main()

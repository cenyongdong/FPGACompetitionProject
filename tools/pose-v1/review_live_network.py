"""Match new RTP reconstruction against this run's capture, sampled sources and decoded pixels."""
import argparse,hashlib,json,re
from pathlib import Path
import cv2

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(r) for r in p.read_text().splitlines()]
def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--client',type=Path,required=True);p.add_argument('--video-review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True)
    data=(a.results/'encoder/video.h264').read_bytes();captures=rows(a.results/'packets.jsonl');offset=0;expected=[];params=[]
    for packet in captures:
        chunk=data[offset:offset+packet['bytes']];offset+=len(chunk);starts=list(re.finditer(b'\x00\x00(?:\x00)?\x01',chunk));assert not chunk or starts and starts[0].start()==0
        for i,start in enumerate(starts):
            end=starts[i+1].start() if i+1<len(starts) else len(chunk);nal=chunk[start.end():end];typ=nal[0]&31
            if typ in (7,8):
                if len(params)<2:params.append(nal.hex())
                else:assert nal.hex()==params[typ-7]
            else:
                assert typ in (1,5) and len(starts)==1 and nal[1]&128
                expected.append(dict(encoded_id=len(expected),pts_us=packet['pts_us'],digest=hashlib.sha256(nal).hexdigest(),idr=typ==5))
    assert offset==len(data)
    samples=rows(a.results/'samples.jsonl');local=load(a.video_review)['records'];client=load(a.client/'review.json')
    assert client['status']=='live_received_pending_board_content_review' and client['server_closed'] and client['sequence_gaps']==0 and client['SDP_parameters_hex']==params
    delivered=[r for r in rows(a.results/'network/events.jsonl') if r['event']=='nal_delivered' and r['type'] in (1,5)]
    frames=client['frames'];assert len(frames)==len(delivered) and len(expected)==len(samples)==len(local)
    joined={r['digest']:r['encoded_id'] for r in expected if r['idr']};assert len(joined)==sum(r['idr'] for r in expected)
    first=joined[frames[0]['vcl_sha256']]
    assert samples[first]['sample_ns']<rows(a.results/'lifecycle.jsonl')[0]['time_ns'],'Client did not receive startup before Engine ready'
    records=[];cap=cv2.VideoCapture(str(a.client/'received.h264'),cv2.CAP_FFMPEG);assert cap.isOpened()
    try:
        for i,network in enumerate(frames):
            current=expected[first+i];assert delivered[i]['encoded_id']==current['encoded_id'] and delivered[i]['pts_us']==current['pts_us']
            assert network['vcl_sha256']==current['digest'] and network['idr']==current['idr']
            ticks=(network['timestamp']-frames[0]['timestamp'])&0xffffffff
            assert abs(ticks-(current['pts_us']-expected[first]['pts_us'])*0.09)<=1.1,'RTP capture time differs'
            ok,image=cap.read();assert ok and image.shape==(720,1280,3);id=first+i
            actual=sum((float(image[608:628,48+b*64:80+b*64].mean())>128)<<b for b in range(10));assert actual==id
            digest=hashlib.sha256(image.tobytes()).hexdigest();assert digest==local[id]['decoded_bgr_sha256']
            sample=samples[id];records.append(dict(encoded_id=id,source_frame_id=sample['source_frame_id'],invocation=sample['invocation'] if sample['inference_result'] else None,capture_pts_us=current['pts_us'],decoded_bgr_sha256=digest))
            if i==0 or sample['inference_result'] and not any(r['invocation']==sample['invocation'] for r in records[:-1]):assert cv2.imwrite(str(a.output/f'first-source-{records[-1]["invocation"]}.png'),image)
        assert not cap.read()[0],'Unexpected decoded tail'
    finally:cap.release()
    n=load(a.results/'summary.json')['forward_calls'];assert {r['invocation'] for r in records if r['invocation'] is not None}==set(range(n)),'Network missed a model source'
    assert records[-1]['encoded_id']==len(samples)-1 and any(r['invocation'] is None for r in records)
    report=dict(status='real_capture_RTSP_bytes_PTS_sources_pixels_verified',network_frames=len(records),new_inference_sources=n,NoInput_frames=sum(r['invocation'] is None for r in records),first_encoded_id=first,last_encoded_id=records[-1]['encoded_id'],all_pixels_equal_current_capture=True,actual_RTP_capture_PTS=True,all_sources_present=True,records=records,scope='bounded real capture pipeline, not whole-system5Hz or30minute acceptance')
    (a.output/'review.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report['status'],len(records))
if __name__=='__main__':main()

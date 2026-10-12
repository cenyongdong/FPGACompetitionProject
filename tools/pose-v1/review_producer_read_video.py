"""Review complete returned high-address VPU NoInput video and actual overlap."""
from pathlib import Path
import hashlib,json
import cv2
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-source-read-20261011-r2';P=E/'on-return/run-on/results'
load=lambda p:[json.loads(x) for x in p.read_text().splitlines()]
events=load(P/'vpu/encoder/events.jsonl');obs=load(P/'vpu-ioctl.jsonl');packets=load(P/'vpu/packets.jsonl');summary=json.loads((P/'vpu/summary.json').read_text())
assert summary['drained'] and summary['joined'] and not summary['SDK_on_encoder_thread']
count=summary['submitted'];assert count==summary['returned'] and 0<count<1000
sources=[x for x in events if x['event']=='source_frame'];assert len(sources)==count and [x['encoded_id'] for x in sources]==list(range(count))
assert all(not x['inference_result'] for x in sources)
checks=[x for x in events if x['event']=='host_copy_check'];assert len(checks)==count and all(x['equal'] for x in checks)
formats={x['fourcc']:x for x in events if x['event']=='format'};raw=formats['NV12']['type'];coded=formats['H264']['type'];assert (raw,coded)==(10,9)
q=[x for x in obs if x['type']==raw and x['request']=='QBUF' and x['return']==0]
d=[x for x in obs if x['type']==coded and x['request']=='DQBUF' and x['return']==0]
assert len(q)==count and len(d)==len(packets)==summary['packets'] and len(obs)<8192
assert len({x['thread'] for x in obs})==1 and {x['index'] for x in q}=={0,1} and {x['index'] for x in d}=={0,1}
assert [(x['pts_us'],x['bytesused']) for x in d]==[(x['pts_us'],x['bytes']) for x in packets]
assert d[-1]['flags']&0x100000 and d[-1]['bytesused']==0 and packets[-1]['bytes']==0
body=packets[:-1];assert all(a['pts_us']<=b['pts_us'] for a,b in zip(body,body[1:]));assert len({x['pts_us'] for x in body})==count
assert all(x['owned'] for x in packets)
video=P/'vpu/encoder/video.h264';assert sum(x['bytes'] for x in packets)==video.stat().st_size
completion=[x for x in events if x['event']=='encoding_complete'];assert len(completion)==1 and completion[0]['last'] and completion[0]['queued']==completion[0]['returned']==count
assert len([x for x in events if x['event']=='streamoff'])==2 and not any(x['event']=='abort_streamoff' for x in events)
by_pts={x['pts_us']:x for x in q};assert len(by_pts)==count
intervals=[(by_pts[x['pts_us']]['begin_ns'],x['end_ns']) for x in d[:-1]]
overlaps=[]
for i in range(100):
    trace=json.loads((P/('call-'+str(i))/'trace.json').read_text())
    for x in trace['reads']:
        overlaps.append({'invocation':i,'value':x['value'],'count':sum(a<x['copy_end_ns'] and x['copy_begin_ns']<b for a,b in intervals)})
c=cv2.VideoCapture(str(video));ids=[];hashes=[]
while True:
    ok,f=c.read()
    if not ok:break
    assert f.shape==(720,1280,3);ids.append(sum((int(f[618,64+b*64].mean())>127)<<b for b in range(10)));hashes.append(hashlib.sha256(f.tobytes()).hexdigest())
c.release();assert ids==list(range(count))
life=load(P/'lifecycle.jsonl');assert [x['event'] for x in life]==['VPU_actual_capture','SDK_initialized','fixed_sequence_started','fixed_sequence_completed','workers_joined','SDK_destroyed'];assert all(a['time_ns']<=b['time_ns'] for a,b in zip(life,life[1:]))
r={'status':'complete_NoInput_video_and_release_passed','video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'video_bytes':video.stat().st_size,
   'raw_submitted_returned':count,'owned_packets':len(packets),'decoded_images':len(ids),'decoded_ids':ids,'decoded_BGR_sha256':hashes,
   'body_pts_nondecreasing':True,'terminal_LAST_empty_pts0_excluded_from_image_PTS':True,'normal_drain_LAST':True,
   'copy_spans':overlaps,'copy_overlap_spans':sum(x['count']>0 for x in overlaps),'copy_total':200,'ioctl_records':len(obs),
   'single_encoder_thread':True,'two_buffers_each_port':True,'all_sources_NoInput':True,'new_pose_throughput':0,
   'overlap_limit':'Submission-to-capture overlap is not hardware busy or DMA completion/fence proof.'}
(E/'on.video-review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print('NoInput images',count,'packets',len(packets),'overlap',r['copy_overlap_spans'],'/200; drain passed')

"""Review actual aborted coded prefix; terminal counts are not normal-drain proof."""
from pathlib import Path
import json,hashlib
import cv2
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-source-read-20261011-r2';P=E/'on-return/run-on/results'
load=lambda p:[json.loads(x) for x in p.read_text().splitlines()]
events=load(P/'vpu/encoder/events.jsonl');obs=load(P/'vpu-ioctl.jsonl');packets=load(P/'vpu/packets.jsonl')
sources=[x for x in events if x['event']=='source_frame'];raw=[x for x in obs if x['type']==10 and x['request']=='QBUF' and x['return']==0];capture=[x for x in obs if x['type']==9 and x['request']=='DQBUF' and x['return']==0]
count=len(sources);assert len(raw)==count and [x['encoded_id'] for x in sources]==list(range(count)) and all(not x['inference_result'] for x in sources)
assert len(packets)==len(capture) and all(x['owned'] for x in packets)
assert [(x['pts_us'],x['bytesused']) for x in capture]==[(x['pts_us'],x['bytes']) for x in packets]
video=P/'vpu/encoder/video.h264';assert sum(x['bytes'] for x in packets)==video.stat().st_size
assert all(a['pts_us']<=b['pts_us'] for a,b in zip(packets,packets[1:]))
by_pts={x['pts_us']:x for x in raw};intervals=[(by_pts[x['pts_us']]['begin_ns'],x['end_ns']) for x in capture];coverage=[]
for i in range(int(json.loads((P/'lease-summary.json').read_text())['opened'])):
    t=json.loads((P/('call-'+str(i))/'trace.json').read_text())
    for x in t['reads']:coverage.append({'invocation':i,'value':x['value'],'overlap':sum(a<x['copy_end_ns'] and x['copy_begin_ns']<b for a,b in intervals)})
c=cv2.VideoCapture(str(video));ids=[];hashes=[]
while True:
    ok,f=c.read()
    if not ok:break
    assert f.shape==(720,1280,3);ids.append(sum((int(f[618,64+b*64].mean())>127)<<b for b in range(10)));hashes.append(hashlib.sha256(f.tobytes()).hexdigest())
c.release();assert ids==list(range(len(ids)))
life=load(P/'lifecycle.jsonl');assert [x['event'] for x in life]==['VPU_actual_capture','SDK_initialized','fixed_sequence_started','workers_joined','SDK_destroyed'];assert all(a['time_ns']<=b['time_ns'] for a,b in zip(life,life[1:]))
assert len(obs)<8192 and len({x['thread'] for x in obs})==1
r={'status':'aborted_NoInput_prefix_verified_not_drain_pass','video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'video_bytes':video.stat().st_size,
   'owned_packets':len(packets),'decoded_images':len(ids),'decoded_ids':ids,'decoded_BGR_sha256':hashes,'raw_submitted':count,
   'raw_returned':sum(x['event']=='input_returned' for x in events),'body_pts_nondecreasing':True,'source_NoInput':True,'new_pose_throughput':0,
   'ioctl_records':len(obs),'copy_overlap':coverage,'copy_overlap_spans':sum(x['overlap']>0 for x in coverage),'copy_spans_total':len(coverage),
   'normal_drain_LAST_pass':False,'abort_STREAMOFF_successes':2,'two_buffers_each_port':True,
   'summary_zero_counts_limit':'Abort threw before frozen EncodeResult returned; submitted/returned0 are not actual no-work.',
   'overlap_limit':'Submission-to-capture spans do not prove hardware busy or DMA fence.'}
(E/'on.video-review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print('Decoded prefix',len(ids),'owned packets',len(packets),'raw queued',count,'overlaps',r['copy_overlap_spans'],'/',len(coverage))

"""Full source/PTS/NV12 review and decoded bone checks using existing OpenCV."""
import argparse,json,hashlib,re
from pathlib import Path
import cv2,numpy as np
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def nal_types(blob):
    starts=list(re.finditer(b'\x00\x00(?:\x00)?\x01',blob));assert starts and starts[0].start()==0;return [blob[x.end()]&31 for x in starts]
p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--references',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();a.output.mkdir()
vpu=a.results/'vpu';summary=json.loads((vpu/'summary.json').read_text());events=rows(vpu/'encoder/events.jsonl');samples=rows(vpu/'samples.jsonl');packets=rows(vpu/'packets.jsonl');pictures=rows(a.results/'pictures/index.jsonl');calls=rows(a.results/'inference.jsonl')
assert summary['joined'] and summary['drained'] and summary['published']==summary['consumed']==107 and not summary['overwritten'] and not summary['coalesced']
assert len(pictures)==len(calls)==107 and 2<=len(samples)==summary['submitted']==summary['returned']<1000
cache={};NV12=[]
for i in range(-1,107):
    name='warmup.nv12' if i<0 else f'result{i}.nv12';actual=(a.results/'pictures'/name).read_bytes();native=(a.references/name).read_bytes();assert actual==native and len(actual)==1382400
    cache[i]=np.frombuffer(native,np.uint8).reshape(1080,1280).copy();NV12.append(dict(invocation=i,SHA256=hashlib.sha256(actual).hexdigest()))
for i,x in enumerate(pictures):
    assert x['invocation']==i and x['frame_id']==100000+i and x['best_index']==calls[i]['best_index'] and x['case']==calls[i]['case']
    assert x['draw_begin_ns']<=x['draw_end_ns']<=x['convert_end_ns']<=x['publish_begin_ns']
raw=(vpu/'encoder/video.h264').read_bytes();assert len(raw)==sum(x['bytes'] for x in packets);offset=0;images=[];headers=[];last=[]
for x in packets:
    if x['bytes']:
        types=nal_types(raw[offset:offset+x['bytes']]);(images if any(v in (1,5) for v in types) else headers).append(x)
        assert sum(v in (1,5) for v in types)<=1
    else:last.append(x)
    offset+=x['bytes']
assert len(images)==len(samples) and len(headers)==len(last)==1 and all(x['owned'] for x in packets)
queued=[x for x in events if x['event']=='input_queued'];clock=[x for x in events if x['event']=='sample_clock'];captures=[x for x in events if x['event']=='capture' and x['bytes']]
assert [x['pts_us'] for x in queued]==[x['pts_us'] for x in images]==[x['pts_us'] for x in clock] and [(x['pts_us'],x['bytes']) for x in captures]==[(x['pts_us'],x['bytes']) for x in packets if x['bytes']]
assert all(x['equal'] for x in events if x['event']=='host_copy_check') and len([x for x in events if x['event']=='host_copy_check'])==len(samples)
cap=cv2.VideoCapture(str(vpu/'encoder/video.h264'));assert cap.isOpened();records=[];seen=set();tiles=[];previous=None;previous_real=False
try:
    while True:
        ok,image=cap.read()
        if not ok:break
        i=len(records);assert i<len(samples) and image.shape==(720,1280,3);s=samples[i];assert s['encoded_id']==i and s['sample_ns']==clock[i]['sample_ns'] and s['generated_ns']<=s['sample_ns']
        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY);id=0
        for bit in range(10):
            patch=gray[608:628,48+bit*64:80+bit*64];lo,hi=int(patch.min()),int(patch.max());assert hi<64 or lo>192;id|=(lo>192)<<bit
        assert id==i;key=s['invocation'] if s['inference_result'] else -1
        if key>=0:
            assert 0<=key<107 and s['source_frame_id']==100000+key and s['generated_ns']==pictures[key]['convert_end_ns'] and s['sample_ns']>=pictures[key]['publish_begin_ns']
        assert s['repeated_source']==bool(key>=0 and previous_real and key==previous);previous=key;previous_real=key>=0
        marked=cache[key].copy();marked[600:680,40:1240]=16;marked[1020:1060,40:1240]=128
        for bit in range(10):marked[604:632,44+bit*64:84+bit*64]=235 if i&(1<<bit) else 16
        expected=cv2.cvtColor(marked,cv2.COLOR_YUV2BGR_NV12);difference=np.abs(image.astype(np.int16)-expected.astype(np.int16));points=[]
        if key>=0:
            pose=np.fromfile(a.results/f'result{key}.poses.f32',dtype='<f4').reshape(100,14,3)[calls[key]['best_index']].astype(np.float64)
            x,y,z=(pose-np.array([1.75,1.75,3.4])).T;z=-z;cy,sy=np.cos(np.pi/6),np.sin(np.pi/6);ce,se=np.cos(np.pi/9),np.sin(np.pi/9);projected=np.stack((460+220*(cy*x-sy*y),355-220*(ce*z-se*(sy*x+cy*y))),axis=-1)
            for x,y in projected:
                cx,cy=int(round(x)),int(round(y));assert 8<=cx<1272 and 8<=cy<590
                patch=image[cy-6:cy+7,cx-6:cx+7].astype(np.int16);yy,xx=np.nonzero((patch[:,:,2]>110)&(patch[:,:,2]-patch[:,:,1]>45)&(patch[:,:,2]-patch[:,:,0]>45));assert len(xx);points.append(float(np.sqrt((xx-6)**2+(yy-6)**2).min()))
        records.append(dict(encoded_id=i,invocation=key,source_frame_id=s['source_frame_id'],repeated_source=s['repeated_source'],RGB_mean_abs_8bit=float(difference.mean()),joint_visibility=points,decoded_bgr_SHA256=hashlib.sha256(image.tobytes()).hexdigest()))
        if key not in seen:
            seen.add(key)
            if key in (-1,0,1,2,4,5):cv2.imwrite(str(a.output/f'first-invocation-{key}.png'),image);tiles.append(cv2.resize(image,(640,360)))
finally:cap.release()
assert len(records)==len(samples) and seen-{ -1 }==set(range(107))
assert [x['invocation'] for x in samples if x['inference_result'] and not x['repeated_source']]==list(range(107))
while len(tiles)<6:tiles.append(np.zeros((360,640,3),np.uint8))
assert cv2.imwrite(str(a.output/'contact-sheet.png'),np.vstack([np.hstack(tiles[i:i+2]) for i in range(0,6,2)]))
report=dict(status='real_owned_picture_NV12_sources_and_actual_PTS_video_passed',decoded_frames=len(records),unique_real_sources=107,NV12_files=108,NV12_bytewise_Native=True,NV12_bytes_compared=108*1382400,actual_PTS_match=True,NoInput_frames=sum(not x['inference_result'] for x in samples),repeated_real_frames=sum(x['repeated_source'] for x in samples),joint_visibility_checks=sum(len(x['joint_visibility']) for x in records),mean_RGB_abs_8bit=float(np.mean([x['RGB_mean_abs_8bit'] for x in records])),maximum_frame_RGB_mean_abs_8bit=float(max(x['RGB_mean_abs_8bit'] for x in records)),RGB_is_lossy_diagnostic_not_bitwise=True,stream_bytes=len(raw),stream_SHA256=hashlib.sha256(raw).hexdigest(),records=records,NV12=NV12,render_projection_source='frozen bones/project with displayC2 flip, raw model units; no MPJPE',OpenCV_version=cv2.__version__,NumPy_version=np.__version__)
(a.output/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ('records','NV12')}))

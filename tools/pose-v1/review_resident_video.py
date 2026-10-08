"""Decode bounded actual-clock resident video with existing OpenCV; no board IO."""
import argparse,hashlib,json
from pathlib import Path
import cv2
import numpy as np

p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists();a.output.mkdir()
samples=[json.loads(x) for x in (a.results/'samples.jsonl').read_text().splitlines()]
calls=[json.loads(x) for x in (a.results/'inference.jsonl').read_text().splitlines()]
assert 2<=len(samples)<=1000
cache={None:np.fromfile(a.results/'frames/warmup.nv12',dtype=np.uint8).reshape(1080,1280)}
for record in calls:cache[record['invocation']]=np.fromfile(a.results/'frames'/f"result{record['call']}.nv12",dtype=np.uint8).reshape(1080,1280)
capture=cv2.VideoCapture(str(a.results/'encoder/video.h264'),cv2.CAP_FFMPEG);assert capture.isOpened()
records=[];first_source=set();tiles=[]
try:
    while True:
        ok,image=capture.read()
        if not ok:break
        i=len(records);assert i<len(samples) and image.shape==(720,1280,3)
        levels=[float(image[608:628,48+bit*64:80+bit*64].mean()) for bit in range(10)]
        actual=sum((level>128)<<bit for bit,level in enumerate(levels));assert actual==i
        sample=samples[i];key=sample['invocation'] if sample['inference_result'] else None
        marked=cache[key].copy();marked[600:680,40:1240]=16;marked[1020:1060,40:1240]=128
        for bit in range(10):marked[604:632,44+bit*64:84+bit*64]=235 if i&(1<<bit) else 16
        expected=cv2.cvtColor(marked,cv2.COLOR_YUV2BGR_NV12)
        difference=np.abs(image.astype(np.int16)-expected.astype(np.int16))
        points=[]
        if key is not None:
            call=calls[key];pose=np.fromfile(a.results/f"result{key}.poses.f32",dtype='<f4').reshape(100,14,3)[call['best_index']].astype(np.float64)
            x,y,z=(pose-np.array([1.75,1.75,3.4])).T;z=-z
            cy,sy=np.cos(np.pi/6),np.sin(np.pi/6);ce,se=np.cos(np.pi/9),np.sin(np.pi/9)
            projected=np.stack((460+220*(cy*x-sy*y),355-220*(ce*z-se*(sy*x+cy*y))),axis=-1)
            for x,y in projected:
                cx,cy=int(round(x)),int(round(y));assert 8<=cx<1272 and 8<=cy<590
                patch=image[cy-6:cy+7,cx-6:cx+7].astype(np.int16)
                yy,xx=np.nonzero((patch[:,:,2]>110)&(patch[:,:,2]-patch[:,:,1]>45)&(patch[:,:,2]-patch[:,:,0]>45));assert len(xx)
                points.append(float(np.sqrt((xx-6)**2+(yy-6)**2).min()))
        records.append(dict(encoded_id=i,source_frame_id=sample['source_frame_id'],invocation=key,
            repeated_source=sample['repeated_source'],RGB_mean_abs_8bit=float(difference.mean()),
            joint_visibility=points,decoded_bgr_sha256=hashlib.sha256(image.tobytes()).hexdigest()))
        if key not in first_source:
            first_source.add(key);cv2.imwrite(str(a.output/f'first-invocation-{key}.png'),image)
            if len(tiles)<6:tiles.append(cv2.resize(image,(640,360)))
finally:capture.release()
assert len(records)==len(samples) and first_source==set(range(len(calls)))|{None}
while len(tiles)<6:tiles.append(np.zeros((360,640,3),np.uint8))
assert cv2.imwrite(str(a.output/'contact-sheet.png'),np.vstack([np.hstack(tiles[i:i+2]) for i in range(0,6,2)]))
report=dict(status='resident_video_sources_and_IDs_verified',decoded_frames=len(records),
    inference_sources=len(calls),joint_visibility_checks=sum(len(r['joint_visibility']) for r in records),
    mean_RGB_abs_8bit=float(np.mean([r['RGB_mean_abs_8bit'] for r in records])),records=records,
    scope='Actual-clock bounded encoding, repeated video frames do not count as new inference results')
(a.output/'review.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report['status'],len(records))

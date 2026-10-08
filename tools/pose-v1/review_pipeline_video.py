"""Decode the finite combined clip against its actual submitted Host frames."""
import argparse,json,hashlib
from pathlib import Path
import cv2
import numpy as np
def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir()
    meta=[json.loads(x) for x in (a.results/'frames.jsonl').read_text().splitlines()]
    raw=np.memmap(a.results/'encoder/submitted.nv12',dtype=np.uint8,mode='r',shape=(10,1080,1280))
    cap=cv2.VideoCapture(str(a.results/'encoder/review.mp4'),cv2.CAP_FFMPEG);assert cap.isOpened()
    assert cap.get(cv2.CAP_PROP_FPS)==10 and cap.get(cv2.CAP_PROP_FRAME_COUNT)==10
    records=[];total_error=0.;tiles=[]
    try:
        while True:
            ok,frame=cap.read()
            if not ok:break
            i=len(records);assert i<10 and frame.shape==(720,1280,3)
            levels=[float(frame[604:628,44+b*64:84+b*64].mean()) for b in range(6)]
            decoded=sum((v>128)<<b for b,v in enumerate(levels));assert decoded==i
            reference=cv2.cvtColor(np.asarray(raw[i]),cv2.COLOR_YUV2BGR_NV12)
            err=float(np.abs(frame.astype(np.int16)-reference.astype(np.int16)).mean());total_error+=err
            points=[]
            if i>=2:
                for x,y in meta[(i-2)//2]['projected']:
                    cx,cy=int(round(x)),int(round(y));r=6;assert 8<=cx<1272 and 8<=cy<590
                    patch=frame[cy-r:cy+r+1,cx-r:cx+r+1].astype(np.int16)
                    yy,xx=np.nonzero((patch[:,:,2]>110)&(patch[:,:,2]-patch[:,:,1]>45)&(patch[:,:,2]-patch[:,:,0]>45));assert len(xx)
                    points.append(float(np.sqrt((xx-r)**2+(yy-r)**2).min()))
            records.append({'encoded_id':i,'inference_result':i>=2,'source_index':(i-2)//2 if i>=2 else None,
                            'source_frame_id':meta[(i-2)//2]['frame_id'] if i>=2 else None,'RGB_mean_abs_8bit':err,
                            'nearest_red_pixel_distances':points,'decoded_bgr_sha256':hashlib.sha256(frame.tobytes()).hexdigest()})
            if i in (0,2,4,6,8):
                assert cv2.imwrite(str(a.output/f'frame{i:02d}.png'),frame)
                tile=cv2.resize(frame,(640,360));cv2.putText(tile,'NO INPUT' if i==0 else f'encoded {i} / source frame {meta[(i-2)//2]["frame_id"]}',(12,345),cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1);tiles.append(tile)
    finally:cap.release()
    assert len(records)==10
    tiles.append(np.zeros_like(tiles[0]));sheet=np.vstack([np.hstack(tiles[i:i+2]) for i in range(0,6,2)])
    assert cv2.imwrite(str(a.output/'contact-sheet.png'),sheet)
    report={'status':'finite_pipeline10_frames_decode_verified','warmup_frames':2,'real_encoded_frames':8,'new_inference_results':4,
            'joint_visibility_checks':112,'all_encoded_IDs_correct':True,'RGB_mean_abs_8bit':total_error/10,'records':records,
            'scope':'same-process finite serial inference/encoding, nominal offline PTS, no realtime FPS/3D accuracy claim'}
    (a.output/'review.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report['status'])
if __name__=='__main__':main()

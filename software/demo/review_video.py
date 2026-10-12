"""Decode original VPU stream and verify real-source geometry/pixels."""
from pathlib import Path
import argparse,hashlib,json
import cv2,numpy as np
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['short','demo']);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    E=a.evidence;P=E/(a.stage+'-return/run-'+a.stage)/'results';native=E/(a.stage+'-native-render')
    samples=lines(P/'video/samples.jsonl');meta=lines(P/'results/frames.jsonl');cap=cv2.VideoCapture(str(P/'video/encoder/video.h264'))
    decoded=0;seen={};errors=[];joint_total=0;first=[]
    try:
        while True:
            ok,image=cap.read()
            if not ok:break
            assert image.shape==(720,1280,3) and decoded<len(samples)
            marker=sum((int(image[618,64+b*64].mean())>127)<<b for b in range(10));s=samples[decoded];assert marker==s['encoded_id']==decoded
            if s['inference_result'] and s['invocation'] not in seen:
                inv=s['invocation'];assert s['source_frame']==meta[inv]['frame_id']
                info=json.loads((native/(f'frame{inv}.json')).read_text());raw=(native/(f'frame{inv}.ppm')).read_bytes().split(b'\n',3)[3];expected=np.frombuffer(raw,np.uint8).reshape(720,1280,3)
                diff=np.abs(image[:590,:,::-1].astype(np.int16)-expected[:590].astype(np.int16));errors.append(float(diff.mean()))
                visible=0
                for x,y in info['projected']:
                    x,y=int(round(x)),int(round(y))
                    if x<0 or y<0 or x>=1280 or y>=590:continue
                    crop=image[max(0,y-5):min(590,y+6),max(0,x-5):min(1280,x+6)].astype(np.int16)
                    assert ((crop[:,:,2]>crop[:,:,0]+25)&(crop[:,:,2]>crop[:,:,1]+25)).any(),(inv,x,y)
                    visible+=1
                assert visible>0;seen[inv]=s['source_frame'];joint_total+=visible
                if len(first)<3:
                    path=E/(a.stage+f'-pose-{inv}.png');cv2.imwrite(str(path),image);first.append(image)
            decoded+=1
    finally:cap.release()
    assert decoded==len(samples) and set(seen)==set(range(len(meta)))
    host=lines(E/(a.stage+'-host')/'decoded.jsonl');assert all(0<=s['encoded_id']<decoded for s in host)
    if first:cv2.imwrite(str(E/(a.stage+'-contact.png')),np.concatenate([cv2.resize(x,(640,360)) for x in first],axis=1))
    report={'status':'original_VPU_video_real_pose_geometry_verified','decoded_frames':decoded,'real_source_frames':len(seen),
            'visible_joints_verified':joint_total,'mean_body_RGB_absolute_difference':float(np.mean(errors)),
            'max_source_body_mean_difference':max(errors),'lossy_H264_not_RGB_bitwise':True,
            'all_encoded_ids_ordered':True,'NoInput_repeated_not_new_throughput':True,
            'video_sha256':hashlib.sha256((P/'video/encoder/video.h264').read_bytes()).hexdigest()}
    (E/(a.stage+'.video-review.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(report)
if __name__=='__main__':main()

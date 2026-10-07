"""Host54-frame decode, actual source mapping and skeleton landmark audit."""
import argparse,hashlib,json,math
from pathlib import Path
import cv2
import numpy as np

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def red(p):
    a=p.astype(np.int16)
    return (a[:,:,2]>110)&(a[:,:,2]-a[:,:,1]>45)&(a[:,:,2]-a[:,:,0]>45)
def main():
    a=argparse.ArgumentParser();a.add_argument('--package',type=Path,required=True);a.add_argument('--video',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
    assert not args.output.exists();args.output.mkdir(parents=True)
    m=json.loads((args.package/'manifest.json').read_text());assert m['frames']==54 and m['sources']==27 and sha(args.package/'frames.nv12')==m['input_sha256']
    source=np.memmap(args.package/'frames.nv12',dtype=np.uint8,mode='r',shape=(54,1080,1280))
    cap=cv2.VideoCapture(str(args.video),cv2.CAP_FFMPEG);assert cap.isOpened()
    meta={name:cap.get(flag) for name,flag in [('width',cv2.CAP_PROP_FRAME_WIDTH),('height',cv2.CAP_PROP_FRAME_HEIGHT),('fps',cv2.CAP_PROP_FPS),('declared_frames',cv2.CAP_PROP_FRAME_COUNT)]}
    assert meta['width']==1280 and meta['height']==720 and meta['fps']==10 and meta['declared_frames']==54
    records=[];tiles=[];total_abs=total_sq=0.;pixel_count=0;max_error=0;source_geometry=set()
    try:
        while True:
            ok,frame=cap.read()
            if not ok:break
            i=len(records);assert i<54 and frame.shape==(720,1280,3)
            declared=m['frame_records'][i];original=m['source_records'][i//2]
            assert declared['source_index']==i//2 and declared['source_frame_id']==original['source_frame_id'] and declared['repeated_source']==bool(i%2)
            levels=[float(frame[604:628,44+bit*64:84+bit*64].mean()) for bit in range(6)]
            decoded_id=sum((v>128)<<bit for bit,v in enumerate(levels));assert decoded_id==i,(i,decoded_id)
            x=declared['marker_x'];assert frame[646:674,x+4:x+20].mean()>200
            ref=cv2.cvtColor(np.asarray(source[i]),cv2.COLOR_YUV2BGR_NV12)
            errors=frame.astype(np.int16)-ref.astype(np.int16);abs_error=np.abs(errors)
            total_abs+=float(abs_error.sum());sq=float(np.square(errors.astype(np.float64)).sum());total_sq+=sq;pixel_count+=errors.size;max_error=max(max_error,int(abs_error.max()))
            distances=[]
            for px,py in original['projected']:
                cx=int(round(px));cy=int(round(py));r=6
                assert 8<=cx<1272 and 8<=cy<590,'Joint touches diagnostic area/border'
                region=frame[cy-r:cy+r+1,cx-r:cx+r+1]
                refregion=ref[cy-r:cy+r+1,cx-r:cx+r+1]
                assert red(refregion).any(),'Declared joint missing in raw frame'
                yy,xx=np.nonzero(red(region));assert len(xx),'Joint not recognizable after decode'
                distances.append(float(np.sqrt((xx-r)**2+(yy-r)**2).min()))
            source_geometry.add(json.dumps(original['projected']))
            records.append({'encoded_frame_id':i,'decoded_frame_id':decoded_id,'source_case':original['source_case'],'source_frame_id':original['source_frame_id'],
                            'source_index':i//2,'repeated_source':bool(i%2),'decoded_bgr_sha256':hashlib.sha256(frame.tobytes()).hexdigest(),
                            'joint_nearest_red_pixel_distances':distances,'RGB_mean_abs_8bit':float(abs_error.mean()),'RGB_PSNR_dB':10*math.log10(255**2/(sq/errors.size)) if sq else None})
            if i in (0,10,20,30,40,52):
                assert cv2.imwrite(str(args.output/f'frame{i:02d}.png'),frame)
                tile=cv2.resize(frame,(640,360),interpolation=cv2.INTER_AREA)
                cv2.putText(tile,f'{original["source_case"]} / encoded {i}',(10,345),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,255),1)
                tiles.append(tile)
    finally:cap.release()
    assert len(records)==54 and len(source_geometry)==27
    assert len({r['decoded_bgr_sha256'] for r in records})==54
    sheet=np.vstack([np.hstack(tiles[i:i+2]) for i in range(0,6,2)]);assert cv2.imwrite(str(args.output/'contact-sheet.png'),sheet)
    result={'status':'real27_skeletons54_encoded_frames_host_verified','scope':'prerecorded_discrete_windows_no_live_inference','video_sha256':sha(args.video),'input_sha256':m['input_sha256'],
            'opencv_version':cv2.__version__,'metadata':meta,'frames':54,'sources':27,'all_frame_ids_correct':True,'source_mapping_checked':True,
            'distinct_declared_poses':27,'landmark_checks':54*14,'max_nearest_red_pixel_distance':max(max(r['joint_nearest_red_pixel_distances']) for r in records),
            'RGB_mean_abs_8bit':total_abs/pixel_count,'RGB_max_abs_8bit':max_error,'RGB_PSNR_dB':10*math.log10(255**2/(total_sq/pixel_count)),
            'limitations':'Lossy metrics include NV12 conversion conventions; red-neighborhood test checks visibility near expected rendered joints, not3D accuracy/physical calibration',
            'records':records}
    (args.output/'review.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))

if __name__=='__main__':main()

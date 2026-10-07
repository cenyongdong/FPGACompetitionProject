"""Host-side decoding with existing OpenCV/FFmpeg, no environment changes."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import cv2
import numpy as np

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--video',type=Path,required=True)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--annexb',action='store_true',help='Raw elementary stream has no container PTS; rate metadata is diagnostic only')
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
    assert sha(args.input)==manifest['input_sha256']
    source=np.memmap(args.input,dtype=np.uint8,mode='r',shape=(30,1080,1280))
    cap=cv2.VideoCapture(str(args.video),cv2.CAP_FFMPEG)
    assert cap.isOpened(),'Host decoder failed to open stream'
    meta={'width':cap.get(cv2.CAP_PROP_FRAME_WIDTH),'height':cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
          'fps':cap.get(cv2.CAP_PROP_FPS),'declared_frames':cap.get(cv2.CAP_PROP_FRAME_COUNT),'backend':cap.getBackendName()}
    records=[]; tiles=[]; sum_abs=0.; sum_sq=0.; max_abs=0; count=0
    try:
        while True:
            ok,bgr=cap.read()
            if not ok:break
            i=len(records)
            assert i<30 and bgr.shape==(720,1280,3),'Unexpected decoded frame size/count'
            assert np.isfinite(bgr).all()
            # These deliberately large binary blocks tolerate compression and
            # recover source ID without relying on packet ordering/timestamps.
            levels=[float(bgr[604:628,44+bit*64:84+bit*64].mean()) for bit in range(5)]
            frame_id=sum((value>128)<<bit for bit,value in enumerate(levels))
            assert frame_id==i,f'Frame identity mismatch: expected {i}, decoded {frame_id}'
            marker_x=40+i*38
            assert bgr[646:674,marker_x+4:marker_x+28].mean()>200,'Moving marker missing'
            reference=cv2.cvtColor(np.asarray(source[i]),cv2.COLOR_YUV2BGR_NV12)
            delta=bgr.astype(np.int16)-reference.astype(np.int16)
            mae=float(np.abs(delta).mean()); mse=float(np.square(delta.astype(np.float64)).mean())
            sum_abs+=float(np.abs(delta).sum());sum_sq+=float(np.square(delta.astype(np.float64)).sum());count+=delta.size
            max_abs=max(max_abs,int(np.abs(delta).max()))
            records.append({'frame':i,'decoded_frame_id':frame_id,'decoded_bgr_sha256':hashlib.sha256(bgr.tobytes()).hexdigest(),
                            'mean_abs_RGB_8bit':mae,'PSNR_RGB_dB':10*math.log10(255**2/mse) if mse else None,'binary_block_levels':levels})
            if i in (0,5,10,15,20,29):
                assert cv2.imwrite(str(args.output/f'frame{i:02d}.png'),bgr)
                tile=cv2.resize(bgr,(640,360),interpolation=cv2.INTER_AREA)
                cv2.putText(tile,f'HOST DECODE: frame {i}',(12,345),cv2.FONT_HERSHEY_SIMPLEX,.65,(255,255,255),1)
                tiles.append(tile)
    finally:cap.release()
    assert len(records)==30,'Missing encoded/decoded frames'
    assert len({r['decoded_bgr_sha256'] for r in records})==30,'Frames unexpectedly identical'
    assert meta['width']==1280 and meta['height']==720,'Metadata dimensions mismatch'
    if not args.annexb:
        assert abs(meta['fps']-10)<.001,'Container playback rate mismatch'
    sheet=np.vstack([np.hstack(tiles[i:i+2]) for i in range(0,6,2)])
    assert cv2.imwrite(str(args.output/'contact-sheet.png'),sheet)
    report={'status':'host_decode_30_frames_identity_passed','scope':'finite_independent_VPU_no_HDMI_no_NPU_no_RTSP',
            'opencv_version':cv2.__version__,'video_sha256':sha(args.video),'input_sha256':sha(args.input),'metadata':meta,
            'decoded_frames':len(records),'all_frame_ids_correct':True,'all_unique':True,
            'raw_annexb':args.annexb,'container_rate_verified':not args.annexb,
            'RGB_mean_abs_8bit':sum_abs/count,'RGB_max_abs_8bit':max_abs,'RGB_PSNR_dB':10*math.log10(255**2/(sum_sq/count)),
            'lossy_metrics_reference':'OpenCV NV12-to-BGR decoding of original input; not an exact colorimetric calibration',
            'records':records}
    (args.output/'review.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))

if __name__=='__main__':main()

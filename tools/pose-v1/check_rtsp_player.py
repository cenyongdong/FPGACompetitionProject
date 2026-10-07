"""Direct bounded RTSP decoding through the host's existing OpenCV/FFmpeg."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS']='rtsp_transport;tcp'
import cv2

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True)
    ref=json.loads((Path(__file__).parent/'evidence/video-descriptor-20261007-r5/host-review/review.json').read_text())['records']
    started=time.perf_counter();records=[]
    cap=cv2.VideoCapture('rtsp://192.168.126.49:8554/pose',cv2.CAP_FFMPEG,
                         [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,5000,cv2.CAP_PROP_READ_TIMEOUT_MSEC,5000])
    try:
        assert cap.isOpened(),'Direct RTSP open failed'
        for i in range(100):
            assert time.perf_counter()-started<25
            ok,frame=cap.read();assert ok and frame.shape==(720,1280,3),'Direct RTSP decode failed'
            levels=[float(frame[604:628,44+bit*64:84+bit*64].mean()) for bit in range(6)]
            frame_id=sum((v>128)<<bit for bit,v in enumerate(levels));assert 0<=frame_id<54
            if records:assert frame_id==(records[-1]['encoded_id']+1)%54
            digest=hashlib.sha256(frame.tobytes()).hexdigest();assert digest==ref[frame_id]['decoded_bgr_sha256']
            records.append({'index':i,'encoded_id':frame_id,'decoded_bgr_sha256':digest,'source_case':ref[frame_id]['source_case'],'arrival_elapsed_s':time.perf_counter()-started})
            if i in (0,30,60,99):assert cv2.imwrite(str(a.output/f'frame{i:03d}.png'),frame)
        result={'status':'direct_RTSP_OpenCV_FFmpeg_100_frames_verified','opencv_version':cv2.__version__,
                'transport':'TCP','shape':[1280,720],'all_pixels_equal_r5':True,'all_IDs_in_order':True,
                'elapsed_s':time.perf_counter()-started,'records':records,'scope':'prerecorded stream only, no display or whole-system latency claim'}
        (a.output/'review.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
        print(result['status'])
    except Exception as error:
        (a.output/'failure.json').write_bytes((json.dumps({'error':str(error),'records':records},indent=2)+'\n').encode())
        raise
    finally:cap.release()

if __name__=='__main__':main()

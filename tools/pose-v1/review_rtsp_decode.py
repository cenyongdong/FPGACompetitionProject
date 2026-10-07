"""Decode captured RTP reconstruction with the existing host OpenCV environment."""
import argparse
import hashlib
import json
from pathlib import Path
import cv2

def main():
    p=argparse.ArgumentParser();p.add_argument('--clients',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();a.output.mkdir()
    baseline=Path(__file__).resolve().parent/'evidence/video-descriptor-20261007-r5/host-review/review.json'
    ref=json.loads(baseline.read_text())['records'];reports=[]
    for number in (1,2):
        directory=a.clients/f'client{number}';review=json.loads((directory/'review.json').read_text())
        assert review['status']=='finite_RTSP_RTP_verified' and len(review['frames'])==100
        cap=cv2.VideoCapture(str(directory/'received.h264'),cv2.CAP_FFMPEG);assert cap.isOpened()
        decoded=[]
        try:
            while True:
                ok,frame=cap.read()
                if not ok:break
                i=len(decoded);assert i<100 and frame.shape==(720,1280,3)
                expected=review['frames'][i]['encoded_id']
                levels=[float(frame[604:628,44+bit*64:84+bit*64].mean()) for bit in range(6)]
                actual=sum((value>128)<<bit for bit,value in enumerate(levels));assert actual==expected
                digest=hashlib.sha256(frame.tobytes()).hexdigest()
                assert digest==ref[expected]['decoded_bgr_sha256'],'Decoded pixel mismatch from verified encoder stream'
                decoded.append({'index':i,'encoded_id':actual,'decoded_bgr_sha256':digest,'source_case':ref[expected]['source_case']})
                if i in (0,30,60,99):assert cv2.imwrite(str(a.output/f'client{number}-frame{i:03d}.png'),frame)
        finally:cap.release()
        assert len(decoded)==100
        reports.append({'client':number,'frames':len(decoded),'all_frame_ids_correct':True,'all_decoded_pixels_equal_r5':True,'records':decoded})
    report={'status':'RTSP_host_200_frames_decoded_verified','opencv_version':cv2.__version__,'clients':reports,'scope':'prerecorded replay, no new inference or VPU encoding'}
    (a.output/'review.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(report['status'])

if __name__=='__main__':main()

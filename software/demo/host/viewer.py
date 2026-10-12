"""Display actual board RTSP decode. This process uses existing OpenCV/FFmpeg."""
from pathlib import Path
import argparse, hashlib, json, os, time

def main():
    p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--headless',action='store_true');a=p.parse_args();out=a.output
    assert out.is_dir() and not (out/'viewer.json').exists()
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS']='rtsp_transport;tcp'
    import cv2
    frames=0;ready=False;cap=None;first=time.perf_counter();status='failed';error=None;last_saved=-1
    window='WiFi 3D Pose | Lite PS+NPU / VPU | Q closes viewer'
    try:
        while time.perf_counter()-first<90:
            if (out/'stop.request').exists():raise RuntimeError('Controller cancelled viewer startup')
            cap=cv2.VideoCapture(a.url,cv2.CAP_FFMPEG,[cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,10000,cv2.CAP_PROP_READ_TIMEOUT_MSEC,5000])
            if cap.isOpened():break
            cap.release();time.sleep(.2)
        if not cap or not cap.isOpened():raise TimeoutError('RTSP startup timeout')
        if not a.headless:cv2.namedWindow(window,cv2.WINDOW_NORMAL);cv2.resizeWindow(window,1280,720)
        with (out/'decoded.jsonl').open('w',encoding='utf-8') as log:
            while time.perf_counter()-first<175:
                if (out/'stop.request').exists():status='controller_cancelled';break
                ok,image=cap.read()
                if not ok:
                    if (out/'sender.finished').exists():status='stream_ended';break
                    raise RuntimeError('RTSP decode interrupted before input finished')
                if image.shape!=(720,1280,3):raise RuntimeError('Unexpected video dimensions')
                stamp=time.perf_counter_ns();encoded_id=sum((int(image[618,64+b*64].mean())>127)<<b for b in range(10))
                log.write(json.dumps({'decoded':frames,'encoded_id':encoded_id,'decoded_pc_ns':stamp,'BGR_sha256':hashlib.sha256(image.tobytes()).hexdigest()})+'\n')
                if not ready:(out/'viewer.ready').write_text(str(stamp)+'\n');ready=True
                if frames==0:cv2.imwrite(str(out/'startup.png'),image)
                if (out/'sender.started').exists() and frames-last_saved>=20:
                    cv2.imwrite(str(out/'latest.png'),image);last_saved=frames
                frames+=1
                if not a.headless:
                    cv2.imshow(window,image)
                    if cv2.waitKey(1)&255 in (ord('q'),27) or cv2.getWindowProperty(window,cv2.WND_PROP_VISIBLE)<1:
                        status='user_closed';break
            else:raise TimeoutError('Viewer finite budget exceeded')
        if not frames:raise RuntimeError('No video decoded')
    except Exception as e:error=str(e)
    finally:
        if cap:cap.release()
        if not a.headless:cv2.destroyAllWindows()
        (out/'viewer.json').write_text(json.dumps({'status':status,'error':error,'decoded_frames':frames,'display_window':not a.headless,'opencv':cv2.__version__,'RTSP_transport':'TCP','HDMI':False,'cross_clock_latency_claimed':False},indent=2)+'\n',encoding='utf-8')
    if error:raise RuntimeError(error)
if __name__=='__main__':main()

"""Record Kinect and three real RX streams on this PC; no developer board or model."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--seconds',type=int,default=60)
    p.add_argument('--guided',action='store_true',help='Five-minute Chinese spoken protocol; stop camera gracefully after the final cue')
    p.add_argument('--panel',action='store_true',help='External visual panel controls the bounded camera stop file')
    a=p.parse_args()
    if not 10<=a.seconds<=540:raise ValueError('Finite 10..540 second camera budget required')
    if a.guided and a.seconds!=300:raise ValueError('The fixed guided protocol lasts 300 seconds')
    if a.guided and a.panel:raise ValueError('Choose one prompt controller')
    root=Path(__file__).resolve().parents[2];output=a.output.resolve();output.mkdir(exist_ok=False)
    raw=output/'csi-raw';stop=output/'csi-stop.request'
    executable=root/'.local/kinect-check-20261028-r1/bin/ExportBodies.exe'
    camera_code=None;radio_code=None;guide_code=None;camera=None;guide=None;guide_log=None
    camera_seconds=a.seconds+45 if a.guided or a.panel else a.seconds
    with (output/'csi.log').open('w',encoding='utf-8') as radio_log:
        process=subprocess.Popen([sys.executable,'-B',str(Path(__file__).with_name('capture_pcaps.py')),
            '--output',str(raw),'--seconds',str(min(600,camera_seconds+45)),'--stop-file',str(stop)],stdout=radio_log,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+38
            while not (raw/'ready.json').exists():
                if (output/'cancel.request').exists():raise InterruptedError('Visual panel requested stop during receiver setup')
                if process.poll() is not None:raise RuntimeError('CSI receiver exited; inspect csi.log')
                if time.monotonic()>deadline:raise TimeoutError('Three RX streams did not become ready within the setup budget')
                time.sleep(.1)
            print('All three RX streams received. Starting actual Kinect recording now.',flush=True)
            with (output/'kinect.log').open('w',encoding='utf-8') as camera_log:
                command=[str(executable),str(output/'kinect'),str(camera_seconds)]
                if a.guided or a.panel:command+=['--stop-file',str(output/'kinect-stop.request')]
                camera=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                if a.guided:
                    guide_log=(output/'guide.log').open('w',encoding='utf-8')
                    guide=subprocess.Popen(['pwsh','-NoProfile','-File',str(Path(__file__).with_name('guide.ps1')),'-Directory',str(output)],stdout=guide_log,stderr=subprocess.STDOUT)
                for line in camera.stdout:camera_log.write(line);camera_log.flush();print(line,end='',flush=True)
                camera_code=camera.wait()
        finally:
            if camera is not None and camera.poll() is None:
                (output/'kinect-stop.request').write_text('Requested finite shutdown.\n')
                camera_code=camera.wait()
            if a.guided:(output/'guide-stop.request').write_text('Camera closed.\n')
            if guide is not None:guide_code=guide.wait()
            if guide_log is not None:guide_log.close()
            stop.write_text('Finite session complete; close raw receive sockets.\n')
            radio_code=process.wait()
            summary=dict(schema='KINECT-DIRECT-SESSION1',Kinect_exit=camera_code,CSI_exit=radio_code,
                board_used=False,model_inference=False,training_started=False,clock_alignment_verified=False,
                requested_camera_seconds=a.seconds,camera_safety_budget_seconds=camera_seconds,guided=a.guided,visual_panel=a.panel,guide_exit=guide_code,output=str(output))
            (output/'session.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
    if camera_code!=0 or radio_code!=0 or (a.guided and guide_code!=0):raise SystemExit(1)


if __name__=='__main__':main()

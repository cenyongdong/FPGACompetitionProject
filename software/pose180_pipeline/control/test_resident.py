"""Linux integration fault injection; mock is explicit and never opens the SDK."""
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import threading
import time

def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]

def frame(n):
    return struct.pack('<8sIIQQ',b'PIWCSI2\0',2,86400,n,time.time_ns())+struct.pack('<dd',1.25,.5)*5400

def main():
    parser=argparse.ArgumentParser();parser.add_argument('binary');parser.add_argument('output');args=parser.parse_args()
    root=Path(args.output);root.mkdir()
    ip,op,sp=port(),port(),port()
    cmd=[args.binary,'--output',str(root/'run'),'--session','123400','--input-port',str(ip),'--result-port',str(op),
         '--status-port',str(sp),'--seconds','60','--mock-delay-ms','20','--mock-slow-at','8']
    p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    samples=[];sender=None;finish=threading.Event()
    def status():
        with socket.create_connection(('127.0.0.1',sp),1) as s:
            data=b''
            while True:
                b=s.recv(4096)
                if not b:break
                data+=b
        value=json.loads(data);samples.append(value);return value
    def until(test,seconds=5):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            value=status()
            if test(value):return value
            time.sleep(.05)
        raise AssertionError(samples[-1])
    def feed():
        with socket.create_connection(('127.0.0.1',ip),2) as s:
            for n in range(1,3000):
                if finish.is_set():return
                s.sendall(frame(n));time.sleep(.004)
    try:
        ready=p.stdout.readline();assert 'RESIDENT_READY mock=1' in ready,ready
        recorder=int(ready.strip().split('recorder_pid=')[1])
        sender=threading.Thread(target=feed);sender.start()
        busy=until(lambda s:s['state']=='degraded')
        assert busy['forward_age_ms']>=1000 and busy['inferred']==7,busy
        recovered=until(lambda s:s['inferred']>30)
        assert recovered['replaced']>20 and recovered['stale']>=1,recovered
        # Freeze a disk writer in the middle of its lifetime. Inference must
        # continue and queue overflow must be observable without memory growth.
        os.kill(recorder,signal.SIGSTOP);before=status()['inferred']
        until(lambda s:s['inferred']>before+30 and s['record_dropped']>0)
        os.kill(recorder,signal.SIGCONT)
        until(lambda s:s['recording'])
        slow=socket.create_connection(('127.0.0.1',op),1);slow.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,1024)
        before=status()['inferred'];time.sleep(3)
        assert status()['inferred']>before+50
        slow.close();until(lambda s:not s['pc_connected'])
        # Disk-full failure isolated in the recorder; original history is not touched.
        for i in range(4):
            path=root/'run'/('recent-%d.full'%i)
            if path.exists():path.unlink()
            path.symlink_to('/dev/full')
        before=status()['inferred'];until(lambda s:not s['recording'],5)
        until(lambda s:s['inferred']>before+20)
        for i in range(4):(root/'run'/('recent-%d.full'%i)).unlink()
        until(lambda s:s['recording'],8)
        finish.set();sender.join();sender=None
        until(lambda s:not s['input_connected'])
        epoch=status()['input_epoch'];before=status()['inferred']
        # Partial frame and changed frame numbering cannot leak across reconnect.
        with socket.create_connection(('127.0.0.1',ip),1) as s:s.sendall(frame(999)[:300])
        time.sleep(.1)
        with socket.create_connection(('127.0.0.1',ip),1) as s:
            s.sendall(frame(1));time.sleep(.2)
            fresh=until(lambda x:x['inferred']>before)
            assert fresh['input_epoch']>epoch
        p.send_signal(signal.SIGTERM);out,err=p.communicate(timeout=5)
        assert p.returncode==0,(out,err)
        for endpoint in (ip,op,sp):
            with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',endpoint))
        (root/'samples.json').write_text(json.dumps(samples,indent=2))
        (root/'native.stdout.log').write_text(ready+out);(root/'native.stderr.log').write_text(err)
        # Real application exception: one attempt only; control plane stays alive.
        p=subprocess.Popen([args.binary,'--output',str(root/'isolated'),'--session','123400',
            '--input-port',str(ip),'--result-port',str(op),'--status-port',str(sp),
            '--seconds','10','--mock-fail-at','1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        ready=p.stdout.readline();assert 'mock=1' in ready
        with socket.create_connection(('127.0.0.1',ip),1) as s:
            s.sendall(frame(1));until(lambda s:s['state']=='isolated');s.sendall(frame(2));time.sleep(.3)
            assert status()['inferred']==0
        p.send_signal(signal.SIGTERM);out,err=p.communicate(timeout=5);assert p.returncode==3,(out,err)
        (root/'isolated.stdout.log').write_text(ready+out)
        print(json.dumps({'mock':True,'checks':['slow SDK returns','latest replacement','stalled recorder',
            'slow/disconnected PC','disk full/recovery','input reconnect/partial discard','SDK failure isolation','ports reclaimed']}))
    finally:
        finish.set()
        if sender:sender.join(timeout=2)
        if p.poll() is None:p.terminate();p.wait(timeout=5)

if __name__=='__main__':main()

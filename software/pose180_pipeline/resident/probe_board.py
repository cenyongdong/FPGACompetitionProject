"""PC replay producer for a finite resident test; never launches or retries SDK."""
import argparse
import json
from pathlib import Path
import socket
import struct
import threading
import time

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--host',default='192.168.126.49')
    parser.add_argument('--data',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();out=Path(args.output);out.mkdir()
    samples=[];stop=threading.Event();errors=[];sent=0
    def status():
        with socket.create_connection((args.host,39384),2) as s:
            raw=b''
            while True:
                part=s.recv(4096)
                if not part:break
                raw+=part
        value=json.loads(raw);samples.append(value);return value
    # Wait only for the external one-use controller to start; this has no launch authority.
    deadline=time.monotonic()+45
    while True:
        try:status();break
        except (OSError,ValueError):
            if time.monotonic()>deadline:raise
            time.sleep(.2)
    def feed():
        nonlocal sent
        try:
            with Path(args.data).open('rb') as file:
                for epoch in range(2):
                    with socket.create_connection((args.host,39382),2) as s:
                        for number in range(450):
                            if stop.is_set():return
                            payload=file.read(86400)
                            if len(payload)!=86400:raise ValueError('Input source exhausted')
                            s.sendall(struct.pack('<8sIIQQ',b'PIWCSI2\0',2,86400,number+1,time.time_ns())+payload)
                            sent+=1;time.sleep(1/15)
                    time.sleep(2)
        except Exception as e:errors.append(repr(e))
    sender=threading.Thread(target=feed);sender.start()
    try:
        while sender.is_alive():
            value=status()
            if value['state']=='isolated':stop.set();break
            time.sleep(.5)
        sender.join();time.sleep(.5)
        final=status()
        (out/'samples.json').write_text(json.dumps(samples,indent=2))
        report=dict(CSI_live=False,HDMI=False,sent=sent,final=final,errors=errors,PC_input_only=True)
        (out/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
        if errors or final['inferred']<100 or final['state']=='isolated':raise RuntimeError('Resident trial incomplete; no automatic retry')
    finally:stop.set();sender.join(timeout=3)
if __name__=='__main__':main()

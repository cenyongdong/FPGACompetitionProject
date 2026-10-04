"""Windows loopback test for the raw sender; not a board/network acceptance."""
import argparse
import json
import socket
import subprocess
import sys
import threading
from pathlib import Path
from csi_io import HEADER, MAGIC, PAYLOAD_BYTES, encode_window, load_mat


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    csi=args.repo/'data/wifipose/test_data/csi'
    records,errors=[],[]
    with socket.socket() as server:
        server.bind(('127.0.0.1',0)); server.listen(1); server.settimeout(10)
        port=server.getsockname()[1]
        def receive():
            try:
                stream,_=server.accept()
                with stream:
                    stream.settimeout(5)
                    def exact(size):
                        chunks=[]
                        remaining=size
                        while remaining:
                            block=stream.recv(min(remaining,11))
                            if not block: raise ValueError('Unexpected EOF')
                            chunks.append(block); remaining-=len(block)
                        return b''.join(chunks)
                    for index in range(3):
                        header=exact(HEADER.size)
                        magic,version,size,frame,stamp=HEADER.unpack(header)
                        if (magic,version,size,frame)!=(MAGIC,1,PAYLOAD_BYTES,index) or stamp<=0:
                            raise ValueError('Invalid raw sender header')
                        payload=exact(size)
                        path=csi/f'S11_01_{308+index}.mat'
                        expected=encode_window(load_mat(path),index,stamp)
                        if header+payload!=expected: raise ValueError('Raw CSI changed during transport')
                        records.append({'frame_id':frame,'source':path.name,'bytes':len(expected),'unchanged':True})
                    if stream.recv(1): raise ValueError('Unexpected extra records')
            except Exception as exc:
                errors.append(str(exc))
        thread=threading.Thread(target=receive,daemon=True);thread.start()
        client=subprocess.run([sys.executable,str(Path(__file__).with_name('replay_raw_csi.py')),
            '--host','127.0.0.1','--port',str(port),'--csi-dir',str(csi),'--prefix','S11_01',
            '--start','308','--end','310','--fps','10'],capture_output=True,text=True,timeout=10)
        thread.join(10)
        if client.returncode or thread.is_alive() or errors or len(records)!=3:
            raise RuntimeError(str(errors)+client.stderr)
    report={'scope':'Windows loopback sender only; no board service or model',
            'records':records,'client_stdout':client.stdout,'status':'passed'}
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Raw sender loopback PASS: 3 original windows, forced fragmented reads')


if __name__=='__main__':
    main()

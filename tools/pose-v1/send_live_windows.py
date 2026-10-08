"""Bounded startup rendezvous, then one original-CSI stream plus repeated first window."""
import argparse,hashlib,json,socket,struct,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--cases',choices=['three','27'],required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();catalog=[]
    for line in (a.package/'cases.tsv').read_text(encoding='utf-8').splitlines():
        group,name,frame,stamp=line.split()
        if group!=('base' if a.cases=='three' else 'expanded'):continue
        raw=(a.package/'inputs'/(name+'.csi')).read_bytes()
        assert len(raw)==86432 and raw[:8]==b'PIWCSI1\0' and struct.unpack_from('<QQ',raw,16)==(int(frame),int(stamp))
        catalog.append((name,raw))
    assert len(catalog)==(3 if a.cases=='three' else 27)
    assert all(struct.unpack_from('<Q',x[1],16)[0]<struct.unpack_from('<Q',y[1],16)[0] for x,y in zip(catalog,catalog[1:]))
    report=dict(status='not_completed',fps=2,sent=[],startup_wait_only=True)
    def opened(startup=False):
        deadline=time.monotonic()+65 if startup else time.monotonic()+5
        while True:
            try:
                stream=socket.create_connection(('192.168.126.49',39001),timeout=1)
                stream.settimeout(5);stream.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1);return stream
            except ConnectionRefusedError:
                if not startup or time.monotonic()>=deadline:raise
                time.sleep(.1) # Expected listener startup; never reconnect a failed data session.
    def send(stream,name,raw,session):
        stream.sendall(raw);report['sent'].append(dict(case=name,frame_id=struct.unpack_from('<Q',raw,16)[0],session=session,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
    try:
        with opened(True) as stream:
            start=time.monotonic()
            for i,(name,raw) in enumerate(catalog):
                delay=start+i*.5-time.monotonic()
                if delay>0:time.sleep(delay)
                send(stream,name,raw,1)
        delay=start+len(catalog)*.5-time.monotonic()
        if delay>0:time.sleep(delay)
        with opened() as stream:send(stream,*catalog[0],2)
        report['status']='raw_stream_plus_repeat_sent_no_receiver_ack'
    except Exception as e:report['error']=str(e);raise
    finally:
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes((json.dumps(report,indent=2)+'\n').encode())
if __name__=='__main__':main()

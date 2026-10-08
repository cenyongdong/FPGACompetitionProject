"""One finite input session and a normal guarded RTSP recorder; no data retries."""
import argparse,hashlib,json,socket,struct,threading,time
from pathlib import Path
from live_rtsp_client import LiveClient

def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--fps',choices=[2,5],type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True);catalog=[]
    for line in (a.package/'cases.tsv').read_text().splitlines():
        group,name,frame,stamp=line.split()
        if group=='expanded':catalog.append((name,(a.package/'inputs'/(name+'.csi')).read_bytes(),int(frame)))
    assert len(catalog)==27;sent=[];errors=[]
    def sender():
        report=dict(fps=a.fps,sent=sent,startup_only=True,session_count=1)
        try:
            deadline=time.monotonic()+65
            while True:
                try:s=socket.create_connection(('192.168.126.49',39001),1);break
                except (ConnectionRefusedError,TimeoutError):
                    assert time.monotonic()<deadline,'Input startup timeout';time.sleep(.1)
            with s:
                s.settimeout(5);s.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1);epoch=time.monotonic()
                for i in range(33):
                    delay=epoch+i/a.fps-time.monotonic()
                    if delay>0:time.sleep(delay)
                    name,original,fixture=catalog[i%27];raw=bytearray(original);struct.pack_into('<Q',raw,16,100000+i)
                    before=time.monotonic_ns();s.sendall(raw);sent.append(dict(sequence=i,transport_id=100000+i,case=name,fixture_frame_id=fixture,sha256=hashlib.sha256(raw).hexdigest(),payload_sha256=hashlib.sha256(raw[32:]).hexdigest(),begin_pc_ns=before,end_pc_ns=time.monotonic_ns()))
            report['status']='sent_no_receiver_ack'
        except Exception as e:errors.append(e);report.update(status='failed',error=str(e))
        finally:(a.output/'sender.json').write_text(json.dumps(report,indent=2)+'\n')
    worker=threading.Thread(target=sender);client=None;worker.start()
    try:
        client=LiveClient(a.output);result=client.run_live();client.save(result)
    except Exception as e:
        if client:client.save(dict(status='failed',error=str(e),frames=client.frames,packets=client.packet_log))
        raise
    finally:
        if client:client.sock.close()
        worker.join(timeout=70)
    assert not worker.is_alive() and not errors and len(sent)==33,str(errors)
    print('Finite system peer completed:',len(client.frames),'AUs; PC/board clocks not subtracted',flush=True)
if __name__=='__main__':main()

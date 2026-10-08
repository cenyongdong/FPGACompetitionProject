"""Three-window process regression uses original cases with independent transport IDs."""
import argparse,hashlib,json,socket,struct,threading,time
from pathlib import Path
from live_rtsp_client import LiveClient

def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();a.output.mkdir(parents=True)
    catalog=[]
    for line in (a.package/'cases.tsv').read_text().splitlines():
        group,name,frame,stamp=line.split()
        if group=='base':catalog.append((name,(a.package/'inputs'/(name+'.csi')).read_bytes(),int(frame)))
    assert len(catalog)==3;catalog.append(catalog[0]);errors=[];sent=[]
    def sender():
        report=dict(fps=2,sent=sent,session_count=1)
        try:
            deadline=time.monotonic()+65
            while True:
                try:s=socket.create_connection(('192.168.126.49',39001),1);break
                except (ConnectionRefusedError,TimeoutError):
                    assert time.monotonic()<deadline,'First listener readiness timed out';time.sleep(.1)
            with s:
                s.settimeout(5);epoch=time.monotonic()
                for i,(name,original,frame) in enumerate(catalog):
                    delay=epoch+i*.5-time.monotonic()
                    if delay>0:time.sleep(delay)
                    raw=bytearray(original);struct.pack_into('<Q',raw,16,100000+i);s.sendall(raw);sent.append(dict(sequence=i,case=name,fixture_frame_id=frame,transport_id=100000+i,payload_sha256=hashlib.sha256(raw[32:]).hexdigest()))
            report['status']='sent_no_receiver_ack'
        except Exception as e:errors.append(e);report.update(status='failed',error=str(e))
        finally:(a.output/'sender.json').write_text(json.dumps(report,indent=2)+'\n')
    worker=threading.Thread(target=sender);worker.start();client=None
    try:client=LiveClient(a.output);result=client.run_live();client.save(result)
    except Exception as e:
        if client:client.save(dict(status='failed',error=str(e),frames=client.frames,packets=client.packet_log))
        raise
    finally:
        if client:client.sock.close()
        worker.join(timeout=70)
    assert not worker.is_alive() and not errors and len(sent)==4,str(errors)
    print('Display process original-three peer completed',len(client.frames),'AUs',flush=True)
if __name__=='__main__':main()

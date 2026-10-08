"""Intentional no-read peer after PLAY; send keepalive without reading replies."""
import argparse,json,re,socket,time
from pathlib import Path
from rtsp_replay_client import Client

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();a.output.mkdir(parents=True)
    client=Client.__new__(Client);client.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);client.sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,4096);client.sock.settimeout(5)
    client.buffer=b'';client.cseq=0;client.session=None;client.uri='rtsp://192.168.126.49:8554/pose';client.backlog=[]
    try:
        client.sock.connect(('192.168.126.49',8554));client.request('OPTIONS');h,sdp=client.request('DESCRIBE',headers={'Accept':'application/sdp'});(a.output/'session.sdp').write_bytes(sdp)
        tracks=[r.strip() for r in re.findall(r'^a=control:(.+)\r?$',sdp.decode(),re.MULTILINE) if r.strip()!='*'];assert len(tracks)==1
        uri=tracks[0] if tracks[0].startswith('rtsp://') else h.get('content-base',client.uri+'/')+tracks[0]
        h,_=client.request('SETUP',uri=uri,headers={'Transport':'RTP/AVP/TCP;unicast;interleaved=0-1'});client.session=h['session'].split(';')[0];client.request('PLAY')
        started=time.perf_counter();actual_buffer=client.sock.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF);sent=[];error=None
        print('SLOW_CLIENT_PLAYED: reads stopped for bounded8s',flush=True)
        for i in range(8):
            time.sleep(1)
            if i in (2,5):
                client.cseq+=1;request=f'GET_PARAMETER {client.uri} RTSP/1.0\r\nCSeq: {client.cseq}\r\nSession: {client.session}\r\n\r\n'
                try:client.sock.sendall(request.encode());sent.append(time.perf_counter()-started)
                except OSError as e:error=str(e);break
        result=dict(status='intentional_slow_reader_completed',no_reads_after_PLAY=True,requested_receive_buffer=4096,actual_receive_buffer=actual_buffer,held_seconds=time.perf_counter()-started,raw_keepalive_sent_at_s=sent,send_error=error,pre_PLAY_interleaved_packets=len(client.backlog),VPU_NPU=False)
        (a.output/'review.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(result['status'])
    finally:client.sock.close()
if __name__=='__main__':main()

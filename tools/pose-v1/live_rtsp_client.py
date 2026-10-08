"""Bounded receiver for new real-capture stream. References are reviewed afterwards."""
import argparse,base64,hashlib,json,re,socket,struct,time
from pathlib import Path
from rtsp_replay_client import Client

class LiveClient(Client):
    def __init__(self,output):
        self.sock=socket.create_connection(('192.168.126.49',8554),5);self.sock.settimeout(8)
        self.buffer=b'';self.cseq=0;self.session=None;self.uri='rtsp://192.168.126.49:8554/pose'
        self.output=output;self.packet_log=[];self.frames=[];self.backlog=[];self.seq=None;self.ssrc=None;self.fu=None;self.pending=[];self.pts=None;self.keepalives=[]
        self.params=[];self.raw=bytearray()

    def rtp(self,channel,packet):
        if channel==1:self.packet_log.append(dict(event='rtcp',bytes=len(packet)));return
        assert channel==0 and len(packet)>=12 and packet[0]>>6==2 and packet[1]&127==self.payload_type
        seq,pts,ssrc=struct.unpack('!HII',packet[2:12]);assert self.seq is None or seq==(self.seq+1)&65535,'RTP sequence gap';self.seq=seq
        if self.ssrc is None:self.ssrc=ssrc
        assert self.ssrc==ssrc
        header=12+4*(packet[0]&15);assert header<=len(packet)
        if packet[0]&16:
            assert header+4<=len(packet);header+=4+4*struct.unpack('!H',packet[header+2:header+4])[0]
        end=len(packet)-packet[-1] if packet[0]&32 else len(packet);assert header<end
        payload=packet[header:end];typ=payload[0]&31;marker=bool(packet[1]&128)
        if self.pts is None:self.pts=pts
        assert self.pts==pts,'Timestamp changed within AU'
        self.packet_log.append(dict(event='rtp',seq=seq,timestamp=pts,ssrc=ssrc,marker=marker,bytes=len(payload),arrival_ns=time.perf_counter_ns()))
        if typ in (1,5,7,8):assert self.fu is None;self.nal(payload)
        elif typ==24:
            assert self.fu is None;pos=1
            while pos<len(payload):
                assert pos+2<=len(payload);n=struct.unpack('!H',payload[pos:pos+2])[0];pos+=2
                assert n>0 and pos+n<=len(payload);self.nal(payload[pos:pos+n]);pos+=n
        elif typ==28:
            assert len(payload)>=3 and not payload[1]&32;start,last=bool(payload[1]&128),bool(payload[1]&64)
            if start:assert self.fu is None and not last;self.fu=bytearray([(payload[0]&224)|(payload[1]&31)])
            assert self.fu is not None and self.fu[0]&31==payload[1]&31
            self.fu.extend(payload[2:]);assert len(self.fu)<=262144
            if last:self.nal(bytes(self.fu));self.fu=None
        else:raise AssertionError(f'Unsupported RTP NAL {typ}')
        if marker:
            assert self.fu is None;vcl=[n for n in self.pending if n[0]&31 in (1,5)];assert len(vcl)==1
            if not self.frames:assert vcl[0][0]&31==5,'Initial frame is not IDR'
            for nal in self.pending:self.raw+=b'\0\0\0\1'+nal
            self.frames.append(dict(index=len(self.frames),timestamp=pts,vcl_sha256=hashlib.sha256(vcl[0]).hexdigest(),idr=vcl[0][0]&31==5,arrival_ns=time.perf_counter_ns()))
            self.pending=[];self.pts=None
            if len(self.frames)%100==0:print(f'Live receiver: {len(self.frames)} complete AUs',flush=True)

    def run_live(self):
        self.request('OPTIONS');headers,sdp=self.request('DESCRIBE',headers={'Accept':'application/sdp'});(self.output/'session.sdp').write_bytes(sdp)
        text=sdp.decode('ascii');rtp=re.search(r'a=rtpmap:(\d+) H264/90000',text);assert rtp;self.payload_type=int(rtp[1])
        sets=re.search(r'sprop-parameter-sets=([^;\r\n]+)',text);assert sets;self.params=[base64.b64decode(x,validate=True) for x in sets[1].split(',')]
        assert len(self.params)==2 and [n[0]&31 for n in self.params]==[7,8];self.raw=bytearray(b'\0\0\0\1'+self.params[0]+b'\0\0\0\1'+self.params[1])
        track=[x.strip() for x in re.findall(r'^a=control:(.+)\r?$',text,re.MULTILINE) if x.strip()!='*'];assert len(track)==1
        uri=track[0] if track[0].startswith('rtsp://') else headers.get('content-base',self.uri+'/')+track[0]
        h,_=self.request('SETUP',uri=uri,headers={'Transport':'RTP/AVP/TCP;unicast;interleaved=0-1'});assert 'interleaved=0-1' in h['transport'];self.session=h['session'].split(';')[0]
        self.request('PLAY',headers={'Range':'npt=0.000-'});start=time.perf_counter();keep=start+3;ended=False
        while True:
            assert time.perf_counter()-start<95 and len(self.frames)<1000,'Finite live client limit'
            try:
                m=self.backlog.pop(0) if self.backlog else self.message();assert m[0]=='packet';self.rtp(m[1],m[2])
                if time.perf_counter()>=keep:
                    self.request('GET_PARAMETER');self.keepalives.append(dict(response=200,elapsed_s=time.perf_counter()-start));keep=time.perf_counter()+3
            except EOFError:
                while self.backlog:
                    m=self.backlog.pop(0);assert m[0]=='packet';self.rtp(m[1],m[2])
                assert not self.buffer,'Server closed during a partial message'
                ended=True;break # Accepted only after independent board EOF/exit review.
        assert ended and self.fu is None and not self.pending and len(self.frames)>=100,'Incomplete stream end'
        return dict(status='live_received_pending_board_content_review',frames=self.frames,packets=self.packet_log,keepalives=self.keepalives,SDP_parameters_hex=[n.hex() for n in self.params],server_closed=True,clock_rate=90000,sequence_gaps=0,elapsed_s=time.perf_counter()-start)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();a.output.mkdir(parents=True);client=None
    try:
        client=LiveClient(a.output);result=client.run_live();client.save(result);print(f'Live recording completed: {len(client.frames)} AUs; content review pending',flush=True)
    except Exception as e:
        if client:client.save(dict(status='failed',error=str(e),frames=client.frames,packets=client.packet_log))
        raise
    finally:
        if client:client.sock.close()
if __name__=='__main__':main()

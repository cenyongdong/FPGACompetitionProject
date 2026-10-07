"""Finite TCP-interleaved RTSP client: verify real RTP NAL bytes and capture PTS.

Two independent sessions, first join then reconnect; no decoding dependencies.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import socket
import struct
import time

def sha(data): return hashlib.sha256(data).hexdigest()

class Client:
    def __init__(self, host, output, package):
        self.sock=socket.create_connection((host,8554),5);self.sock.settimeout(5)
        self.buffer=b'';self.cseq=0;self.session=None;self.uri=f'rtsp://{host}:8554/pose'
        self.output=output;self.package=package;self.packet_log=[];self.frames=[]
        self.backlog=[];self.seq=None;self.ssrc=None;self.fu=None;self.pending=[];self.pts=None
        self.keepalives=[]
        data=(package/'video.h264').read_bytes();self.expected={};self.params=[]
        for line in (package/'index.tsv').read_text().splitlines():
            kind,pts,offset,size,typ=line.split();offset=int(offset);size=int(size)
            nal=data[offset+4:offset+size]
            if kind=='FRAME':self.expected[sha(nal)]={'encoded_id':int(pts)//100000,'nal':nal}
            else:self.params.append(nal)
        assert len(self.expected)==54 and len(self.params)==2
        self.raw=bytearray(b'\0\0\0\1'+self.params[0]+b'\0\0\0\1'+self.params[1])

    def fill(self, n):
        assert n<=4*1024*1024
        while len(self.buffer)<n:
            b=self.sock.recv(65536)
            if not b:raise EOFError('RTSP connection closed')
            self.buffer+=b
            assert len(self.buffer)<=4*1024*1024

    def message(self):
        self.fill(1)
        if self.buffer[0]==36:
            self.fill(4);channel=self.buffer[1];length=struct.unpack('!H',self.buffer[2:4])[0]
            self.fill(4+length);data=self.buffer[4:4+length];self.buffer=self.buffer[4+length:]
            return ('packet',channel,data)
        while b'\r\n\r\n' not in self.buffer:self.fill(len(self.buffer)+1)
        head,end=self.buffer.split(b'\r\n\r\n',1);assert len(head)<131072
        lines=head.decode('ascii').split('\r\n');headers={}
        for line in lines[1:]:
            k,v=line.split(':',1);headers[k.lower()]=v.strip()
        size=int(headers.get('content-length','0'));assert 0<=size<131072
        self.fill(len(head)+4+size)
        body=self.buffer[len(head)+4:len(head)+4+size];self.buffer=self.buffer[len(head)+4+size:]
        return ('response',lines[0],headers,body)

    def request(self,method,uri=None,headers=None):
        self.cseq+=1
        fields={'CSeq':str(self.cseq),'User-Agent':'pose-v1-finite-audit'}
        if self.session:fields['Session']=self.session
        fields.update(headers or {})
        raw=f'{method} {uri or self.uri} RTSP/1.0\r\n'+''.join(f'{k}: {v}\r\n' for k,v in fields.items())+'\r\n'
        self.sock.sendall(raw.encode())
        while True:
            m=self.message()
            if m[0]=='packet':self.backlog.append(m);continue
            _,status,h,body=m
            assert status=='RTSP/1.0 200 OK',status
            assert int(h['cseq'])==self.cseq
            return h,body

    def nal(self, data):
        assert data and len(data)<=262144
        typ=data[0]&31
        assert typ in (1,5,7,8),typ
        if typ in (7,8):assert data==self.params[typ-7], 'Actual parameter set differs'
        self.pending.append(data)

    def rtp(self, channel, packet):
        if channel==1:
            self.packet_log.append({'event':'rtcp','bytes':len(packet),'packet_type':packet[1] if len(packet)>1 else None});return
        assert channel==0 and len(packet)>=12 and packet[0]>>6==2
        assert packet[1]&127==self.payload_type
        seq,pts,ssrc=struct.unpack('!HII',packet[2:12])
        if self.seq is not None:assert seq==(self.seq+1)&65535,'RTP sequence gap'
        self.seq=seq
        if self.ssrc is None:self.ssrc=ssrc
        assert self.ssrc==ssrc
        header=12+4*(packet[0]&15);assert header<=len(packet)
        if packet[0]&16:
            assert header+4<=len(packet)
            header+=4+4*struct.unpack('!H',packet[header+2:header+4])[0]
        end=len(packet)-packet[-1] if packet[0]&32 else len(packet)
        assert header<end
        payload=packet[header:end];typ=payload[0]&31;marker=bool(packet[1]&128)
        if self.pts is None:self.pts=pts
        assert pts==self.pts,'Timestamp changed within pending AU'
        self.packet_log.append({'event':'rtp','seq':seq,'timestamp':pts,'ssrc':ssrc,'marker':marker,'payload_bytes':len(payload),'nal_type':typ,'arrival_ns':time.perf_counter_ns()})
        if typ in (1,5,7,8):
            assert self.fu is None;self.nal(payload)
        elif typ==24:
            assert self.fu is None;pos=1
            while pos<len(payload):
                assert pos+2<=len(payload);n=struct.unpack('!H',payload[pos:pos+2])[0];pos+=2
                assert n>0 and pos+n<=len(payload);self.nal(payload[pos:pos+n]);pos+=n
        elif typ==28:
            assert len(payload)>=3
            start,end_bit=bool(payload[1]&128),bool(payload[1]&64)
            assert not payload[1]&32
            if start:
                assert self.fu is None and not end_bit
                self.fu=bytearray([(payload[0]&224)|(payload[1]&31)])
            assert self.fu is not None
            assert (self.fu[0]&31)==(payload[1]&31)
            self.fu.extend(payload[2:]);assert len(self.fu)<=262144
            if end_bit:self.nal(bytes(self.fu));self.fu=None
        else:raise AssertionError(f'Unsupported RTP packetization {typ}')
        if marker:
            assert self.fu is None
            vcl=[n for n in self.pending if n[0]&31 in (1,5)];assert len(vcl)==1
            digest=sha(vcl[0]);assert digest in self.expected, 'RTP reconstructed VCL differs from encoder'
            expected=self.expected[digest];frame_id=expected['encoded_id']
            if self.frames:
                assert frame_id==(self.frames[-1]['encoded_id']+1)%54
                assert (pts-self.frames[-1]['timestamp'])&0xffffffff==9000
            else:assert vcl[0][0]&31==5,'Join must start on IDR'
            for n in self.pending:self.raw+=b'\0\0\0\1'+n
            self.frames.append({'index':len(self.frames),'encoded_id':frame_id,'timestamp':pts,
                                'vcl_sha256':digest,'idr':vcl[0][0]&31==5,'arrival_ns':time.perf_counter_ns()})
            self.pending=[];self.pts=None

    def run(self,count):
        self.request('OPTIONS')
        headers,sdp=self.request('DESCRIBE',headers={'Accept':'application/sdp'})
        (self.output/'session.sdp').write_bytes(sdp)
        text=sdp.decode('ascii')
        match=re.search(r'a=rtpmap:(\d+) H264/90000',text);assert match
        self.payload_type=int(match[1]);assert 96<=self.payload_type<=127
        sets=re.search(r'sprop-parameter-sets=([^;\r\n]+)',text);assert sets
        assert [base64.b64decode(x,validate=True) for x in sets[1].split(',')]==self.params
        controls=re.findall(r'^a=control:(.+)\r?$',text,re.MULTILINE)
        track=[c.strip() for c in controls if c.strip()!='*'];assert len(track)==1
        # urllib does not classify rtsp as a relative-resolution scheme.
        control=track[0] if track[0].startswith('rtsp://') else headers.get('content-base',self.uri+'/')+track[0]
        h,_=self.request('SETUP',uri=control,headers={'Transport':'RTP/AVP/TCP;unicast;interleaved=0-1'})
        assert 'interleaved=0-1' in h['transport'];self.session=h['session'].split(';')[0]
        self.request('PLAY',headers={'Range':'npt=0.000-'})
        start=time.perf_counter();next_keepalive=start+3
        while len(self.frames)<count:
            assert time.perf_counter()-start<20
            m=self.backlog.pop(0) if self.backlog else self.message()
            assert m[0]=='packet';self.rtp(m[1],m[2])
            if time.perf_counter()>=next_keepalive:
                self.request('GET_PARAMETER')
                self.keepalives.append({'method':'GET_PARAMETER','response':200,'elapsed_s':time.perf_counter()-start})
                next_keepalive=time.perf_counter()+3
        self.request('TEARDOWN')
        return {'status':'finite_RTSP_RTP_verified','frames':self.frames,'packets':self.packet_log,
                'SDP_actual_parameter_sets':True,'RTP_step_ticks':9000,'clock_rate':90000,
                'payload_type':self.payload_type,'sequence_gaps':0,'keepalives':self.keepalives,
                'reconstructed_h264_sha256':sha(self.raw)}

    def save(self,result):
        (self.output/'received.h264').write_bytes(self.raw)
        (self.output/'review.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())

def main():
    p=argparse.ArgumentParser();p.add_argument('--host',default='192.168.126.49');p.add_argument('--package',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--frames',type=int,default=100)
    a=p.parse_args();assert a.host=='192.168.126.49' and 54<=a.frames<=120
    assert not a.output.exists();a.output.mkdir(parents=True)
    for number in range(2):
        out=a.output/f'client{number+1}';out.mkdir();client=None
        try:
            client=Client(a.host,out,a.package);result=client.run(a.frames);client.save(result)
            print(f'Client {number+1}: {len(result["frames"])} verified frames, exact NAL bytes/9000 RTP ticks, teardown OK',flush=True)
        except Exception as e:
            if client:client.save({'status':'failed','error':str(e),'frames':client.frames,'packets':client.packet_log})
            raise
        finally:
            if client:client.sock.close()
        if number==0:time.sleep(2)
    (a.output/'summary.json').write_bytes((json.dumps({'status':'two_sessions_RTSP_verified','frames_per_session':a.frames,'reconnect':True,'scope':'verified prerecorded encoder output only'},indent=2)+'\n').encode())

if __name__=='__main__':main()

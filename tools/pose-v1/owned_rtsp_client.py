"""Use tested RTSP transport; audit each owned VCL against actual capture PTS."""
import argparse,hashlib,json,socket,struct,time
from pathlib import Path
from rtsp_replay_client import Client

class OwnedClient(Client):
    def __init__(self,host,output,package):
        self.sock=socket.create_connection((host,8554),5);self.sock.settimeout(5)
        self.buffer=b'';self.cseq=0;self.session=None;self.uri=f'rtsp://{host}:8554/pose'
        self.output=output;self.package=package;self.packet_log=[];self.frames=[];self.backlog=[]
        self.seq=None;self.ssrc=None;self.fu=None;self.pending=[];self.pts=None;self.keepalives=[]
        reference=json.loads((package/'expected.json').read_text())
        self.params=[bytes.fromhex(x) for x in reference['parameters']]
        self.expected=reference['frames']
        self.idr={r['vcl_sha256']:r for r in self.expected if r['idr']}
        self.raw=bytearray(b'\0\0\0\1'+self.params[0]+b'\0\0\0\1'+self.params[1])

    def rtp(self,channel,packet):
        if channel==1:self.packet_log.append({'event':'rtcp','bytes':len(packet)});return
        assert channel==0 and len(packet)>=12 and packet[0]>>6==2 and packet[1]&127==self.payload_type
        seq,pts,ssrc=struct.unpack('!HII',packet[2:12])
        assert self.seq is None or seq==(self.seq+1)&65535,'RTP sequence gap'
        self.seq=seq
        if self.ssrc is None:self.ssrc=ssrc
        assert self.ssrc==ssrc
        header=12+4*(packet[0]&15);assert header<=len(packet)
        if packet[0]&16:
            assert header+4<=len(packet);header+=4+4*struct.unpack('!H',packet[header+2:header+4])[0]
        end=len(packet)-packet[-1] if packet[0]&32 else len(packet);assert header<end
        payload=packet[header:end];typ=payload[0]&31;marker=bool(packet[1]&128)
        if self.pts is None:self.pts=pts
        assert pts==self.pts,'Pending AU timestamp changed'
        self.packet_log.append(dict(event='rtp',seq=seq,timestamp=pts,ssrc=ssrc,marker=marker,payload_bytes=len(payload),nal_type=typ,arrival_ns=time.perf_counter_ns()))
        if typ in (1,5,7,8):assert self.fu is None;self.nal(payload)
        elif typ==24:
            assert self.fu is None;pos=1
            while pos<len(payload):
                assert pos+2<=len(payload);n=struct.unpack('!H',payload[pos:pos+2])[0];pos+=2
                assert n>0 and pos+n<=len(payload);self.nal(payload[pos:pos+n]);pos+=n
        elif typ==28:
            assert len(payload)>=3 and not payload[1]&32
            start,last=bool(payload[1]&128),bool(payload[1]&64)
            if start:assert self.fu is None and not last;self.fu=bytearray([(payload[0]&224)|(payload[1]&31)])
            assert self.fu is not None and self.fu[0]&31==payload[1]&31
            self.fu.extend(payload[2:]);assert len(self.fu)<=262144
            if last:self.nal(bytes(self.fu));self.fu=None
        else:raise AssertionError(f'Unsupported packetization {typ}')
        if marker:
            assert self.fu is None;vcl=[n for n in self.pending if n[0]&31 in (1,5)];assert len(vcl)==1
            digest=hashlib.sha256(vcl[0]).hexdigest()
            expected=self.expected[self.frames[-1]['encoded_id']+1] if self.frames else self.idr[digest]
            assert digest==expected['vcl_sha256'],'VCL differs from actual capture order'
            frame_id=expected['encoded_id']
            if self.frames:
                assert frame_id==self.frames[-1]['encoded_id']+1
                first=self.frames[0];ticks=(pts-first['timestamp'])&0xffffffff
                assert abs(ticks-(expected['pts_us']-first['capture_pts_us'])*0.09)<=1.1,'RTP differs from actual capture clock'
            else:assert expected['idr'] and vcl[0][0]&31==5
            for nal in self.pending:self.raw+=b'\0\0\0\1'+nal
            self.frames.append(dict(index=len(self.frames),encoded_id=frame_id,capture_pts_us=expected['pts_us'],timestamp=pts,vcl_sha256=digest,idr=expected['idr']))
            self.pending=[];self.pts=None

def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--frames',type=int,choices=(54,100),default=100);p.add_argument('--join-delay',type=float,default=0);a=p.parse_args()
    assert 0<=a.join_delay<=26
    assert not a.output.exists();a.output.mkdir(parents=True)
    time.sleep(a.join_delay)
    for i in range(2):
        out=a.output/f'client{i+1}';out.mkdir();client=None
        try:
            client=OwnedClient('192.168.126.49',out,a.package);result=client.run(a.frames)
            result.pop('RTP_step_ticks');result.update(actual_capture_PTS=True,scope='owned_AU_adapter_with_recorded_resident_packets')
            client.save(result);print(f'Client{i+1}: {a.frames} exact VCL/actual PTS, IDR join and teardown verified',flush=True)
        except Exception as error:
            if client:client.save(dict(status='failed',error=str(error),frames=client.frames,packets=client.packet_log))
            raise
        finally:
            if client:client.sock.close()
        if i==0:time.sleep(2)
    (a.output/'summary.json').write_bytes((json.dumps(dict(status='owned_AU_two_sessions_passed',frames=2*a.frames,reconnect=True,new_VPU_NPU=False),indent=2)+'\n').encode())
if __name__=='__main__':main()

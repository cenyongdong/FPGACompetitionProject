"""Controller-only startup URI readiness; no data-session or model retries."""
from pathlib import Path
p=Path(__file__).with_name('source_readback_peer_stream_ready.py');assert not p.exists()
s=Path(__file__).with_name('source_readback_peer_ready.py').read_text(encoding='utf-8')
s=s.replace('def main():','''class StreamReadyClient(LiveClient):
    def request(self,method,uri=None,headers=None):
        if method!='DESCRIBE' or self.session:
            return super().request(method,uri,headers)
        deadline=time.monotonic()+10;events=[]
        try:
            while True:
                try:
                    result=super().request(method,uri,headers)
                    events.append(dict(status=200,time_pc_ns=time.monotonic_ns()));return result
                except AssertionError as error:
                    if str(error)!='RTSP/1.0 404 Stream Not Found' or time.monotonic()>=deadline:raise
                    events.append(dict(status=404,time_pc_ns=time.monotonic_ns()));time.sleep(.1)
        finally:
            (self.output/'stream-startup.json').write_text(json.dumps(dict(startup_only=True,PLAY_retried=False,input_session_retried=False,events=events))+'\\n')

def main():''').replace('try:client=LiveClient(a.output);break','try:client=StreamReadyClient(a.output);break')
p.write_text(s,encoding='utf-8',newline='\n')

"""Send frozen raw CSI records unchanged; no preprocessing, predictions or GT."""
import argparse,json,socket,time,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--package',type=Path,required=True);p.add_argument('--host',required=True);p.add_argument('--port',type=int,default=39001)
p.add_argument('--cases',choices=['three','27'],required=True);p.add_argument('--fps',type=float,default=2);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();assert 0<a.fps<=10 and not a.output.exists()
m=json.loads((a.package/'manifest.json').read_text());cases=m['cases'] if a.cases=='three' else m['expanded_cases']
payloads=[(a.package/'inputs'/(c['case']+'.csi')).read_bytes() for c in cases]
for c,raw in zip(cases,payloads):
    assert len(raw)==86432 and raw[:8]==b'PIWCSI1\0' and hashlib.sha256(raw).hexdigest()==c['raw_sha256']
report=dict(status='not_completed',cases=a.cases,fps=a.fps,sent=[])
try:
    with socket.create_connection((a.host,a.port),timeout=5) as stream:
        stream.settimeout(5);stream.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1);start=time.monotonic()
        for i,(c,raw) in enumerate(zip(cases,payloads)):
            delay=start+i/a.fps-time.monotonic()
            if delay>0:time.sleep(delay)
            stream.sendall(raw);report['sent'].append(dict(case=c['case'],frame_id=c['frame_id'],bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    report['status']='raw_send_completed_no_receiver_ack';print('Sent raw records:',len(cases))
finally:
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')

"""Local Linux mock only: the optional derived subscriber cannot pace inference."""
import json,socket,subprocess,sys,time,threading,signal
from pathlib import Path
from test_resident import port,frame
binary,output=sys.argv[1:];root=Path(output);root.mkdir()
ip,raw,stat,view=[port() for _ in range(4)]
p=subprocess.Popen([binary,'--output',str(root/'run'),'--session','1234','--seconds','20','--input-port',str(ip),'--result-port',str(raw),'--status-port',str(stat),'--view-port',str(view),'--mock-delay-ms','1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
finish=threading.Event();thread=None;slow=None
def status():
 with socket.create_connection(('127.0.0.1',stat),1) as s:
  b=b''
  while True:
   part=s.recv(4096)
   if not part:break
   b+=part
  return json.loads(b)
def feed():
 with socket.create_connection(('127.0.0.1',ip),2) as s:
  for i in range(1,10000):
   if finish.is_set():break
   s.sendall(frame(i));time.sleep(.003)
try:
 ready=p.stdout.readline();assert 'mock=1' in ready,ready
 slow=socket.socket();slow.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,1024);slow.connect(('127.0.0.1',view))
 thread=threading.Thread(target=feed);thread.start();time.sleep(.5);before=status();time.sleep(4);after=status()
 assert after['inferred']>before['inferred']+100,(before,after)
 slow.close();slow=None;time.sleep(.7)
 with socket.create_connection(('127.0.0.1',view),2) as s:
  s.settimeout(2);data=b''
  while b'\n' not in data:data+=s.recv(37)
  first=json.loads(data.split(b'\n')[0]);assert first['schema']=='PIWVIEW1' and first['replay'] is False
 finish.set();thread.join();thread=None;p.send_signal(signal.SIGTERM);out,err=p.communicate(timeout=8);assert p.returncode==0,(out,err)
 (root/'result.json').write_text(json.dumps(dict(before=before,after=after,reconnected_sequence=first['sequence'],native_exit=p.returncode),indent=2))
 (root/'stdout.log').write_text(ready+out);(root/'stderr.log').write_text(err);print('PRESENTATION_IO_PASS inferred_progress',after['inferred']-before['inferred'])
finally:
 finish.set()
 if slow:slow.close()
 if thread:thread.join(timeout=3)
 if p.poll() is None:p.send_signal(signal.SIGTERM);p.wait(timeout=8)

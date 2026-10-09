"""Prepare the controller-only readiness fix; does not alter the board program."""
from pathlib import Path
p=Path(__file__).with_name('source_readback_peer_ready.py');assert not p.exists()
s=Path(__file__).with_name('display_process_peer.py').read_text(encoding='utf-8')
s=s.replace('deadline=time.monotonic()+65','deadline=time.monotonic()+110').replace('worker.join(timeout=70)','worker.join(timeout=115)')
s=s.replace('try:client=LiveClient(a.output);result=client.run_live();client.save(result)', '''print('PEER_ARMED: waiting for the first RTSP and input listeners; no data retries',flush=True)
    try:
        deadline=time.monotonic()+110
        while True:
            try:client=LiveClient(a.output);break
            except (ConnectionRefusedError,TimeoutError):
                assert time.monotonic()<deadline,'First RTSP listener readiness timed out';time.sleep(.1)
        result=client.run_live();client.save(result)''')
s=s.replace("catalog=[]","(a.output/'controller-source.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),startup_only_connection_wait=True,frame_protocol_unchanged=True,one_input_session=True))+'\\n')\n    catalog=[]")
p.write_text(s,encoding='utf-8',newline='\n')

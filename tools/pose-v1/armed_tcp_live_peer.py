"""Prestart host tools; START from the controller releases the ready peer once."""
import argparse,hashlib,json,queue,sys,threading,time
from pathlib import Path
import tcp_live_peer_ready

def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--cases',choices=['three','27'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    commands=queue.Queue(maxsize=1)
    threading.Thread(target=lambda:commands.put(sys.stdin.readline()),daemon=True).start()
    print('PEER_ARMED '+hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),flush=True)
    start=time.monotonic();command=commands.get(timeout=90)
    assert command.strip()=='START','Explicit startup release required'
    waited=time.monotonic()-start
    try:tcp_live_peer_ready.main()
    finally:
        if a.output.exists():
            report=dict(launcher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),prearmed=True,release='START',armed_wait_s=waited,bounded_wait_s=90)
            (a.output/'launch-provenance.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
if __name__=='__main__':main()

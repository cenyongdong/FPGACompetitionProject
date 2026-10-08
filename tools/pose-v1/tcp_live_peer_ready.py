"""Start the RTSP recorder and input sender together at actual RTSP readiness."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from live_rtsp_client import LiveClient

def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--cases',choices=['three','27'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True)
    stdout=(a.output/'sender.stdout.log').open('wb');stderr=(a.output/'sender.stderr.log').open('wb');client=None
    provenance={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in (Path(__file__).name,'send_live_windows_ready.py')}
    (a.output/'controller-sources.json').write_bytes((json.dumps(provenance,indent=2)+'\n').encode())
    sender=subprocess.Popen([sys.executable,str(Path(__file__).with_name('send_live_windows_ready.py')),'--package',str(a.package),'--cases',a.cases,'--output',str(a.output/'sender.json')],stdout=stdout,stderr=stderr)
    try:
        client=LiveClient(a.output);result=client.run_live();client.save(result)
        assert sender.wait(timeout=2)==0,'CSI sender failed or did not finish'
        print('TCP input and live RTSP recording completed:',len(client.frames),flush=True)
    except Exception as e:
        if client:client.save(dict(status='failed',error=str(e),frames=client.frames,packets=client.packet_log))
        raise
    finally:
        if client:client.sock.close()
        if sender.poll() is None:sender.terminate();sender.wait(timeout=5)
        stdout.close();stderr.close()
if __name__=='__main__':main()

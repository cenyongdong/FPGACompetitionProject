"""Exercise the real watchdog against temporary files, never a router."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import subprocess
import sys
import time


def scenario(root, case):
    folder=root/case
    folder.mkdir()
    now=int(float(Path('/proc/uptime').read_text().split()[0]))
    (folder/'armed').touch()
    (folder/'started').write_text(str(now))
    (folder/'guard-status.json').write_text('{}')
    (folder/'lease').write_text('' if case!='healthy' else str(now))
    (folder/'watchdog.sh').write_bytes(Path(__file__).with_name('router_watchdog.sh').read_bytes())
    (folder/'restore.sh').write_text('touch restored; rm -f armed\n')
    process=subprocess.Popen(['sh','watchdog.sh'],cwd=folder,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        if case=='transient_empty':
            time.sleep(3.3)
            # The second bounded read must observe the recovered heartbeat.
            (folder/'lease.tmp').write_text(str(now+3))
            (folder/'lease.tmp').replace(folder/'lease')
        if case!='persistent_empty':
            time.sleep(1.2 if case=='transient_empty' else 4.5)
            assert not (folder/'restored').exists(),case
            (folder/'armed').unlink()
        stdout,stderr=process.communicate(timeout=8)
        assert process.returncode==0,(case,stdout,stderr)
        assert (folder/'restored').exists()==(case=='persistent_empty'),case
        if case=='persistent_empty':
            assert 'last=0' in (folder/'watchdog-trigger.log').read_text()
        return {'passed':True,'restored':(folder/'restored').exists()}
    finally:
        if process.poll() is None:
            process.terminate()
            process.communicate(timeout=4)


if __name__=='__main__':
    root=Path(sys.argv[1]).resolve()
    root.mkdir()
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={case:pool.submit(scenario,root,case) for case in ('healthy','transient_empty','persistent_empty')}
        results={case:future.result() for case,future in futures.items()}
    (root/'result.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results))

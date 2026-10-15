"""One foreground, bounded run with scoped process-group cleanup and full logs."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

out = Path(sys.argv[1]).resolve()
assert out.parent == Path('/public/cyd/Person-in-WiFi-3D-repo/result')
assert not (out / 'execution.json').exists(), 'Do not restart an execution'
started = time.monotonic()
env = dict(os.environ, CUDA_VISIBLE_DEVICES='0', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
command = [sys.executable, '-u', str(out / 'paired_eval.py'), '--output', str(out)]
info = dict(status='starting', wrapper_pid=os.getpid(), command=command,
            cwd=str(out.parent.parent), GPU=0, timeout_seconds=1800)
def save():
    (out / 'execution.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
save()
with (out / 'stdout.log').open('xb') as stdout, (out / 'stderr.log').open('xb') as stderr:
    proc = subprocess.Popen(command,cwd=info['cwd'],env=env,stdout=stdout,stderr=stderr,start_new_session=True)
    info.update(status='running',child_pid=proc.pid,process_group=proc.pid)
    save()
    try:
        code = proc.wait(timeout=1800)
        info.update(status='complete' if code == 0 else 'failed',exit_code=code)
    except subprocess.TimeoutExpired:
        info.update(status='timeout',exit_code=124)
        os.killpg(proc.pid,signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL)
            proc.wait()
    finally:
        # Only this run's process group; never other users' GPU processes.
        try:
            os.killpg(proc.pid,signal.SIGTERM)
        except ProcessLookupError:
            pass
        info['seconds'] = time.monotonic()-started
        save()
print(json.dumps(info),flush=True)
sys.exit(info['exit_code'])

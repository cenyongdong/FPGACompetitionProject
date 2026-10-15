"""Collect only a completed run; prove cleanup, then archive complete raw evidence."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

out = Path(sys.argv[1]).resolve()
assert out.parent == Path('/public/cyd/Person-in-WiFi-3D-repo/result')
execution = json.loads((out / 'execution.json').read_text())
assert execution['status'] == 'complete' and execution['exit_code'] == 0
assert not (out / 'failure.json').exists()
archive = out.with_suffix('.tar.gz')
assert not archive.exists()
ps = subprocess.run(['ps','-eo','pid,ppid,pgid,args'],check=True,capture_output=True,text=True)
owned = []
for row in ps.stdout.splitlines()[1:]:
    fields = row.split(None,3)
    if len(fields) == 4 and (int(fields[0]) in (execution['wrapper_pid'],execution['child_pid'])
                            or int(fields[2]) == execution['process_group']):
        owned.append(row)
assert not owned, 'Run still owns processes: ' + repr(owned)
gpu = subprocess.run(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,process_name,used_memory',
                      '--format=csv,noheader'],check=True,capture_output=True,text=True)
shutil.copyfile(out.parent.parent / 'data/wifipose/test_data/test_data_list.txt',out / 'test_data_list.txt')
cleanup = dict(status='run_process_group_and_wrapper_absent',execution=execution,
               matching_processes=owned,nvidia_compute_snapshot=gpu.stdout,
               only_owned_processes_checked=True,other_users_untouched=True)
(out / 'cleanup.json').write_text(json.dumps(cleanup,indent=2)+'\n')
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()
files = {p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()}
(out / 'files.json').write_text(json.dumps(files,indent=2)+'\n')
with tarfile.open(archive,'w:gz',compresslevel=1) as tar:
    tar.add(out,arcname=out.name)
identity = dict(path=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),
                unpacked_bytes=sum(f['bytes'] for f in files.values()),files=len(files)+1)
archive.with_suffix(archive.suffix+'.json').write_text(json.dumps(identity,indent=2)+'\n')
print(json.dumps(identity),flush=True)

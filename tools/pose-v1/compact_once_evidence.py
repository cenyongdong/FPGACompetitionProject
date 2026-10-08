"""User-authorized single compaction observation; no retry/cache clearing."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
output=Path(sys.argv[1]);assert not output.exists();output.mkdir()
def snapshots(label):
    for name in ('buddyinfo','pagetypeinfo','meminfo','vmstat','cmdline'):
        (output/(label+'.'+name+'.txt')).write_bytes((Path('/proc')/name).read_bytes())
    result=subprocess.run(['dmesg'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    (output/(label+'.dmesg.log')).write_bytes(result.stdout)
snapshots('before')
report=dict(status='single_write_attempted',requested_compactions=1,user_authorized=True,drop_caches=False,reboot=False,persistent_sysctl=False)
(output/'action.json').write_text(json.dumps(report)+'\n')
begin=time.monotonic_ns()
try:
    Path('/proc/sys/vm/compact_memory').write_text('1\n')
    report.update(status='single_compaction_completed',elapsed_ns=time.monotonic_ns()-begin)
finally:
    snapshots('after');(output/'action.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'files.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(output.iterdir()) if p.is_file() and p.name!='files.sha256'))
print(json.dumps(report))

"""Explicit one-shot preparation authorized by agent; no cache/reboot changes."""
from pathlib import Path
import json,subprocess,time,re,sys,hashlib
root=Path('/tmp/pose-producer-vpu-20261011-r2');out=root/'resources-on';assert sys.argv[1]=='compact-once' and not out.exists();out.mkdir()
def take(prefix):
    for n in ('buddyinfo','pagetypeinfo','meminfo','vmstat'):(out/(prefix+'.'+n)).write_bytes(Path('/proc/'+n).read_bytes())
    (out/(prefix+'.dmesg.txt')).write_bytes(subprocess.check_output(['dmesg']))
def units(p):
    total=0;rows=[]
    for line in p.read_text().splitlines():
        m=re.match(r'Node\s+\d+,\s+zone\s+(\w+),\s+type\s+(Unmovable|Movable|Reclaimable)\s+(.*)',line)
        if m:
            counts=[int(x) for x in m[3].split()];assert len(counts)==11
            n=sum(v*(1<<(order-7)) for order,v in enumerate(counts) if order>=7);rows.append({'zone':m[1],'type':m[2],'units512KiB':n});total+=n
    assert rows;return total,rows
take('before');before,rows=units(out/'before.pagetypeinfo')
# This invocation is the agent's explicit resource decision, not a production
# allocation gate or retry. Existing sparse ordinary pages motivate preparation.
start=time.monotonic_ns();Path('/proc/sys/vm/compact_memory').write_text('1\n');end=time.monotonic_ns();take('after');after,after_rows=units(out/'after.pagetypeinfo')
report={'reason':'off-stage had7 ordinary512KiB units; prepare single VPU first start; not success guarantee','before_units512KiB':before,'after_units512KiB':after,'before_rows':rows,'after_rows':after_rows,'writes':1,'elapsed_ns':end-start,'drop_caches':False,'reboot':False,'CMA_changed':False}
(out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
with (out/'files.sha256').open('w') as f:
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!='files.sha256':f.write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n')
print(json.dumps(report),flush=True)

"""Explicit resource decision before VPU; no loop, cache clearing or restart."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,time
root=Path('/tmp/pose-producer-source-read-20261011-r1');out=root/'resources-on';assert not out.exists();out.mkdir()
assert sys.argv[1] in ('audit','compact-once');compact=sys.argv[1]=='compact-once'
def take(prefix):
    for name in ('buddyinfo','pagetypeinfo','meminfo','vmstat'):(out/(prefix+'.'+name)).write_bytes(Path('/proc/'+name).read_bytes())
    (out/(prefix+'.dmesg.txt')).write_bytes(subprocess.check_output(['dmesg']))
def units(p):
    rows=[]
    for line in p.read_text().splitlines():
        m=re.match(r'Node\s+\d+,\s+zone\s+(\w+),\s+type\s+(Unmovable|Movable|Reclaimable)\s+(.*)',line)
        if m:
            counts=[int(x) for x in m[3].split()];assert len(counts)==11
            rows.append({'zone':m[1],'type':m[2],'units512KiB':sum(v*(1<<(order-7)) for order,v in enumerate(counts) if order>=7)})
    assert rows;return sum(x['units512KiB'] for x in rows),rows
take('before');before,rows=units(out/'before.pagetypeinfo');start=time.monotonic_ns()
if compact:Path('/proc/sys/vm/compact_memory').write_text('1\n')
elapsed=time.monotonic_ns()-start;take('after');after,after_rows=units(out/'after.pagetypeinfo')
r={'decision':'compact_once' if compact else 'audit_only','reason':'Agent selected from off-stage ordinary high-order availability; not a guaranteed startup gate',
   'before_units512KiB':before,'after_units512KiB':after,'before_rows':rows,'after_rows':after_rows,'writes':int(compact),'elapsed_ns':elapsed,
   'drop_caches':False,'reboot':False,'CMA_changed':False}
(out/'review.json').write_text(json.dumps(r,indent=2)+'\n')
with (out/'files.sha256').open('w') as f:
    for p in sorted(out.iterdir()):
        if p.name!='files.sha256':f.write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n')
print(json.dumps(r),flush=True)

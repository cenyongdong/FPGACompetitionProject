"""One recorded resource-policy decision; not a numerical-fault fix or retry."""
import json,re,subprocess,time,sys
from pathlib import Path
out=Path(sys.argv[1]);assert not out.exists();out.mkdir()
def snapshot(prefix):
    for name in ('buddyinfo','pagetypeinfo','meminfo','vmstat'):
        (out/(prefix+'.'+name)).write_bytes((Path('/proc')/name).read_bytes())
    (out/(prefix+'.dmesg')).write_bytes(subprocess.check_output(['dmesg']))
    (out/(prefix+'.processes')).write_bytes(subprocess.check_output(['ps','-eo','pid,comm,args']))
snapshot('before')
assert not any(line.split(maxsplit=2)[1].startswith('pose_') for line in (out/'before.processes').read_text().splitlines()[1:])
units=0
for line in (out/'before.pagetypeinfo').read_text().splitlines():
    m=re.search(r'type\s+(Unmovable|Movable|Reclaimable|HighAtomic)\s+([\d\s]+)$',line)
    if m:
        counts=list(map(int,m[2].split()));assert len(counts)==11;units+=sum(counts[i]*2**(i-7) for i in range(7,11))
performed=units<16
begin=time.monotonic_ns()
if performed:
    Path('/proc/sys/vm/compact_memory').write_text('1\n')
elapsed=time.monotonic_ns()-begin
snapshot('after')
report=dict(status='recorded_pre_VPU_resource_decision',ordinary_512KiB_units_before=units,
    policy_margin_units=16,compaction_writes=int(performed),elapsed_ns=elapsed,
    reason='Frozen two-buffer mappings are about6.64MiB and firmware has an observed512KiB ordinary-page request; below16 units is a preparation policy, not a proven allocation bound.',
    kernel_unchanged=(out/'before.dmesg').read_bytes()==(out/'after.dmesg').read_bytes(),
    drop_caches=False,reboot=False,CMA_changed=False,numerical_fault_fixed=False)
(out/'decision.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['kernel_unchanged'],'New kernel diagnostics after resource preparation; stop'
print(json.dumps(report))

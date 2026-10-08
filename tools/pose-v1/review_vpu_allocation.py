"""Independent r7 allocation audit. No hardware calls or pass gate for failure."""
import gzip,json,re
from pathlib import Path
import mixed_validation_gate as old

root=old.ROOT;ev=root/'tools/pose-v1/evidence/pipeline-20261008-r7';run=ev/'combined'
count=old.verify(run);old.verify(ev/'kernel-audit')
assert (run/'exit.txt').read_text().strip()=='1'
assert (run/'stderr.log').read_text().strip()=='STOP: DQBUF: Input/output error'
before=(run/'dmesg.before.log').read_bytes();after=(run/'dmesg.after.log').read_bytes();assert after.startswith(before)
added=after[len(before):].decode();assert 'order:7' in added and 'mvx_mmu_alloc_contiguous_pages' in added and '0x10dc0' in added
assert 'MMU ABORT' not in added and 'Killed process' not in added
out=run/'results';assert not (out/'lifecycle.jsonl').read_bytes() and not (out/'inference.jsonl').read_bytes()
events=old.lines(out/'encoder/events.jsonl');assert not any(x['event']=='capture' for x in events)
assert [x['result'] for x in events if x['event']=='abort_streamoff']==[0,0]
stages=[]
for row in events:
    if row['event']!='memory_snapshot':continue
    memory=out/'encoder/memory';prefix=row['prefix']
    raw=(memory/(prefix+'-pagetypeinfo.txt')).read_text();types={}
    for line in raw.splitlines():
        match=re.search(r'type\s+(\w+)\s+([\d\s]+)$',line)
        if match:
            values=[int(x) for x in match[2].split()];assert len(values)==11;types[match[1]]=values
    normal=sum(sum(v[7:]) for k,v in types.items() if k not in ('CMA','Isolate'))
    free=int(re.search(r'CmaFree:\s+(\d+)',(memory/(prefix+'-meminfo.txt')).read_text())[1])
    stages.append(dict(stage=row['stage'],time_ns=row['time_ns'],normal_order7plus_blocks=normal,CmaFree_kib=free,orders_by_type=types))
assert len(stages)==14 and stages[0]['normal_order7plus_blocks']>0
assert next(x for x in stages if x['stage']=='capture-after-reqbufs')['normal_order7plus_blocks']==0
mapped=[x for x in events if x['event']=='mapped_total']
assert mapped==[dict(event='mapped_total',type=10,bytes=8294400,buffers=6),dict(event='mapped_total',type=9,bytes=12582912,buffers=6)]
module=ev/'kernel-audit/amvx.ko';config=gzip.decompress((ev/'kernel-audit/config.gz').read_bytes()).decode()
assert 'CONFIG_CMA_SIZE_MBYTES=256\n' in config and 'CONFIG_COMPACTION=y\n' in config
disassembly=(root/'.local/pose-v1-module-r7/alloc-disassembly.txt').read_text()
assert '96fc: R_AARCH64_CALL26\t__alloc_pages_nodemask' in disassembly
assert 'mov\tw0, #0xdc0' in disassembly and 'movk\tw0, #0x1, lsl #16' in disassembly
text=(root/'.local/pose-v1-module-r7/alloc-instructions.txt').read_text()
assert 'dma_direct_map_page' in text
target=ev/'allocation-review.json';assert not target.exists()
target.write_bytes((json.dumps(dict(status='r7_failure_and_allocation_path_verified',returned_hashed_files=count,
    exit=1,Engine_created=False,forward_calls=0,capture_packets=0,cleanup_streamoff=[0,0],
    amvx_sha256=old.sha(module),kernel='5.4.52',gfp=0x10dc0,direct_allocation='__alloc_pages_nodemask',
    CMA_MiB=256,CMA_address='0x30000000',module_source_available=False,
    current_reserved_memory_audit_properties=0,not_proof_no_other_reserved_memory=True,
    mapped_bytes=sum(x['bytes'] for x in mapped),snapshots=stages,
    next_candidate='Isolate requested buffers6->2; fixed prime2 and all math/cookie/format/BOOT/SDK retained; validate actual negotiated counts and startup repetitions.'),indent=2)+'\n').encode())
print('r7 allocation failure independently verified: ordinary high-order blocks exhausted after capture REQBUFS')

"""New pre-hardware build identity for exception cleanup correction."""
from pathlib import Path
R=Path(__file__).resolve().parents[2];T=R/'tools/pose-v1'
for name in ('build_producer_address','execute_producer_address','review_producer_address'):
    old=T/(name+'.py');new=T/(name+'_r2.py');assert not new.exists();s=old.read_text().replace('20261011-r1','20261011-r2');new.write_text(s,encoding='utf-8',newline='\n')
p=T/'ssh_memory_transport.py';s=p.read_text();assert '/tmp/pose-producer-address-20261011-r2/' not in s;p.write_text(s.replace("remote.startswith(('/tmp/pose-producer-address-", "remote.startswith(('/tmp/pose-producer-address-20261011-r2/','/tmp/pose-producer-address-"),encoding='utf-8',newline='\n')
print('r1 compiled/no board execution retained; r2 cleanup-safe identity prepared')

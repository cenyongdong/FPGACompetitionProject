"""Preserve missing-header r1 failure; prepare new source-read build identity."""
from pathlib import Path
R=Path(__file__).resolve().parents[2];T=R/'tools/pose-v1'
names=('build_producer_read','execute_producer_read','review_producer_read','producer_read_resources','prepare_producer_read_resources','board_producer_read_final','collect_producer_read_final','audit_producer_read_api')
for name in names:
    p=T/(name+'_r2.py');assert not p.exists();s=(T/(name+'.py')).read_text().replace('producer-source-read-20261011-r1','producer-source-read-20261011-r2')
    if name=='build_producer_read':s=s.replace("tag='20261011-r1'","tag='20261011-r2'")
    if name=='collect_producer_read_final':s=s.replace('board_producer_read_final.py','board_producer_read_final_r2.py')
    if name=='prepare_producer_read_resources':s=s.replace('producer_read_resources.py','producer_read_resources_r2.py')
    p.write_text(s,encoding='utf-8',newline='\n')
p=T/'ssh_memory_transport.py';s=p.read_text();assert '/tmp/pose-producer-source-read-20261011-r2/' not in s;p.write_text(s.replace("remote.startswith(('/tmp/pose-producer-source-read-", "remote.startswith(('/tmp/pose-producer-source-read-20261011-r2/','/tmp/pose-producer-source-read-"),encoding='utf-8',newline='\n')
print('r1 incomplete Network header failure retained; r2 prepared, not board tested')

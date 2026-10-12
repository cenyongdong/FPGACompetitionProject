"""Prepare isolated source lease build/Host/board tools; no device execution."""
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[2];T=R/'tools/pose-v1'
def put(name,s):
    ast.parse(s);p=T/name;assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
def rep(s,a,b):assert s.count(a)==1,a[:100];return s.replace(a,b)
s=(T/'build_producer_address_r2.py').read_text().replace('producer-address-','producer-source-read-').replace("tag='20261011-r2'", "tag='20261011-r1'")
s=s.replace('producer_high_sdk.cpp','producer_read_sdk.cpp').replace('producer_high_check.cpp','producer_read_check.cpp').replace('pose_producer_high_check','pose_producer_read_check')
s=rep(s,"'producer_address_selftest.cpp','producer_schedule_selftest.cpp'", "'producer_address_selftest.cpp','producer_read_contract.cpp','producer_read_selftest.cpp','producer_output_source.cpp','producer_read_host_check.cpp','producer_schedule_selftest.cpp'")
s=rep(s,"'address':['producer_address_contract.cpp','producer_address_selftest.cpp']", "'address':['producer_address_contract.cpp','producer_address_selftest.cpp'],'read':['producer_read_contract.cpp','producer_read_selftest.cpp']")
s=rep(s,"'producer_address_contract.cpp','producer_address_sdk.cpp','vpu_ioctl_observation.cpp'", "'producer_address_contract.cpp','producer_address_sdk.cpp','producer_read_contract.cpp','producer_output_source.cpp','vpu_ioctl_observation.cpp'")
s=rep(s,"objects={}\n", "run(['exec','FPAI','aarch64-linux-gnu-g++',*flags,remote+'/source/producer_payload.cpp',remote+'/source/producer_read_host_check.cpp','-licraft_xrt','-licraft_xir','-licraft_utils','-o',remote+'/pose_producer_read_host_check'])\nrun(['cp','FPAI:'+remote+'/pose_producer_read_host_check',str(B/'pose_producer_read_host_check')])\nobjects={}\n")
s=rep(s,"B/'build-result.json',*[B/", "B/'build-result.json',B/'pose_producer_read_host_check',*[B/")
s=s.replace('tools/pose-v1/board_producer_address_run.py','tools/pose-v1/board_producer_read_run.py')
put('build_producer_read.py',s)
s=(T/'board_producer_address_run.py').read_text().replace('pose_producer_high_check','pose_producer_read_check')
s=rep(s,"capture(['./pose_producer_address_selftest'],'address-arm.txt');", "capture(['./pose_producer_address_selftest'],'address-arm.txt');capture(['./pose_producer_read_selftest'],'read-arm.txt');capture(['./pose_producer_read_host_check',str(graph),'patterns',str(run/'read-host')],'read-host-arm.txt');")
put('board_producer_read_run.py',s)
s=(T/'execute_producer_address_r2.py').read_text().replace('producer-address-20261011-r2','producer-source-read-20261011-r1').replace('board_producer_address_run.py','board_producer_read_run.py').replace('pose_producer_high_check','pose_producer_read_check')
s=rep(s,'pose_producer_address_selftest;', 'pose_producer_address_selftest pose_producer_read_selftest pose_producer_read_host_check;')
put('execute_producer_read.py',s)
s=(T/'review_producer_address_r2.py').read_text().replace('producer-address-20261011-r2','producer-source-read-20261011-r1')
s=rep(s,"assert load(P/'prefix-release.json')['after_prefix_drop_chunks']==0", "assert load(P/'prefix-release.json')['after_prefix_drop_chunks']==0\nassert not (P/'lease-release.error.txt').exists()\nleases=load(P/'lease-summary.json');assert leases['opened']==leases['closed'] and leases['forced_expired']==0\nassert leases['source_read_calls']==0")
put('review_producer_read.py',s)
for old,new in [('producer_address_resources.py','producer_read_resources.py'),('prepare_producer_address_resources.py','prepare_producer_read_resources.py'),('board_producer_address_final.py','board_producer_read_final.py'),('collect_producer_address_final.py','collect_producer_read_final.py'),('audit_producer_address_api.py','audit_producer_read_api.py')]:
    s=(T/old).read_text().replace('producer-address-20261011-r2','producer-source-read-20261011-r1').replace('board_producer_address_final.py','board_producer_read_final.py').replace('board_producer_address_run.py','board_producer_read_run.py').replace('producer_address_resources.py','producer_read_resources.py');put(new,s)
p=T/'ssh_memory_transport.py';s=p.read_text();assert '/tmp/pose-producer-source-read-20261011-r1/' not in s;p.write_text(s.replace("remote.startswith(('/tmp/pose-producer-address-", "remote.startswith(('/tmp/pose-producer-source-read-20261011-r1/','/tmp/pose-producer-address-"),encoding='utf-8',newline='\n')
print('New lease/source evidence tools prepared; no hardware executed')

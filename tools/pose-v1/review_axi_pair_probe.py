"""Independent NumPy pattern and FNV trace review; never changes returned bytes."""
from pathlib import Path
import sys,json,hashlib,numpy as np
from archive_bytes import extract_bytes
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/axi-pair-20261011-r4';stage=sys.argv[1]
archive=E/('return-'+stage+'.tar');out=E/('return-'+stage);extract_bytes(archive,out)
p=out/('run-'+stage);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for line in (p/'files.sha256').read_text().splitlines():h,n=line.split('  ',1);assert sha(p/n)==h
assert (p/'exit.txt').read_text().strip()=='0' and not (p/'stderr.log').read_bytes()
assert (p/'dmesg.before.log').read_bytes()==(p/'dmesg.after.log').read_bytes()
b=json.loads((R/'.local/pose-v1-build/axi-pair-20261011-r4/build-result.json').read_text());report={'status':'passed','stage':stage,'manifest_sha256':b['manifest_sha256'],'programs':b['programs'],'archive_sha256':sha(archive)}
if stage=='host':
    h=json.loads((p/'stdout.log').read_text());assert h==dict(status='passed',Host_bytes=376320,refusals=8,device_opened=False);report.update(h);report['stage']=stage
else:
    s=json.loads((p/'results/summary.json').read_text());assert s['completed_pairs']==100 and s['all_bitwise'] and s['dynamic_writes'] and not s['full_model_Session'] and not s['NPU_forward'] and s['normal_source_read_pairs']==1
    def pattern(slot,index):
        a=np.arange((30240,16800)[slot]//4,dtype=np.float32)+np.float32((100000 if slot else 0)+index*8192)
        if not slot:a+=np.float32(.25)
        return a.astype('<f4').tobytes()
    def fnv(v):
        h=14695981039346656037
        for c in v:h=((h^c)*1099511628211)&((1<<64)-1)
        return h
    rows=[json.loads(x) for x in (p/'results/pairs.jsonl').read_text().splitlines()];assert len(rows)==100
    previous=0
    for i,row in enumerate(rows):
        assert row['pair']==i and row['pattern_index']==i+1 and row['previous_pattern_index']==i and row['matched']
        for slot,key in enumerate(('a','b')):
            assert row['fnv_'+key]==fnv(pattern(slot,i+1))
            assert previous<=row['write_'+key+'_begin_ns']<=row['write_'+key+'_end_ns']<=row['copy_'+key+'_begin_ns']<=row['copy_'+key+'_end_ns']<=row['shadow_'+key+'_begin_ns']<=row['shadow_'+key+'_end_ns']
        assert row['copy_a_end_ns']<=row['copy_b_begin_ns'];previous=row['shadow_b_end_ns']
    for name,index in (('preload',0),('first-pair',1),('last-pair',100)):
        for slot,key in enumerate(('a','b')):assert (p/'results'/name/(key+'.f32')).read_bytes()==pattern(slot,index)
    assert json.loads((p/'results/sdk/manager-released.json').read_text())['chunks']==[]
    assert not (p/'results/sdk/release.error.txt').exists()
    lifecycle=[json.loads(x) for x in (p/'results/lifecycle.jsonl').read_text().splitlines()]
    assert lifecycle[-2]['event']=='workers_joined' and lifecycle[-1]['event']=='SDK_destroyed'
    if stage.endswith('vpu'):
        v=json.loads((p/'results/vpu/summary.json').read_text());assert v['drained'] and v['joined'] and not v['SDK_on_encoder_thread'] and v['submitted']==v['returned']
        assert lifecycle[0]['event']=='VPU_actual_capture' and lifecycle[0]['time_ns']<lifecycle[1]['time_ns']
        report['VPU']=v
    report.update({'pairs':100,'FP32_Cpp_bitwise':1176000,'NumPy_FNV_trace_pairs':100,'NumPy_saved_FP32_bitwise':35280,'NPU_forward':False,'all_chunks_released':True})
report['kernel_unchanged']=True
dest=E/('review-'+stage+'.json');assert not dest.exists();dest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('Reviewed',stage,'passed')

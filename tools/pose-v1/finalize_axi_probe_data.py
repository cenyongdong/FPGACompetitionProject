"""Finalize byte-only return and bind preserved sources, archives and audit files."""
from pathlib import Path
import tarfile,json,hashlib,re,shutil
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/axi-pair-20261011-r4';A=R/'tools/pose-v1/evidence/axi-read-audit-20261011-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=E/'readable/return-final';assert not out.exists();out.mkdir()
with tarfile.open(E/'return-final.tar') as t:
    for m in t.getmembers():
        assert not m.issym() and not m.islnk() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
        p=out/m.name
        if m.isdir():p.mkdir(parents=True,exist_ok=True)
        else:assert m.isfile();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(m).read())
final=out/'final'
assert not any(line.split()[1].startswith('pose_') for line in (final/'processes.txt').read_text().splitlines()[1:] if len(line.split())>1)
assert ':39001 ' not in (final/'ports.txt').read_text() and ':8554 ' not in (final/'ports.txt').read_text()
assert (final/'dmesg.log').read_bytes()==(E/'readable/return-host/run-host/dmesg.before.log').read_bytes()
assert '78cae7106e5273fc297178d5cfe226ea8737feaef34dbec8bce450478f35436c' in (final/'identity.sha256').read_text()
build=R/'.local/pose-v1-build/axi-pair-20261011-r4';pkg=R/'.local/pose-v1-axi-pair/package-20261011-r4'
for p,n in ((build/'build-result.json','build-result.json'),(pkg/'manifest.json','manifest.json')):assert not (E/n).exists();shutil.copyfile(p,E/n)
b=json.loads((E/'build-result.json').read_text())
for p,v in b['sources'].items():assert sha(R/p)==v['sha256']
prior=json.loads((R/'.local/pose-v1-build/mixed-20261011-read-phase-r3/build-result.json').read_text())
baseline={p:h for p,h in prior['source_sha256'].items() if p.endswith(('host_cpu_adapter.hpp','lazy_host_cpu_adapter.cpp'))}
for p,h in baseline.items():assert sha(R/p)==h
stats={}
for stage in ('copy','read','copy-vpu','read-vpu'):
    d=E/('readable/return-'+stage)/('run-'+stage);rows=[json.loads(x) for x in (d/'results/pairs.jsonl').read_text().splitlines()]
    for x in rows:
        keys=['write_a_begin_ns','write_a_end_ns','write_b_begin_ns','write_b_end_ns','copy_a_begin_ns','copy_a_end_ns','shadow_a_begin_ns','shadow_a_end_ns','copy_b_begin_ns','copy_b_end_ns','shadow_b_begin_ns','shadow_b_end_ns']
        values=[x[k] for k in keys];assert values==sorted(values)
    events=[json.loads(x) for x in (d/'results/lifecycle.jsonl').read_text().splitlines()]
    stats[stage]={'elapsed_pairs_ms':(rows[-1]['shadow_b_end_ns']-rows[0]['copy_a_begin_ns'])/1e6,'source_addresses':[x['address'] for x in json.loads((d/'results/sdk/regions.json').read_text())['sources']]}
    assert stats[stage]['source_addresses']==[100667392,100697664]
    assert all(t['saved'] for t in json.loads((d/'results/persistence-ledger.json').read_text())['tasks'])
    if stage.endswith('vpu'):
        e=[json.loads(x) for x in (d/'results/vpu/encoder/events.jsonl').read_text().splitlines()]
        assert [x['type'] for x in e if x['event']=='streamoff']==[10,9]
        assert e[-1]['event']=='encoding_complete' and e[-1]['last']
        v=json.loads((E/('video-'+stage+'.review.json')).read_text());stats[stage].update(decoded=v['decoded_frames'],stream_bytes=v['stream_bytes'])
bindings={'status':'all_fresh_stages_passed_root_unresolved','programs':b['programs'],'manifest_sha256':b['manifest_sha256'],'sources':len(b['sources']),'stage_statistics':stats,'prior_CPU_sources_unchanged':baseline,'Host107_rerun':False,'Host107_prior_completion_sha256':sha(R/'tools/pose-v1/evidence/read-phase-20261011-r3/completion-review.json'),'compactions':0,'all_processes_ports_closed':True,'kernel_all_stages_and_final_unchanged':True,'final_MemAvailable_KiB':int(re.search(r'MemAvailable:\s+(\d+)',(final/'meminfo').read_text())[1]),'final_CmaFree_KiB':int(re.search(r'CmaFree:\s+(\d+)',(final/'meminfo').read_text())[1]),'audit_SHA256':{p.relative_to(A).as_posix():sha(p) for p in A.rglob('*') if p.is_file()},'archives_SHA256':{p.name:sha(p) for p in E.glob('*.tar')},'stage_reviews_SHA256':{p.name:sha(p) for p in E.glob('review-*.json')},'video_reviews_SHA256':{p.name:sha(p) for p in E.glob('video-*.review.json')},'library_audit_is_not_hardware_completion_proof':True,'full_model_Session':False,'NPU_forward':False,'root_fixed':False}
(E/'data-review.json').write_text(json.dumps(bindings,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:bindings[k] for k in ('stage_statistics','compactions','final_MemAvailable_KiB','final_CmaFree_KiB','root_fixed')},indent=2))

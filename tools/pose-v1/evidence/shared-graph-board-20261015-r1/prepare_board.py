"""Reuse the tested no-Scatter engine; specialize only pinned new graph counts/ports."""
import hashlib,json
from pathlib import Path
import re,shutil
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
S=R/'.local/shared-source-20261015-r1';D=R/'.local/shared-delivery-20261015-r1'
OLD=R/'.local/noscatter-source-20261015-r1';OLD_D=R/'.local/noscatter-delivery-20261015-r1'
M=R/'model/piw24_shared-20261015-r1'
assert not S.exists() and not D.exists()
g=json.loads((M/'piw24_shared_ZG.json').read_text(encoding='utf-8'))
hard=[o for o in g['ops'] if o['_type_key']=='icraft::xir::HardOp']
host=[o for o in g['ops'] if o['_type_key']!='icraft::xir::HardOp']
assert [(o['op_id'],o['_type_key'].split('::')[-1]) for o in host]==[(0,'Input'),(188,'TopK'),(192,'GatherElements'),(437,'TopK'),(442,'Gather'),(565,'Output')]
assert len(hard)==1021 and len(g['ops'])==1027
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copytree(OLD,S);D.mkdir();shutil.copytree(OLD_D/'fixtures',D/'fixtures');(D/'models').mkdir()
for ext in ('json','raw'):shutil.copyfile(M/('piw24_shared_ZG.'+ext),D/'models'/('piw24_shared_ZG.'+ext))
for p in (S/'baseline').iterdir():
    if p.name not in ('application_core.cpp','mixed_fusion_baseline.hpp','lazy_runtime_validation.hpp'):continue
    text=p.read_text(encoding='utf-8')
    for a,b in [('1158','1021'),('1164','1027'),('664','565')]:text=re.sub(r'\b'+a+r'\b',b,text)
    p.write_bytes(text.encode())
for name in ('CMakeLists.txt','main.cpp'):
    p=S/name;text=p.read_text(encoding='utf-8').replace('pose_noscatter_timing','pose_shared_timing').replace('piw24_noscatter_ZG','piw24_shared_ZG');p.write_bytes(text.encode())
for name in ('board_run.py','board_application_preflight.py'):
    text=(OLD_D/name).read_text(encoding='utf-8').replace('pose_noscatter_timing','pose_shared_timing');(D/name).write_bytes(text.encode())
manifest=dict(status='shared_source_prepared_not_board_executed',source_origin=str(OLD),
    original_HardOps=1021,original_ops=1027,host_ids=[0,188,192,437,442,565],
    model_json_sha256=sha(M/'piw24_shared_ZG.json'),model_raw_sha256=sha(M/'piw24_shared_ZG.raw'),
    runtime_group_sync='derive and completely validate public SDK metadata before forward; no static final threshold',
    strict_comparison='same original board full outputs; save then stop on any byte discrepancy',
    files={str(p.relative_to(S)):sha(p) for p in sorted(S.rglob('*')) if p.is_file() and p.name!='source-manifest.json'})
(S/'source-manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
shutil.copyfile(S/'source-manifest.json',E/'source-manifest.json');shutil.copyfile(S/'source-manifest.json',D/'source-manifest.json')
transport=R/'.local/shared-transport-20261015-r1';transport.mkdir()
text=(R/'.local/noscatter-transport-20261015-r1/secure_transport.py').read_text(encoding='utf-8').replace('/tmp/wifi-pose-noscatter-20261015-r1/','/tmp/wifi-pose-shared-20261015-r1/')
(transport/'secure_transport.py').write_bytes(text.encode())
print(json.dumps({k:v for k,v in manifest.items() if k!='files'}))

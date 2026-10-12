"""Add an error observation after pacing, before the next Engine call."""
import json,shutil
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT;base=root/'.local/pose-v1-model-vpu/package-20261010-r1';g.verify(base);m=g.load(base/'manifest.json')
old='software/pose_v1/src/model_vpu_check_r1.cpp';new='software/pose_v1/src/model_vpu_check_r2.cpp';s=(root/old).read_text(encoding='utf-8')
needle='            const auto begin=now();need(begin-entry<180000000000ULL'
assert s.count(needle)==1;s=s.replace(needle,'            load.check();\n'+needle);assert not (root/new).exists();(root/new).write_text(s,encoding='utf-8',newline='\n')
m['model_vpu_r1_frozen_sources']={old:g.sha(root/old)};item=m['build_files'].pop(old);m['build_files'][new]=dict(destination=item['destination'],sha256=g.sha(root/new))
rel='tools/pose-v1/prepare_model_vpu_r2.py';m['sources'][rel]=g.sha(root/rel);m['model_vpu']['revision']='r2_post_pacing_error_observation_only'
out=root/'.local/pose-v1-model-vpu/package-20261010-r2';assert not out.exists();shutil.copytree(base,out);(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n');(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))

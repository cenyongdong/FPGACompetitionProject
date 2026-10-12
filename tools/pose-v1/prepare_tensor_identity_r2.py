"""Remove new ambiguous formatting before any board execution; preserve r1."""
import json,shutil
import mixed_validation_gate as g
root=g.ROOT
def put(rel,text):p=root/rel;assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n')
base=root/'.local/pose-v1-tensor-identity/package-20261010-r1';g.verify(base);m=g.load(base/'manifest.json')
before='software/pose_v1/src/tensor_identity_bridge_r1.cpp';after='software/pose_v1/src/tensor_identity_bridge_r2.cpp'
s=(root/before).read_text(encoding='utf-8');a='for(size_t i=0;i<type->shape.size();++i)f<<type->layout.getAxisCharName(int64_t(i));f<<';b='for(size_t i=0;i<type->shape.size();++i){f<<type->layout.getAxisCharName(int64_t(i));}\n    f<<';assert s.count(a)==1;put(after,s.replace(a,b))
m['tensor_identity_r1_frozen_sources']={before:g.sha(root/before)};item=m['build_files'].pop(before);m['build_files'][after]=dict(destination=item['destination'],sha256=g.sha(root/after))
put('tools/pose-v1/Build-TensorIdentityR2.ps1',(root/'tools/pose-v1/Build-TensorIdentity.ps1').read_text(encoding='utf-8').replace('mixed-20261010-tensor-identity-r1','mixed-20261010-tensor-identity-r2'))
r=(root/'tools/pose-v1/review_tensor_identity_stage.py').read_text(encoding='utf-8').replace('Build-TensorIdentity.ps1','Build-TensorIdentityR2.ps1');r=r.replace("'tensor_identity_frozen_sources')","'tensor_identity_frozen_sources','tensor_identity_r1_frozen_sources')");put('tools/pose-v1/review_tensor_identity_r2_stage.py',r)
for name in ('prepare_tensor_identity_r2.py','Build-TensorIdentityR2.ps1','review_tensor_identity_r2_stage.py'):rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-TensorIdentityR2.ps1'
out=root/'.local/pose-v1-tensor-identity/package-20261010-r2';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))

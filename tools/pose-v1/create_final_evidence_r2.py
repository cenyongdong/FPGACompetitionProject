"""Preserve r1 compilation failure; bounded corrections in a fresh package."""
import json,shutil
import mixed_validation_gate as g
r=g.ROOT;base=r/'.local/pose-v1-final-evidence/package-20261010-r1';g.verify(base);m=g.load(base/'manifest.json')
m['final_evidence_r1_frozen_sources']={p:v['sha256'] for p,v in m['build_files'].items()}
for name in ['final_source_sdk','final_source_selftest','final_source_sdk_selftest']:
    m['build_files'].pop('software/pose_v1/src/'+name+'.cpp');p='software/pose_v1/src/'+name+'_r2.cpp';m['build_files'][p]=dict(destination=name+'.cpp',sha256=g.sha(r/p))
m['sources']['tools/pose-v1/create_final_evidence_r2.py']=g.sha(r/'tools/pose-v1/create_final_evidence_r2.py')
m['final_evidence']['r1_not_executed']='SDK selftest Werror misleading indentation, log retained';m['final_evidence']['late_storage_identity_checked']=True
out=r/'.local/pose-v1-final-evidence/package-20261010-r2';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(g.verify(out),len(m['build_files']))

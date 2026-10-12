"""Bind only original Gather Host context; preserve all prior failed fixtures."""
import json,shutil
import mixed_validation_gate as g
r=g.ROOT;base=r/'.local/pose-v1-upstream-boundary/package-20261011-r2';g.verify(base);m=g.load(base/'manifest.json');m['upstream_r2_frozen_sources']={p:v['sha256'] for p,v in m['build_files'].items()}
m['build_files'].pop('software/pose_v1/src/upstream_boundary_sdk_selftest_r2.cpp');rel='software/pose_v1/src/upstream_boundary_sdk_selftest_r3.cpp';m['build_files'][rel]=dict(destination='upstream_boundary_sdk_selftest.cpp',sha256=g.sha(r/rel));m['sources']['tools/pose-v1/create_upstream_boundary_r3.py']=g.sha(r/'tools/pose-v1/create_upstream_boundary_r3.py')
m['upstream_boundary']['r2_Host_probe']='construct/init/public pre samples succeed; bare unbound originalGather forward139, kernel same';m['upstream_boundary']['Host_Gather_context']='Backend::Create<HostBackend>(only442 view, HostDevice::Default); explicit Host output'
out=r/'.local/pose-v1-upstream-boundary/package-20261011-r3';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n');(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))

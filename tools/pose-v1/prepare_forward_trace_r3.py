"""Fix only Host probe context; preserve stopped r2 source and identity."""
import json,shutil
from pathlib import Path
import mixed_validation_gate as old
root=old.ROOT
def put(rel,text):
    p=root/rel;assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n')
probe=(root/'software/pose_v1/src/host_failure_adapter_test.cpp').read_text(encoding='utf-8')
needle='namespace xir=icraft::xir;namespace xrt=icraft::xrt;';assert probe.count(needle)==1
put('software/pose_v1/src/host_failure_adapter_test_r3.cpp',probe.replace(needle,needle+'\n    // Host gate local log has ended; use an explicitly empty public bridge context.\n    pose_v1::mixed_candidate::configure(nullptr,false);'))
put('tools/pose-v1/Build-ForwardTraceR3.ps1',(root/'tools/pose-v1/Build-ForwardTraceR2.ps1').read_text(encoding='utf-8').replace('mixed-20261009-forward-trace-r2','mixed-20261009-forward-trace-r3'))
put('tools/pose-v1/run-forward-trace-r3.sh',(root/'tools/pose-v1/run-forward-trace-r2.sh').read_text(encoding='utf-8'))
put('tools/pose-v1/review_forward_r3_stage.py',(root/'tools/pose-v1/review_forward_r2_stage.py').read_text(encoding='utf-8').replace('Build-ForwardTraceR2.ps1','Build-ForwardTraceR3.ps1').replace('run-forward-trace-r2.sh','run-forward-trace-r3.sh').replace("'trace_r2_frozen_sources')","'trace_r2_frozen_sources','trace_r3_frozen_sources')"))
base=root/'.local/pose-v1-forward-trace/package-20261009-r2';old.verify(base);m=old.load(base/'manifest.json')
for rel,item in m['build_files'].items():assert old.sha(root/rel)==item['sha256']
for rel,digest in m['sources'].items():assert old.sha(root/rel)==digest
before='software/pose_v1/src/host_failure_adapter_test.cpp';after='software/pose_v1/src/host_failure_adapter_test_r3.cpp'
item=m['build_files'].pop(before);m['trace_r3_frozen_sources']={before:old.sha(root/before)};m['build_files'][after]=dict(destination=item['destination'],sha256=old.sha(root/after))
for name in ('prepare_forward_trace_r3.py','Build-ForwardTraceR3.ps1','run-forward-trace-r3.sh','review_forward_r3_stage.py'):
    rel='tools/pose-v1/'+name;m['sources'][rel]=old.sha(root/rel)
m['build_script']='tools/pose-v1/Build-ForwardTraceR3.ps1';m['forward_trace']['Host_probe_context_cleared']=True
out=root/'.local/pose-v1-forward-trace/package-20261009-r3';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(old.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(json.dumps(dict(payloads=old.verify(out),build_sources=len(m['build_files']))))

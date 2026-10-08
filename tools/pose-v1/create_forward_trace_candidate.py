"""Prepare isolated bounded tracing; preserve the accepted parent and SDK modules."""
from pathlib import Path
import json, shutil
import mixed_validation_gate as old

root=old.ROOT
def write(rel, text):
    p=root/rel
    if p.exists():
        assert p.read_text(encoding="utf-8")==text, p
        return
    p.write_text(text,encoding='utf-8',newline='\n')

entry=(root/'software/pose_v1/src/display_process_check.cpp').read_text(encoding="utf-8")
entry=entry.replace('measure-2hz|measure-5hz','measure-2hz|measure-5hz|trace-5hz')
entry=entry.replace('mode=="measure-5hz"','(mode=="measure-5hz"||mode=="trace-5hz")')
entry=entry.replace('mode!="measure-5hz"','!(mode=="measure-5hz"||mode=="trace-5hz")')
assert entry.count('cfg.diagnostic_frames=0;')==1
entry=entry.replace('cfg.diagnostic_frames=0;','cfg.diagnostic_frames=mode=="trace-5hz"?32:0;')
write('software/pose_v1/src/forward_trace_check.cpp',entry)
cm=(root/'tools/pose-v1/display-process-CMakeLists.txt').read_text(encoding="utf-8").replace('display_process_check.cpp','forward_trace_check.cpp')
write('tools/pose-v1/forward-trace-CMakeLists.txt',cm)
builder=(root/'tools/pose-v1/Build-DisplayProcess.ps1').read_text(encoding="utf-8").replace('mixed-20261008-display-process-r1','mixed-20261008-forward-trace-r1')
write('tools/pose-v1/Build-ForwardTrace.ps1',builder)
runner=(root/'tools/pose-v1/run-display-process.sh').read_text(encoding="utf-8")
runner=runner.replace('measure-5hz}', 'measure-5hz / trace-5hz}')
runner=runner.replace('measure-5hz) previous=measure-2hz; seconds=180;;','measure-5hz) previous=measure-2hz; seconds=180;; trace-5hz) previous=process-three; seconds=180;;')
write('tools/pose-v1/run-forward-trace.sh',runner)
review=(root/'tools/pose-v1/review_display_process.py').read_text(encoding="utf-8")
review=review.replace('Build-DisplayProcess.ps1','Build-ForwardTrace.ps1').replace('run-display-process.sh','run-forward-trace.sh')
review=review.replace("'measure-2hz','measure-5hz']","'measure-2hz','measure-5hz','trace-5hz']")
review=review.replace("'measure-5hz':'measure-2hz'}","'measure-5hz':'measure-2hz','trace-5hz':'process-three'}")
review=review.replace("len(calls)==expected and queue['consumed']==33","len(calls)==expected and queue['consumed']==expected")
# Traced timing remains a diagnosis, never a low-log performance gate.
review=review.replace("whole_5Hz_threshold_met=bool(rate>=5", "whole_5Hz_threshold_met=bool(a.stage!='trace-5hz' and rate>=5")
write('tools/pose-v1/review_forward_stage.py',review)
base=root/'.local/pose-v1-display-process/package-20261008-r1'
old.verify(base);m=old.load(base/'manifest.json')
for rel,item in m['build_files'].items():assert old.sha(root/rel)==item['sha256']
for rel,digest in m['sources'].items():assert old.sha(root/rel)==digest
m['trace_frozen_parent']={rel:old.sha(root/rel) for rel in ('software/pose_v1/src/display_process_check.cpp','tools/pose-v1/display-process-CMakeLists.txt')}
for rel in m['trace_frozen_parent']:del m['build_files'][rel]
for rel,destination in [('software/pose_v1/src/forward_trace_check.cpp','forward_trace_check.cpp'),('tools/pose-v1/forward-trace-CMakeLists.txt','CMakeLists.txt')]:m['build_files'][rel]=dict(destination=destination,sha256=old.sha(root/rel))
for name in ('create_forward_trace_candidate.py','Build-ForwardTrace.ps1','run-forward-trace.sh','review_forward_stage.py'):
    rel='tools/pose-v1/'+name;m['sources'][rel]=old.sha(root/rel)
m['build_script']='tools/pose-v1/Build-ForwardTrace.ps1'
m['forward_trace']=dict(sample_limit=32,record_limit=8192,SDK_profiling=False,existing_Engine_and_bridge_unchanged=True,performance_acceptance=False)
out=root/'.local/pose-v1-forward-trace/package-20261008-r1';assert not out.exists()
shutil.copytree(base,out);(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',newline='\n')
(out/'files.sha256').write_text(''.join(old.sha(f)+'  '+f.relative_to(out).as_posix()+'\n' for f in sorted(out.rglob('*')) if f.is_file() and f.name!='files.sha256'),newline='\n')
print(json.dumps(dict(payloads=old.verify(out),build_sources=len(m['build_files']))))

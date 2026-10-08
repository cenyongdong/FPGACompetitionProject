"""Isolate the evidence-based2-buffer startup candidate; preserve r7."""
import hashlib,json,shutil
from pathlib import Path
import mixed_validation_gate as old

root=old.ROOT
source=root/'software/pose_v1/src/vpu_pipeline_encoder.cpp'
candidate=root/'software/pose_v1/src/vpu_startup_encoder.cpp'
assert not candidate.exists()
text=source.read_bytes();old_line=b'r.memory=V4L2_MEMORY_MMAP; r.count=6;'
assert text.count(old_line)==1
candidate.write_bytes(text.replace(old_line,b'r.memory=V4L2_MEMORY_MMAP; r.count=2;'))
original=root/'.local/pose-v1-pipeline/package-20261008-r7'
old.verify(original)
dest=root/'.local/pose-v1-pipeline/package-20261008-r8';assert not dest.exists();shutil.copytree(original,dest)
m=json.loads((dest/'manifest.json').read_text())
item=m['build_files'].pop('software/pose_v1/src/vpu_pipeline_encoder.cpp')
item['sha256']=old.sha(candidate);m['build_files']['software/pose_v1/src/vpu_startup_encoder.cpp']=item
m['requested_queue_buffers']=2
m['startup_candidate']='r7 snapshots show raw/capture REQBUFS exhaust ordinary order>=7 blocks; only requested buffer count6->2 changed'
m['frozen_r7_encoder_sha256']=old.sha(source)
m['sources']['tools/pose-v1/prepare_startup_package.py']=old.sha(Path(__file__))
(dest/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode())
(dest/'files.sha256').write_bytes(''.join(old.sha(p)+'  '+p.relative_to(dest).as_posix()+'\n' for p in sorted(dest.rglob('*')) if p.is_file() and p.name!='files.sha256').encode())
print('Newr8 candidate prepared; sole encoder change requested buffers6->2; actual returned counts checked independently')

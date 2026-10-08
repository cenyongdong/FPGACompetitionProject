"""Repackage the verified main-owner candidate into a fresh directory."""
import argparse,json,shutil
from pathlib import Path
import mixed_validation_gate as old

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
root=old.ROOT;base=root/'.local/pose-v1-resident/package-20261008-r6';old.verify(base)
m=old.load(base/'manifest.json')
for rel,item in m['build_files'].items():assert old.sha(root/rel)==item['sha256']
assert 'software/pose_v1/src/resident_owner_check.cpp' in m['build_files']
shutil.copytree(base,a.output)
# The old one-shot generator remains historical; new packages bind this tool.
m['sources']={rel:value for rel,value in m['sources'].items() if not rel.startswith('.local/')}
m['sources']['tools/pose-v1/prepare_resident_owner_package.py']=old.sha(Path(__file__))
(a.output/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode())
(a.output/'files.sha256').write_bytes(''.join(old.sha(f)+'  '+f.relative_to(a.output).as_posix()+'\n' for f in sorted(a.output.rglob('*')) if f.is_file() and f.name!='files.sha256').encode())
print('Verified main-owner resident candidate repackaged:',a.output)

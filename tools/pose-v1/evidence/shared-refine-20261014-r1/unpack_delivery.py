"""Verify archive identity and extract ordinary files into the dedicated directory."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

e = Path(r'D:\FPGACompetitionProject\tools\pose-v1\evidence\shared-refine-20261014-r1')
root = Path(r'D:\FPGACompetitionProject\.local\shared-refine-20261014-r1').resolve()
archive = root / 'shared_refine_20261014_r1.tar.gz'
identity = json.loads((e / 'archive.json').read_text(encoding='utf-8'))
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()
assert archive.stat().st_size == identity['bytes']
assert sha(archive) == identity['sha256']
output = root / 'shared_refine_20261014_r1'
assert not output.exists(), 'Do not overwrite an existing raw delivery'
count = 0
with tarfile.open(archive,'r:gz') as tar:
    for member in tar:
        path = root / member.name
        resolved = path.resolve()
        assert resolved == output or output in resolved.parents, member.name
        assert member.isdir() or member.isfile(), 'No links or special files'
        if member.isdir():
            resolved.mkdir(parents=True,exist_ok=True)
        else:
            resolved.parent.mkdir(parents=True,exist_ok=True)
            with tar.extractfile(member) as source, resolved.open('xb') as dest:
                shutil.copyfileobj(source,dest,1024*1024)
            assert resolved.stat().st_size == member.size
            count += 1
manifest = json.loads((output / 'files.json').read_text(encoding='utf-8'))
for name,expected in manifest.items():
    path = output / name
    assert path.stat().st_size == expected['bytes'] and sha(path) == expected['sha256'], name
for path in output.iterdir():
    if path.suffix in ('.json','.jsonl','.log'):
        dest = e / path.name
        if dest.exists():
            assert dest.read_bytes() == path.read_bytes(), 'Existing evidence identity mismatch: '+path.name
        else:
            shutil.copyfile(path,dest)
result = dict(status='complete_archive_extracted_and_all_file_hashes_verified',
              archive_sha256=identity['sha256'],file_count=count,
              raw_directory=str(output),archive_bytes=identity['bytes'])
(e / 'unpack-review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))

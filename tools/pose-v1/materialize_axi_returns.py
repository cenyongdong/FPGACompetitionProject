"""Materialize only regular archive bytes; do not import Linux ACL/mode metadata."""
from pathlib import Path
import tarfile,json,hashlib
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/axi-pair-20261011-r4';out=E/'readable';assert not out.exists();out.mkdir()
bindings={}
for archive in sorted(E.glob('return-*.tar')):
    directory=out/archive.stem;directory.mkdir()
    with tarfile.open(archive) as t:
        for m in t.getmembers():
            assert not m.issym() and not m.islnk() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
            p=directory/m.name
            if m.isdir():p.mkdir(parents=True,exist_ok=True)
            else:
                assert m.isfile();p.parent.mkdir(parents=True,exist_ok=True);data=t.extractfile(m).read();assert len(data)==m.size;p.write_bytes(data)
    bindings[archive.name]={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':sum(p.is_file() for p in directory.rglob('*'))}
(out/'identity.json').write_text(json.dumps(bindings,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Archives materialized without imported permissions',len(bindings))

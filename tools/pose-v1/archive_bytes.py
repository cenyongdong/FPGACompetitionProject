"""Extract bounded regular evidence bytes without importing archive permissions."""
from pathlib import Path,PurePosixPath
import tarfile

def extract_bytes(archive:Path,fresh:Path):
    assert not fresh.exists(),'Preserve prior return'
    fresh.mkdir();root=fresh.resolve();total=0;names=set()
    with tarfile.open(archive) as stream:
        for member in stream.getmembers():
            name=PurePosixPath(member.name)
            assert not name.is_absolute() and '..' not in name.parts and '\\' not in member.name and ':' not in member.name
            assert member.name not in names and len(names)<5000;names.add(member.name)
            target=(fresh/member.name).resolve();assert target.is_relative_to(root)
            if member.isdir():target.mkdir(parents=True,exist_ok=True)
            else:
                assert member.isfile();total+=member.size;assert total<=128*1024*1024
                target.parent.mkdir(parents=True,exist_ok=True)
                data=stream.extractfile(member).read();assert len(data)==member.size;target.write_bytes(data)
    return {'members':len(names),'bytes':total}

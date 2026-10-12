"""Extract regular evidence; the one intentional Host test link is metadata."""
from pathlib import Path, PurePosixPath
import tarfile

def extract_prepared(archive: Path, fresh: Path, host: bool = False):
    assert not fresh.exists(), 'Preserve prior return'
    fresh.mkdir(); root = fresh.resolve(); total = 0; names = set(); links = []
    with tarfile.open(archive) as stream:
        for member in stream.getmembers():
            p = PurePosixPath(member.name)
            assert not p.is_absolute() and '..' not in p.parts and '\\' not in member.name and ':' not in member.name
            assert member.name not in names and len(names) < 5000; names.add(member.name)
            dst = (fresh/member.name).resolve(); assert dst.is_relative_to(root)
            if member.isdir(): dst.mkdir(parents=True, exist_ok=True); continue
            if member.issym():
                assert host and member.name == 'run-host/directories/link'
                assert member.linkname == '/tmp/pose-producer-prepared-20261011-r1/run-host/directories'
                links.append({'name':member.name,'target':member.linkname,'extracted':False}); continue
            assert member.isfile(); total += member.size; assert total <= 128*1024*1024
            assert not dst.exists(); dst.parent.mkdir(parents=True, exist_ok=True)
            data = stream.extractfile(member).read(); assert len(data) == member.size
            dst.write_bytes(data)
    assert len(links) == (1 if host else 0)
    return {'members':len(names),'bytes':total,'links':links}

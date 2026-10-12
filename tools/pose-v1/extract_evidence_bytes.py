"""Extract regular evidence bytes without applying Linux ownership/mode on Windows."""
import argparse,tarfile
from pathlib import Path,PurePosixPath
def main():
    p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('destination',type=Path);a=p.parse_args();assert not a.destination.exists();a.destination.mkdir()
    root=a.destination.resolve()
    with tarfile.open(a.archive) as f:
        for member in f:
            rel=PurePosixPath(member.name);assert not rel.is_absolute() and '..' not in rel.parts and all(':' not in x for x in rel.parts)
            target=(root/Path(*rel.parts)).resolve();assert target==root or root in target.parents
            if member.isdir():target.mkdir(parents=True,exist_ok=True)
            else:
                assert member.isfile() and not target.exists();target.parent.mkdir(parents=True,exist_ok=True)
                source=f.extractfile(member);assert source is not None;target.write_bytes(source.read())
    print('Evidence bytes extracted without Unix attributes',root)
if __name__=='__main__':main()

"""Archive only finalized listed samples for one portable training transfer."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset',required=True,type=Path)
    p.add_argument('--archive',required=True,type=Path);a=p.parse_args();root=a.dataset.resolve()
    manifest=json.loads((root/'dataset.json').read_text(encoding='utf-8-sig'))
    if manifest.get('schema')!='KINECT-WIFI-RECEIPT-FT1' or manifest.get('synthetic_fixture'):raise ValueError('Final actual experimental bundle required')
    members=[root/'dataset.json',root/'local-frame.json']
    for split,count in manifest['counts'].items():
        if not count:continue
        folder=root/(split+'_data');listing=folder/('train_data_list.txt' if split=='train' else 'test_data_list.txt')
        names=listing.read_text().splitlines()
        if len(names)!=count or len(set(names))!=count:raise ValueError('Final sample list differs from manifest')
        members.append(listing)
        for name in names:
            if Path(name).name!=name or '/' in name or '\\' in name:raise ValueError('Invalid sample identity')
            for kind in ('tokens','keypoint'):
                path=folder/kind/(name+'.npy')
                if not path.is_file():raise FileNotFoundError(path)
                members.append(path)
    members.extend(sorted((root/'records').glob('*')))
    with zipfile.ZipFile(a.archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
        for i,path in enumerate(members):
            archive.write(path,'dataset/'+path.relative_to(root).as_posix())
            if i and i%20000==0:print('Archived members:',i,flush=True)
    digest=hashlib.sha256()
    with a.archive.open('rb') as source:
        for block in iter(lambda:source.read(8*1024**2),b''):digest.update(block)
    report=dict(archive=str(a.archive.resolve()),bytes=a.archive.stat().st_size,sha256=digest.hexdigest(),members=len(members),counts=manifest['counts'],profile=manifest['supervision_profile'],training_started=False)
    with a.archive.with_suffix('.json').open('x') as output:json.dump(report,output,indent=2);output.write('\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()

"""Preserve exact current files before updating current status; leave old manifests intact."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]
FILES = ('PROJECT-PROGRESS.md','DIFFICULTIES.md','Done.md','software/engine_timing/README.md','software/engine_timing/board_run.py')
def identities():
    return {name:hashlib.sha256((PROJECT/name).read_bytes()).hexdigest() for name in FILES}
if sys.argv[1] == 'before':
    dest=ROOT/'revision-before'
    dest.mkdir()
    for name in FILES:
        path=dest/name
        path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(PROJECT/name,path)
    (ROOT/'revision-before.json').write_text(json.dumps(identities(),indent=2)+'\n',encoding='utf-8')
else:
    result={'before':json.loads((ROOT/'revision-before.json').read_text(encoding='utf-8')),'after':identities(),
            'reason':'Current timing status and same-source kernel comparator; historical source/build/delivery manifests not rewritten.'}
    (ROOT/'revision-record.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(sys.argv[1]+' revision recorded')

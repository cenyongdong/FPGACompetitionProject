import base64
import json
from pathlib import Path

here = Path(__file__).resolve().parent
mapping = json.loads((here / 'upload-map.json').read_text())
payload = {remote: base64.b64encode((here / local).read_bytes()).decode('ascii')
           for remote, local in mapping.items()}
script = '''import ast,base64,hashlib,json
from pathlib import Path
ROOT=Path('/public/cyd/Person-in-WiFi-3D-repo')
payload=json.loads(PAYLOAD)
manifest=json.loads(base64.b64decode(payload['tools/pose26_diff_nodecay/manifest.json']))
for name,expected in manifest['files'].items():
 if name not in payload:
  assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
for name,value in payload.items():
 target=ROOT/name
 target.resolve().relative_to(ROOT.resolve())
 assert not target.exists(),str(target)
 data=base64.b64decode(value)
 if name.endswith('.py'): ast.parse(data,filename=name)
 if name in manifest['files']: assert hashlib.sha256(data).hexdigest()==manifest['files'][name]
assert not (ROOT/'result/tpami2026_diff_nodecay_20261004').exists()
for name,value in payload.items():
 target=ROOT/name
 target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f: f.write(base64.b64decode(value))
(ROOT/'result/tpami2026_diff_nodecay_20261004/gates').mkdir(parents=True,exist_ok=False)
print(json.dumps(dict(uploaded_files=len(payload),old_shared_hashes_verified=True)))
'''.replace('PAYLOAD', repr(json.dumps(payload)))
(here / 'upload-reviewed.py').write_text(script, encoding='ascii', newline='\n')

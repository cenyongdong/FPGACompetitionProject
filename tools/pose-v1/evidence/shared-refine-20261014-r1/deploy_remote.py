"""Identity-checked deployment; stages and preserves both source revisions."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import sys

root = Path('/public/cyd/Person-in-WiFi-3D-repo')
out = Path(sys.argv[1]).resolve()
assert out.parent == root / 'result' and out.is_dir()
assert not (out / 'deployment.json').exists()
rows = [('transformer', root / 'opera/models/utils/transformer.py',
         '8952d85edee1470c669943ddeec3655b71cb868ca834ea9ab8fe75183ff478e2'),
        ('petr_head', root / 'opera/models/dense_heads/petr_head.py',
         '75bc37c0cc402837cb9638d42df6067c5e4dd29c9a1647130ccacb51ce704ad7')]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for name, dest, expected in rows:
    assert sha(dest) == expected, 'Remote source identity changed: ' + str(dest)
    assert sha(out / (name + '.before.py')) == expected
    ast.parse((out / (name + '.after.py')).read_text(encoding='utf-8'))
for name, dest, _ in rows:
    shutil.copyfile(dest, out / (name + '.remote-original.py'))
for name, dest, _ in rows:
    temporary = dest.with_name(dest.name + '.shared-refine-staging')
    assert not temporary.exists()
    temporary.write_bytes((out / (name + '.after.py')).read_bytes())
    temporary.chmod(dest.stat().st_mode)
    temporary.replace(dest)
    assert dest.read_bytes() == (out / (name + '.after.py')).read_bytes()
result = dict(status='deployed', cwd=str(root), result_dir=str(out),
              source_sha256={str(dest.relative_to(root)):sha(dest) for _,dest,_ in rows},
              original_sha256={name:expected for name,_,expected in rows},
              weights_changed=False, topk_removed=False)
(out / 'deployment.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result))

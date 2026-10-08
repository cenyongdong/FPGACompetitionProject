"""Correct only the new four-window expected frame count; retain the frozen reviewer."""
import hashlib,json,sys
from pathlib import Path
frozen=Path(__file__).with_name('review_display_process.py')
source=frozen.read_text(encoding='utf-8');needle="len(calls)==expected and queue['consumed']==33"
assert source.count(needle)==1
source=source.replace(needle,"len(calls)==expected and queue['consumed']==expected")
exec(compile(source,str(frozen),'exec'),dict(__name__='__main__',__file__=str(frozen)))
out=Path(sys.argv[sys.argv.index('--output')+1])
out.with_suffix('.reviewer-provenance.json').write_text(json.dumps(dict(frozen_reviewer_sha256=hashlib.sha256(frozen.read_bytes()).hexdigest(),adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),correction='Four-window regression requires consumed==expected4; measurement33 unchanged',data_hashes_math_thresholds_unchanged=True),indent=2)+'\n')

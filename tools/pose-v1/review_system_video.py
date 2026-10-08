"""Use the frozen NoInput reference explicitly; never manufacture a returned board file."""
import hashlib,json,sys
from pathlib import Path

root=Path(__file__).resolve().parents[2]
reference=root/'tools/pose-v1/evidence/tcp-presaved-20261008-r1/live-three/results/frames/warmup.nv12'
assert reference.is_file() and reference.stat().st_size==1280*720*3//2
source=Path(__file__).with_name('review_resident_video.py').read_text(encoding='utf-8')
needle="np.fromfile(a.results/'frames/warmup.nv12',dtype=np.uint8)"
assert source.count(needle)==1
source=source.replace(needle,'np.fromfile(reference,dtype=np.uint8)')
source=source.replace("report=dict(status=", "report=dict(warm_reference_origin=str(reference),warm_reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),warm_reference_returned_in_current_run=False,status=")
exec(compile(source,str(Path(__file__).with_name('review_resident_video.py')),'exec'),dict(reference=reference,hashlib=hashlib,__name__='__main__'))

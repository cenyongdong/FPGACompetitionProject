"""Generate bounded independent 720p NV12 test sequence from checked renderer."""
import hashlib
import json
import argparse
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.local/pose-v1-vpu/package-20261007-r2'
SOURCE = ROOT / 'tools/pose-v1/evidence/render-20261007-r1/cpu-render/self-test/synthetic.nv12'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=OUT, help='New package directory; refuses existing paths')
    OUT = parser.parse_args().output
    OUT.mkdir(parents=True, exist_ok=False)
    base = np.frombuffer(SOURCE.read_bytes(), dtype=np.uint8).copy()
    assert base.size == 1280*720*3//2
    records = []
    with (OUT/'frames.nv12').open('xb') as f:
        for i in range(30):
            frame = base.copy()
            y = frame[:1280*720].reshape(720, 1280)
            uv = frame[1280*720:].reshape(360, 1280)
            # A moving white marker, plus five binary luma blocks identifying
            # every frame. Chroma is neutral in the entire diagnostic region.
            y[600:680, 40:1240] = 16
            uv[300:340, 40:1240] = 128
            x = 40 + i*38
            y[640:680, x:x+32] = 235
            for bit in range(5):
                left = 40 + bit*64
                y[600:632, left:left+48] = 235 if i & (1<<bit) else 16
            data = frame.tobytes()
            f.write(data)
            records.append({'frame_id':i,'pts_us':i*100000,'sha256':hashlib.sha256(data).hexdigest(),'marker_x':x})
    manifest = {'scope':'independent_vpu_no_npu_no_hdmi','width':1280,'height':720,'fps':10,'frames':30,
                'format':'NV12','colorimetry':'BT.601 limited; transfer709','base_source':str(SOURCE.relative_to(ROOT)),
                'base_sha256':sha(SOURCE),'input_sha256':sha(OUT/'frames.nv12'),'frame_records':records}
    (OUT/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode('utf-8'))
    (OUT/'files.sha256').write_bytes(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(OUT.iterdir()) if p.is_file()).encode('ascii'))
    print(OUT)

if __name__ == '__main__':
    main()

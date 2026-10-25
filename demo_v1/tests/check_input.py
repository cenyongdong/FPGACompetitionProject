"""实际论文MAT的v2传输与冻结CSI/预处理参考逐位对照。"""
from pathlib import Path
import struct, subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
origin=ROOT/'.local/shared-stability-delivery-20261015-r2/fixtures'
data=ROOT/'demo_v1/data/full/aligned.bin'
for i,name in enumerate(['S11_01_308','S11_01_309','S11_01_310']):
    with data.open('rb') as f: f.seek(i*86400); payload=f.read(86400)
    internal=np.frombuffer(payload,dtype='<f8').reshape(3,3,20,30,2).transpose(0,1,3,2,4).copy().tobytes()
    if internal != (origin/(name+'.csi')).read_bytes()[32:]: raise ValueError('Original raw CSI mismatch')
    wire=ROOT/'demo_v1/build'/('test-'+name+'.wire')
    wire.write_bytes(struct.pack('<8sIIQQ',b'PIWCSI2\0',2,86400,i+1,123)+payload)
    subprocess.run([str(ROOT/'demo_v1/build/codec.exe'),str(wire),str(origin/(name+'.input.f32'))],check=True)
print('3/3 original MAT -> aligned v2 -> frozen raw bytes and input FP32 bitwise passed')

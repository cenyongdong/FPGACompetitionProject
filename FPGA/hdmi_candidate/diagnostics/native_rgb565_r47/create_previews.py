from pathlib import Path
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parent
E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-render-speed-20261024-r47')
for kind in ('old','native'):
    raw=np.fromfile(W/f'board-cpu/cpu-output/{kind}-308.rgb565',dtype='<u2').reshape(1080,1920).astype(np.uint32)
    rgb=np.stack([((raw>>11)&31)*255//31,((raw>>5)&63)*255//63,(raw&31)*255//31],axis=-1).astype(np.uint8)
    Image.fromarray(rgb).save(E/f'preview-{kind}.png')
print('Rendered actual CPU benchmark RGB565 bytes as inspection PNGs.')

from pathlib import Path
import shutil
W=Path(__file__).resolve().parent;P=W/'benchmark';P.mkdir(exist_ok=True)
base=Path('D:/FPGACompetitionProject/.local/hp2-deferred-consume-20261024-r45/source/display')
for name in ('skeleton_render.cpp','skeleton_render.hpp','hdmi_canvas.cpp','hdmi_canvas.hpp','hdmi_format.hpp'):
    shutil.copyfile(base/name,P/name)
F=W/'fixtures';F.mkdir(exist_ok=True)
src=Path('D:/FPGACompetitionProject/.local/shared-stability-delivery-20261015-r2/fixtures')
for n in ('308','309','310'):
    for kind in ('scores','poses'):shutil.copyfile(src/f'S11_01_{n}.{kind}.f32',F/f'S11_01_{n}.{kind}.f32')
print('Prepared original renderer+canvas benchmark baseline and three frozen pose inputs; no SDK.')

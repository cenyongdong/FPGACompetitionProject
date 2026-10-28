"""Render actual SDK joints at ten recorded visual-cue midpoints, without RGB."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

EDGES=[(0,1),(1,20),(20,2),(2,3),(20,4),(4,5),(5,6),(6,7),(7,21),(6,22),
       (20,8),(8,9),(9,10),(10,11),(11,23),(10,24),(0,12),(12,13),(13,14),
       (14,15),(0,16),(16,17),(17,18),(18,19)]


def render(folder):
    folder=Path(folder)
    frames=[json.loads(line) for line in (folder/'kinect/bodies.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    frames=[f for f in frames if f['body_count']==1]
    if not frames:raise ValueError('No actual single-person frames')
    meta=json.loads((folder/'kinect/metadata.json').read_text(encoding='utf-8-sig'))
    times=np.asarray([f['host_acquire_end_qpc'] for f in frames],dtype=np.int64)
    events=[json.loads(line) for line in (folder/'visual-protocol.jsonl').read_text().splitlines()]
    cues=[e for e in events if e.get('type')=='phase']
    fig,axes=plt.subplots(2,5,figsize=(14,8),sharex=True,sharey=True)
    for ax,cue in zip(axes.flat,cues):
        target=int(cue['host_qpc'])+15*meta['host_qpc_frequency_hz']
        frame=frames[int(np.argmin(np.abs(times-target)))];joints=frame['bodies'][0]['joints']
        positions=np.asarray([[j['x'],j['y'],j['z']] for j in joints],dtype=float)
        good=np.asarray([j['tracking_state']=='Tracked' for j in joints])
        for a,b in EDGES:
            ax.plot(positions[[a,b],0],positions[[a,b],1],color='#1c7ed6' if good[a] and good[b] else '#e67700',linewidth=2)
        ax.scatter(positions[:,0],positions[:,1],c=np.where(good,'#1c7ed6','#e67700'),s=12)
        ax.set_title('Phase '+str(int(cue['data']['phase'])+1)+' midpoint');ax.set_aspect('equal');ax.set_xlim(-1.5,1.5);ax.set_ylim(-2,.9);ax.grid(alpha=.2)
    fig.suptitle('Actual Kinect v2 joints: blue=Tracked, orange=Inferred; no predicted poses')
    fig.supxlabel('SDK camera X (m)');fig.supylabel('SDK camera Y (m)');fig.tight_layout()
    output=folder/'skeleton-quality.png'
    if output.exists():raise FileExistsError(output)
    fig.savefig(output,dpi=120);plt.close(fig)
    return str(output.resolve())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('session',type=Path)
    print(render(parser.parse_args().session))

"""Check saved SDK actions against the five-minute routine; never create GT."""
import argparse
from collections import Counter
import json
from pathlib import Path
import numpy as np

PHASES = [('relaxed', '自然站立，双臂略离身体'), ('T', '双臂侧平举'),
          ('left', '左臂侧平举，右臂放下'), ('right', '右臂侧平举，左臂放下'),
          ('bent', '双手位于肩旁'), ('step', '左移小半步后站稳'),
          ('return', '右移小半步回中间'), ('T', '双臂侧平举'),
          ('bent', '双手位于肩旁'), ('relaxed', '自然站立，双臂略离身体')]


def percentile(values):
    return np.percentile(values, [5, 50, 95]).tolist() if len(values) else None


def audit(folder):
    folder = Path(folder)
    frames = [json.loads(line) for line in (folder/'kinect/bodies.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    first = frames[0]['sensor_relative_ticks_100ns']
    meta = json.loads((folder/'kinect/metadata.json').read_text(encoding='utf-8-sig'))
    first_qpc=frames[0]['host_acquire_end_qpc']; frequency=meta['host_qpc_frequency_hz']
    cue_path=folder/'protocol-events.jsonl'
    cues=[json.loads(line) for line in cue_path.read_text().splitlines() if line.strip()] if cue_path.exists() else []
    cues=[c for c in cues if c.get('event')=='phase']
    phases=PHASES
    visual=folder/'visual-protocol.jsonl'
    if visual.exists():
        visual_events=[json.loads(line) for line in visual.read_text().splitlines() if line.strip()]
        starts=[e for e in visual_events if e.get('type')=='start']
        if not starts:raise ValueError('Visual protocol has not started')
        protocol=starts[0]['data'];number=int(protocol['session'])
        kinds={1:['relaxed','T','left','right','bent']*2,
               2:['dynamic','dynamic','dynamic','dynamic','relaxed']*2,
               3:['relaxed','T','bent','step','T','bent','step','T','bent','return']}[number]
        custom_kinds=folder.parent/'protocol-action-kinds.json'
        if custom_kinds.exists():
            kinds=json.loads(custom_kinds.read_text(encoding='utf-8-sig'))[number-1]
            if len(kinds)!=10:raise ValueError('Custom protocol must identify ten diagnostic phase kinds')
        phases=list(zip(kinds,protocol['instructions']))
        cues=[dict(phase=e['data']['phase'],host_qpc=e['host_qpc']) for e in visual_events if e.get('type')=='phase']
    boundaries={int(c['phase']):(int(c['host_qpc'])-first_qpc)/frequency for c in cues}
    end_time=(frames[-1]['host_acquire_end_qpc']-first_qpc)/frequency
    if visual.exists():
        ends=[e for e in visual_events if e.get('type')=='end']
        if ends:end_time=(int(ends[-1]['host_qpc'])-first_qpc)/frequency
    normals = np.asarray([frame['floor_clip_plane'][:3] for frame in frames if frame['body_count'] == 1], dtype=float)
    normals = normals[np.isfinite(normals).all(axis=1) & (np.linalg.norm(normals, axis=1) > .8)]
    if not len(normals):
        raise ValueError('No usable measured up direction')
    up = np.median(normals, axis=0); up /= np.linalg.norm(up)
    rows = []
    for frame in frames:
        t = (frame['host_acquire_end_qpc']-first_qpc)/frequency
        if frame['body_count'] != 1:
            rows.append(dict(t=t, usable=False)); continue
        body = frame['bodies'][0]; joints = {j['name']: j for j in body['joints']}
        required = ['ShoulderLeft', 'ShoulderRight', 'ElbowLeft', 'ElbowRight', 'HandLeft', 'HandRight', 'SpineBase']
        usable = all(joints[n]['tracking_state'] == 'Tracked' and joints[n]['finite'] for n in required)
        pos = {name: np.asarray([joint['x'], joint['y'], joint['z']], dtype=float) for name, joint in joints.items()}
        row = dict(t=t, usable=usable, tracking_id=body['tracking_id'], clipped=body['clipped_edges'],
                   root=pos['SpineBase'].tolist(), neck=pos['Neck'].tolist())
        if usable:
            arms = []
            for side in ('Left', 'Right'):
                upper = pos['Elbow'+side]-pos['Shoulder'+side]
                fore = pos['Hand'+side]-pos['Elbow'+side]
                hand = pos['Hand'+side]-pos['Shoulder'+side]
                un = np.linalg.norm(upper); fn = np.linalg.norm(fore); hn = np.linalg.norm(hand)
                if min(un, fn, hn) < .03:
                    usable = False; break
                upper_vertical = float(upper@up/un); hand_vertical = float(hand@up/hn)
                extension_cos = float(upper@fore/un/fn)
                arms.append(dict(horizontal=abs(upper_vertical) < .5 and abs(hand_vertical) < .5 and extension_cos > .5,
                    down=upper_vertical < -.65 and hand_vertical < -.65,
                    bent=float(fore@up/fn) > .4 and extension_cos < .5 and np.linalg.norm(hand) < .5))
            row['usable'] = usable
            if usable:
                left, right = arms
                row['matches'] = dict(T=left['horizontal'] and right['horizontal'],
                    left=left['horizontal'] and right['down'], right=right['horizontal'] and left['down'],
                    bent=left['bent'] and right['bent'], relaxed=left['down'] and right['down'])
        rows.append(row)
    reports = []; initial_start=boundaries.get(0,0)
    first_roots = [r['root'] for r in rows if initial_start+5 <= r['t'] < initial_start+27 and r.get('usable')]
    baseline = np.median(first_roots, axis=0) if first_roots else None
    for index, (kind, description) in enumerate(phases):
        # Exclude transitions and leave a guard for manual chat delivery timing.
        lo=boundaries.get(index,index*30)
        hi=boundaries.get(index+1,end_time if index==9 else (index+1)*30)
        selected = [r for r in rows if lo+5 <= r['t'] < hi-2]
        good = [r for r in selected if r.get('usable')]
        roots = np.asarray([r['root'] for r in good], dtype=float)
        matched = [r for r in good if r.get('matches', {}).get(kind, False)]
        root_med = np.median(roots, axis=0) if len(roots) else None
        match_fraction = len(matched)/len(good) if good and kind in ('T','left','right','bent','relaxed') else None
        report = dict(phase=index+1, seconds=[lo,hi], instruction=description,
            evaluated_body_frames=len(selected), tracked_upper_body_frames=len(good),
            tracked_upper_body_fraction=len(good)/len(selected) if selected else 0,
            geometric_action_match_fraction_among_tracked=match_fraction,
            matching_tracked_frames=len(matched) if match_fraction is not None else None,
            median_root_camera_metres=root_med.tolist() if root_med is not None else None,
            root_delta_from_first_camera_metres=(root_med-baseline).tolist() if root_med is not None and baseline is not None else None,
            root_p95_distance_to_median_m=float(np.percentile(np.linalg.norm(roots-root_med, axis=1), 95)) if len(roots) else None)
        reports.append(report)
    report = dict(schema='KINECT-ACTION-AUDIT1', source='Actual SDK named joints; no predicted or generated skeletons',
        phase_time_policy=('Actual visual-panel phase QPC; 5s start/2s end guards; not RF exposure synchronization.' if visual.exists() else 'Actual locally logged chat cue QPC when available; otherwise nominal phases. Prompt delivery latency unmeasured; 5s start/2s end guards. QPC identifies prompt phases, not RF exposure synchronization.'),
        coordinate_policy='Measured SDK floor normal used only as an up direction; no floor height or official label transform inferred',
        limitations=['Geometric heuristic is a diagnostic, not independent motion ground truth',
                     'Step direction is reported in raw camera coordinates; anatomical left is not assumed from its sign',
                     'No RF-to-Kinect synchronization or trainable labels are certified here'],
        measured_up_direction=up.tolist(), phases=reports,
        tracking_ids=dict(Counter(r['tracking_id'] for r in rows if 'tracking_id' in r)),
        training_started=False)
    with (folder/'action-quality.json').open('x', encoding='utf-8') as target:
        json.dump(report, target, indent=2, ensure_ascii=False, allow_nan=False); target.write('\n')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('session', type=Path)
    print(json.dumps(audit(parser.parse_args().session), indent=2, ensure_ascii=False))

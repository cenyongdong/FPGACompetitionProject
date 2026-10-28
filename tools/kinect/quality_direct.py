"""Summarize real direct recordings without making synchronized training labels."""
import argparse
import json
from pathlib import Path
import numpy as np

TARGET = ['Neck', 'Head', 'ShoulderLeft', 'ShoulderRight', 'ElbowLeft', 'HipLeft',
          'ElbowRight', 'HipRight', 'HandLeft', 'KneeLeft', 'HandRight', 'KneeRight',
          'AnkleLeft', 'AnkleRight']


def summarize(folder):
    folder = Path(folder)
    metadata = json.loads((folder/'kinect/metadata.json').read_text(encoding='utf-8-sig'))
    csi = json.loads((folder/'csi/metadata.json').read_text(encoding='utf-8-sig'))
    frames = [json.loads(line) for line in (folder/'kinect/bodies.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    single = [frame for frame in frames if frame['body_count'] == 1]
    if not single:
        raise ValueError('No actual single-person observations')
    names = metadata['joint_names']; indices = [names.index(name) for name in TARGET]
    positions = np.asarray([[[j['x'], j['y'], j['z']] for j in f['bodies'][0]['joints']] for f in single], dtype=float)
    tracked = np.asarray([[j['tracking_state'] == 'Tracked' and j['finite'] for j in f['bodies'][0]['joints']] for f in single])
    hz = metadata['host_qpc_frequency_hz']
    host = np.asarray([f['host_acquire_end_qpc']/hz for f in single])
    sensor = np.asarray([f['sensor_relative_ticks_100ns']/1e7 for f in single])
    receipt_difference_ms = (host-sensor)*1e3
    differences=np.linalg.norm(np.diff(positions,axis=0),axis=2)
    adjacent_tracked=tracked[1:] & tracked[:-1] & (np.diff(sensor)[:,None]<.05)
    joint_jump=(differences>.25)&adjacent_tracked
    core=[names.index(n) for n in ('Neck','SpineBase','SpineShoulder')]
    core_jump=((differences[:,core]>.15)&adjacent_tracked[:,core]).any(axis=1)
    suspicious=joint_jump.any(axis=1)|core_jump
    suspicious_frames=sorted({single[i]['frame'] for j in np.flatnonzero(suspicious) for i in (j,j+1)})
    tokens = np.memmap(folder/'csi/tokens.f32', dtype='<f4', mode='r')
    if tokens.size != csi['windows']*180*60:
        raise ValueError('Native feature count differs from recorded windows')
    finite = bool(np.isfinite(tokens).all())
    windows = [json.loads(line) for line in (folder/'csi/windows.jsonl').read_text().splitlines()]
    stationary = {str(limit): 0 for limit in (.03, .05, .08)}
    for window in windows:
        if not window['valid']:
            continue
        center = window['host_window_end_receipt_qpc']/hz
        selected = np.abs(host-center) <= 1
        if selected.sum() < 40 or host[selected].min() > center-.8 or host[selected].max() < center+.8:
            continue
        good = tracked[selected][:, indices]
        if good.mean(axis=0).min() < .8:
            continue
        points = positions[selected][:, indices]
        medians = np.asarray([np.median(points[good[:, j], j], axis=0) for j in range(14)])
        distance = max(float(np.percentile(np.linalg.norm(points[good[:, j], j]-medians[j], axis=1), 95)) for j in range(14))
        for limit in stationary:
            stationary[limit] += distance <= float(limit)
    report = dict(frames=len(frames), frames_one_body=len(single),
        target14_all_tracked=int(tracked[:, indices].all(axis=1).sum()),
        target_joint_tracked_fraction={name: round(float(tracked[:, index].mean()), 4) for name, index in zip(TARGET, indices)},
        motion_diagnostics=dict(policy='Adjacent Tracked joints within 50ms; >25cm/joint or >15cm neck/spine displacement flags only',
            suspicious_adjacent_pairs=int(suspicious.sum()),flagged_camera_frame_ids=suspicious_frames,
            per_joint_jump_counts={name:int(joint_jump[:,i].sum()) for i,name in enumerate(names) if joint_jump[:,i].any()},
            core_jump_pairs=int(core_jump.sum())),
        nonfinite_joint_coordinates=int((~np.isfinite(positions)).sum()),
        csi_windows=csi['windows'], original_preprocess=csi['original_preprocess'],
        all_input_features_finite=finite, input_shape=[csi['windows'], 180, 60],
        sensor_ticks_vs_receipt_qpc_observed_difference_ms_percentiles_0_5_50_95_100=np.percentile(receipt_difference_ms, [0, 5, 50, 95, 100]).tolist(),
        numeric_clock_difference_is_not_calibration=True,
        stationary_2s_windows=stationary,
        stationary_policy='At least 40 body frames covering center +/-0.8s; each target joint >=80% Tracked; maximum per-joint 95th percentile distance to median <= threshold in metres. Receipt-based diagnostic only.',
        target_mapping_status='Candidate named mapping; original official Kinect export mapping is not yet verified',
        not_a_trainable_pairing=True, label_clock_verified=False, coordinate_contract_verified=False)
    with (folder/'quality-summary.json').open('x', encoding='utf-8') as target:
        json.dump(report, target, indent=2, allow_nan=False); target.write('\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session', type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.session), indent=2))

"""Check an actual Kinect v2 capture and export its raw joints as long-form CSV."""
import argparse
from collections import Counter
import csv
import json
import math
from pathlib import Path
import statistics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    folder = args.capture
    metadata = json.loads((folder/'metadata.json').read_text(encoding='utf-8-sig'))
    result = json.loads((folder/'result.json').read_text(encoding='utf-8-sig'))
    names = metadata['joint_names']
    if len(names) != 25 or metadata['position_units'] != 'metres':
        raise ValueError('This analyzer requires unmodified Kinect v2 camera-space joints.')
    frames = people_frames = observations = joint_rows = all_tracked = 0
    timestamps = []
    ids = set()
    counts = Counter()
    states = Counter()
    nonfinite = 0
    output = folder/'joints.csv'
    fields = ['frame', 'sensor_relative_ticks_100ns', 'host_acquire_begin_qpc',
              'host_acquire_end_qpc', 'host_acquire_end_utc', 'tracking_id',
              'joint_index', 'joint_name', 'x_m', 'y_m', 'z_m', 'tracking_state', 'finite']
    with output.open('x', newline='', encoding='utf-8') as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        with (folder/'bodies.jsonl').open(encoding='utf-8-sig') as source:
            for line in source:
                row = json.loads(line)
                frames += 1
                if row['schema'] != 'KINECT2-BODIES1' or row['frame'] != frames:
                    raise ValueError('Unexpected schema or frame sequence')
                if row['body_count'] != len(row['bodies']):
                    raise ValueError('Body count disagrees with saved bodies')
                if row['host_acquire_begin_qpc'] > row['host_acquire_end_qpc']:
                    raise ValueError('Invalid host QPC bracket')
                timestamps.append(row['sensor_relative_ticks_100ns'])
                counts[row['body_count']] += 1
                people_frames += bool(row['bodies'])
                for body in row['bodies']:
                    observations += 1
                    ids.add(body['tracking_id'])
                    joints = body['joints']
                    if [j['index'] for j in joints] != list(range(25)) or [j['name'] for j in joints] != names:
                        raise ValueError('Joint identity differs from the original SDK enum')
                    all_tracked += all(j['tracking_state'] == 'Tracked' and j['finite'] for j in joints)
                    for joint in joints:
                        finite = all(isinstance(joint[k], (int, float)) and math.isfinite(joint[k]) for k in ('x', 'y', 'z'))
                        if finite != joint['finite']:
                            raise ValueError('Finite flag disagrees with saved values')
                        states[joint['tracking_state']] += 1
                        nonfinite += not finite
                        writer.writerow(dict(frame=row['frame'], sensor_relative_ticks_100ns=timestamps[-1],
                            host_acquire_begin_qpc=row['host_acquire_begin_qpc'],
                            host_acquire_end_qpc=row['host_acquire_end_qpc'], host_acquire_end_utc=row['host_acquire_end_utc'],
                            tracking_id=body['tracking_id'], joint_index=joint['index'], joint_name=joint['name'],
                            x_m=joint['x'], y_m=joint['y'], z_m=joint['z'],
                            tracking_state=joint['tracking_state'], finite=joint['finite']))
                        joint_rows += 1
    if (frames, people_frames, observations) != (result['frames'], result['frames_with_bodies'], result['total_body_observations']):
        raise ValueError('Capture summary disagrees with actual saved frames')
    intervals = [(b-a)/10000 for a, b in zip(timestamps, timestamps[1:])]
    span = (timestamps[-1]-timestamps[0])/10000000 if len(timestamps) > 1 else 0
    report = dict(actual_frames=frames, frames_with_bodies=people_frames,
        actual_body_observations=observations, joint_rows=joint_rows, body_count_histogram=dict(counts),
        distinct_tracking_ids=len(ids), joint_tracking_states=dict(states), nonfinite_joint_positions=nonfinite,
        body_observations_with_all25_joints_tracked=all_tracked,
        sensor_timestamp_span_seconds=span, observed_frame_rate_hz=(frames-1)/span if span > 0 else None,
        timestamp_intervals_ms=dict(min=min(intervals), median=statistics.median(intervals), max=max(intervals)) if intervals else None,
        duplicate_timestamps=sum(x == 0 for x in intervals), backwards_timestamps=sum(x < 0 for x in intervals),
        source='Actual Kinect v2 SDK body frames; no CSI or model inference',
        label_mapping='Original 25 joints, not converted into Person-in-WiFi 14-joint labels',
        cross_device_synchronization=False, csv=output.name,
        skeleton_export_observed=people_frames > 0, sensor_closed=result['sensor_closed'], reader_disposed=result['reader_disposed'])
    with (folder/'analysis.json').open('x', encoding='utf-8') as target:
        json.dump(report, target, indent=2, ensure_ascii=False, allow_nan=False)
        target.write('\n')
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()

"""Pair saved CSI input tensors with independently measured Kinect labels.

Never use model predictions as labels or infer synchronization from filenames.
An explicit measured per-session clock transform and a checked joint/coordinate
contract are required before emitting trainable data. No hardware or training.
"""
import argparse
from bisect import bisect_left
from collections import Counter
import json
from pathlib import Path
import re
import struct
import numpy as np

FULL_BYTES = 74544
INPUT_OFFSET = 384


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')


def transform_contract(contract):
    if not all(contract.get(key) for key in ('mapping_verified', 'coordinates_verified', 'evidence')):
        raise ValueError('Verify the 25-to-14 joint mapping and coordinates with actual calibration evidence first')
    names = contract['target_joint_source_names']
    matrix = np.asarray(contract['camera_metres_to_model_metres'], dtype=float)
    if len(names) != 14 or len(set(names)) != 14 or matrix.shape != (4,4) or not np.isfinite(matrix).all():
        raise ValueError('A distinct 14-joint map and finite 4x4 coordinate transform are required')
    if not np.allclose(matrix[3], [0,0,0,1]) or not np.allclose(matrix[:3,:3].T@matrix[:3,:3],np.eye(3),atol=1e-4):
        raise ValueError('Coordinate transform must preserve metre scale; axis handedness changes are allowed')
    return names, matrix


def label(frame, names, matrix, allow_inferred=False):
    # Reject the whole sample when any observed person lacks a usable skeleton;
    # dropping only that person would manufacture a negative training label.
    if not 1 <= frame['body_count'] <= 3 or len(frame['bodies']) != frame['body_count']:
        return None
    values=[]
    states={'Tracked','Inferred'} if allow_inferred else {'Tracked'}
    for body in frame['bodies']:
        joints={j['name']:j for j in body['joints']}
        result=[]
        for name in names:
            joint=joints.get(name)
            if not joint or joint['tracking_state'] not in states or not joint['finite']:
                return None
            position=np.asarray([joint['x'],joint['y'],joint['z'],1],dtype=float)
            if not np.isfinite(position).all():return None
            result.append((matrix@position)[:3])
        values.append(result)
    return np.asarray(values,dtype='<f4')


def nearest(timestamps, target):
    i=bisect_left(timestamps,target)
    choices=[j for j in (i-1,i) if 0<=j<len(timestamps)]
    return min(choices,key=lambda j:abs(timestamps[j]-target)) if choices else None


def prepare(plan_path, output):
    plan_path=Path(plan_path).resolve();base=plan_path.parent;plan=read(plan_path)
    names,matrix=transform_contract(plan['label_contract'])
    sessions=plan['sessions']
    if not sessions:raise ValueError('No actual paired recordings in the session plan')
    roles={s['split'] for s in sessions}
    if not {'train','val'}.issubset(roles) or not roles.issubset({'train','val','test'}):
        raise ValueError('Separate train and validation recording sessions are required; held-out test is optional')
    if len({s['id'] for s in sessions})!=len(sessions):raise ValueError('Duplicate recording identifier')
    for s in sessions:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',s['id']):raise ValueError('Use a simple recording identifier')
    output=Path(output);output.mkdir(exist_ok=False)
    folders={split:output/(split+'_data') for split in roles}
    for folder in folders.values():
        (folder/'tokens').mkdir(parents=True);(folder/'keypoint').mkdir()
    selected={split:[] for split in roles};recordings=[];source_roles={};camera_roles={}
    for session in sessions:
        root=(base/session['directory']).resolve();split=session['split'];identifier=session['id']
        camera_meta=read(root/'kinect/metadata.json');capture=read(root/'kinect/result.json')
        tap_meta=read(root/'csi/metadata.json');tap_result=read(root/'csi/result.json')
        if tap_meta.get('simulation') or not capture['frames_with_bodies'] or not tap_result['records']:
            raise ValueError('Actual tracked Kinect bodies and actual board inputs are required: '+identifier)
        camera_identity=camera_meta['started_utc']
        if camera_identity in camera_roles and camera_roles[camera_identity]!=split:
            raise ValueError('One Kinect recording cannot appear across training/validation/test splits')
        camera_roles[camera_identity]=split
        clock=read(base/session['clock_calibration'])
        if not clock.get('verified') or not clock.get('evidence') or clock.get('input_source')!='live-csi':
            raise ValueError('Measured clock calibration and confirmed live-CSI provenance required: '+identifier)
        if clock.get('label_time_reference')!='window_end':raise ValueError('Explicit window-end label time policy required')
        scale=float(clock['ticks_per_source_ns']);max_error=float(clock['max_error_ms'])
        max_pair=float(plan.get('max_total_time_error_ms',20))
        if not (np.isfinite(scale) and scale>0 and 0<=max_error<max_pair):raise ValueError('Invalid measured clock uncertainty')
        csi_ref=int(clock['reference_source_ns']);kinect_ref=int(clock['reference_kinect_ticks_100ns'])
        frames=[json.loads(line) for line in (root/'kinect/bodies.jsonl').read_text(encoding='utf-8-sig').splitlines()]
        times=[f['sensor_relative_ticks_100ns'] for f in frames]
        if any(b<=a for a,b in zip(times,times[1:])):raise ValueError('Split Kinect recordings at timestamp discontinuities')
        rejected=Counter();kept=0;max_observed=0
        with (root/'csi/actual.full').open('rb') as raw, (root/'csi/arrival.jsonl').open(encoding='utf-8') as ledger, (output/(identifier+'-pairs.jsonl')).open('x',encoding='utf-8') as pairs:
            for line in ledger:
                receipt=json.loads(line);record=raw.read(FULL_BYTES)
                if len(record)!=FULL_BYTES:raise ValueError('Short original CSI record')
                if not receipt.get('valid'):rejected['invalid_original_record']+=1;continue
                if record[:8]!=b'PIWFUL3\0' or struct.unpack_from('<II',record,8)!=(3,FULL_BYTES):raise ValueError('PIWFUL3 framing differs')
                domain,frame,invocation,source=struct.unpack_from('<QQQQ',record,16)
                if (str(domain),str(frame),str(source))!=(receipt['session'],receipt['frame'],receipt['source_ns']):raise ValueError('CSI ledger identity differs')
                if str(domain)!=str(clock['csi_session']):raise ValueError('Clock calibration belongs to a different board session')
                identity=(domain,frame,source)
                if identity in source_roles:raise ValueError('A CSI input was reused across recordings or splits')
                source_roles[identity]=split
                if not int(clock['valid_source_min_ns'])<=source<=int(clock['valid_source_max_ns']):
                    rejected['outside_clock_calibration']+=1;continue
                target=kinect_ref+(source-csi_ref)*scale
                index=nearest(times,target)
                if index is None:rejected['no_camera_frame']+=1;continue
                delta_ms=abs(times[index]-target)/10000
                if delta_ms+max_error>max_pair:rejected['time_uncertain_or_outside_capture']+=1;continue
                gt=label(frames[index],names,matrix,bool(plan.get('allow_inferred_joints',False)))
                if gt is None:rejected['missing_or_untracked_skeleton']+=1;continue
                tokens=np.frombuffer(record,dtype='<f4',count=180*60,offset=INPUT_OFFSET).reshape(180,60).copy()
                if not np.isfinite(tokens).all():rejected['nonfinite_input']+=1;continue
                name=identifier+'_'+str(frame)
                np.save(folders[split]/'tokens'/(name+'.npy'),tokens)
                np.save(folders[split]/'keypoint'/(name+'.npy'),gt)
                selected[split].append(name);kept+=1;max_observed=max(max_observed,delta_ms+max_error)
                pairs.write(json.dumps(dict(name=name,csi_record=receipt['record'],csi_session=str(domain),source_ns=source,
                    kinect_frame=frames[index]['frame'],kinect_sensor_ticks_100ns=times[index],
                    nearest_frame_error_ms=delta_ms,total_time_error_bound_ms=delta_ms+max_error,
                    label_tracking_ids=[b['tracking_id'] for b in frames[index]['bodies']]))+'\n')
            if raw.read(1):raise ValueError('Unindexed original CSI records')
        recordings.append(dict(id=identifier,split=split,directory=str(root),accepted=kept,rejected=dict(rejected),
            max_total_time_error_ms=max_observed,clock=clock))
    if not selected['train'] or not selected['val']:raise ValueError('No usable training or validation pairs; inspect the retained rejection records')
    for split,names_in_split in selected.items():
        mode='train' if split=='train' else 'test'
        (folders[split]/(mode+'_data_list.txt')).write_text('\n'.join(names_in_split)+'\n',encoding='utf-8')
    manifest=dict(schema='KINECT-WIFI-FT1',trainable=not bool(plan.get('synthetic_fixture')),synthetic_fixture=bool(plan.get('synthetic_fixture')),recording_disjoint_splits=True,
        counts={s:len(v) for s,v in selected.items()},held_out_test_available=bool(selected.get('test')),
        label_source='actual Kinect SDK joints; never model predicted poses',input='unchanged board preprocessed float32[180,60]',
        label_contract=plan['label_contract'],allow_inferred_joints=bool(plan.get('allow_inferred_joints',False)),recordings=recordings)
    save(output/'dataset.json',manifest);return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();print(json.dumps(prepare(a.plan,a.output),indent=2,ensure_ascii=False))


if __name__=='__main__':main()

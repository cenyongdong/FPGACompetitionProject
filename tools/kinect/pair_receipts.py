"""Pair real CSI window receipts with real Kinect acquisitions on one PC QPC.

This creates inspectable receipt-time pairs, NOT verified RF/exposure alignment
or model-coordinate training labels. Preserve the distinction in every report.
"""
import argparse
from bisect import bisect_left
from collections import Counter
import json
from pathlib import Path
import numpy as np

TARGET={'Neck','Head','ShoulderLeft','ShoulderRight','ElbowLeft','HipLeft','ElbowRight',
        'HipRight','HandLeft','KneeLeft','HandRight','KneeRight','AnkleLeft','AnkleRight'}
STATES={'NotTracked':0,'Inferred':1,'Tracked':2}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def nearest(times,target):
    i=bisect_left(times,target)
    choices=[j for j in (i-1,i) if 0<=j<len(times)]
    return min(choices,key=lambda j:(abs(times[j]-target),times[j])) if choices else None


def observed_clock_fit(x_values,y_values,y_hz):
    if len(x_values)<3:return None
    x0=int(x_values[0]);y0=int(y_values[0])
    x=np.asarray([int(v)-x0 for v in x_values],dtype=float)/1e9
    y=np.asarray([int(v)-y0 for v in y_values],dtype=float)/y_hz
    slope,offset=np.linalg.lstsq(np.column_stack((x,np.ones_like(x))),y,rcond=None)[0]
    residual=(y-(slope*x+offset))*1000
    return dict(reference_source_ns=str(x0),reference_receipt_qpc=str(y0),
        receipt_seconds_per_source_second=float(slope),offset_seconds=float(offset),
        fitted_rate_difference_ppm=float((slope-1)*1e6),
        residual_ms_p0_p5_p50_p95_p100=np.percentile(residual,[0,5,50,95,100]).tolist(),
        interpretation='Source-clock to receipt-clock observation only; intercept includes unknown one-way/processing latency; not a physical clock calibration')


def pair(session,output,maximum_receipt_delta_ms=25,synthetic_fixture=False):
    root=Path(session).resolve();output=Path(output).resolve()
    camera_meta=read(root/'kinect/metadata.json');csi_meta=read(root/'csi/metadata.json')
    if (camera_meta.get('simulation') or csi_meta.get('simulation')) and not synthetic_fixture:
        raise ValueError('Synthetic fixtures cannot be reported as actual paired data')
    hz=int(camera_meta['host_qpc_frequency_hz'])
    if hz!=int(csi_meta['qpc_frequency_hz']) or hz<=0:
        raise ValueError('The recording must use the same verified PC QPC frequency')
    if not 0<maximum_receipt_delta_ms<=1000:raise ValueError('Finite explicit receipt matching tolerance required')
    token_source=root/'csi/tokens.f32';total_windows=int(csi_meta['windows'])
    if token_source.stat().st_size!=total_windows*180*60*4:
        raise ValueError('Native feature tensor count differs from saved window count')
    if camera_meta['position_units']!='metres' or len(camera_meta['joint_names'])!=25:
        raise ValueError('Original named 25-joint metre coordinates required')
    names=camera_meta['joint_names'];required=[i for i,n in enumerate(names) if n in TARGET]
    if len(required)!=14:raise ValueError('Missing candidate named joints')
    frames=[json.loads(line) for line in (root/'kinect/bodies.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    times=[(int(f['host_acquire_begin_qpc'])+int(f['host_acquire_end_qpc']))//2 for f in frames]
    if any(f['host_acquire_begin_qpc']>f['host_acquire_end_qpc'] for f in frames):raise ValueError('Invalid camera acquisition bracket')
    if any(b<=a for a,b in zip(times,times[1:])):raise ValueError('Split recordings at host QPC discontinuities')
    flagged=set();motion_available=False
    if (root/'quality-summary.json').exists():
        motion=read(root/'quality-summary.json').get('motion_diagnostics')
        if motion is not None:flagged.update(motion['flagged_camera_frame_ids']);motion_available=True
    if (root/'motion-quality.json').exists():
        flagged.update(read(root/'motion-quality.json')['flagged_camera_frame_ids']);motion_available=True
    formal=None;visual=root/'visual-protocol.jsonl'
    if visual.exists():
        events=[json.loads(line) for line in visual.read_text().splitlines()]
        starts=[e for e in events if e.get('type')=='start'];ends=[e for e in events if e.get('type')=='end']
        if starts and ends:formal=[int(starts[0]['host_qpc']),int(ends[-1]['host_qpc'])]
    output.mkdir(exist_ok=False)
    poses=[];states=[];indices=[];reference_good=[];deltas=[];rejected=Counter();clock_x=[];clock_y=[]
    camera_matches=Counter();valid_sources=0
    with (output/'pairs.jsonl').open('x',encoding='utf-8') as pairs,(output/'rejected.jsonl').open('x',encoding='utf-8') as bad:
        with (root/'csi/windows.jsonl').open() as source:
            for line in source:
                window=json.loads(line);record=int(window['record']);reason=None
                if record!=valid_sources:raise ValueError('CSI record ordering changed')
                valid_sources+=1
                if not window.get('valid') or window['host_window_end_receipt_qpc'] is None:
                    reason='missing_original_receipt'
                else:
                    target=int(window['host_window_end_receipt_qpc']);clock_x.append(int(window['source_ns']));clock_y.append(target)
                    i=nearest(times,target)
                    if i is None:reason='no_camera_frame'
                    elif target<times[0] or target>times[-1]:reason='outside_camera_acquisition_range'
                    elif abs(times[i]-target)*1000/hz>maximum_receipt_delta_ms:reason='receipt_difference_exceeds_tolerance'
                    else:
                        frame=frames[i]
                        if frame['body_count']!=1 or len(frame['bodies'])!=1:reason='not_one_observed_person'
                        else:
                            body=frame['bodies'][0];joints=body['joints']
                            if [j['name'] for j in joints]!=names:raise ValueError('Original joint ordering changed')
                            position=np.asarray([[j['x'],j['y'],j['z']] for j in joints],dtype='<f4')
                            state=np.asarray([STATES[j['tracking_state']] for j in joints],dtype=np.uint8)
                            if not np.isfinite(position).all() or not all(j['finite'] for j in joints):reason='nonfinite_original_joint'
                            else:
                                signed_ms=(target-times[i])*1000/hz
                                complete=bool((state[required]==2).all())
                                jump=frame['frame'] in flagged
                                in_formal=formal is None or formal[0]<=target<=formal[1]
                                selected=complete and not jump and in_formal
                                index=len(indices);indices.append(record);poses.append(position);states.append(state)
                                reference_good.append(selected);deltas.append(signed_ms);camera_matches[frame['frame']]+=1
                                pairs.write(json.dumps(dict(pair=index,csi_record=record,csi_frame=window['frame'],
                                    csi_source_ns=window['source_ns'],csi_receipt_qpc=target,
                                    kinect_frame=frame['frame'],kinect_sensor_ticks_100ns=frame['sensor_relative_ticks_100ns'],
                                    kinect_acquire_begin_qpc=frame['host_acquire_begin_qpc'],kinect_acquire_end_qpc=frame['host_acquire_end_qpc'],
                                    receipt_delta_ms=signed_ms,tracking_id=body['tracking_id'],
                                    target14_all_tracked=complete,motion_diagnostic_available=motion_available,
                                    camera_jump_flag=jump,in_formal_receipt_interval=in_formal,
                                    reference_quality_candidate=selected,RF_exposure_alignment_verified=False))+'\n')
                if reason:
                    rejected[reason]+=1;bad.write(json.dumps(dict(csi_record=record,reason=reason))+'\n')
    if valid_sources!=total_windows:raise ValueError('CSI ledger count differs from native feature tensor count')
    count=len(indices)
    np.save(output/'poses-camera-m.npy',np.asarray(poses,dtype='<f4').reshape(count,25,3))
    np.save(output/'tracking-states.npy',np.asarray(states,dtype=np.uint8).reshape(count,25))
    np.save(output/'csi-record-indices.npy',np.asarray(indices,dtype='<i8'))
    np.save(output/'reference-quality-candidate.npy',np.asarray(reference_good,dtype=bool))
    acquisition_ns=[int(f['sensor_relative_ticks_100ns'])*100 for f in frames if f['body_count']==1]
    acquisition_qpc=[times[i] for i,f in enumerate(frames) if f['body_count']==1]
    report=dict(schema='KINECT-RECEIPT-PAIRS1',session=str(root),qpc_frequency_hz=hz,paired_windows=count,total_csi_windows=total_windows,
        rejected=dict(rejected),reference_quality_candidates=int(sum(reference_good)),
        pairing_method='Nearest real Kinect acquisition midpoint to actual CSI window-end PC receipt, on the same PC QPC; no interpolation or delay invention',
        max_receipt_delta_tolerance_ms=maximum_receipt_delta_ms,
        observed_absolute_receipt_delta_ms_p50_p95_max=np.percentile(np.abs(deltas),[50,95,100]).tolist() if deltas else None,
        observed_signed_receipt_delta_ms_p5_p50_p95=np.percentile(deltas,[5,50,95]).tolist() if deltas else None,
        input_features=dict(path=str(token_source),dtype='<f4',shape=[total_windows,180,60],selection='csi-record-indices.npy'),
        joint_names=names,position_units='metres',coordinates='Unchanged Kinect SDK camera space; NOT the model training coordinate system',
        tracking_state_encoding=STATES,formal_receipt_interval_qpc=formal,
        repeated_camera_frame_assignments=sum(n-1 for n in camera_matches.values() if n>1),
        source_to_receipt_observation=observed_clock_fit(clock_x,clock_y,hz),
        kinect_timestamp_to_acquisition_observation=observed_clock_fit(acquisition_ns,acquisition_qpc,hz),
        RF_exposure_alignment_verified=False,physical_time_error_bound_ms=None,
        unknown_delay_terms=['Router capture-to-PC transport and buffering','Kinect exposure-to-body acquisition processing'],
        trainable=False,model_coordinate_transform_verified=False,official_14_joint_map_verified=False,
        synthetic_fixture=synthetic_fixture,training_started=False,
        warning='Receipt delta and fitted residual are NOT total RF/exposure synchronization error. Reference-quality selection is not a training-ready label assertion.')
    with (output/'pairing.json').open('x',encoding='utf-8') as target:json.dump(report,target,indent=2,ensure_ascii=False,allow_nan=False);target.write('\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--session',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path);parser.add_argument('--max-receipt-delta-ms',type=float,default=25)
    args=parser.parse_args();report=pair(args.session,args.output,args.max_receipt_delta_ms)
    print(json.dumps({k:report[k] for k in ('session','paired_windows','total_csi_windows','rejected','reference_quality_candidates','observed_absolute_receipt_delta_ms_p50_p95_max','trainable')},indent=2))

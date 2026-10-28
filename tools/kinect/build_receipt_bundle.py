"""Stage real receipt-supervised fine-tuning samples in an explicit local frame.

Experimental local-scene labels are NOT certified official coordinates or
RF/exposure synchronization. The strict calibrated-data path stays separate.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import numpy as np

JOINTS=['Neck','Head','ShoulderLeft','ShoulderRight','ElbowLeft','HipLeft','ElbowRight',
        'HipRight','HandLeft','KneeLeft','HandRight','KneeRight','AnkleLeft','AnkleRight']


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save_new(path,value):
    with Path(path).open('x',encoding='utf-8') as target:json.dump(value,target,indent=2,ensure_ascii=False,allow_nan=False);target.write('\n')


def fit_local_frame(sessions):
    """Fit only actual standing training reference frames, never val/test."""
    selected=[];normals=[];feet=[]
    for root in map(Path,sessions):
        source_index=root.parent/'candidate-index.json'
        if source_index.exists():
            roles=[r['suggested_split'] for r in read(source_index)['recordings'] if Path(r['directory']).resolve()==root.resolve()]
            if roles and roles!=['train']:raise ValueError('Validation/test data cannot fit the local coordinate frame')
        meta=read(root/'kinect/metadata.json');frequency=meta['host_qpc_frequency_hz']
        events=[json.loads(l) for l in (root/'visual-protocol.jsonl').read_text().splitlines()]
        phase0=next(e['host_qpc'] for e in events if e['type']=='phase' and e['data']['phase']==0)
        records=[]
        with (root/'kinect/bodies.jsonl').open(encoding='utf-8-sig') as source:
            for line in source:
                frame=json.loads(line)
                elapsed=(frame['host_acquire_end_qpc']-phase0)/frequency
                if not 5<=elapsed<=25 or frame['body_count']!=1:continue
                joints={j['name']:j for j in frame['bodies'][0]['joints']}
                if not all(joints[n]['tracking_state']=='Tracked' and joints[n]['finite'] for n in ['FootLeft','FootRight','AnkleLeft','AnkleRight']):continue
                normal=np.asarray(frame['floor_clip_plane'][:3],dtype=float)
                if not np.isfinite(normal).all() or np.linalg.norm(normal)<.8:continue
                normals.append(normal/np.linalg.norm(normal))
                for name in ['FootLeft','FootRight']:
                    joint=joints[name];feet.append([joint['x'],joint['y'],joint['z']])
                records.append(frame['frame'])
        if not records:raise ValueError('No actual tracked standing feet in training reference '+str(root))
        selected.append(dict(directory=str(root.resolve()),role='train',phase=0,frame_count=len(records),frame_range=[min(records),max(records)]))
    up=np.median(normals,axis=0);up/=np.linalg.norm(up)
    lateral=np.asarray([1.,0,0]);lateral-=up*float(lateral@up);lateral/=np.linalg.norm(lateral)
    forward=np.cross(lateral,up);forward/=np.linalg.norm(forward)
    projection=np.asarray(feet)@up;foot_reference=float(np.median(projection))
    matrix=np.eye(4);matrix[:3,:3]=np.asarray([lateral,forward,-up]);matrix[:3,3]=[1.75,0,4.2+foot_reference]
    if not np.allclose(matrix[:3,:3]@matrix[:3,:3].T,np.eye(3),atol=1e-8):raise ValueError('Nonrigid label conversion')
    return dict(schema='KINECT-LOCAL-FRAME1',target_joint_source_names=JOINTS,
        camera_metres_to_local_metres=matrix.tolist(),training_reference_recordings=selected,
        SDK_measured_up=up.tolist(),tracked_foot_reference_projection_m=foot_reference,
        tracked_foot_projection_p5_p50_p95_m=np.percentile(projection,[5,50,95]).tolist(),
        definition='C0=1.75+horizontal SDK-X projection; C1=horizontal camera-forward projection; C2=4.2-height above tracked-foot reference plane; metre scale preserved',
        coordinate_frame_defined=True,physical_floor_height_calibrated=False,official_coordinate_equivalence_verified=False,
        joint_mapping_definition='Explicit local named SDK subset following paper table/topology candidate; Hand is not replaced by Wrist',
        official_joint_export_map_verified=False,physical_time_alignment_verified=False,
        supervision_profile='receipt_supervised_local_scene_experiment')


def export_record(pair_directory,dataset,identifier,split,allow_test_fixture=False):
    pair_directory=Path(pair_directory).resolve();dataset=Path(dataset).resolve()
    if split not in ('train','val','test'):raise ValueError('Explicit whole-recording role required')
    contract=read(dataset/'local-frame.json');report=read(pair_directory/'pairing.json')
    if report.get('synthetic_fixture') and not allow_test_fixture:raise ValueError('Synthetic fixtures cannot enter the real training candidate')
    names=report['joint_names'];joint_indices=[names.index(name) for name in contract['target_joint_source_names']]
    matrix=np.asarray(contract['camera_metres_to_local_metres'],dtype=float)
    poses=np.load(pair_directory/'poses-camera-m.npy',mmap_mode='r');states=np.load(pair_directory/'tracking-states.npy',mmap_mode='r')
    indices=np.load(pair_directory/'csi-record-indices.npy',mmap_mode='r');selected=np.load(pair_directory/'reference-quality-candidate.npy',mmap_mode='r')
    source=report['input_features'];tokens=np.memmap(source['path'],dtype='<f4',mode='r',shape=tuple(source['shape']))
    root=dataset/(split+'_data');(root/'tokens').mkdir(parents=True,exist_ok=True);(root/'keypoint').mkdir(exist_ok=True)
    records=dataset/'records';records.mkdir(exist_ok=True);entry=records/(identifier+'.json')
    if entry.exists():raise FileExistsError(entry)
    kept=[];rejected=Counter();low=np.full(3,np.inf);high=np.full(3,-np.inf)
    with (records/(identifier+'-provenance.jsonl')).open('x',encoding='utf-8') as ledger:
        for i in np.flatnonzero(selected):
            if not (states[i,joint_indices]==2).all():raise ValueError('Candidate mask disagrees with actual tracking state')
            actual=np.asarray(poses[i,joint_indices],dtype=float);converted=actual@matrix[:3,:3].T+matrix[:3,3]
            feature=np.asarray(tokens[int(indices[i])],dtype='<f4')
            if not np.isfinite(converted).all() or not np.isfinite(feature).all():rejected['nonfinite']+=1;continue
            name=identifier+'_'+str(int(indices[i]));token_path=root/'tokens'/(name+'.npy');pose_path=root/'keypoint'/(name+'.npy')
            if token_path.exists() or pose_path.exists():raise FileExistsError('Existing candidate sample '+name)
            np.save(token_path,feature);np.save(pose_path,converted.astype('<f4')[None])
            low=np.minimum(low,converted.min(axis=0));high=np.maximum(high,converted.max(axis=0));kept.append(name)
            ledger.write(json.dumps(dict(name=name,pair_index=int(i),csi_record=int(indices[i]),source_pairing=str(pair_directory),split=split))+'\n')
    result=dict(id=identifier,split=split,pair_directory=str(pair_directory),original_recording=report['session'],
        count=len(kept),names=kept,rejected=dict(rejected),target_coordinate_min=low.tolist() if kept else None,
        target_coordinate_max=high.tolist() if kept else None,actual_input_unchanged=True,original_label_units='metres',
        synthetic_fixture=bool(report.get('synthetic_fixture')),physical_time_alignment_verified=False)
    save_new(entry,result);return result


def delay_consistency(pair_directory,budget_ms=50):
    """Reject delay outliers without claiming a bound on constant physical delay."""
    root=Path(pair_directory);report=read(root/'pairing.json')
    hz=report.get('qpc_frequency_hz')
    if hz is None:hz=read(Path(report['session'])/'kinect/metadata.json')['host_qpc_frequency_hz']
    rows=[json.loads(line) for line in (root/'pairs.jsonl').read_text().splitlines()]
    if not rows:return set(),dict(removed=0,policy='No paired observations')
    x0=int(rows[0]['csi_source_ns']);y0=int(rows[0]['csi_receipt_qpc'])
    transport=np.asarray([((int(r['csi_receipt_qpc'])-y0)/hz-(int(r['csi_source_ns'])-x0)/1e9)*1000 for r in rows])
    camera=np.asarray([(((int(r['kinect_acquire_begin_qpc'])+int(r['kinect_acquire_end_qpc']))/2)/hz-int(r['kinect_sensor_ticks_100ns'])/1e7)*1000 for r in rows])
    transport-=np.median(transport);camera-=np.median(camera)
    keep=(np.abs(transport)<=budget_ms)&(np.abs(camera)<=budget_ms)
    return {int(row['pair']) for row,ok in zip(rows,keep) if ok},dict(
        relative_delay_outlier_budget_ms=budget_ms,removed=int((~keep).sum()),
        CSI_relative_delay_ms_p5_p50_p95_max=np.percentile(transport,[5,50,95,100]).tolist(),
        camera_relative_delay_ms_p5_p50_p95_max=np.percentile(camera,[5,50,95,100]).tolist(),
        physical_error_bound_ms=None,
        policy='Within-recording receipt-minus-source and acquisition-minus-sensor deviations from median; rejects jitter/stale outliers only; unknown constant delay remains')


def finalize(dataset):
    dataset=Path(dataset).resolve();entries=[read(p) for p in sorted((dataset/'records').glob('*.json'))]
    if not entries:raise ValueError('No actual staged recordings')
    source_roles={};names={s:[] for s in ('train','val','test')};final_entries=[]
    for entry in entries:
        source=entry['original_recording'];role=entry['split']
        if source in source_roles:raise ValueError('One original recording exported more than once')
        source_roles[source]=role
        final_entry=dict(entry)
        if not entry.get('synthetic_fixture'):
            allowed,temporal=delay_consistency(entry['pair_directory']);kept=[]
            ledger=dataset/'records'/(entry['id']+'-provenance.jsonl')
            with ledger.open() as provenance:
                for line in provenance:
                    row=json.loads(line)
                    if int(row['pair_index']) in allowed:kept.append(row['name'])
            final_entry['exported_before_temporal_filter']=len(entry['names'])
            final_entry['names']=kept;final_entry['count']=len(kept);final_entry['delay_consistency']=temporal
        names[role].extend(final_entry['names']);final_entries.append(final_entry)
    if not all(names[s] for s in ('train','val')):raise ValueError('Independent train and validation recordings required')
    for split,items in names.items():
        if not items:continue
        mode='train' if split=='train' else 'test';path=dataset/(split+'_data')/(mode+'_data_list.txt')
        with path.open('x',encoding='utf-8') as target:target.write('\n'.join(items)+'\n')
    synthetic=any(entry.get('synthetic_fixture') for entry in entries)
    report=dict(schema='KINECT-WIFI-RECEIPT-FT1',trainable=False,experimental_trainable=not synthetic,
        supervision_profile='receipt_supervised_local_scene_experiment',synthetic_fixture=synthetic,
        counts={s:len(v) for s,v in names.items()},recording_disjoint_splits=True,
        held_out_test_available=bool(names['test']),local_frame=read(dataset/'local-frame.json'),
        recordings=[{k:v for k,v in e.items() if k!='names'} for e in final_entries],
        input='Original native float32[180,60]; no reprocessing or model-predicted inputs/labels',
        target='Actual named SDK14 subset transformed by one fixed training-only rigid local scene frame',
        physical_time_alignment_verified=False,official_coordinate_equivalence_verified=False,
        official_joint_export_map_verified=False,physical_time_error_bound_ms=None,training_started=False,
        note='Runnable experimental supervision profile only; strict calibrated-data path must not treat this as certified data')
    save_new(dataset/'dataset.json',report);return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);subs=parser.add_subparsers(dest='action',required=True)
    fit=subs.add_parser('frame');fit.add_argument('--dataset',required=True,type=Path);fit.add_argument('--training-reference',required=True,nargs='+',type=Path)
    exp=subs.add_parser('export');exp.add_argument('--dataset',required=True,type=Path);exp.add_argument('--pairs',required=True,type=Path);exp.add_argument('--id',required=True);exp.add_argument('--split',required=True,choices=['train','val','test'])
    finish=subs.add_parser('finalize');finish.add_argument('--dataset',required=True,type=Path)
    args=parser.parse_args()
    if args.action=='frame':args.dataset.mkdir(exist_ok=False);result=fit_local_frame(args.training_reference);save_new(args.dataset/'local-frame.json',result)
    elif args.action=='export':result=export_record(args.pairs,args.dataset,args.id,args.split);result={k:v for k,v in result.items() if k!='names'}
    else:result=finalize(args.dataset);result={k:v for k,v in result.items() if k not in ('recordings','local_frame')}
    print(json.dumps(result,indent=2,ensure_ascii=False))

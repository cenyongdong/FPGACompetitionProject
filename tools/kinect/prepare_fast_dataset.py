"""Stage continuous original tokens, then re-export measured-frame labels.

The source recording, selected pairs, splits and raw camera labels are immutable.
Only a new output directory is written. Physical exposure synchronization and
official label-export equivalence are not invented by spatial calibration.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from build_receipt_bundle import JOINTS


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as out:json.dump(value,out,ensure_ascii=False,indent=2,allow_nan=False);out.write('\n')


def stage(source,destination):
    source=Path(source).resolve();destination=Path(destination).resolve()
    manifest=read(source/'dataset.json')
    if manifest.get('synthetic_fixture') or not manifest.get('experimental_trainable'):raise ValueError('Actual finalized source required')
    destination.mkdir(exist_ok=False,parents=True)
    records={entry['id']:entry for entry in manifest['recordings']}
    result=[]
    for split,count in manifest['counts'].items():
        root=destination/(split+'_data');root.mkdir()
        listing='train_data_list.txt' if split=='train' else 'test_data_list.txt'
        names=(source/(split+'_data')/listing).read_text().splitlines()
        if len(names)!=count or len(set(names))!=count:raise ValueError('Source list count/identity mismatch')
        tokens=np.lib.format.open_memmap(root/'tokens.npy',mode='w+',dtype='<f4',shape=(count,180,60))
        camera=np.lib.format.open_memmap(root/'camera_keypoints.npy',mode='w+',dtype='<f4',shape=(count,25,3))
        states=np.lib.format.open_memmap(root/'tracking_states.npy',mode='w+',dtype='u1',shape=(count,25))
        selected_records={}
        for index,name in enumerate(names):
            identifier,number=name.rsplit('_',1);selected_records.setdefault(identifier,[]).append((index,int(number),name))
        with (root/'provenance.jsonl').open('x',encoding='utf-8') as ledger:
            for identifier,selected in selected_records.items():
                entry=records[identifier]
                if entry['split']!=split:raise ValueError('Recording split mismatch')
                pair=Path(entry['pair_directory']);p=read(pair/'pairing.json');features=p['input_features']
                rows=np.load(pair/'csi-record-indices.npy');lookup={int(n):i for i,n in enumerate(rows)}
                original=np.memmap(features['path'],dtype='<f4',mode='r',shape=tuple(features['shape']))
                raw=np.load(pair/'poses-camera-m.npy',mmap_mode='r');tracking=np.load(pair/'tracking-states.npy',mmap_mode='r')
                for index,number,name in selected:
                    row=lookup[number];tokens[index]=original[number];camera[index]=raw[row];states[index]=tracking[row]
                    ledger.write(json.dumps(dict(index=index,name=name,recording=identifier,pair_index=row,csi_record=number,source_pairs=str(pair)))+'\n')
                del original,raw,tracking
                print('staged',split,identifier,len(selected),flush=True)
        if not np.isfinite(tokens).all() or not np.isfinite(camera).all():raise ValueError('Nonfinite source')
        tokens.flush();camera.flush();states.flush()
        save(root/'names.json',names);(root/listing).write_text('\n'.join(names)+'\n',encoding='utf-8')
        result.append(dict(split=split,count=count,recordings=list(selected_records)))
        del tokens,camera,states
    save(destination/'staging.json',dict(source=str(source),counts=manifest['counts'],splits=result,
        source_manifest=manifest,camera_joint_names=p['joint_names'],tokens_unchanged=True,labels_exported=False,training_started=False))


def labels(destination,calibration):
    destination=Path(destination).resolve();calibration=read(calibration);staging=read(destination/'staging.json')
    if not calibration.get('site_calibration_accepted'):raise ValueError('Measured site calibration required')
    m=np.array(calibration['camera_metres_to_model_metres'],dtype=float)
    if m.shape!=(4,4) or not np.isfinite(m).all() or not np.allclose(m[3],[0,0,0,1]):raise ValueError('Invalid transform')
    if not np.allclose(m[:3,:3]@m[:3,:3].T,np.eye(3),atol=1e-6):raise ValueError('Scaling/shearing labels is prohibited')
    indices=[staging['camera_joint_names'].index(name) for name in JOINTS]
    checks=[]
    for split,count in staging['counts'].items():
        root=destination/(split+'_data');path=root/'keypoints.npy'
        if path.exists():raise FileExistsError(path)
        camera=np.load(root/'camera_keypoints.npy',mmap_mode='r');states=np.load(root/'tracking_states.npy',mmap_mode='r')
        if not (states[:,indices]==2).all():raise ValueError('Untracked joint in selected target')
        target=np.lib.format.open_memmap(path,mode='w+',dtype='<f4',shape=(count,1,14,3))
        for start in range(0,count,2048):
            raw=np.asarray(camera[start:start+2048,indices],dtype=float)
            target[start:start+2048,0]=raw@m[:3,:3].T+m[:3,3]
        target.flush()
        if not np.isfinite(target).all():raise ValueError('Nonfinite exported labels')
        before=np.linalg.norm(camera[:,indices[0]]-camera[:,indices[1]],axis=1)
        after=np.linalg.norm(target[:,0,0]-target[:,0,1],axis=1)
        error=float(np.max(np.abs(before-after)))
        if error>2e-6:raise ValueError('Rigid bone-distance preservation failed')
        checks.append(dict(split=split,count=count,max_neck_head_distance_change_m=error,
            target_min=target.min(axis=(0,1,2)).tolist(),target_max=target.max(axis=(0,1,2)).tolist()))
        del target,camera,states
    source=staging['source_manifest'];report=dict(source)
    report.update(storage='continuous_numpy_v1',supervision_profile='partially_measured_local_scene_receipt_experiment',
        site_coordinate_calibration_verified=bool(calibration.get('fully_measured')),official_coordinate_equivalence_verified=False,
        physical_time_alignment_verified=False,physical_time_error_bound_ms=None,
        calibration=calibration,target_joint_source_names=JOINTS,export_validation=checks,
        input='Original selected native float32[180,60], copied without preprocessing or permutation',
        target='Actual Tracked SDK14 joints, fixed measured site transform plus declared model coordinate convention',
        note='Official sensor-export extrinsics and joint equivalence remain unknown; timing is receipt-supervised.',
        local_frame=None,training_started=False)
    save(destination/'calibration.json',calibration);save(destination/'dataset.json',report)
    print(json.dumps(dict(labels_exported=True,counts=report['counts'],checks=checks),indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);subs=p.add_subparsers(dest='action',required=True)
    s=subs.add_parser('stage');s.add_argument('--source',required=True,type=Path);s.add_argument('--output',required=True,type=Path)
    s=subs.add_parser('labels');s.add_argument('--output',required=True,type=Path);s.add_argument('--calibration',required=True,type=Path)
    a=p.parse_args()
    if a.action=='stage':stage(a.source,a.output)
    else:labels(a.output,a.calibration)

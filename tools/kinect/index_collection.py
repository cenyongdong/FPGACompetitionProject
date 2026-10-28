"""Index independent real recordings and formal cue intervals; no GT pairing."""
import argparse
import json
from pathlib import Path

TARGET={'Neck','Head','ShoulderLeft','ShoulderRight','ElbowLeft','HipLeft','ElbowRight',
        'HipRight','HandLeft','KneeLeft','HandRight','KneeRight','AnkleLeft','AnkleRight'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def index(work,roles=('train','val','test')):
    work=Path(work).resolve();panel=read(work/'panel-result.json')
    if panel['user_stopped'] or len(panel['sessions'])!=3:
        raise ValueError('Index only the completed three-session batch; retain partial originals separately')
    records=[];camera_identities=set()
    if len(roles)!=3 or any(role not in ('train','val','test') for role in roles):raise ValueError('Three explicit reserved recording roles required')
    for item,role in zip(panel['sessions'],roles):
        if item['exit_code']!=0 or not item['protocol_complete']:
            raise ValueError('Incomplete capture cannot be indexed as completed')
        root=Path(item['directory']);meta=read(root/'kinect/metadata.json')
        if meta['started_utc'] in camera_identities:raise ValueError('Repeated original recording')
        camera_identities.add(meta['started_utc'])
        events=[json.loads(line) for line in (root/'visual-protocol.jsonl').read_text().splitlines()]
        start=next(e for e in events if e['type']=='start');end=next(e for e in events if e['type']=='end')
        lo=int(start['host_qpc']);hi=int(end['host_qpc']);frequency=int(start['qpc_frequency_hz'])
        phases=[e for e in events if e['type']=='phase']
        if len(phases)!=10 or not end['data']['completed'] or hi<=lo:
            raise ValueError('Actual complete visual protocol required')
        camera_frames=[];body_frames=0;tracked_frames=0
        with (root/'kinect/bodies.jsonl').open(encoding='utf-8-sig') as source:
            for line in source:
                frame=json.loads(line)
                if not lo<=frame['host_acquire_end_qpc']<=hi:continue
                camera_frames.append(frame['frame'])
                if frame['body_count']==1:
                    body_frames+=1
                    tracked_frames+=all(j['tracking_state']=='Tracked' and j['finite'] for j in frame['bodies'][0]['joints'] if j['name'] in TARGET)
        windows=[]
        with (root/'csi/windows.jsonl').open() as source:
            for line in source:
                window=json.loads(line)
                if window['valid'] and lo<=window['host_window_end_receipt_qpc']<=hi:
                    windows.append(window['record'])
        quality=read(root/'quality-summary.json')
        records.append(dict(id=root.name,directory=str(root),suggested_split=role,
            formal_prompt_qpc_interval=[lo,hi],qpc_frequency_hz=frequency,
            formal_duration_seconds=(hi-lo)/frequency,
            formal_camera_frame_count=len(camera_frames),formal_body_frames=body_frames,
            formal_camera_frame_range=[min(camera_frames),max(camera_frames)] if camera_frames else None,
            formal_target14_all_tracked_frames=tracked_frames,
            receipt_gated_csi_records=windows,receipt_gated_csi_count=len(windows),
            all_csi_windows=quality['csi_windows'],all_input_features_finite=quality['all_input_features_finite'],
            suspicious_adjacent_pairs=quality['motion_diagnostics']['suspicious_adjacent_pairs']))
    report=dict(schema='KINECT-CANDIDATE-INDEX1',trainable=False,simulation=False,training_started=False,
        recordings=records,recordings_are_independent=True,
        formal_duration_seconds=sum(r['formal_duration_seconds'] for r in records),
        input_source='Real three-RX PCAP; native original preprocessing; no predicted poses used as labels',
        index_policy='Formal camera frames and CSI receipt records indexed independently on the same PC QPC. This is an interval index, not frame-exact RF/Kinect synchronization or final paired labels.',
        clock_contract_verified=False,coordinate_contract_verified=False,official_joint_map_verified=False,
        split_policy='Reserve whole recordings; proposed roles only, no adjacent-frame random split')
    with (work/'candidate-index.json').open('x',encoding='utf-8') as target:
        json.dump(report,target,ensure_ascii=False,indent=2);target.write('\n')
    print(json.dumps(dict(recordings=[{k:v for k,v in r.items() if k!='receipt_gated_csi_records'} for r in records],
        formal_duration_seconds=report['formal_duration_seconds'],trainable=False),ensure_ascii=False,indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('work',type=Path)
    parser.add_argument('--roles',nargs=3,choices=['train','val','test'],default=['train','val','test'])
    args=parser.parse_args();index(args.work,args.roles)

"""Independent full CSI/result/source/decoder accounting for a returned demo."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['short','demo']);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--reference',type=Path,default=ROOT/'.local/pose-v1-combined-read/package-20261010-r1');a=p.parse_args()
    E=a.evidence;D=E/(a.stage+'-return/run-'+a.stage);P=D/'results';H=E/(a.stage+'-host');count=3 if a.stage=='short' else 60
    assert (D/'exit.txt').read_text().strip()=='0' and (D/'before.dmesg.txt').read_bytes()==(D/'after.dmesg.txt').read_bytes()
    assert not (P/'failure.txt').exists()
    for line in (D/'files.sha256').read_text().splitlines():h,n=line.split('  ',1);assert sha(D/n)==h
    result=load(P/'summary.json');video=load(P/'video/summary.json');assert result['completed']==result['received']==count and result['overwritten']==0 and not result['failed']
    assert video['pose_published']==video['pose_adopted']==video['frame_adopted']==count and video['drained'] and video['encoded']==video['returned']
    assert all(video[k]==0 for k in ('pose_overwritten','pose_coalesced','frame_overwritten','frame_coalesced'))
    sent=load(H/'sent.json')['records'];rows=lines(P/'results/frames.jsonl');assert len(rows)==len(sent)==count
    refs=a.reference;checked=[];poses=[]
    rendered=E/(a.stage+'-render-input');assert not rendered.exists();rendered.mkdir();catalog=[]
    for i,(record,row) in enumerate(zip(sent,rows)):
        assert row['frame_id']==record['frame_id'] and row['invocation']==i and row['source_time_ns']==record['source_time_ns']
        assert row['layers']==745 and row['host_callbacks']==7 and row['zg_callbacks']==7
        d=P/'results'/('frame-'+str(row['frame_id']));assert sha(d/'csi.payload')==record['payload_sha256']
        arrays={n:np.fromfile(d/(n+'.f32'),dtype='<f4') for n in ('input','scores','poses')}
        assert [arrays[n].size for n in ('input','scores','poses')]==[10800,100,4200]
        assert all(np.isfinite(x).all() for x in arrays.values())
        best=int(np.argmax(arrays['scores']));assert best==row['best_slot']
        assert np.array_equal(np.asarray(row['selected_pose'],dtype='<f4'),arrays['poses'].reshape(100,42)[best])
        stem=Path(record['source_file']).stem
        if (refs/'r6-reference'/(stem+'.scores.f32')).exists():
            for n in ('scores','poses'):assert (d/(n+'.f32')).read_bytes()==(refs/'r6-reference'/(stem+'.'+n+'.f32')).read_bytes(),(stem,n)
            assert (d/'input.f32').read_bytes()==(refs/'reference'/(stem+'.input.f32')).read_bytes()
            checked.append(stem)
        poses.append(sha(d/'poses.f32'))
        for n in ('scores','poses'):(rendered/(f'frame{i}.{n}.f32')).write_bytes((d/(n+'.f32')).read_bytes())
        catalog.append(f'frame{i} {row["frame_id"]}\n')
    (E/(a.stage+'-render-catalog.tsv')).write_text(''.join(catalog),encoding='utf-8',newline='\n')
    assert len(set(poses))>1,'All outputs unchanged despite different CSI'
    samples=lines(P/'video/samples.jsonl');packets=lines(P/'video/packets.jsonl');assert len(samples)==video['encoded'] and all(x['encoded_id']==i for i,x in enumerate(samples))
    actual=[s for s in samples if s['inference_result']];assert {s['source_frame'] for s in actual}=={r['frame_id'] for r in rows}
    assert all(s['source_frame']==rows[s['invocation']]['frame_id'] for s in actual)
    assert sum(x['bytes'] for x in packets)==(P/'video/encoder/video.h264').stat().st_size
    assert packets[-1]['bytes']==0 and packets[-1]['flags']&0x100000
    assert all(x['pts_us']<=y['pts_us'] for x,y in zip(packets[:-1],packets[1:-1]))
    events=lines(P/'video/encoder/events.jsonl');assert len([x for x in events if x['event']=='streamoff'])==2 and not any(x['event']=='abort_streamoff' for x in events)
    network=lines(P/'video/network/events.jsonl');end=network[-1];assert end['event']=='completed' and not end['failed'] and end['sources_live']==0
    player=load(H/'viewer.json');assert player['status']=='stream_ended' and player['decoded_frames']>0 and player['error'] is None
    decoded=lines(H/'decoded.jsonl');assert len(decoded)==player['decoded_frames']
    decoded_ids={x['encoded_id'] for x in decoded};assert decoded_ids.issubset({s['encoded_id'] for s in samples})
    network_sources={s['source_frame'] for s in samples if s['inference_result'] and s['encoded_id'] in decoded_ids}
    assert network_sources=={r['frame_id'] for r in rows},'A real pose was never decoded on host'
    assert not any(x.split()[1].startswith('pose_') for x in (D/'processes.txt').read_text().splitlines()[1:] if len(x.split())>1)
    assert ':8554 ' not in (D/'ports.txt').read_text() and ':39001 ' not in (D/'ports.txt').read_text()
    life=lines(P/'lifecycle.jsonl');assert [x['event'] for x in life]==['VPU_actual_capture','Engine_created_main_thread','production_stopped','workers_joined','Engine_destroyed']
    report={'status':'end_to_end_demo_passed','stage':a.stage,'input_windows':count,'CSI_payloads_bitwise':count,
            'fixed_reference_bitwise_cases':checked,'other_cases_checked_for_shape_finite_selection_only':count-len(checked),
            'all_sources_rendered_encoded_and_host_decoded':count,'different_pose_outputs':len(set(poses)),
            'encoded_frames':video['encoded'],'host_decoded_frames':len(decoded),'GUI':player['display_window'],
            'actual_H264_sha256':sha(P/'video/encoder/video.h264'),'normal_drain_LAST':True,'kernel_unchanged':True,
            'project_processes_ports_released':True,'workers_joined_before_Engine_destroyed':True,
            'compactions':load(D/'resources.json')['compactions'],'HDMI':False,'root_cause_fixed':False,
            'strict_5Hz_or_long_term_acceptance':False,'board_archive_sha256':sha(E/('return-'+a.stage+'.tar'))}
    (E/(a.stage+'.review.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(a.stage,count,'real windows; encoded',video['encoded'],'host decoded',len(decoded),'GUI',player['display_window'])
if __name__=='__main__':main()

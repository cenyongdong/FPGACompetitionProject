"""Independent full-byte verification of saved outputs and timing records."""
import argparse
import json
from pathlib import Path
import numpy as np


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('run',type=Path)
    parser.add_argument('--instruction',action='store_true')
    parser.add_argument('--case-offset',type=int,default=0)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[3]/'model/piw24_pose180_shared-20261024-r1'
    folder=args.run/'results'
    dtype=np.dtype([('invocation','<u8'),('case_index','<u4'),('values','<u4'),('scores','<f4',(180,)),('poses','<f4',(180,14,3))])
    actual_path=folder/'actual.bin'
    if actual_path.stat().st_size%dtype.itemsize:
        raise ValueError('Incomplete full-output record; original retained')
    actual=np.memmap(actual_path,dtype=dtype,mode='r')
    names=['S11_01_308','S12_03_316','S13_41_304']
    prefix='instruction.' if args.instruction else ''
    scores=np.stack([np.fromfile(root/'fixtures'/(n+'.'+prefix+'scores.f32'),dtype='<f4') for n in names])
    poses=np.stack([np.fromfile(root/'fixtures'/(n+'.'+prefix+'poses.f32'),dtype='<f4').reshape(180,14,3) for n in names])
    score_changes=pose_changes=nonfinite=0
    repeat_score_changes=repeat_pose_changes=repeat_changed_calls=0
    first_scores=np.stack([actual[i]['scores'].copy() for i in range(min(3,len(actual)))])
    first_poses=np.stack([actual[i]['poses'].copy() for i in range(min(3,len(actual)))])
    max_score=max_joint=max_checked_joint=0.
    selection_changes=argmax_changes=0
    for start in range(0,len(actual),256):
        batch=actual[start:start+256]
        if not np.array_equal(batch['invocation'],np.arange(start,start+len(batch))) or not np.array_equal(batch['case_index'],(batch['invocation']+args.case_offset)%3) or not np.all(batch['values']==7740):
            raise ValueError('Saved call/case identity differs')
        s= scores[batch['case_index']];p=poses[batch['case_index']]
        score_changes+=int(np.count_nonzero(batch['scores'].view('<u4')!=s.view('<u4')))
        pose_changes+=int(np.count_nonzero(batch['poses'].view('<u4')!=p.view('<u4')))
        nonfinite+=int(np.count_nonzero(~np.isfinite(batch['scores'])))+int(np.count_nonzero(~np.isfinite(batch['poses'])))
        max_score=max(max_score,float(np.max(np.abs(batch['scores'].astype('f8')-s))))
        max_joint=max(max_joint,float(np.max(np.linalg.norm(batch['poses'].astype('f8')-p,axis=-1)))*1000)
        distances=np.linalg.norm(batch['poses'].astype('f8')-p,axis=-1)*1000
        mask=s>np.float32(0.2)
        if mask.any():max_checked_joint=max(max_checked_joint,float(distances[mask].max()))
        selection_changes+=int(np.count_nonzero((batch['scores']>np.float32(0.2))!=mask))
        argmax_changes+=int(np.count_nonzero(batch['scores'].argmax(axis=1)!=s.argmax(axis=1)))
        if len(actual)>=3 and args.case_offset==0:
            same_scores=batch['scores'].view('<u4')!=first_scores[batch['case_index']].view('<u4')
            same_poses=batch['poses'].view('<u4')!=first_poses[batch['case_index']].view('<u4')
            repeat_score_changes+=int(np.count_nonzero(same_scores))
            repeat_pose_changes+=int(np.count_nonzero(same_poses))
            repeat_changed_calls+=int(np.count_nonzero(np.any(same_scores,axis=1)|np.any(same_poses,axis=(1,2,3))))
    timing=[]
    for line in (folder/'frames.jsonl').read_text().splitlines():
        timing.append(json.loads(line))
    if len(timing)!=len(actual):
        raise ValueError('Saved full outputs and timing record counts differ')
    result=dict(saved_calls=len(actual),record_bytes=dtype.itemsize,actual_bytes=actual_path.stat().st_size,
                score_changed_values=score_changes,pose_changed_values=pose_changes,nonfinite_values=nonfinite,
                max_score_delta=max_score,max_joint_delta_mm=max_joint,timing_records=len(timing),
                exact_quantized_reference=not(score_changes or pose_changes or nonfinite))
    result.update(reference='generated_instruction' if args.instruction else 'quantized_Host',case_offset=args.case_offset,
                  max_checked_joint_delta_mm=max_checked_joint,selected_identity_changes=selection_changes,argmax_changes=argmax_changes,
                  approved_gate_passed=bool(args.instruction and not(nonfinite or selection_changes or argmax_changes) and max_score<=0.001 and max_checked_joint<=3.0))
    for name in ('process_ms','forward_ms'):
        values=np.array([row[name] for row in timing])
        def summarize(v):
            return dict(samples=len(v),mean=float(v.mean()),median=float(np.median(v)),p95=float(np.quantile(v,.95)),p99=float(np.quantile(v,.99)),max=float(v.max()),over_33_333ms=int(np.count_nonzero(v>1000/30)))
        result[name]=summarize(values)
        if len(values)>100:
            result[name+'_after_first_100']=summarize(values[100:])
    result['largest_process_latencies']=[{k:r[k] for k in ('invocation','case_index','process_ms','forward_ms') if k in r}
                                       for r in sorted(timing,key=lambda r:r['process_ms'],reverse=True)[:10]]
    summary=folder/'summary.json'
    result['native_summary']=json.loads(summary.read_text()) if summary.exists() else None
    failure=folder/'failure.json'
    result['native_failure']=json.loads(failure.read_text()) if failure.exists() else None
    result['guard']=json.loads((args.run/'guard-summary.json').read_text())
    result['repeat_consistency']=dict(score_changed_values=repeat_score_changes,pose_changed_values=repeat_pose_changes,changed_calls=repeat_changed_calls)
    inference=folder/'inference-summary.json'
    result['inference_summary']=json.loads(inference.read_text()) if inference.exists() else None
    if result['inference_summary']:
        result['saved_calls_per_second_including_archive_comparison']=len(actual)*1000/result['inference_summary']['elapsed_ms']
    resources=[json.loads(line) for line in (args.run/'resources.jsonl').read_text().splitlines() if line.strip()]
    warmed=[r for r in resources if r['elapsed']>=60]
    result['resources_after_60s']={name:dict(min=min(r[name] for r in warmed),max=max(r[name] for r in warmed)) for name in ('rss_kib','data_kib','threads','fds','available_kib')} if warmed else None
    result['kernel_log_changed']=(args.run/'before.dmesg').read_bytes()!=(args.run/'after.dmesg').read_bytes()
    guard=result['guard']
    result['execution_stability_passed']=bool((args.run/'exit.txt').read_text().strip()=='0' and guard['native_exit']==0 and guard['wrapper_error'] is None and guard['SDK_unchanged'] and guard['boot_id_unchanged'] and guard['boot_files_match'] and not guard['device_owners'] and result['native_summary'] and result['native_summary']['resources_destroyed'] and result['inference_summary'] and result['inference_summary']['elapsed_ms']>=1800000 and not nonfinite)
    (args.run/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()

"""Analyze preserved finite-output mismatch without changing evidence or gates."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    count=g.verify(a.results);out=a.results/'results';entries=sorted((out/'presaved-results').iterdir(),key=lambda p:int(p.name));assert len(entries)==38
    comparisons=[]
    for i,entry in enumerate(entries):
        identity=json.loads((entry/'identity.json').read_text());assert identity['call']==i and identity['frame_id']==100000+i and identity['invocation']==i
        assert identity['before_forward']==0 and identity['completed_layers']==745 and identity['host_callbacks']==identity['zg_callbacks']==7
        actual={};changed={}
        for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:
            blob=(entry/(suffix+'.f32')).read_bytes();gold=(a.package/folder/(identity['case']+'.'+suffix+'.f32')).read_bytes()
            x=np.frombuffer(blob,'<f4');y=np.frombuffer(gold,'<f4');assert np.isfinite(x).all() and len(blob)==len(gold)
            changed[suffix]=int((x.view('<u4')!=y.view('<u4')).sum());actual[suffix]=x
            assert changed[suffix]==identity[suffix]['bit_mismatches']
        assert changed['input']==0
        if i<37:assert not any(changed.values())
        comparisons.append(dict(call=i,case=identity['case'],changed=changed))
    bad=entries[-1];identity=json.loads((bad/'identity.json').read_text());case=identity['case']
    poses=np.fromfile(bad/'poses.f32','<f4').reshape(100,42);gold=np.fromfile(a.package/'r6-reference'/(case+'.poses.f32'),'<f4').reshape(100,42)
    scores=np.fromfile(bad/'scores.f32','<f4');refScores=np.fromfile(a.package/'r6-reference'/(case+'.scores.f32'),'<f4');assert (scores.view('<u4')==refScores.view('<u4')).all()
    exact=(poses.view('<u4')[:,None,:]==gold.view('<u4')[None,:,:]).all(2)
    mapping=[np.nonzero(row)[0].tolist() for row in exact];d=np.abs(poses.astype(float)-gold.astype(float));badindices=np.nonzero(poses.ravel().view('<u4')!=gold.ravel().view('<u4'))[0]
    ranges=[]
    for idx in badindices:
        if not ranges or idx!=ranges[-1][1]:ranges.append([int(idx),int(idx)+1])
        else:ranges[-1][1]+=1
    best=int(np.argmax(scores));joints=np.linalg.norm((poses[best]-gold[best]).reshape(14,3),axis=1)
    timings=[json.loads(x) for x in (out/'timing.jsonl').read_text().splitlines()];calls=[json.loads(x) for x in (out/'inference.jsonl').read_text().splitlines()]
    assert len(timings)==38 and len(calls)==37
    ingress=json.loads((out/'input-summary.json').read_text());assert ingress['received']==39 and ingress['consumed']==ingress['returned']==38 and ingress['overwritten']==0 and ingress['final_after_join'] and ingress['failure_path']
    report=dict(status='finite_pose_failure_complete_values_verified_not_acceptance',returned_files=count,
        completed_returned_calls=38,correct_prefix_calls=37,correct_prefix_FP32=558700,bad_case=case,bad_invocation=37,bad_frame=100037,
        input_bitwise=True,scores_bitwise=True,poses_finite=True,poses_changed_FP32=len(badindices),poses_max_abs=float(d.max()),poses_mean_abs=float(d.mean()),poses_RMS=float(np.sqrt((d*d).mean())),
        changed_candidates=np.nonzero((d!=0).any(1))[0].tolist(),fully_changed_candidate_rows_missing_from_reference=[i for i,x in enumerate(mapping) if not x],
        all_actual_pose_rows_exist_in_reference=bool(exact.any(1).all()),exact_pose_row_mapping=mapping,
        best_index=best,reference_best_index=int(np.argmax(refScores)),best_pose_changed_FP32=int((poses[best].view('<u4')!=gold[best].view('<u4')).sum()),best_pose_max_abs=float(d[best].max()),best_pose_joint_distance_max=float(joints.max()),
        changed_FP32_ranges=ranges,received=39,consumed=38,returned=38,pending_unconsumed=1,
        CPU_input_rejection_triggered=False,error_source_readback_triggered=False,new_Host_shadow_metadata_persisted=(out/'copy-observations/metadata.jsonl').exists(),
        metadata_loss_reason='process_system_timing.save invokes saveThenVerifyResult; repeated output gate throws before separate metadata and frame-reference writes in the same try block',
        third_start_executed=False,root_cause_proven=False,ranking_exchange_proven=False,original_failure_preserved=True,
        actual_files_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in bad.iterdir() if p.is_file()},comparisons=comparisons)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k] for k in ['status','bad_case','poses_changed_FP32','poses_max_abs','all_actual_pose_rows_exist_in_reference','best_index','best_pose_max_abs','new_Host_shadow_metadata_persisted']},indent=2))
if __name__=='__main__':main()

"""独立复核归档原值；冻结数值门检仅作用已有三窗参考。"""
from pathlib import Path
import argparse, hashlib, json, struct
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
FULL_BYTES=60784

def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args()
    summary=json.loads((a.run/'summary.json').read_text())
    runtime=json.loads((a.run/'runtime.json').read_text())
    catalog=json.loads((Path(runtime.get('data',ROOT/'demo_v1/data/full'))/'catalog.json').read_text())['samples']
    origin=ROOT/'.local/shared-stability-delivery-20261015-r2/fixtures'
    names=['S11_01_308','S11_01_309','S11_01_310']
    refs={name:tuple(np.fromfile(origin/(name+suffix),dtype='<f4') for suffix in ['.input.f32','.scores.f32','.poses.f32']) for name in names}
    errors=[];gates=[];n=0;digest=hashlib.sha256(); full_digest=hashlib.sha256()
    first={};repeat_count=0;repeat_input_changes=0;repeat_score_changes=0;repeat_pose_changes=0
    max_repeat_all_mm=0.0;max_repeat_high_mm=0.0
    splits={}
    sent_rows=(a.run/'sent.jsonl').open()
    with (a.run/'actual.full').open('rb') as f, (a.run/'actual.full').open('rb') as baseline:
        while True:
            record=f.read(FULL_BYTES)
            if not record:break
            if len(record)!=FULL_BYTES:raise ValueError('Truncated full archive')
            full_digest.update(record);digest.update(record[384:])
            frame,invocation=struct.unpack_from('<QQ',record,24)
            if frame!=1000000+n or invocation!=n:errors.append({'row':n,'error':'identity'})
            values=np.frombuffer(record,dtype='<f4',offset=384)
            if len(values)!=15100 or not np.isfinite(values).all():errors.append({'row':n,'error':'shape/finite'})
            sample=catalog[n%len(catalog)];name=sample['name'];split=sample.get('split','test')
            splits[split]=splits.get(split,0)+1
            sent=json.loads(next(sent_rows))
            if int(sent['source_ns'])!=struct.unpack_from('<Q',record,40)[0] or sent['sample']!=name:
                errors.append({'row':n,'error':'actual source timestamp/sample differs from sender'})
            scores=values[10800:10900];poses=values[10900:];best=int(np.argmax(scores))
            if struct.unpack_from('<I',record,184)[0]!=best or record[192:196]!=scores[best].tobytes() or record[216:384]!=poses.reshape(100,42)[best].tobytes():
                errors.append({'row':n,'error':'selected/full output mismatch'})
            key=(split,name)
            if key not in first:first[key]=n
            else:
                repeat_count+=1;baseline.seek(first[key]*FULL_BYTES);original=baseline.read(FULL_BYTES)
                if record[384:43584]!=original[384:43584]:repeat_input_changes+=1
                if record[43584:43984]!=original[43584:43984]:repeat_score_changes+=1
                if record[43984:]!=original[43984:]:
                    repeat_pose_changes+=1
                    reference_pose=np.frombuffer(original,dtype='<f4',offset=43984)
                    reference_score=np.frombuffer(original,dtype='<f4',offset=43584,count=100)
                    distance=np.linalg.norm((poses.astype(np.float64)-reference_pose.astype(np.float64)).reshape(100,14,3),axis=-1)*1000
                    max_repeat_all_mm=max(max_repeat_all_mm,float(distance.max()))
                    mask=reference_score>np.float32(.2)
                    if mask.any():max_repeat_high_mm=max(max_repeat_high_mm,float(distance[mask].max()))
            if name in refs:
                inp,scores,poses=refs[name];actual_input=values[:10800];actual_score=values[10800:10900];actual_pose=values[10900:]
                input_equal=actual_input.tobytes()==inp.tobytes();score_equal=actual_score.tobytes()==scores.tobytes()
                selected=scores>np.float32(.2)
                delta=np.linalg.norm((actual_pose.astype(np.float64)-poses.astype(np.float64)).reshape(100,14,3),axis=-1)*1000
                maximum=float(delta[selected].max()) if selected.any() else None
                gate={'row':n,'sample':name,'input_bitwise':input_equal,'scores_bitwise':score_equal,
                      'checked_candidates':int(selected.sum()),'max_checked_joint_delta_mm':maximum,
                      'max_all_joint_delta_mm':float(delta.max()),'accepted':bool(input_equal and score_equal and (maximum is None or maximum<=3))}
                gates.append(gate)
                if not gate['accepted']:errors.append(gate)
            n+=1
    sent_rows.close()
    report={'records':n,'split_counts':splits,'unique_sources':len(first),'finite_and_identity_errors':errors,'frozen_reference_checks':gates,
            'repeat_consistency':{'comparisons':repeat_count,'input_bitwise_changes':repeat_input_changes,
                'score_bitwise_changes':repeat_score_changes,'pose_bitwise_changes':repeat_pose_changes,
                'max_all_joint_delta_mm':max_repeat_all_mm,'max_high_score_joint_delta_mm':max_repeat_high_mm,
                'scope':'Compared with first actual output of the same source; consistency, not accuracy reference'},
            'complete_actual_SHA256':digest.hexdigest(),'wire_archive_SHA256':full_digest.hexdigest(),
            'host_count_matches':n==summary['received'],'all_saved_before_compare':True,
            'numeric_scope':'Three frozen windows only; remaining samples finite/identity/selection verified, not a frozen-accuracy claim'}
    (a.run/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if errors or repeat_input_changes or repeat_score_changes or (summary['complete'] and not report['host_count_matches']):raise SystemExit(1)

if __name__=='__main__':main()

"""Analyze unmodified slots and possible vector permutations; no acceptance thresholds."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def metrics(actual,expected):
    assert actual.shape==expected.shape and np.isfinite(actual).all() and np.isfinite(expected).all()
    delta=actual.astype(np.float64)-expected.astype(np.float64);absolute=np.abs(delta)
    return dict(bit_mismatches=int(np.count_nonzero(actual.view('<u4')!=expected.view('<u4'))),max_abs=float(absolute.max()),mean_abs=float(absolute.mean()),RMS=float(np.sqrt(np.mean(delta*delta))),P95=float(np.percentile(absolute,95)),signed_zero_mismatches=int(np.count_nonzero((actual==0)&(expected==0)&(actual.view('<u4')!=expected.view('<u4')))))
def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();records=[]
    for directory in sorted((a.results/'presaved-results').iterdir(),key=lambda p:int(p.name)):
        identity=load(directory/'identity.json');assert identity['saved_before_gate'];name=identity['case']
        assert (directory/'raw-payload.bin').read_bytes()==(a.package/'inputs'/(name+'.csi')).read_bytes()[32:]
        actual={k:np.fromfile(directory/(k+'.f32'),dtype='<f4') for k in ('input','scores','poses')}
        expected={k:np.fromfile(a.package/('reference' if k=='input' else 'r6-reference')/(name+'.'+k+'.f32'),dtype='<f4') for k in actual}
        diff={k:metrics(actual[k],expected[k]) for k in actual}
        poses=actual['poses'].reshape(100,42);gold=expected['poses'].reshape(100,42)
        lookup={};matches=[]
        for i,row in enumerate(gold):lookup.setdefault(row.tobytes(),[]).append(i)
        for row in poses:matches.append(lookup.get(row.tobytes(),[]))
        unique=all(len(x)==1 for x in matches) and len({x[0] for x in matches if x})==100
        permutation=[x[0] for x in matches] if unique else None
        ai=int(np.argmax(actual['scores']));ei=int(np.argmax(expected['scores']));order=np.argsort(-expected['scores'],kind='stable')
        record=dict(identity=identity,differences=diff,actual_best=ai,reference_best=ei,reference_top_gap=float(expected['scores'][order[0]]-expected['scores'][order[1]]),best_pose_difference=metrics(poses[ai].copy(),gold[ei].copy()),exact_pose_row_matches=matches,unique_exact_pose_row_permutation=permutation,pose_permutation_supported=bool(unique and permutation!=list(range(100))),sorted_scores_bitwise_equal=np.sort(actual['scores']).tobytes()==np.sort(expected['scores']).tobytes(),candidate_query_identity_proven=False,fixed_point_truncation_cause_proven=False)
        records.append(record)
    assert records
    report=dict(status='saved_actual_data_analyzed_no_threshold_acceptance',frames=len(records),all_bitwise_reference=all(all(m['bit_mismatches']==0 for m in r['differences'].values()) for r in records),input_all_bitwise_reference=all(r['differences']['input']['bit_mismatches']==0 for r in records),original_slot_errors_preserved=True,units='model_original',records=records)
    a.output.write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in report.items() if k!='records'}))
    for r in records:
        if any(m['bit_mismatches'] for m in r['differences'].values()):print(json.dumps({k:v for k,v in r.items() if k!='exact_pose_row_matches'}))
if __name__=='__main__':main()

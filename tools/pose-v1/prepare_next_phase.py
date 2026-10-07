"""Review existing results and propose fixed cases; no inference, build or board access."""
import argparse
import json
import struct
from pathlib import Path
import numpy as np
from mixed_validation_gate import ROOT, verify, load, lines, save, sha

def prepare(output):
    if output.exists(): raise ValueError('Preserve existing preparation evidence')
    base=ROOT/'tools/pose-v1/evidence/mixed-20261006-frame-state-r6'
    board=base/'mixed-three'; reference=ROOT/'.local/pose-v1-mixed-validation/onnx-20261006'
    verify(board);verify(reference)
    accepted=load(base/'mixed-three.acceptance.json')
    assert accepted['stage']=='mixed-three' and accepted['binary_sha256']==sha(board/'pose_mixed_check')
    comparison=load(base/'onnx-comparison.json')
    timing=lines(board/'results/results.jsonl')+[load(board/'results/repeat-first.json')]
    preproc=load(ROOT/'tools/pose-v1/evidence/replay-300-summary.json')['preprocess_only_ms']['median']
    forward=float(np.median([r['forward_ms'] for r in timing]))
    case_metrics=[]
    for entry in comparison['cases']:
        name=entry['case']; scores={}
        for kind,directory in [('ONNX',reference),('board',board/'results')]:
            a=np.frombuffer((directory/(name+'.scores.f32')).read_bytes(),dtype='<f4')
            assert a.size==100 and np.isfinite(a).all()
            ordered=np.sort(a.astype(np.float64))[::-1]; gaps=ordered[:-1]-ordered[1:]
            scores[kind]=dict(top_score=float(ordered[0]),runner_up=float(ordered[1]),
                top_margin=float(ordered[0]-ordered[1]),adjacent_equal_score_pairs=int(np.count_nonzero(gaps==0)),
                median_adjacent_score_gap=float(np.median(gaps)),sorted_output=bool((a[:-1]>=a[1:]).all()))
        case_metrics.append(dict(case=name,score_order_diagnostics=scores,
            same_slot_scores=entry['scores'],same_slot_poses=entry['poses'],
            selected_best_coordinates=entry['selected_best_coordinates'],top_slot_changed=entry['top_slot_changed']))
    audit=dict(status='existing_evidence_reviewed_no_new_inference',cases=case_metrics,
        instrumented_budget=dict(observations=len(timing),forward_median_ms=forward,
            separate_preprocess_median_ms=preproc,indicative_sum_ms=forward+preproc,
            five_Hz_budget_ms=200.0,gap_to_200_ms=forward+preproc-200,
            indicative_rate_Hz=1000/(forward+preproc),
            limit='Instrumented few-frame run plus separately measured preprocess; not a sustained benchmark or hard performance ceiling'),
        candidate_identity_verified=False,numerical_tolerance_set=False,performance_accepted=False,
        sources={str(p.relative_to(ROOT)):sha(p) for p in [base/'mixed-three.acceptance.json',base/'onnx-comparison.json',
            ROOT/'tools/pose-v1/evidence/replay-300-summary.json']})
    output.mkdir(parents=True)
    save(output/'existing-evidence-analysis.json',audit)
    manifest_path=ROOT/'tools/pose-v1/evidence/replay-300-manifest.json'
    manifest=load(manifest_path);real=[r for r in manifest['cases'] if r['kind']=='real']
    assert len(real)==300
    fixtures=ROOT/'.local/pose-v1-validation/host-300-20261004/fixtures'
    groups={group:[r for r in real if r['case'].split('_')[0]==group] for group in sorted(manifest['group_counts'])}
    proposed=[]
    for group,items in groups.items():
        assert len(items)==manifest['group_counts'][group]['selected']
        for index in (0,(len(items)-1)//2,len(items)-1):
            r=items[index];raw=fixtures/(r['stem']+'.csi');ref=fixtures/(r['stem']+'.reference.f32')
            host=fixtures/(r['stem']+'.host.f32')
            assert sha(raw)==r['input_sha256'] and sha(ref)==r['reference_sha256']==sha(host)
            blob=raw.read_bytes();magic,version,payload,frame,stamp=struct.unpack('<8sIIQQ',blob[:32])
            assert magic==b'PIWCSI1\x00' and version==1 and payload==86400 and len(blob)==86432
            assert np.isfinite(np.frombuffer(ref.read_bytes(),dtype='<f4')).all() and ref.stat().st_size==43200
            proposed.append(dict(group=group,index_in_fixed_group=index,case=r['case'],stem=r['stem'],frame_id=frame,
                source_time_ns=stamp,raw_path=str(raw.relative_to(ROOT)).replace('\\','/'),
                reference_path=str(ref.relative_to(ROOT)).replace('\\','/'),raw_sha256=r['input_sha256'],
                reference_sha256=r['reference_sha256']))
    assert len(proposed)==27 and len({r['case'] for r in proposed})==27
    save(output/'proposed-27-cases.json',dict(status='proposed_selection_only_not_model_tested',
        policy='First, middle floor((n-1)/2), last of each fixed preprocessed group; nine groups x three',
        source_manifest_sha256=sha(manifest_path),cases=proposed,
        ONNX_executed=False,board_inference_executed=False,numerical_tolerance_set=False))
    (output/'proposed-27-cases.tsv').write_bytes(('group\tcase\tframe_id\tindex_in_fixed_group\n'+
        ''.join(f"{r['group']}\t{r['case']}\t{r['frame_id']}\t{r['index_in_fixed_group']}\n" for r in proposed)).encode())
    print(f'Existing evidence reviewed; {len(proposed)} proposed cases hash-checked. No new model or board execution.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    prepare(p.parse_args().output)

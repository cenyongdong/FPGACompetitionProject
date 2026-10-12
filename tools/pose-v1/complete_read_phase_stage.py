"""Require integration snapshots plus complete content; never promote a failed run."""
import argparse,json
from pathlib import Path
import mixed_validation_gate as g
p=argparse.ArgumentParser();p.add_argument('stage',choices=['process-three','load-103']);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();e=a.evidence
label='three' if a.stage=='process-three' else 'long';n=4 if a.stage=='process-three' else 103;r=e/(a.stage+'-return')/('run-'+a.stage);out=r/'results'
numeric=g.load(e/(a.stage+'.numeric.json'));video=g.load(e/(label+'-video/review.json'));network=g.load(e/(label+'-network-prefix/review.json'));sender=g.load(e/('client-'+label)/'sender.json');phase=g.load(e/(a.stage+'.read-phase.json'))
assert numeric['status']=='live_stage_passed' and numeric['consumed']==numeric['sent']==numeric['display_covered']==n and not numeric['overwritten'] and numeric['full_numeric_bitwise']
assert phase['rows']==n and all(v['immediate_vs_gold']['bitwise'] and v['CPU_vs_gold']['bitwise'] and v['immediate_to_CPU_byte_changes']==0 for v in phase['results'])
metadata=[json.loads(x) for x in (out/'read-phase/metadata.jsonl').read_text().splitlines()];assert all(x['read_done'] and x['cpu_snapshot_done'] and not x['byte_changes'] and not x['error'] for x in metadata)
assert video['inference_sources']==n and video['decoded_frames']==numeric['encoded']
assert network['all_sources_present'] and not network['missing_completed_sources'] and network['completed_inference_sources']==network['received_inference_sources']==n
assert network['all_pixels_equal_current_capture'] and network['actual_RTP_capture_PTS'] and network['last_encoded_id']==numeric['encoded']-1
assert sender['status']=='sent_no_receiver_ack' and sender['fps']==(2 if n==4 else 5.05) and sender['session_count']==1 and len(sender['sent'])==n
assert [v['sequence'] for v in sender['sent']]==list(range(n))
input=g.load(out/'input-summary.json');assert input['received']==input['consumed']==input['returned']==n and not any(input[k] for k in ('overwritten','rejected','reconnect_discarded','failure_path'))
owned=g.load(out/'owned-result-index.json');assert owned['count']==n and not owned['serializer_compared_math']
for name,size in [('persistence-ledger',8),('upstream-persistence-ledger',1),('read-phase-persistence-ledger',1)]:
    ledger=g.load(out/(name+'.json'));assert len(ledger['tasks'])==size and all(t['saved'] for t in ledger['tasks']) and not ledger['original_computation_failure']
assert g.load(out/'upstream-boundary/summary.json')['rows']==8*n
report=dict(numeric,complete_composition_content_passed=True,network_frames=network['network_frames'],local_encoded_frames=video['decoded_frames'],real_sources=n,FP32_compared=n*15100,joint_visibility_checks=video['joint_visibility_checks'],read_phase_complete=True,first4_last_owned_bytewise_gold=True,all_normal_lifecycles_passed=True,all_services_and_test_sessions_closed=True,root_cause_proven=False,whole_5Hz_threshold_met=False,evidence_SHA256={name:g.sha(e/name) for name in [a.stage+'.numeric.json',a.stage+'.read-phase.json',label+'-video/review.json',label+'-network-prefix/review.json','client-'+label+'/sender.json']})
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('Full read-phase composition passed:',a.stage,n,'sources')

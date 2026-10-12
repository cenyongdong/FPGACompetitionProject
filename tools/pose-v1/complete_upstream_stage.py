"""Promote content matching only with full sources and normal lifecycle evidence."""
import argparse,json
from pathlib import Path
import mixed_validation_gate as g
p=argparse.ArgumentParser();p.add_argument('stage',choices=['process-three','load-103']);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
e=g.ROOT/'tools/pose-v1/evidence/upstream-boundary-20261011-r4';label='three' if a.stage=='process-three' else 'long';n=4 if a.stage=='process-three' else 103;r=e/(a.stage+'-return')/('run-'+a.stage);out=r/'results'
numeric=g.load(e/(a.stage+'.numeric.json'));video=g.load(e/(label+'-video/review.json'));network=g.load(e/(label+'-network-prefix/review.json'));sender=g.load(e/('client-'+label)/'sender.json')
assert numeric['status']=='live_stage_passed' and numeric['consumed']==numeric['sent']==numeric['display_covered']==n and numeric['overwritten']==0 and numeric['full_numeric_bitwise']
assert video['inference_sources']==n and video['decoded_frames']==numeric['encoded']
assert network['all_sources_present'] and not network['missing_completed_sources'] and network['completed_inference_sources']==network['received_inference_sources']==n
assert network['all_pixels_equal_current_capture'] and network['actual_RTP_capture_PTS'] and network['last_encoded_id']==numeric['encoded']-1
assert sender['status']=='sent_no_receiver_ack' and sender['fps']==2 and sender['session_count']==1 and len(sender['sent'])==n
assert [v['sequence'] for v in sender['sent']]==list(range(n))
input=g.load(out/'input-summary.json');assert input['received']==input['consumed']==input['returned']==n and not any(input[k] for k in ('overwritten','rejected','reconnect_discarded','failure_path'))
owned=g.load(out/'owned-result-index.json');assert owned['count']==n and not owned['serializer_compared_math']
assert all(v['runtime_gate_completed'] for v in [json.loads(x) for x in (out/'inference.jsonl').read_text().splitlines()])
ledger=g.load(out/'persistence-ledger.json');assert len(ledger['tasks'])==8 and all(v['saved'] for v in ledger['tasks']) and not ledger['original_computation_failure']
for line in (r/'final.processes').read_text().splitlines()[1:]:
    assert len(line.split())<2 or not line.split()[1].startswith('pose_')
assert not any(port in (r/'final.ports').read_text() for port in (':39001 ',':8554 '))
assert (r/'exit.txt').read_text().strip()=='0' and (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
extra=g.load(out/'upstream-persistence-ledger.json');assert len(extra['tasks'])==1 and all(x['saved'] for x in extra['tasks']) and not extra['original_computation_failure']
boundary=g.load(e/(a.stage+'.boundary.json'));assert boundary['rows']==8*n and boundary['invocations']==n
assert all(all(v[key]['bitwise_equal'] for key in ['Gather_from_observed_retained_pre','producer_data_to_pre','TopK_indices_to_pre','Gather_post_to_ZG_pre']) for v in boundary['frames'])
refs=[a.stage+'.numeric.json',label+'-video/review.json',label+'-network-prefix/review.json','client-'+label+'/review.json','client-'+label+'/sender.json']
report=dict(numeric,complete_composition_content_passed=True,network_frames=network['network_frames'],local_encoded_frames=video['decoded_frames'],real_sources=n,FP32_compared=n*15100,joint_visibility_checks=video['joint_visibility_checks'],full_numeric_bitwise=True,full_network_byte_PTS_pixel_source_match=True,normal_drain_and_reaping=True,all_eight_original_and_one_boundary_tasks_saved=True,all_services_and_test_sessions_closed=True,content_matcher_scope='Existing prefix matcher reused for exact NAL/PTS/pixels; this independent gate additionally requires every source, normal completion and final capture tail.',evidence_SHA256={f:g.sha(e/f) for f in refs},root_cause_proven=False,whole_5Hz_threshold_met=False)
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('Complete composition gate passed',a.stage,n,'sources',network['network_frames'],'network frames')

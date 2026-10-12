"""Bind first owned fingerprints to first/late bytes; no repair or device."""
from pathlib import Path
import json
import numpy as np

R = Path(__file__).resolve().parents[2]
E = R/'tools/pose-v1/evidence/producer-prepared-20261011-r1'
P = E/'on-return/run-on/results'
f = json.loads((E/'on.failure-review.json').read_text())
assert f['failed_invocation'] == 94
d = P/'call-94'; trace = json.loads((d/'trace.json').read_text())
refs = R/'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns'
def fingerprint(data):
    h = 14695981039346656037
    for byte in data: h = ((h ^ byte)*1099511628211)&((1<<64)-1)
    return h
for i,v in enumerate((4386,4390)):
    assert fingerprint((d/f'output-{v}.f32').read_bytes()) == trace['reads'][i]['owned_fingerprint']
for row in f['late_sources']:
    assert fingerprint((d/'late-source'/f"round-{row['round']}-{row['value']}.f32").read_bytes()) == row['owned_fingerprint']
a = np.fromfile(d/'output-4386.f32',dtype='<u4')
b = np.fromfile(refs/'pattern-0/output-4386.f32',dtype='<u4')
previous = np.fromfile(refs/'pattern-1/output-4386.f32',dtype='<u4')
assert (b != previous).all()
bad = np.flatnonzero(a != b); assert len(bad) == 96 and (a[bad] == previous[bad]).all()
runs = f['first_outputs']['4386']['runs']
assert all(y-x == 64 and x%256 == 0 for x,y in runs)
assert [x for x,y in runs] == list(range(28672,29953,256))
report = {'status':'first_owned_fingerprints_and_all_four_late_reads_verified',
          'failed_invocation':94,'current_pattern':0,'previous_pattern':1,
          'data_changed':96,'index_changed':0,
          'all_changed_match_previous_reference_same_offset':True,
          'all_A_B_reference_data_values_differ':True,'runs_bytes':runs,
          'runs_physical_hex':[[hex(trace['reads'][0]['source_address']+x),hex(trace['reads'][0]['source_address']+y)] for x,y in runs],
          'run_size_bytes':64,'run_stride_bytes':256,
          'first_owned_fingerprint_matches_saved_file':True,'fingerprint_computed_after_save':True,
          'late_owned_fingerprints_match_saved_files':True,
          'first_correct_late_read_after_first_copy_end_ms':(f['late_sources'][0]['read_begin_ns']-trace['reads'][0]['copy_end_ns'])/1e6,
          'first_correct_late_read_after_first_owned_end_ms':(f['late_sources'][0]['read_begin_ns']-trace['reads'][0]['owned_end_ns'])/1e6,
          'forward_us':(trace['forward_return_ns']-trace['forward_begin_ns'])/1000,
          'initial_copy_us':[(x['copy_end_ns']-x['copy_begin_ns'])/1000 for x in trace['reads']],
          'no_source_handle_reopen':True,'root_cause_resolved':False,
          'interpretation':'First owned bytes and wrong file have matching fingerprints, recorded after save. Application save does not rewrite owned bytes, supporting first-copy anomaly; no immediate pre-save sample. Later source reads recover; producer versus SDK/DMA/cache/Host responsibility remains unproven.'}
(E/'on.fingerprint-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('First owned fingerprints and all late sources independently bound; DATA96 remains failure')

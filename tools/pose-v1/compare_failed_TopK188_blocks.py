"""Compare captured exception bytes to an accepted same-CSI bridge input."""
from pathlib import Path
import json,hashlib
import numpy as np
import mixed_validation_gate as old
root=old.ROOT;e=root/'tools/pose-v1/evidence/forward-trace-20261009-r3'
actual=e/'process-three/results/failed-host-inputs/input0.f32'
gold=root/'tools/pose-v1/evidence/mixed-20261006-frame-state-r6/mixed-one/results/content/call0.bridge_input.op188.slot0.f32'
assert old.load(e/'process-three/results/failed-host-inputs/failure.json')['op_id']==188
old.verify(root/'tools/pose-v1/evidence/mixed-20261006-frame-state-r6/mixed-one')
va=np.frombuffer(actual.read_bytes(),'<f4');vb=np.frombuffer(gold.read_bytes(),'<f4');a=va.view('<u4');b=vb.view('<u4');assert len(a)==len(b)==180
bad=np.flatnonzero(a!=b);expected=np.concatenate([np.arange(0,32),np.arange(64,96),np.arange(128,160)])
assert np.array_equal(bad,expected) and np.isfinite(vb).all()
assert np.flatnonzero(~np.isfinite(va)).tolist()==[11] and int(a[11])==0xffffffff
assert all(a[i]==0 for i in bad if i!=11)
sender=old.load(e/'client-three/sender.json');assert sender['sent'][0]['case']=='S11_01_308'
report=dict(status='same_CSI_prior_bridge_input_block_comparison',actual_sha256=old.sha(actual),reference_sha256=old.sha(gold),reference_scope='Accepted r6 mixed-one 308 bridge input; historical, without simultaneous VPU',changed_FP32=96,unchanged_FP32=84,changed_byte_ranges=[[0,128],[256,384],[512,640]],byte_ranges_half_open=True,unchanged_tail_bytes=[640,720],changed_values_zero=95,NaN_flat_index=11,NaN_bits='0xffffffff',source_transport=100000,CSI_case='S11_01_308',pattern_explained_by_small_arithmetic_roundoff=False,cache_DMA_or_writer_root_cause_proven=False,independent_source_device_read_performed=False)
(e/'TopK188-block-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

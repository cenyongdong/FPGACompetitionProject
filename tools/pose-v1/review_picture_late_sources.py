"""Compare both late device reads with frozen same-CSI intermediate references."""
import json
import numpy as np
import mixed_validation_gate as g
e=g.ROOT/'tools/pose-v1/evidence/picture-20261010-r1';out=e/'picture-return/run-picture/results';host=g.load(e/'failure-host-comparison.json');reads=g.load(out/'failed-host-inputs/source-readback/readback.json')
assert reads['rounds']==2 and reads['single_round_bytes']==47040 and reads['method']=='Tensor::read' and not reads['explicit_wait_or_reset'] and not reads['direct_device_dereference']
records=[]
for source in reads['sources']:
    slot=source['slot'];record=next(x for x in host['records'] if x['op_id']==192 and x['slot']==slot);gold=(g.ROOT/record['golden_path']).read_bytes();staged=(out/'failed-host-inputs'/f'input{slot}.f32').read_bytes();assert source['device'] and source['pointer']=='ADDR' and source['address']==[109232128,109285376][slot]
    for rr in source['reads']:
        data=(out/'failed-host-inputs/source-readback'/rr['file']).read_bytes();assert len(data)==len(gold)==source['bytes'] and rr['begin_ns']<=rr['end_ns'] and data==gold and np.isfinite(np.frombuffer(data,'<f4')).all()
        records.append(dict(slot=slot,round=rr['round'],bytes=len(data),late_source_bitwise_gold=True,equal_failed_Host=data==staged,SHA256=g.sha(out/'failed-host-inputs/source-readback'/rr['file']),begin_ns=rr['begin_ns'],end_ns=rr['end_ns']))
report=dict(status='both_late_PLDDR_source_reads_correct_failed_Host_index_not_correct',case=host['case'],invocation=20,source_addresses=[109232128,109285376],device_source_read_bytes=94080,records=records,late_read_does_not_prove_copy_time_correct=True,root_cause_proven=False)
p=e/'failure-late-sources.json';assert not p.exists();p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(report['status'],94080)

"""Static readiness boundaries; no model execution or inferred DMA fence."""
import json
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT;out=root/'tools/pose-v1/evidence/startup-guard-20261009-r1/Host-producer-dependency-review.json';assert not out.exists()
model=g.load(root/'.local/pose-v1-stage-guard/package-20261009-r1/graph/piw24_ZG.json');fusion=g.load(root/'tools/pose-v1/mixed-fusion-baseline.json')
ops={x['op_id']:x for x in model['ops']};prod={v['v_id']:x['op_id'] for x in model['ops'] for v in x['outputs']};groups={i:x for x in fusion['groups'] for i in x['members']};cache={};visiting=set()
def ancestors(oid):
    if oid in cache:return cache[oid]
    assert oid not in visiting;visiting.add(oid);result=set()
    for value in ops[oid]['inputs']:
        previous=prod.get(value['v_id'])
        if previous is not None:result.add(previous);result.update(ancestors(previous))
    visiting.remove(oid);cache[oid]=result;return result
rows=[]
for oid in (188,192,437,442,582,649):
    for slot,value in enumerate(v for v in ops[oid]['inputs'] if v['_type_key']!='icraft::xir::Params'):
        source=prod.get(value['v_id']);group=groups.get(source)
        if group:
            safe=all(oid not in ancestors(member) for member in group['members'])
            rows.append(dict(host_op=oid,slot=slot,value=value['v_id'],producer=source,group=group['effective_op_id'],group_end=group['sync_index']+group['layer_count'],group_no_current_Host_ancestor=safe,currently_fresh_checked=oid==582))
        else:rows.append(dict(host_op=oid,slot=slot,value=value['v_id'],producer=source,group=None,group_end=None,Host_producer_not_a_new_NPU_wait=True))
assert all(x['group_no_current_Host_ancestor'] for x in rows if x['group'] is not None)
report=dict(status='six_Host_static_producers_no_wait_cycle_checked_not_runtime_completion_proof',model_sha256=g.sha(root/'.local/pose-v1-stage-guard/package-20261009-r1/graph/piw24_ZG.json'),rows=rows,original_Gather_registration_unchanged=True,DMA_cache_fence_proven=False)
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(report['status'])

import json,sys
from pathlib import Path
import torch
ROOT=Path('/public/cyd/Person-in-WiFi-3D-repo')
sys.path.insert(0,str(ROOT))
from opera.models.transfer_support import load_checkpoint_cpu
OUT=ROOT/'result/tpami2026_scratch_20261004'
ck=load_checkpoint_cpu(OUT/'smoke/epoch_1.pth')
checks=[json.loads(x) for x in (OUT/'smoke/epoch_parameter_checks.jsonl').read_text().splitlines()]
diag=[json.loads(x) for x in (OUT/'smoke/branch_diagnostics.jsonl').read_text().splitlines()]
init=json.loads((OUT/'smoke/initialization.json').read_text())
assert len(checks)==1 and checks[0]['ddp_equal']
assert ck['meta']['epoch']==1 and ck['meta']['iter']==3
assert all(torch.isfinite(v).all() for v in ck['state_dict'].values())
assert len(ck['optimizer']['param_groups'])==1
assert all(g['lr']==2e-5 and g['weight_decay']==1e-4 for g in ck['optimizer']['param_groups'])
assert all(float(v['step'])==3 for v in ck['optimizer']['state'].values())
assert init['checkpoint_loaded'] is False and init['optimizer_restored'] is False
report={'passed':True,'world_size':4,'per_rank_batch':8,'global_batch':32,'samples':96,'steps':3,'all_checkpoint_tensors_finite':True,'optimizer':'Adam','optimizer_lr':2e-5,'weight_decay':1e-4,'no_weight_decay_exclusions':True,'ddp_checks':checks,'initial_parameter_l2':init['module_parameter_l2'],'checkpoint_epoch':1,'checkpoint_iter':3,'short_updates_used_for_formal':False,'diagnostics':diag}
(OUT/'gates/ddp_gate.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='diagnostics'}))

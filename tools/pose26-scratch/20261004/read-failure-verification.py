import datetime,hashlib,json,sys
from pathlib import Path
import torch
ROOT=Path('/public/cyd/Person-in-WiFi-3D-repo')
OUT=ROOT/'result/tpami2026_scratch_20261004'
sys.path.insert(0,str(ROOT))
from opera.models.transfer_support import load_checkpoint_cpu
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(2**20),b''): h.update(block)
 return h.hexdigest()
p=OUT/'best_mpjpe_epoch_4.pth'
before=p.stat()
ck=load_checkpoint_cpu(p)
checkpoint_hash=sha(p)
after=p.stat()
assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
assert ck['meta']['epoch']==4
assert all(torch.isfinite(v).all() for v in ck['state_dict'].values())
audit=json.loads((OUT/'prelaunch-audit.json').read_text())
differences=[name for name,expected in audit['source_hashes'].items() if not (ROOT/name).exists() or sha(ROOT/name)!=expected or sha(OUT/'source_snapshot'/name)!=expected]
assert not differences,differences
report={'checked_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'best_checkpoint':str(p),'best_checkpoint_bytes':p.stat().st_size,'best_checkpoint_sha256':checkpoint_hash,'best_checkpoint_epoch':ck['meta']['epoch'],'best_checkpoint_iter':ck['meta']['iter'],'best_checkpoint_tensors_finite':True,'optimizer_lr':[g['lr'] for g in ck['optimizer']['param_groups']],'optimizer_weight_decay':[g['weight_decay'] for g in ck['optimizer']['param_groups']],'source_snapshot_hashes_verified':len(audit['source_hashes']),'config_sha256_verified':sha(OUT/'resolved_config.py')==audit['config_sha256'],'expected_processes_alive':{str(pid):Path(f'/proc/{pid}').exists() for pid in (54209,54220,54225,54226,54227,54228)},'final_report_exists':(OUT/'final-report.json').exists()}
print(json.dumps(report))

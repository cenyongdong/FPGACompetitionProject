import datetime,json,re,subprocess
from pathlib import Path
OUT=Path('/public/cyd/Person-in-WiFi-3D-repo/result/tpami2026_diff_nodecay_20261004')
def rows(name):
 p=OUT/name
 return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
evals=rows('evaluations.jsonl')
checks=rows('epoch_parameter_checks.jsonl')
diag=rows('branch_diagnostics.jsonl')
text=(OUT/'train.stdout.log').read_text(errors='replace')
logs=re.findall(r'[^\r\n]*Epoch \[\d+\]\[\d+/2811\][^\r\n]*',text)
error_lines=[x for x in text.splitlines() if any(k in x for k in ('Traceback','RuntimeError','AssertionError','Persistent branch collapse','Non-finite','DDP parameter divergence','ChildFailedError'))]
files=[{'name':p.name,'bytes':p.stat().st_size,'mtime':p.stat().st_mtime} for p in OUT.iterdir() if p.is_file()]
best=min(evals,key=lambda x:x['metrics']['mpjpe']) if evals else None
record={'checked_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'pipeline_status':json.loads((OUT/'pipeline-status.json').read_text()),'completed_evaluations':len(evals),'evaluations':evals,'epoch_parameter_checks':checks,'initialization':json.loads((OUT/'initialization.json').read_text()),'diagnostic_count':len(diag),'first_diagnostic':diag[0] if diag else None,'latest_diagnostic':diag[-1] if diag else None,'diagnostic_epoch_ends':[{**next(x for x in reversed(diag) if x['epoch']==e)} for e in sorted(set(x['epoch'] for x in diag))],'last_training_lines':logs[-4:],'error_lines':error_lines[-30:],'log_tail':text.splitlines()[-45:],'files':files,'best_evaluation':best,'latest_evaluation':evals[-1] if evals else None}
print(json.dumps(record))

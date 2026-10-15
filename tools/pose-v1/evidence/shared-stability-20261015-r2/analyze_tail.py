"""Read-only latency tail diagnosis; no discarded frames or root-cause assumption."""
from pathlib import Path
import json
import numpy as np
E=Path(__file__).resolve().parent;run=E/'returned-stress/run-stress'
f=[json.loads(s) for s in (run/'results/frames.jsonl').read_text().splitlines() if s]
r=[json.loads(s) for s in (run/'resources.jsonl').read_text().splitlines() if s]
a=np.array([v['process_ms'] for v in f])
top=[]
for i in np.argsort(a)[-20:][::-1]:
 row=dict(f[int(i)])
 near=min((v for v in r if v.get('completed',-1)>=0),key=lambda v:abs(v['completed']-int(i)))
 row['nearest_resource_sample']=dict(completed=near['completed'],inference_elapsed_s=near['inference_elapsed_s'],
  CmaFree_KiB=near['meminfo_kb']['CmaFree'],MemAvailable_KiB=near['meminfo_kb']['MemAvailable'],
  Dirty_KiB=near['meminfo_kb']['Dirty'],RSS_KiB=near['status_kb']['VmRSS'])
 row['resource_sample_is_coarse_not_exact_invocation']=True
 top.append(row)
def vm(p):return dict((k,int(v)) for k,v in (line.split() for line in p.read_text().splitlines()))
b,z=vm(run/'before.vmstat'),vm(run/'after.vmstat')
d={k:z[k]-b[k] for k in b if k.startswith(('compact_','allocstall','pgscan_','pgsteal_','pswp','pgmajfault','nr_dirty'))}
report=dict(inferences=len(f),percentiles_ms={str(p):float(np.percentile(a,p)) for p in (50,95,99,99.9,99.99,100)},
 count_strictly_over_ms={str(v):int(np.count_nonzero(a>v)) for v in (50,100,1000)},
 top20=top,system_vmstat_delta=d,
 conclusion='Numeric/memory/crash budget passed; multi-second latency spikes exist. No hard real-time or worst-case latency pass is claimed.',
 cause='Unknown. Forward wall time includes SDK callbacks and waits; sparse resource and aggregate vmstat cannot locate the cause. No new inference or diagnostic load was started.')
(E/'latency-tail-analysis.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='top20'},indent=2));print('Top3:',json.dumps(top[:3],indent=2))

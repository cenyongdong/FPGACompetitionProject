"""Preliminary memory-only review; full SHA/numerical audit is separate."""
from pathlib import Path
import json
import numpy as np
E=Path(__file__).resolve().parent
r=[json.loads(s) for s in (E/'stress-resources-preview.jsonl').read_text().splitlines() if s]
s=[v for v in r if v.get('inference_elapsed_s') is not None and v['inference_elapsed_s']>=30]
report={'preliminary_memory_only':True,'samples':len(r),'steady_samples':len(s)}
t=np.array([v['monotonic_s'] for v in s]);t-=t[0]
for name,src,key in [('RSS','status_kb','VmRSS'),('PSS','smaps_kb','Pss'),('Private_Dirty','smaps_kb','Private_Dirty'),('VmData','status_kb','VmData'),('VmSize','status_kb','VmSize')]:
 a=np.array([v[src][key] for v in s],dtype=float)
 report[name]={'first_KiB':float(np.median(a[:5])),'last_KiB':float(np.median(a[-5:])),'range_KiB':[float(a.min()),float(a.max())],'slope_KiB_per_minute':float(np.polyfit(t,a,1)[0]*60)}
for key,src in [('fd_count',None),('Threads','status_kb'),('map_count',None)]:
 a=[v[src][key] if src else v[key] for v in s];report[key]={'min':min(a),'max':max(a)}
(E/'stress-memory-preview.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))

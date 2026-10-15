"""Standalone scientific evidence plots, generated only after complete return."""
from pathlib import Path
import json,os
E=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(E/'mpl-config')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
run=E/'returned-stress/run-stress'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
assert load(E/'stress-analysis.json')['exit']==0
r=[json.loads(s) for s in (run/'resources.jsonl').read_text().splitlines() if s]
first=next(v for v in r if v.get('inference_elapsed_s') is not None)
initialized=first['elapsed_s']-first['inference_elapsed_s']
x=np.array([(v['elapsed_s']-initialized)/60 for v in r])
fig,axes=plt.subplots(2,1,figsize=(10,6.8),sharex=True,constrained_layout=True)
for label,src,key,color in [('RSS','status_kb','VmRSS','#1768ac'),('PSS','smaps_kb','Pss','#ed8b23'),
                            ('Private dirty','smaps_kb','Private_Dirty','#33845b')]:
    y=np.array([v[src].get(key,np.nan) for v in r])/1024
    axes[0].plot(x,y,label=label,color=color,linewidth=1.4)
axes[0].set_ylabel('Process memory (MiB)');axes[0].legend(ncol=3,loc='lower right')
axes[0].set_title('Shared-refinement FP16: 30-minute serial inference test (2026-10-15)')
for label,key,color in [('MemAvailable','MemAvailable','#1768ac'),('File cache','Cached','#7b4fa1'),('CMA free','CmaFree','#33845b')]:
    axes[1].plot(x,[v['meminfo_kb'].get(key,np.nan)/1024 for v in r],label=label,color=color,linewidth=1.2)
axes[1].set_ylabel('System memory (MiB)');axes[1].set_xlabel('Inference elapsed (minutes); negative = initialization')
axes[1].legend(ncol=3,loc='best')
for ax in axes:
    ax.axvline(0,color='#555',linewidth=.8);ax.grid(alpha=.22)
    if x.min()<0:ax.axvspan(x.min(),0,color='#ddd',alpha=.6)
fig.savefig(E/'memory.png',dpi=170);plt.close(fig)
frames=[json.loads(s) for s in (run/'results/frames.jsonl').read_text().splitlines() if s]
chunks=[]
for i in range(0,len(frames),1000):
    values=np.array([v['process_ms'] for v in frames[i:i+1000]])
    chunks.append((i+len(values)/2,float(values.mean()),float(np.percentile(values,95)),float(values.max())))
a=np.array(chunks)
fig,ax=plt.subplots(figsize=(10,3.6),constrained_layout=True)
for col,name,color in [(1,'Mean','#1768ac'),(2,'P95','#ed8b23'),(3,'Maximum','#b73e42')]:
    ax.plot(a[:,0],a[:,col],label=name,color=color,linewidth=1.3)
ax.set_xlabel('Inference index (blocks of up to 1,000 calls)');ax.set_ylabel('Engine process time (ms)')
ax.set_title('Engine latency; save/compare time excluded; no frame trimming')
ax.grid(alpha=.22);ax.legend(ncol=3);fig.savefig(E/'latency.png',dpi=170);plt.close(fig)
print('memory.png and latency.png saved')

"""Reproduce the retained r11/r12 subsets locally. Never opens a device or network."""
from pathlib import Path
import argparse,subprocess,json
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--binary',required=True);p.add_argument('--output',required=True);a=p.parse_args()
out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
for name,folder in [('r11',ROOT/'.local/pose180-top3-20261025-r11/evidence/pipeline/run'),('r12',ROOT/'.local/pose180-top3-pc-20261025-r12/pc-archive')]:
 files=sorted(folder.glob('recent-*.full'))
 if not files:raise RuntimeError('Retained source absent: '+str(folder))
 with (out/(name+'-replay.ndjson')).open('wb') as records,(out/(name+'-summary.json')).open('wb') as summary:
  result=subprocess.run([a.binary,*map(str,files)],stdout=records,stderr=summary)
 if result.returncode:raise RuntimeError(name+' replay failed; see summary')
 print(name,json.loads((out/(name+'-summary.json')).read_text()),flush=True)

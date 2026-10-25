"""Read current timing records only; never initialize a device or run inference."""
import json
from pathlib import Path
import statistics
import sys
import time

root=Path(sys.argv[1])
rows=[]
for line in (root/'results/frames.jsonl').read_bytes().splitlines():
    try:rows.append(json.loads(line))
    except ValueError:pass  # Last writer record may still be incomplete.
warm=rows[100:]

def summary(values):
    values=sorted(values);n=len(values)
    def q(p):
        x=(n-1)*p;i=int(x);j=min(i+1,n-1)
        return values[i]+(values[j]-values[i])*(x-i)
    return dict(samples=n,mean=statistics.mean(values),median=q(.5),p95=q(.95),p99=q(.99),
                max=max(values),min=min(values),over_33_333ms=sum(x>1000/30 for x in values))

progress=None
for _ in range(3):
    try:
        progress=json.loads((root/'results/progress.json').read_text())
        break
    except (ValueError,FileNotFoundError):time.sleep(.02)
report=dict(new_SDK_load=False,snapshot_saved_calls=len(rows),progress=progress,warmup_excluded=100,
            process_ms=summary([r['process_ms'] for r in warm]),forward_ms=summary([r['forward_ms'] for r in warm]),
            initialization=json.loads((root/'results/initialized.json').read_text()),
            definition='process includes input write/status reset/forward/completion wait/output SFB read; excludes CSI preprocessing, output archive and comparison; forward alone is not completed inference')
(root/'timing-snapshot-r2.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)

"""Read-only bounded monitoring; no SDK/device access or whole-log scans."""
from pathlib import Path
import json, time
base=Path(__file__).resolve().parent
def tail(p, count=16384):
    if not p.exists():return ''
    with p.open('rb') as f:
        f.seek(max(0,p.stat().st_size-count));return f.read(count).decode(errors='replace')
def last_json(p):
    for line in reversed(tail(p).splitlines()):
        try:return json.loads(line)
        except (ValueError,TypeError):pass
    return None
meta=base/'metadata';run=base/'software/run-long-native'
issued=json.loads((meta/'long-controller-issued.json').read_text())
row=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
         controller_pid=issued['pid'],controller_alive=Path('/proc',str(issued['pid'])).exists(),
         controller=last_json(base/'long-controller.stdout.log'),
         controller_stderr=tail(base/'long-controller.stderr.log',2000),
         native_stderr=tail(run/'stderr.txt',2000),resources=last_json(run/'resources.jsonl'))
events=[]
for line in tail(run/'results/hdmi.jsonl').splitlines():
    try:events.append(json.loads(line))
    except ValueError:pass
row['HDMI_recent']=[x for x in events if x.get('event') in ('adopted','stop_proved','frames_released_after_stop')][-3:]
if (meta/'long-controller-finished.json').exists():
    row['finished']=json.loads((meta/'long-controller-finished.json').read_text())
    if (meta/'long-test.json').exists():row['result']=json.loads((meta/'long-test.json').read_text())
print(json.dumps(row),flush=True)

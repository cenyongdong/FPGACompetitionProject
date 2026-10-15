"""Finite read-only host monitor. Never launches/retries inference or changes budget."""
from pathlib import Path
import json,subprocess,sys,time
E=Path(__file__).resolve().parent
start=time.monotonic()
for sequence in range(3,63):
    if time.monotonic()-start>2000:raise SystemExit('Host monitoring budget ended; inspect owned controller')
    name='poll-'+str(sequence).zfill(3)+'.txt'
    result=subprocess.run([sys.executable,str(E/'control_stress.py'),'poll',name],capture_output=True,timeout=45)
    (E/(name+'.console')).write_bytes(result.stdout+result.stderr)
    if result.returncode:
        print(json.dumps(dict(status='poll_failed',sequence=sequence,exit=result.returncode)),flush=True);raise SystemExit(1)
    d=json.loads((E/name).read_text(encoding='utf-8'));r=d.get('latest_resource') or {};p=d.get('progress') or {}
    summary=dict(sequence=sequence,running=d['controller_running'],elapsed_seconds=round(p.get('elapsed_ms',0)/1000,1),
        completed=p.get('completed'),RSS_KiB=r.get('status_kb',{}).get('VmRSS'),PSS_KiB=r.get('smaps_kb',{}).get('Pss'),
        fd=r.get('fd_count'),threads=r.get('status_kb',{}).get('Threads'),
        MemAvailable_KiB=r.get('meminfo_kb',{}).get('MemAvailable'),exit=d.get('exit'),evidence_complete=d['evidence_complete'],
        error=d.get('failure') or d.get('monitor_failure'))
    (E/'latest-poll-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary),flush=True)
    if not d['controller_running']:
        raise SystemExit(0 if d['exit']==0 and d['evidence_complete'] else 2)
    time.sleep(43)
raise SystemExit('Host poll-count budget exhausted')

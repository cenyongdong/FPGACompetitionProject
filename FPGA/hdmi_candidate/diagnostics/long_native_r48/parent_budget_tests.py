"""Only ordinary files and mocked audit/Popen; no board, SDK or BOOT."""
from pathlib import Path
import importlib.util,json,uuid
from types import SimpleNamespace
W=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r48_offline_parent',W/'ps_release_board.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
root=W/('offline-budget-'+uuid.uuid4().hex);root.mkdir();p.META=root
actions=[]
p.b=SimpleNamespace(audit=lambda value:actions.append(('audit',value)),boot_id=lambda:'offline-original')
p.subprocess.Popen=lambda *a,**kw:(actions.append(('reboot',a,kw)) or SimpleNamespace(pid=123))
results=[]
for stage in ('candidate-reboot','fallback-reboot'):
    p.reboot(stage,'offline-digest')
    before=sum(a[0]=='reboot' for a in actions)
    try:p.reboot(stage,'offline-digest')
    except FileExistsError:pass
    else:raise AssertionError('Repeated reboot accepted')
    assert sum(a[0]=='reboot' for a in actions)==before
    results.append(dict(case=stage+'_one_shot',passed=True))
p.reserve('long-test',SDK_Open=1)
try:p.reserve('long-test',SDK_Open=1)
except FileExistsError:pass
else:raise AssertionError('Second SDK attempt accepted')
results.append(dict(case='one_SDK_reservation',passed=True))
report=dict(offline_only=True,SDK=0,BOOT=0,actual_reboots=0,total=3,passed=3,results=results)
(W/'parent-budget-tests.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
print('OFFLINE_BUDGET_TESTS 3/3; no actual actions')

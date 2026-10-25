from pathlib import Path
import json,re,shutil
W=Path(__file__).resolve().parent;O=Path('D:/FPGACompetitionProject');old=O/'.local/ai-hdmi-drain-joint-20261024-r39'
for name in ('source','frame-source'):
    shutil.copytree(old/name,W/name,ignore=shutil.ignore_patterns('build','__pycache__'))
    p=W/name/('display/r9_startup_observer.hpp' if name=='source' else 'r9_startup_observer.hpp')
    s=p.read_text();assert 'initial<=18' in s;p.write_bytes(s.replace('initial<=18','initial<=20').encode())
    p=W/name/('board/main.cpp' if name=='source' else 'frame_probe.cpp')
    s=p.read_text();changes=[]
    def shift(match):
        n=int(match[2]);changes.append(dict(phase=match[1],before=n,after=n+2))
        return 'observer.epoch("'+match[1]+'",'+str(n+2)+','
    s=re.sub(r'observer\.epoch\("([^"]+)",(\d+),',shift,s)
    assert len(changes)==(4 if name=='source' else 5)
    p.write_bytes(s.encode())
    (W/(name+'-diagnostic-epochs.json')).write_text(json.dumps(changes,indent=2)+'\n')
    # Exact r40 command timing instrumentation; 200ms and predicate unchanged.
    shutil.copyfile(old/'next-diagnostic/hdmi_output.cpp',W/name/('display/hdmi_output.cpp' if name=='source' else 'hdmi_output.cpp'))
print('Software source ready: only diagnostic epoch +2 and accepted initial <=20; exact r40 timing code reused. No build or SDK load.')

from pathlib import Path
import json,shlex,subprocess,sys
W=Path(__file__).resolve().parent
BASE='/root/hp2-mmio32-20261024-r46'
record=dict(valid=True,passed=False,boot_id='ca5ae553-4b37-4daf-b30c-84746f081176',
    user_first_reply='短暂出现四色图后直接黑屏了',
    user_timing_clarification='图案仅闪现或几秒内就黑屏',
    classification='physical_display_failure',joint_test_cancelled=True,
    no_SDK_or_functional_retry=True,SDK_Open_actual=1,
    error='User observed only a brief/few-second pattern before black, distinct from the planned 8s per pattern then STOP.')
code="import sys;sys.path.insert(0,"+repr(BASE)+");import ps_release_board as p;p.authorize();p.bind(1);r="+repr(record)+";p.save(p.ROOT_META/'physical-screen-observation.json',r);p.mark_stopped('physical-screen-observation',1,r);print('Display failure retained; no joint/SDK retry; original fallback only.')"
subprocess.run([sys.executable,str(W/'board_call.py'),'physical-display-failure-saved','ssh','python3 -c '+shlex.quote(code),'--timeout','30'],check=True)
E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hp2-mmio32-20261024-r46')
(E/'physical-screen-observation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

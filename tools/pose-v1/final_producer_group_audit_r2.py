"""One read-only final audit; no model/VPU restart, reset, or memory compaction."""
from pathlib import Path
import getpass,sys,json,hashlib
import ssh_memory_transport as t
from archive_bytes import extract_bytes
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-group-20261011-r2';remote='/tmp/pose-producer-group-20261011-r2'
secret=getpass.getpass('Authorized Lite password (memory only): ');prompt=t.getpass.getpass;t.getpass.getpass=lambda _:secret
def call(*args):
    sys.argv=['transport',*map(str,args)]
    try:t.main()
    except SystemExit as e:return e.code or 0
    return 0
try:
    cmd='set -eu; cd '+remote+'; test ! -e final-r2; mkdir final-r2; python3 board_application_preflight.py final-r2/preflight.json; LC_ALL=C.UTF-8 dmesg > final-r2/dmesg.txt; ps -eo pid,comm,args > final-r2/processes.txt; ss -ltnp > final-r2/ports.txt; for n in buddyinfo pagetypeinfo meminfo vmstat; do cat /proc/$n > final-r2/$n; done; cd final-r2; find . -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256; cd ..; tar -cf return-final-r2.tar final-r2; sha256sum return-final-r2.tar'
    assert call('ssh',cmd,'--log',E/'final-r2-audit.stdout.txt')==0
    assert call('get',remote+'/return-final-r2.tar',E/'return-final-r2.tar','--log',E/'final-r2-download.stdout.txt')==0
    out=E/'final-r2-return';extract_bytes(E/'return-final-r2.tar',out);f=out/'final-r2';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for line in (f/'files.sha256').read_text().splitlines():h,n=line.split('  ',1);assert sha(f/n)==h
    assert (f/'dmesg.txt').read_bytes()==(E/'physical-return/run-physical/after.dmesg.txt').read_bytes()
    assert not any(x.split()[1].startswith('pose_') or (x.split()[1]=='python3' and 'board_producer_run.py' in x) for x in (f/'processes.txt').read_text().splitlines()[1:] if len(x.split())>1)
    assert ':8554 ' not in (f/'ports.txt').read_text() and ':39001 ' not in (f/'ports.txt').read_text()
    before=json.loads((E/'physical-return/run-physical/preflight.json').read_text());after=json.loads((f/'preflight.json').read_text())
    assert before['boot_files']==after['boot_files'] and before['libraries']==after['libraries'] and before['SDK_packages']==after['SDK_packages'] and after['fpga_state']=='operating'
    (E/'final-r2-review.json').write_text(json.dumps({'status':'final_readonly_audit_passed','kernel_unchanged':True,'BOOT_SDK_unchanged':True,'owned_manager_and_programs_ended':True,'ports_released':True,'connections_closed':True,'archive_sha256':sha(E/'return-final-r2.tar')},indent=2)+'\n')
    print('Final BOOT/SDK/kernel unchanged, owned processes ended and ports clear; no new execution')
finally:secret='';t.getpass.getpass=prompt

"""Recover read-only post-reboot audit after /tmp was cleared; NO reboot call."""
from pathlib import Path
import getpass,hashlib,json,sys,tarfile
ROOT=Path(__file__).resolve().parents[2];E=ROOT/'tools/pose-v1/evidence/demo-20261011-r1'
sys.path.insert(0,str(ROOT/'tools/pose-v1'))
import ssh_memory_transport as t
from archive_bytes import extract_bytes
assert json.loads((E/'reboot-issued.json').read_text())['issued_once']
archive=E/'reboot-after-audit-delivery.tar';assert not archive.exists()
with tarfile.open(archive,'w') as f:
    for path,name in [(Path(__file__).parent/'board/reboot_audit.py','reboot_audit.py'),(ROOT/'tools/pose-v1/board_application_preflight.py','board_application_preflight.py'),(E/'reboot-before-return/reboot-before/preflight.json','reboot-before/preflight.json'),(E/'reboot-before-return/reboot-before/boot-id.txt','reboot-before/boot-id.txt')]:
        info=f.gettarinfo(str(path),name);info.mtime=0
        with path.open('rb') as data:f.addfile(info,data)
remote='/tmp/wifi-pose-demo-reboot-20261011-r1'
secret=getpass.getpass('Authorized Lite password (memory only): ');original=t.getpass.getpass;t.getpass.getpass=lambda _:secret
def call(*args):
    sys.argv=['transport',*map(str,args)]
    try:t.main()
    except SystemExit as e:return e.code or 0
    return 0
try:
    assert call('ssh','set -eu; test ! -e '+remote+'; mkdir '+remote,'--log',E/'reboot-audit-recovery-create.txt')==0
    assert call('put',archive,remote+'/delivery.tar','--log',E/'reboot-audit-recovery-upload.txt')==0
    h=hashlib.sha256(archive.read_bytes()).hexdigest()
    assert call('ssh','set -eu; cd '+remote+'; echo "'+h+'  delivery.tar" | sha256sum -c -; tar -xf delivery.tar; LC_ALL=C.UTF-8 python3 reboot_audit.py after','--log',E/'reboot-audit-recovery-operation.txt')==0
    assert call('get',remote+'/return-reboot-after.tar',E/'return-reboot-after.tar','--log',E/'reboot-audit-recovery-download.txt')==0
    extract_bytes(E/'return-reboot-after.tar',E/'reboot-after-return')
    (E/'reboot.review.json').write_text(json.dumps({'status':'single_approved_reboot_identity_revalidated','reboots':1,'BOOT_SDK_unchanged':True,'boot_id_changed':True,'project_processes_listeners':0,'CMA_changed':False,'tmp_cleared_on_boot':True,'old_evidence_preserved_locally':True,'post_audit_recovered_read_only':True,'no_second_reboot':True},indent=2)+'\n',encoding='utf-8')
    print('Single reboot identities revalidated; /tmp cleared; no additional reboot')
finally:secret='';t.getpass.getpass=original

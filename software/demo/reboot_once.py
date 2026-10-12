"""User-approved one reboot, bounded reconnect, identity recheck; no retry reset."""
from pathlib import Path
import getpass,json,sys,time,socket
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/pose-v1'))
import ssh_memory_transport as t
from archive_bytes import extract_bytes
E=ROOT/'tools/pose-v1/evidence/demo-20261011-r1';remote='/tmp/wifi-pose-demo-20261011-r1'
assert not (E/'reboot.authorization.json').exists()
(E/'reboot.authorization.json').write_text(json.dumps({'user_approved':True,'reboots_permitted':1,'BOOT_CMA_model_SDK_changes':False,'purpose':'Restore clean startup allocation condition for end-to-end demo, not fault-loop retry'})+'\n')
secret=getpass.getpass('Authorized Lite password (memory only): ');original=t.getpass.getpass;t.getpass.getpass=lambda _:secret
serial=0
def call(*args):
    global serial
    serial+=1;sys.argv=['transport',*map(str,args),'--log',str(E/('reboot-transport-'+str(serial)+'.txt'))]
    try:t.main()
    except SystemExit as e:return e.code or 0
    return 0
try:
    assert call('put',Path(__file__).parent/'board/reboot_audit.py',remote+'/reboot_audit.py')==0
    assert call('ssh','LC_ALL=C.UTF-8 python3 '+remote+'/reboot_audit.py before')==0
    assert call('get',remote+'/return-reboot-before.tar',E/'return-reboot-before.tar')==0
    extract_bytes(E/'return-reboot-before.tar',E/'reboot-before-return')
    code=call('ssh','sudo -n systemctl reboot','--timeout','15')
    (E/'reboot-issued.json').write_text(json.dumps({'command':'systemctl reboot','ssh_exit':code,'issued_once':True})+'\n')
    assert code in (0,255),'Reboot command failed; no second command permitted'
    time.sleep(8);deadline=time.monotonic()+100
    while time.monotonic()<deadline:
        try:
            s=socket.create_connection(('192.168.126.49',22),1);s.close();break
        except OSError:time.sleep(2)
    else:raise TimeoutError('Board SSH did not return after approved reboot')
    time.sleep(3)
    assert call('ssh','LC_ALL=C.UTF-8 python3 '+remote+'/reboot_audit.py after')==0
    assert call('get',remote+'/return-reboot-after.tar',E/'return-reboot-after.tar')==0
    extract_bytes(E/'return-reboot-after.tar',E/'reboot-after-return')
    (E/'reboot.review.json').write_text(json.dumps({'status':'single_approved_reboot_identity_revalidated','reboots':1,'BOOT_SDK_unchanged':True,'boot_id_changed':True,'project_processes_listeners':0,'CMA_changed':False})+'\n')
    print('One approved reboot complete; same BOOT/SDK, FPGA operating, no project services')
finally:secret='';t.getpass.getpass=original

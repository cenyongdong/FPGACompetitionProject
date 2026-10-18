"""Remote r11 controller. Reuses r9 FAT/atomic BOOT safety code, never its closed approval."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,time,traceback
import board_support as b

HERE=Path(__file__).resolve().parent
cfg=json.loads((HERE/'config.json').read_text())
b.CFG=cfg;b.ROOT=Path(cfg['board']['remote_root']);b.PACKAGE=b.ROOT/'package';b.META=b.ROOT/'metadata';b.MOUNT=b.ROOT/'boot-mount'
ROOT,PACKAGE,META=b.ROOT,b.PACKAGE,b.META
ORIGINAL=cfg['original_boot_sha256'];CANDIDATE=cfg['files']['BOOT-ai-read-v3.bin']['sha256']

def record(name):return b.read_json(META/(name+'.json'))
def save(name,value):b.save_new(META/(name+'.json'),value);return value
def require_restore():
    value=record('restore');b.need(value['passed'] and value['BOOT_sha256']==ORIGINAL and value['boot_id']==b.boot_id(),'Original BOOT not restored in this candidate boot')

def reboot(kind):
    expected=CANDIDATE if kind=='candidate' else ORIGINAL
    identity=cfg['board']['pre_start_boot_id'] if kind=='candidate' else record('restore')['boot_id']
    a=b.audit(expected,identity)
    if kind=='candidate':b.need(record('install')['passed'],'Candidate install missing')
    else:require_restore()
    b.reserve(kind+'-reboot',{'one_command_only':True,'BOOT_sha256':expected})
    # Reservation is durable before a single delayed reboot; no retry on lost SSH.
    p=subprocess.Popen(['/bin/sh','-c','sleep 2; exec /sbin/reboot'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    return save(kind+'-reboot',dict(command_issued=True,boot_id=a['boot_id'],helper_pid=p.pid,time_unix=time.time()))

def main(stage):
    b.need(ROOT.resolve()==ROOT and str(ROOT).startswith(cfg['base']+'/'),'Unsafe remote root')
    for p in (ROOT,PACKAGE,META):b.need(p.is_dir() and not p.is_symlink(),'Unsafe/missing directory')
    auth=b.read_json(HERE/'authorization.json')
    if stage not in ('audit','close'):b.need(auth.get('active') is True and auth.get('approved_by')=='user','Fresh user approval not active')
    if stage=='prepare':
        result=b.prepare()
        for name,row in cfg['files'].items():b.verify_file(PACKAGE/name,row)
        save('verified-files',dict(passed=True,files=cfg['files']))
        return result
    if stage=='install':
        b.audit(ORIGINAL,cfg['board']['pre_start_boot_id']);b.checked_backup()
        r=record('host-backup');b.need(r['passed'] and r['sha256']==ORIGINAL and r['bytes']==7023552,'Independent host backup missing')
        b.need(record('verified-files')['passed'],'Transferred package not checked')
        b.verify_file(PACKAGE/'BOOT-ai-read-v3.bin',cfg['files']['BOOT-ai-read-v3.bin'])
        return b.replace_boot(PACKAGE/'BOOT-ai-read-v3.bin',ORIGINAL,CANDIDATE,'install','install.json')
    if stage=='candidate-reboot':return reboot('candidate')
    if stage=='restore':
        b.need(b.boot_id()!=cfg['board']['pre_start_boot_id'],'No candidate boot change')
        record('candidate-reboot');b.audit(CANDIDATE);b.checked_backup()
        return b.replace_boot(PACKAGE/'BOOT-original.readback.bin',CANDIDATE,ORIGINAL,'restore','restore.json')
    if stage=='probe':
        require_restore();b.audit(ORIGINAL,record('restore')['boot_id'])
        b.verify_file(PACKAGE/'ai_read_segmented_probe',cfg['files']['ai_read_segmented_probe'])
        b.reserve('probe',dict(sizes=[64,4096],allocation_bytes=1048576,SDK_open_max=1,automatic_retry=False))
        out=ROOT/'output';out.mkdir(mode=0o700)
        exe=PACKAGE/'ai_read_segmented_probe';os.chmod(exe,0o700)
        started=time.monotonic()
        with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
            p=subprocess.Popen([str(exe),str(out/'trace.jsonl')],cwd=PACKAGE,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,start_new_session=True)
            save('probe-process',dict(pid=p.pid,boot_id=b.boot_id(),time_unix=time.time(),soft_monitor_seconds=25))
            while p.poll() is None:
                try:p.wait(timeout=25)
                except subprocess.TimeoutExpired:
                    # A wrapper deadline never kills a still executing SDK task.
                    print(json.dumps(dict(event='probe_still_running',pid=p.pid,seconds=time.monotonic()-started,proc=b.proc_snapshot(p.pid))),flush=True)
        result=dict(exit_code=p.returncode,seconds=time.monotonic()-started,pid=p.pid,child_gone=not Path('/proc/'+str(p.pid)).exists(),device_owners=b.owners(),boot_id=b.boot_id(),sizes=[64,4096],no_retry=True)
        save('probe',result);save('after-probe',b.audit(ORIGINAL,result['boot_id']))
        return result
    if stage=='fallback-reboot':return reboot('fallback')
    if stage=='audit':return b.audit(ORIGINAL)
    if stage=='close':
        a=b.audit(ORIGINAL);b.need(a['boot_id']!=record('restore')['boot_id'],'Candidate runtime still active')
        save('final-audit',a);auth['active']=False;auth['remaining']={'candidate_installations':0,'candidate_starts':0,'original_fallbacks':0}
        # Only this packet's mutable receipt is closed. Original evidence stays intact.
        with (HERE/'authorization.json').open('w') as f:json.dump(auth,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        return dict(closed=True,boot_id=a['boot_id'],BOOT_sha256=ORIGINAL,device_owners=a['device_owners'])
    raise RuntimeError('Unknown stage')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','install','candidate-reboot','restore','probe','fallback-reboot','audit','close']);args=parser.parse_args()
    try:print(json.dumps(main(args.stage),ensure_ascii=False,indent=2),flush=True)
    except BaseException as error:traceback.print_exc();raise SystemExit(1)

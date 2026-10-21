"""r26 bounded passive boots. Reuse the existing FAT/identity primitives only."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

BASE=Path(__file__).resolve().parent
cfg=json.loads((BASE/'config.json').read_text())
sys.path.insert(0,'/root/hdmi-reset-calibration-20261018-r20')
import board_support as b
b.CFG=cfg;b.ROOT=BASE;b.META=BASE/'metadata';b.PACKAGE=BASE/'package';b.MOUNT=BASE/'boot-mount'
b.identity_record=lambda x:dict(x,package_id=cfg['package_id'])
ORIGINAL=cfg['original_boot_sha256'];CANDIDATE=cfg['files']['BOOT-candidate.bin']['sha256']
ROOT_META=BASE/'metadata';PACKAGE=BASE/'package'


def read(p):return b.read_json(p)
def save(p,x):b.save_new(p,x);return x
def root(name):return read(ROOT_META/(name+'.json'))


def authorize():
    a=read(BASE/'authorization.json')
    b.need(BASE==Path('/root/hdmi-ps-release-20261020-r26') and cfg['package_id']=='ps-release-r26','Wrong actual package')
    b.need(a['active'] and a['scope']=='PS reset/FIFO/release passive diagnosis' and a['caps']==cfg['caps'],'Diagnostic authorization differs')
    b.need(not (ROOT_META/'closed.json').exists(),'Package already closed')
    b.need(cfg['caps']==dict(candidate_starts=2,original_fallbacks=1,SDK_Open=0,DMA=False,inference=False,HDMI_START=False,physical_key=0,HDMI_long_term=False),'Scope changed')


def bind(n):
    b.need(n in (1,2),'Cycle outside budget')
    run=BASE/('run-'+str(n));b.ROOT=run;b.META=run/'metadata';b.MOUNT=run/'boot-mount'
    return run


def reboot(name,expected_boot,expected_id):
    b.audit(expected_boot,expected_id)
    save(ROOT_META/(name+'-attempt.json'),dict(boot_id=expected_id,time_unix=time.time(),automatic_retry=False))
    p=subprocess.Popen(['/bin/sh','-c','sleep 2; exec /sbin/reboot'],stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    return save(ROOT_META/(name+'-issued.json'),dict(command_issued=True,helper_pid=p.pid,boot_id=expected_id))


def child(run,name,argv):
    out=run/name;out.mkdir(mode=0o700)
    with (out/'stdout.log').open('xb') as so,(out/'stderr.log').open('xb') as se:
        p=subprocess.Popen(argv(out),stdout=so,stderr=se,stdin=subprocess.DEVNULL,start_new_session=True)
        save(b.META/(name+'-process.json'),dict(pid=p.pid,boot_id=b.boot_id(),automatic_retry=False))
        while p.poll() is None:
            try:p.wait(timeout=25)
            except subprocess.TimeoutExpired:print(json.dumps(dict(stage=name,pid=p.pid,process=b.proc_snapshot(p.pid))),flush=True)
    return out,p.returncode


def main(stage,n):
    authorize()
    if stage=='audit':return b.audit(ORIGINAL)
    if stage=='prepare':
        audit=b.audit(ORIGINAL,cfg['board']['pre_start_boot_id'])
        for name,source in cfg['asset_reuse'].items():
            b.verify_file(Path(source),cfg['files'][name])
            target=PACKAGE/name
            if not target.exists():shutil.copyfile(source,target)
        for name,row in cfg['files'].items():b.verify_file(PACKAGE/name,row)
        b.checked_backup();os.chmod(PACKAGE/'ai_preopen_monitor',0o700)
        return save(ROOT_META/'prepare.json',dict(passed=True,boot_id=audit['boot_id']))
    run=bind(n)
    if stage=='install':
        b.need(root('prepare')['passed'] and not (ROOT_META/'original-fallback-attempt.json').exists(),'Preparation absent or fallback already consumed')
        expected=cfg['board']['pre_start_boot_id']
        if n==2:
            previous=read(BASE/'run-1/metadata/observe.json')
            b.need(previous['valid'] and previous['healthy_idle'] and not previous['event_overflow'],'First boot already faulty/inconclusive: no second candidate')
            expected=previous['boot_id']
        b.audit(ORIGINAL,expected);b.checked_backup()
        run.mkdir(mode=0o700);b.META.mkdir(mode=0o700);b.MOUNT.mkdir(mode=0o700)
        return b.replace_boot(PACKAGE/'BOOT-candidate.bin',ORIGINAL,CANDIDATE,'install','install.json')
    if stage=='candidate-reboot':
        installed=read(b.META/'install.json')
        b.need(installed['passed'],'Install not verified')
        return reboot('candidate-'+str(n),CANDIDATE,installed['boot_id'])
    if stage=='restore':
        attempt=root('candidate-'+str(n)+'-attempt')
        b.need(attempt['boot_id']!=b.boot_id(),'Candidate has not booted')
        b.audit(CANDIDATE)
        return b.replace_boot(PACKAGE/'BOOT-original.readback.bin',CANDIDATE,ORIGINAL,'restore','restore.json')
    if stage=='observe':
        restored=read(b.META/'restore.json');identity=b.boot_id()
        b.need(restored['passed'] and restored['boot_id']==identity and restored['BOOT_sha256']==ORIGINAL and not b.owners(),'Restored runtime/ownership differs')
        b.reserve('observe',dict(SDK=0,DMA=0,HDMI_START=0,physical_key=0))
        b.verify_file(PACKAGE/'ai_preopen_monitor',cfg['files']['ai_preopen_monitor'])
        probe_start=time.monotonic()
        out,code=child(run,'legacy',lambda out:[str(PACKAGE/'ai_preopen_monitor'),str(out/'trace.jsonl')])
        result=dict(valid=False,healthy_idle=False,event_overflow=True,boot_id=identity,legacy_exit=code,SDK=0,DMA=0,HDMI_START=0,
            probe_Linux_monotonic_bounds_seconds=[probe_start,time.monotonic()])
        if code==0:
            b.verify_file(PACKAGE/'capture_ps_release.py',cfg['files']['capture_ps_release.py'])
            new,new_code=child(run,'release',lambda out:['python3',str(PACKAGE/'capture_ps_release.py'),str(out/'raw.jsonl'),identity])
            result['release_exit']=new_code
            if new_code==0:
                sys.path.insert(0,str(PACKAGE));from decode_ps_release import decode
                rows=[json.loads(x) for x in (new/'raw.jsonl').read_text().splitlines()]
                captured=next(x for x in rows if x.get('event')=='ps_release_snapshot')
                decoded=decode(captured['words'])
                legacy=next(json.loads(x) for x in (out/'trace.jsonl').read_text().splitlines() if x.strip())
                w=legacy['words'];hist=captured['boot_words']
                quiet=(len(w)==104 and w[0]==0x41495201 and w[1]>0 and w[2]&31==0x19 and w[3]==0 and
                       all(w[8+16*c]==w[9+16*c]==w[15+16*c]==0 for c in range(6)))
                ready_return=decoded['first_PL_ready_PS_RVALID_HP_cycle']
                first_ar=decoded['first_PS_AR_HP_cycle']
                prior_return=ready_return is not None and (first_ar is None or ready_return<first_ar)
                startup_read_idle=ready_return is None and decoded['raw_HP_handshakes']['PS_AR']==0
                result.update(valid=b.boot_id()==identity and not b.owners(),healthy_idle=quiet and startup_read_idle and not decoded['HP_count_overflow_mask'],
                    ready_return_before_first_observed_AR=prior_return,startup_read_idle=startup_read_idle,
                    event_overflow=decoded['event_overflow'],decoded=decoded,boot_words=hist)
        save(b.META/'observe.json',result)
        return result
    if stage=='fallback-reboot':
        restored=read(b.META/'restore.json')
        b.need(restored['passed'] and restored['boot_id']==b.boot_id(),'Runtime not restored')
        return reboot('original-fallback',ORIGINAL,restored['boot_id'])
    if stage=='close':
        attempt=root('original-fallback-attempt')
        b.need(attempt['boot_id']!=b.boot_id(),'Original runtime has not restarted')
        audit=b.audit(ORIGINAL)
        save(ROOT_META/'final-audit.json',audit)
        return save(ROOT_META/'closed.json',dict(closed=True,boot_id=audit['boot_id'],SDK_Open=0,DMA=0,inference=0,HDMI_START=0,
            candidate_starts=len(list(ROOT_META.glob('candidate-*-attempt.json'))),original_fallbacks=1,
            remaining=dict(candidate_starts=0,original_fallbacks=0,SDK_Open=0)))
    raise RuntimeError('Unknown stage')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage');p.add_argument('--cycle',type=int,default=1);a=p.parse_args()
    try:
        result=main(a.stage,a.cycle)
        # Keep the complete canonical result in the durable stage file.
        keys=('passed','valid','healthy_idle','event_overflow','boot_id','BOOT_sha256','closed','command_issued','helper_pid','candidate_starts')
        print(json.dumps({k:result[k] for k in keys if k in result}))
    except BaseException as error:
        print(json.dumps(dict(error=str(error),boot_id=b.boot_id(),automatic_retry=False)),file=sys.stderr)
        raise

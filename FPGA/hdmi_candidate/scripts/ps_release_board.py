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
    scopes={'ps-release-r26':('/root/hdmi-ps-release-20261020-r26','PS reset/FIFO/release passive diagnosis',2),
            's01-isolation-r28':('/root/hdmi-s01-isolation-20261022-r28','S01 source isolation passive diagnosis',1),
            's01-soak-r29':('/root/hdmi-s01-soak-20261022-r29','S01 isolated 30 minute no-SDK soak',1),
            'hp2-cycletrace-r30':('/root/hdmi-hp2-cycletrace-20261022-r30','Passive HP2 consecutive cycle capture',1),
            'hp2-protocol-r31':('/root/hdmi-protocol-checker-20261023-r31','Passive HP2 native protocol check and waveform capture',1)}
    b.need(cfg['package_id'] in scopes,'Unknown actual package')
    directory,scope,starts=scopes[cfg['package_id']]
    b.need(BASE==Path(directory),'Wrong actual package directory')
    b.need(a['active'] and a['scope']==scope and a['caps']==cfg['caps'],'Diagnostic authorization differs')
    b.need(not (ROOT_META/'closed.json').exists(),'Package already closed')
    b.need(cfg['caps']==dict(candidate_starts=starts,original_fallbacks=1,SDK_Open=0,DMA=False,inference=False,HDMI_START=False,physical_key=0,HDMI_long_term=False),'Scope changed')
    if cfg['package_id']=='s01-soak-r29':
        b.need(cfg.get('passive_soak_seconds')==1800,'Unexpected passive soak duration')


def bind(n):
    b.need(1<=n<=cfg['caps']['candidate_starts'],'Cycle outside budget')
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
        soak=cfg['package_id']=='s01-soak-r29'
        extra=['--seconds',str(cfg['passive_soak_seconds'])] if soak else []
        out,code=child(run,'legacy',lambda out:[str(PACKAGE/'ai_preopen_monitor'),str(out/'trace.jsonl'),*extra])
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
                legacy_rows=[json.loads(x) for x in (out/'trace.jsonl').read_text().splitlines() if x.strip()]
                legacy=legacy_rows[0]
                w=legacy['words'];hist=captured['boot_words']
                quiet=(len(w)==104 and w[0]==0x41495201 and w[1]>0 and w[2]&31==0x19 and w[3]==0 and
                       all(w[8+16*c]==w[9+16*c]==w[15+16*c]==0 for c in range(6)))
                ready_return=decoded['first_PL_ready_PS_RVALID_HP_cycle']
                first_ar=decoded['first_PS_AR_HP_cycle']
                prior_return=ready_return is not None and (first_ar is None or ready_return<first_ar)
                startup_read_idle=ready_return is None and decoded['raw_HP_handshakes']['PS_AR']==0
                # Channel4 word11 exposes actual S01 input BURST/SIZE/LEN/ID,
                # ARVALID and RREADY. All must be zero in the isolated image;
                # the original reader always drives ARSIZE=3, ARBURST=1.
                isolation_ok=cfg['package_id'] not in ('s01-isolation-r28','s01-soak-r29','hp2-cycletrace-r30','hp2-protocol-r31') or (len(w)==104 and (w[83]&0x7fff9)==0)
                if cfg['package_id'] in ('s01-isolation-r28','s01-soak-r29','hp2-cycletrace-r30','hp2-protocol-r31'):
                    result.update(source_isolation_live_confirmed=isolation_ok,S01_current_pins=w[83],S01_source_input_mask=w[83]&0x7fff9)
                result.update(valid=b.boot_id()==identity and not b.owners() and isolation_ok,healthy_idle=quiet and startup_read_idle and not decoded['HP_count_overflow_mask'] and isolation_ok,
                    ready_return_before_first_observed_AR=prior_return,startup_read_idle=startup_read_idle,
                    event_overflow=decoded['event_overflow'],decoded=decoded,boot_words=hist)
                if soak:
                    elapsed=next(x for x in legacy_rows if x.get('event')=='passive_soak_window')
                    complete=elapsed['requested_seconds']==1800 and elapsed['observed_seconds']>=1800 and elapsed['stop_flags']==0
                    no_activity=(decoded['first_raw_PS_RVALID_HP_cycle'] is None and decoded['first_PS_AR_HP_cycle'] is None and
                                 not any(decoded['raw_HP_handshakes'].values()) and
                                 all(w[8+16*c+j]==0 for c in range(6) for j in (*range(8),15)))
                    result.update(passive_soak=elapsed,completed_passive_soak=complete,
                                  healthy_idle=result['healthy_idle'] and complete and no_activity)
        save(b.META/'observe.json',result)
        return result
    if stage=='cycletrace':
        restored=read(b.META/'restore.json');identity=b.boot_id()
        b.need(cfg['package_id'] in ('hp2-cycletrace-r30','hp2-protocol-r31') and restored['passed'] and restored['boot_id']==identity and
               restored['BOOT_sha256']==ORIGINAL and not b.owners(),'Cycle capture requires restored candidate runtime')
        b.reserve('cycletrace',dict(SDK=0,DMA=0,HDMI_START=0,MMIO_writes=0))
        for name in ('capture_hp2_cycletrace.py','decode_hp2_cycletrace.py'):
            b.verify_file(PACKAGE/name,cfg['files'][name])
        out,code=child(run,'cycletrace',lambda out:['python3',str(PACKAGE/'capture_hp2_cycletrace.py'),str(out/'raw.json'),identity])
        return save(b.META/'cycletrace.json',dict(valid=code==0 and b.boot_id()==identity and not b.owners(),
            exit_code=code,boot_id=identity,MMIO_writes=0,SDK=0,output=str(out/'raw.json')))
    if stage=='protocol':
        restored=read(b.META/'restore.json');identity=b.boot_id()
        b.need(cfg['package_id']=='hp2-protocol-r31' and restored['passed'] and restored['boot_id']==identity and
               restored['BOOT_sha256']==ORIGINAL and not b.owners(),'Protocol capture requires restored candidate runtime')
        b.reserve('protocol',dict(SDK=0,DMA=0,HDMI_START=0,MMIO_writes=0))
        for name in ('capture_hp2_protocol.py','decode_hp2_protocol.py','decode_hp2_cycletrace.py','hp2_protocol_checks.py'):
            b.verify_file(PACKAGE/name,cfg['files'][name])
        out,code=child(run,'protocol',lambda out:['python3',str(PACKAGE/'capture_hp2_protocol.py'),str(out/'raw.json'),identity])
        return save(b.META/'protocol.json',dict(valid=code==0 and b.boot_id()==identity and not b.owners(),
            exit_code=code,boot_id=identity,MMIO_writes=0,SDK=0,output=str(out/'raw.json')))
    if stage=='launch-observe':
        restored=read(b.META/'restore.json')
        b.need(cfg['package_id']=='s01-soak-r29' and restored['passed'] and restored['boot_id']==b.boot_id(),
               'Passive soak launch requires restored candidate runtime')
        save(b.META/'observe-launch-attempt.json',dict(boot_id=b.boot_id(),automatic_retry=False))
        with (run/'observe-controller.stdout.log').open('xb') as so,(run/'observe-controller.stderr.log').open('xb') as se:
            p=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'observe','--cycle',str(n)],
                               stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
        return save(b.META/'observe-launch.json',dict(boot_id=b.boot_id(),helper_pid=p.pid,command_issued=True))
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

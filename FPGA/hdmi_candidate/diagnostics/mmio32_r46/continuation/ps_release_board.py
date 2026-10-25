"""r45 bounded parent controller. No action on import; each CLI is explicit.

Reuses E41 frame/joint bodies and installed r20 board_support primitives.
Unknown or failed actions never retry. Parent package authorization and actual
file identities are required before any mutation, SDK load or diagnostic CMD.
"""
from pathlib import Path, PurePosixPath
import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
import time

BASE=Path(__file__).resolve().parent
ROOT_META=BASE/'metadata'
PACKAGE=BASE/'package'
cfg=None
b=None
ORIGINAL=CANDIDATE=None
CAPS=dict(candidate_starts=2,original_fallbacks=1,SDK_Open=2,DMA=True,inference=True,
          HDMI_START=True,physical_key=0,HDMI_long_term=False)
SUPPORT=Path('/root/hdmi-reset-calibration-20261018-r20/board_support.py')
DIAGNOSTICS=('observe-before','cycletrace-before','protocol-before','before-seed','consume',
             'revalidate-consume','cycletrace-after','protocol-after','consumed-gate','checker-rearm',
             'post-frame-protocol','post-joint-protocol')
CODE_FILES=('revalidate_consume.py','r45_diagnostic_stages.py','capture_deferred.py','consume_gate.py','before_seed_gate.py',
            'capture_hp2_cycletrace.py','decode_hp2_cycletrace.py','capture_hp2_protocol.py',
            'decode_hp2_protocol.py','hp2_protocol_checks.py','capture_ps_release.py','decode_ps_release.py')


def initialize():
    global cfg,b,ORIGINAL,CANDIDATE
    if b is not None:return
    cfg=json.loads((BASE/'config.json').read_text())
    sys.path.insert(0,str(SUPPORT.parent))
    b=importlib.import_module('board_support')
    b.CFG=cfg;b.ROOT=BASE;b.META=ROOT_META;b.PACKAGE=PACKAGE;b.MOUNT=BASE/'boot-mount'
    b.identity_record=lambda value:dict(value,package_id=cfg['package_id'])
    ORIGINAL=cfg['original_boot_sha256'];CANDIDATE=cfg['files']['BOOT-candidate.bin']['sha256']


def read(path):return b.read_json(path)
def save(path,value):b.save_new(path,value);return value
def root(name):return read(ROOT_META/(name+'.json'))


def asset(name):
    matches=[p for p in (PACKAGE/name,PACKAGE/'gates'/name,PACKAGE/'capture'/name) if p.is_file()]
    b.need(len(matches)==1,'Required package asset missing/ambiguous: '+name)
    return matches[0]


def verify_code():
    rows=cfg['controller_files']
    b.need('ps_release_board.py' in rows,'Actual parent controller identity absent')
    for name,row in rows.items():
        relative=PurePosixPath(name)
        b.need(not relative.is_absolute() and '..' not in relative.parts,'Controller identity path outside package')
        b.verify_file(BASE.joinpath(*relative.parts),row)
    b.need(Path(b.__file__).resolve()==SUPPORT,'Unexpected support primitive path')
    b.verify_file(SUPPORT,cfg['support_identity'])
    for name in CODE_FILES:b.verify_file(asset(name),cfg['files'][name])


def authorize():
    initialize()
    receipt=read(BASE/'authorization.json')
    b.need(cfg['package_id']=='hp2-mmio32-r46' and str(BASE)==cfg['base'],'Wrong actual r46 package')
    b.need(receipt['active'] is True and receipt['package_id']==cfg['package_id'] and
           receipt['caps']==cfg['caps']==CAPS and
           receipt['scope']==cfg.get('scope','Bounded deferred same-boot startup consumption and AI to HDMI test'),
           'Actual r45 authorization/caps/scope differs')
    b.need(not (ROOT_META/'closed.json').exists(),'r45 package already closed')
    verify_code()


def bind(n):
    b.need(type(n) is int and 1<=n<=2,'Candidate cycle outside r45 budget')
    run=BASE/('run-'+str(n))
    b.ROOT=run;b.META=run/'metadata';b.MOUNT=run/'boot-mount'
    return run


def all_sdk_attempts():
    return [path for name in ('frame-test','joint-test') for path in BASE.glob('run-*/metadata/'+name+'.attempt.json')]


def parser_resolution_valid():
    path=ROOT_META/'consume-parser-resolution.json'
    if not path.exists():return False
    receipt=read(path);stop=root('stopped')
    raw=BASE/'run-1/consume/capture/raw.jsonl'
    return (cfg.get('same_boot_continuation',{}).get('approved') is True and
            receipt.get('valid') is True and receipt.get('boot_id')==b.boot_id()==stop.get('boot_id') and
            stop.get('stage')=='consume' and stop.get('cycle')==1 and
            receipt.get('MMIO_commands')==0 and receipt.get('original_failure_preserved') is True and
            receipt.get('original_raw_sha256')==b.digest(raw))


def stopped():
    return ((ROOT_META/'diagnostic-continuation-stopped.json').exists() or
            ((ROOT_META/'stopped.json').exists() and not parser_resolution_valid()))


def device_owners():
    # Preserve the old fb/dri/xdma coverage and add the collector's /dev/axi
    # coverage before any SDK entry. Both scans are read-only and fail closed.
    sys.path.insert(0,str(asset('capture_deferred.py').parent))
    from capture_deferred import owners
    return b.owners()+owners()


def mark_stopped(stage,n,result):
    if stopped():return
    target=ROOT_META/('diagnostic-continuation-stopped.json' if (ROOT_META/'stopped.json').exists() else 'stopped.json')
    save(target,dict(stage=stage,cycle=n,boot_id=b.boot_id(),
         reason=result.get('error',result.get('reasons','Unsafe/inconclusive result')),
         automatic_retry=False,new_candidate_or_functional_actions_forbidden=True))


def restored_context(run):
    identity=b.boot_id()
    restored=read(run/'metadata/restore.json')
    attempt=root('candidate-'+run.name.split('-')[-1]+'-attempt')
    b.need(restored['passed'] is True and restored['boot_id']==identity and
           restored['BOOT_sha256']==ORIGINAL and restored['full_readback_bytes']==7023552 and
           restored['other_startup_files_unchanged'] is True and restored['boot_partition_unmounted'] is True and
           attempt['boot_id']!=identity and not device_owners(),'Restored same-boot identity/ownership differs')
    return identity


def functional_context(run,stage):
    identity=restored_context(run)
    admitted=read(run/'metadata/consumed-gate.json');ready=read(run/'metadata/sdk-ready.json')
    before=read(run/'metadata/before-seed.json')
    b.need(admitted['eligible'] is True and admitted['boot_id']==identity and
           ready['valid'] is True and ready['boot_id']==identity and
           before['eligible'] is True and before['classification']=='known_unmatched_return' and
           before['boot_id']==identity,'Same-boot seed/consumption/fresh-checker admission absent')
    after=read(run/'revalidate-consume/capture/result.json')['normalized']
    b.need(after['observer_generation']==4 and after['boot_id']==identity,'Expected post-consume SDK observer generation4 absent')
    b.need(len(all_sdk_attempts())<2,'Global SDK attempt budget exhausted')
    if stage=='frame-test':
        b.need(not all_sdk_attempts(),'Frame SDK load must be the first and only frame attempt')
    else:
        frame=read(run/'metadata/frame-test.json');native=read(run/'metadata/post-frame-protocol.json')
        b.need(frame['passed'] is True and frame['valid'] is True and frame['boot_id']==identity and
               native['passed'] is True and native['valid'] is True and native['boot_id']==identity,
               'Joint test requires passed frame and fresh post-frame full160 check')
        b.need(len(all_sdk_attempts())==1 and (run/'metadata/frame-test.attempt.json').exists(),
               'Joint SDK load must follow exactly one frame attempt')
    return identity


def reboot(name,expected_boot,identity):
    b.audit(expected_boot,identity)
    save(ROOT_META/(name+'-attempt.json'),dict(boot_id=identity,time_unix=time.time(),automatic_retry=False))
    process=subprocess.Popen(['/bin/sh','-c','sleep 2; exec /sbin/reboot'],stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    return save(ROOT_META/(name+'-issued.json'),dict(command_issued=True,helper_pid=process.pid,boot_id=identity))


def child(run,name,argv):
    out=run/name;out.mkdir(mode=0o700)
    with (out/'stdout.log').open('xb') as so,(out/'stderr.log').open('xb') as se:
        p=subprocess.Popen(argv(out),stdout=so,stderr=se,stdin=subprocess.DEVNULL,start_new_session=True)
        save(b.META/(name+'-process.json'),dict(pid=p.pid,boot_id=b.boot_id(),automatic_retry=False))
        while p.poll() is None:
            try:p.wait(timeout=25)
            except subprocess.TimeoutExpired:print(json.dumps(dict(stage=name,pid=p.pid,process=b.proc_snapshot(p.pid))),flush=True)
    return out,p.returncode


def hdmi_register_snapshot():
    import mmap,struct
    fd=os.open('/dev/mem',os.O_RDONLY|os.O_SYNC|os.O_CLOEXEC)
    try:
        with mmap.mmap(fd,4096,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ,offset=0x400b0000) as page:
            rd=lambda off:struct.unpack_from('<I',page,off)[0]
            v={hex(off):rd(off) for off in [0,0x10,0x14,0x18,0x1c,0x20,0x24,0x28,0x2c,0x30,0x34,0x38,0x3c,0x40,0x44,0x48]}
            b.need(v['0x0']==0x48444d01 and v['0x40']==0x48445301,'Actual HDMI ABI differs')
            return dict(boot_id=b.boot_id(),values=v,MMIO_writes=0)
    finally:os.close(fd)


def frame_stage(run):
    gate=read(b.META/'observe.json');identity=b.boot_id()
    restored=read(b.META/'restore.json')
    b.need(gate['valid'] and gate.get('discard_probe_admissible',False) and read(b.META/'consumed-gate.json')['eligible'] and gate.get('S01_source_connected_confirmed') and
           restored['passed'] and restored['boot_id']==identity and gate['boot_id']==identity,
           'Functional candidate startup not healthy: no SDK or frame test')
    b.audit(ORIGINAL,identity)
    exe=PACKAGE/'hdmi_frame_probe';b.verify_file(exe,cfg['files']['hdmi_frame_probe']);os.chmod(exe,0o700)
    b.reserve('frame-test',dict(SDK_Open_budget=1,DMA=True,HDMI_START=True,patterns=2,seconds_per_pattern=8,
                                inference=0,automatic_retry=False))
    save(b.META/'hdmi-registers-before.json',hdmi_register_snapshot())
    start=time.monotonic()
    out,code=child(run,'frame-test',lambda out:[str(exe),'--patterns',str(out/'frames')])
    end=time.monotonic()
    save(b.META/'hdmi-registers-after.json',hdmi_register_snapshot())
    rows=[];startup=[]
    if (out/'frames/hdmi.jsonl').exists():rows=[json.loads(x) for x in (out/'frames/hdmi.jsonl').read_text().splitlines() if x.strip()]
    if (out/'frames/startup-and-read.jsonl').exists():startup=[json.loads(x) for x in (out/'frames/startup-and-read.jsonl').read_text().splitlines() if x.strip()]
    memory=[x for x in rows if x.get('event')=='memory_verified']
    adopted=[x for x in rows if x.get('event')=='adopted']
    stop=[x for x in rows if x.get('event')=='stop_proved']
    released=[x for x in rows if x.get('event')=='frames_released_after_stop']
    snapshots=[x for x in startup if x.get('event')=='startup_snapshot']
    frame=next((x for x in snapshots if x.get('phase')=='memory_and_HDMI'),None)
    counts={}
    if frame:
        w=frame['words']
        counts={name:dict(AR=w[8+16*c],R=w[9+16*c],RLAST=w[10+16*c],non_OKAY=w[11+16*c],
                         RVALID_cycles=w[15+16*c],expected_R=w[23+16*c]) for c,name in enumerate(['HC0','HC1','HC2','HC3','HDMI_S01','PS_HP2'])}
    valid=(b.boot_id()==identity and not b.owners())
    okay=(code==0 and valid and len(memory)==2 and {x['slot'] for x in memory}=={0,1} and
          all(x['bytes']==4147200 for x in memory) and [x['id'] for x in adopted]==[100,101] and
          len(stop)==1 and len(released)==1 and frame is not None and
          all(counts[k]['AR']>0 and counts[k]['RLAST']==counts[k]['AR'] and counts[k]['R']>0 and counts[k]['R']==counts[k]['expected_R'] and counts[k]['non_OKAY']==0 for k in ['HDMI_S01','PS_HP2']))
    result=dict(valid=valid,passed=okay,boot_id=identity,exit_code=code,seconds=end-start,
                SDK_Open_attempted=sum(x.get('event')=='before_Device_Open' for x in startup),
                DMA_memory_verified_slots=[x['slot'] for x in memory],adopted_ids=[x['id'] for x in adopted],
                stop_proved=bool(stop),frames_released_after_stop=bool(released),AXI_counts=counts,
                physical_screen_verified=False,automatic_retry=False)
    save(b.META/'frame-test.json',result)
    # A separate read-only startup history survives failures without another SDK load.
    _,capture_code=child(run,'after-frame-release',lambda out:['python3',str(PACKAGE/'capture_ps_release.py'),str(out/'raw.jsonl'),identity])
    result['after_frame_capture_exit']=capture_code
    return result

def joint_stage(run):
    gate=read(b.META/'observe.json');identity=b.boot_id();restored=read(b.META/'restore.json')
    b.need(gate['valid'] and gate.get('discard_probe_admissible',False) and read(b.META/'consumed-gate.json')['eligible'] and gate.get('S01_source_connected_confirmed') and restored['passed'] and restored['boot_id']==identity and gate['boot_id']==identity,'Joint test requires healthy connected candidate')
    b.need(read(b.META/'frame-test.json')['passed'],'Pattern stage not passed: no inference')
    b.audit(ORIGINAL,identity)
    package=BASE/'software'
    manifest=read(package/'identity.json')
    for name,digest in manifest['files'].items():b.need(b.digest(package/name)==digest,'Actual software package changed: '+name)
    b.need(manifest['libraries']==cfg['board']['SDK'],'Software SDK identity differs')
    b.reserve('joint-test',dict(SDK_Open_budget=1,DMA=True,HDMI_START=True,inference=True,frames=90,input_hz=5,automatic_retry=False))
    host=read(BASE/'host-session.json');b.need(host['count']==90 and host['hz']==5,'Host bounded session differs')
    save(b.META/'joint-registers-before.json',hdmi_register_snapshot())
    os.chmod(package/'pose_demo_v1',0o700)
    start=time.monotonic()
    command=['python3',str(package/'board_guard.py'),'--stage','basic','--run-name','joint','--frames','90','--session',host['session'],'--max-seconds','150']
    with (run/'joint.stdout.log').open('xb') as so,(run/'joint.stderr.log').open('xb') as se:
        process=subprocess.Popen(command,stdout=so,stderr=se,stdin=subprocess.DEVNULL,start_new_session=True)
        save(b.META/'joint-process.json',dict(pid=process.pid,boot_id=identity))
        while process.poll() is None:
            try:process.wait(timeout=20)
            except subprocess.TimeoutExpired:print(json.dumps(dict(stage='joint',pid=process.pid,seconds=time.monotonic()-start)),flush=True)
    out=package/'run-joint/results';rows=[];snapshots=[]
    if (out/'hdmi.jsonl').exists():rows=[json.loads(x) for x in (out/'hdmi.jsonl').read_text().splitlines() if x.strip()]
    if (out/'startup-and-joint.jsonl').exists():snapshots=[json.loads(x) for x in (out/'startup-and-joint.jsonl').read_text().splitlines() if x.strip()]
    adopted=[x for x in rows if x.get('event')=='adopted'];stop=[x for x in rows if x.get('event')=='stop_proved'];released=[x for x in rows if x.get('event')=='frames_released_after_stop']
    summary=read(out/'summary.json') if (out/'summary.json').exists() else {}
    snapshot=next((x for x in snapshots if x.get('event')=='startup_snapshot' and x.get('phase')=='AI_HDMI'),None)
    counts={}
    if snapshot:
        w=snapshot['words'];counts={name:dict(AR=w[8+16*c],R=w[9+16*c],RLAST=w[10+16*c],non_OKAY=w[11+16*c],RVALID_cycles=w[15+16*c],expected_R=w[23+16*c]) for c,name in enumerate(['HC0','HC1','HC2','HC3','HDMI_S01','PS_HP2'])}
    valid=b.boot_id()==identity and not b.owners()
    passed=process.returncode==0 and valid and summary.get('completed')==90 and summary.get('sent')==90 and summary.get('host_archived')==90 and len(adopted)==90 and len(stop)==1 and len(released)==1 and snapshot is not None and all(x['R']==x['expected_R'] and x['AR']==x['RLAST'] and x['non_OKAY']==0 for x in counts.values())
    result=dict(valid=valid,passed=passed,boot_id=identity,exit_code=process.returncode,seconds=time.monotonic()-start,SDK_Open_attempted=1,inference=summary.get('completed'),adopted_ids=[x['id'] for x in adopted],stop_proved=bool(stop),frames_released_after_stop=bool(released),AXI_counts=counts,summary=summary,physical_screen_verified=False,automatic_retry=False)
    save(b.META/'joint-registers-after.json',hdmi_register_snapshot());save(b.META/'joint-test.json',result)
    child(run,'after-joint-release',lambda out:['python3',str(PACKAGE/'capture_ps_release.py'),str(out/'raw.jsonl'),identity])
    return result



def main(stage,n):
    authorize()
    continuation=cfg.get('same_boot_continuation',{})
    b.need(continuation.get('approved') is True and
           continuation.get('boot_id')==b.boot_id() or stage in ('audit','close'),
           'Approved same-boot continuation identity differs')
    allowed={'audit','revalidate-consume','cycletrace-after','protocol-after','consumed-gate',
             'checker-rearm','frame-test','post-frame-protocol','joint-test','post-joint-protocol',
             'fallback-reboot','close'}
    b.need(stage in allowed,'No new consume, functional reset or candidate start in this continuation')
    if stage=='audit':return b.audit(ORIGINAL)
    if stage=='prepare':
        b.need(not stopped(),'r45 stopped; no preparation retry')
        audit=b.audit(ORIGINAL,cfg['board']['pre_start_boot_id'])
        for name,source in cfg.get('asset_reuse',{}).items():
            b.verify_file(Path(source),cfg['files'][name])
            target=PACKAGE/name
            if not target.exists():shutil.copyfile(source,target)
        for name,row in cfg['files'].items():b.verify_file(asset(name),row)
        b.checked_backup()
        return save(ROOT_META/'prepare.json',dict(passed=True,boot_id=audit['boot_id']))
    if stage=='close':
        attempt=root('original-fallback-attempt')
        identity=b.boot_id()
        b.need(attempt['boot_id']!=identity and root('original-fallback-issued')['command_issued'],
               'Original fallback runtime has not started')
        for path in BASE.glob('run-*/metadata/restore.json'):
            b.need(read(path)['boot_id']!=identity,'Final runtime matches an old candidate boot')
        audit=b.audit(ORIGINAL,identity)
        b.need(len(audit['startup_files'])==9 and len(audit['SDK'])==6 and
               audit['fpga_state']=='operating' and not audit['device_owners'],
               'Final original runtime/startup/SDK audit incomplete')
        save(ROOT_META/'final-audit.json',audit)
        starts=len(list(ROOT_META.glob('candidate-*-attempt.json')))
        sdk=len(all_sdk_attempts())
        b.need(1<=starts<=2 and sdk<=2,'Actual attempt counts exceed r45 caps')
        return save(ROOT_META/'closed.json',dict(closed=True,boot_id=identity,
             candidate_starts=starts,original_fallbacks=1,SDK_Open_attempts=sdk,
             final_original_runtime_chain_verified=True,final_startup_files=9,final_SDK_libraries=6,
             remaining=dict(candidate_starts=0,original_fallbacks=0,SDK_Open=0)))
    run=bind(n)
    if stage=='install':
        b.need(not stopped() and root('prepare')['passed'] and
               not (ROOT_META/'original-fallback-attempt.json').exists(),'Preparation absent, stopped or fallback already used')
        b.need(len(list(ROOT_META.glob('candidate-*-attempt.json')))==n-1,'Candidate start sequence differs')
        b.need(not all_sdk_attempts(),'SDK already attempted: no additional candidate')
        expected=cfg['board']['pre_start_boot_id']
        if n>1:
            previous=BASE/('run-'+str(n-1))
            gate=read(previous/'metadata/before-seed.json')
            original=read(previous/'observe-before/capture/result.json')['normalized']
            control=original['control']
            b.need(gate['valid'] is True and gate['classification']=='healthy_no_target' and
                   gate['continue_allowed'] is True and gate['eligible'] is False and
                   gate['boot_id']==original['boot_id']==b.boot_id() and
                   not control['arm_used'] and not control['arm_issued'] and not control['rearm_used'] and
                   all(original[key]==0 for key in ('SDK','DMA','HDMI_START')) and
                   not (previous/'metadata/consume.attempt.json').exists() and
                   not (previous/'metadata/checker-rearm.attempt.json').exists(),
                   'Earlier startup not untouched healthy_no_target: no next candidate')
            expected=restored_context(previous)
            bind(n)
        b.audit(ORIGINAL,expected);b.checked_backup()
        run.mkdir(mode=0o700);b.META.mkdir(mode=0o700);b.MOUNT.mkdir(mode=0o700)
        return b.replace_boot(PACKAGE/'BOOT-candidate.bin',ORIGINAL,CANDIDATE,'install','install.json')
    if stage=='candidate-reboot':
        b.need(not stopped() and not (ROOT_META/'original-fallback-attempt.json').exists(),
               'Stopped/fallback package cannot start another candidate')
        installed=read(b.META/'install.json')
        b.need(installed['passed'] is True and installed['BOOT_sha256']==CANDIDATE,'Candidate install incomplete')
        b.need(len(list(ROOT_META.glob('candidate-*-attempt.json')))==n-1,'Candidate command budget/sequence differs')
        return reboot('candidate-'+str(n),CANDIDATE,installed['boot_id'])
    if stage=='restore':
        attempt=root('candidate-'+str(n)+'-attempt')
        b.need(attempt['boot_id']!=b.boot_id() and root('candidate-'+str(n)+'-issued')['command_issued'],
               'Candidate runtime has not started')
        b.audit(CANDIDATE)
        return b.replace_boot(PACKAGE/'BOOT-original.readback.bin',CANDIDATE,ORIGINAL,'restore','restore.json')
    if stage=='fallback-reboot':
        identity=restored_context(run)
        b.need(not (ROOT_META/'original-fallback-attempt.json').exists(),'Final fallback already consumed')
        return reboot('original-fallback',ORIGINAL,identity)
    identity=restored_context(run)
    if stage in DIAGNOSTICS:
        recovery_evidence=stage in ('post-frame-protocol','post-joint-protocol')
        b.need(not stopped() or recovery_evidence or (stage=='revalidate-consume' and not (ROOT_META/'diagnostic-continuation-stopped.json').exists()),'Unknown/failed action already stopped r45')
        if recovery_evidence:
            name='frame-test' if stage=='post-frame-protocol' else 'joint-test'
            b.need((run/'metadata'/(name+'.attempt.json')).exists(),'No corresponding SDK attempt to capture')
        else:b.need(not all_sdk_attempts(),'Startup diagnostics cannot run after an SDK attempt')
        b.reserve(stage,dict(SDK=0,DMA=0,HDMI_START=0,physical_key=0,automatic_retry=False))
        sys.path.insert(0,str(asset('r45_diagnostic_stages.py').parent))
        from r45_diagnostic_stages import diagnostic_stage
        result=diagnostic_stage(stage,run,PACKAGE,identity,lambda name,argv_fn:child(run,name,argv_fn))
        if not result.get('valid',False):mark_stopped(stage,n,result)
        elif stage=='revalidate-consume':save(ROOT_META/'consume-parser-resolution.json',result)
        return result
    if stage in ('frame-test','joint-test'):
        b.need(not stopped(),'Unknown/failed action already stopped r45 functionality')
        functional_context(run,stage)
        result=frame_stage(run) if stage=='frame-test' else joint_stage(run)
        if not result.get('passed',False):mark_stopped(stage,n,result)
        return result
    raise RuntimeError('Unknown explicit r45 stage')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=('audit','prepare','install','candidate-reboot','restore',
         'frame-test','joint-test','fallback-reboot','close')+DIAGNOSTICS)
    parser.add_argument('--cycle',type=int,default=1)
    args=parser.parse_args()
    try:
        result=main(args.stage,args.cycle)
        keys=('passed','valid','eligible','classification','continue_allowed','boot_id','BOOT_sha256',
              'closed','command_issued','helper_pid','candidate_starts','SDK_Open_attempts')
        print(json.dumps({key:result[key] for key in keys if key in result}),flush=True)
        if result.get('passed') is False or result.get('valid') is False:raise SystemExit(2)
    except Exception as error:
        if b is not None and args.stage not in ('audit','restore','fallback-reboot','close'):
            try:mark_stopped(args.stage,args.cycle,dict(error=str(error)))
            except Exception as secondary:print('Failure latch preservation failed: '+str(secondary),file=sys.stderr)
        print(json.dumps(dict(error=str(error),automatic_retry=False)),file=sys.stderr)
        raise


"""One fresh candidate, one AI+HDMI long load, one original fallback. No retry."""
from pathlib import Path
import argparse,importlib,json,os,shutil,signal,subprocess,sys,time
BASE=Path(__file__).resolve().parent;META=BASE/'metadata';PACKAGE=BASE/'package'
SUPPORT=Path('/root/hdmi-reset-calibration-20261018-r20/board_support.py')
cfg=b=None
def read(p):return json.loads(p.read_text())
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2)
    return v
def initialize():
    global cfg,b
    cfg=read(BASE/'config.json');sys.path.insert(0,str(SUPPORT.parent));b=importlib.import_module('board_support')
    b.CFG=cfg;b.ROOT=BASE;b.META=META;b.PACKAGE=PACKAGE;b.MOUNT=BASE/'boot-mount'
    b.identity_record=lambda v:dict(v,package_id=cfg['package_id'])
def authorize():
    initialize();auth=read(BASE/'authorization.json')
    b.need(cfg['package_id']=='hdmi-pipeline-r53' and cfg['base']==str(BASE),'Wrong actual package')
    b.need(auth['active'] and auth['caps']==cfg['caps'] and cfg['caps']['candidate_starts']==1 and
           cfg['caps']['original_fallbacks']==cfg['caps']['SDK_Open']==1,'Bounded authorization differs')
    b.need(not (META/'closed.json').exists(),'Package closed')
    b.verify_file(SUPPORT,cfg['support_identity'])
    for name,row in cfg['controller_files'].items():b.verify_file(BASE/name,row)
    for name,row in cfg['files'].items():b.verify_file(PACKAGE/name,row)
def reserve(stage,**data):return save(META/(stage+'.attempt.json'),dict(boot_id=b.boot_id(),automatic_retry=False,**data))
def stopped():return (META/'stopped.json').exists()
def stop(stage,error):
    if not stopped():save(META/'stopped.json',dict(stage=stage,error=str(error),boot_id=b.boot_id(),automatic_retry=False))
def owners():
    sys.path.insert(0,str(PACKAGE));import capture_deferred as c
    return b.owners()+c.owners()
def restored():
    r=read(META/'restore.json');identity=b.boot_id()
    b.need(r['passed'] and r['boot_id']==identity and r['BOOT_sha256']==cfg['original_boot_sha256'] and
           r['other_startup_files_unchanged'] and r['boot_partition_unmounted'] and not owners(),
           'Original BOOT file/restored candidate identity differs')
    return identity
def reboot(stage,expected):
    b.audit(expected);reserve(stage)
    p=subprocess.Popen(['/bin/sh','-c','sleep 2; exec /sbin/reboot'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    return save(META/(stage+'-issued.json'),dict(command_issued=True,helper_pid=p.pid,boot_id=b.boot_id()))
def request_native_stop(guard,run):
    pidfile=run/'pid'
    if pidfile.exists():
        pid=int(pidfile.read_text());exe=Path('/proc')/str(pid)/'exe'
        if exe.exists():
            b.need(exe.resolve()==(BASE/'software/pose_demo_v1').resolve(),'SDK PID identity changed')
            os.kill(pid,signal.SIGTERM)
    elif not owners():guard.terminate() # No native SDK process exists yet.
def long_stage():
    identity=restored();admission=read(BASE/'startup-admission.json')
    b.need(admission['passed'] and admission['boot_id']==identity and admission['observer_generation']==4,
           'Startup admission absent')
    b.audit(cfg['original_boot_sha256'],identity)
    software=BASE/'software';manifest=read(software/'identity.json')
    b.need(manifest['libraries']==cfg['board']['SDK'],'Actual SDK identity differs')
    for name,digest in manifest['files'].items():b.need(b.digest(software/name)==digest,'Software payload changed: '+name)
    host=read(BASE/'host-session.json')
    b.need(host['count']==52800 and host['hz']==30,'Original long-chain host rate/count differs')
    reserve('long-test',SDK_Open=1,inference=True,HDMI_START=True,frames=52800,input_hz=30,hard_seconds=2100)
    sys.path.insert(0,str(PACKAGE));import capture_deferred as c
    out=BASE/'long-test';out.mkdir(mode=0o700)
    evidence=c.Evidence(out/'protocol-running');io=None;failure=None;controls=[]
    mask=((1<<160)-1)^sum(1<<i for i in (92,93,95))
    def pc_snapshot():
        c.wait_command(io,c.CTRL,c.SNAP,evidence)
        ctrl=c.read_control(io,evidence);controls.append(ctrl)
        b.need(ctrl['PC_checker_ready'] and ctrl['PC_system_resetn'] and not ctrl['error'] and
               not ctrl['full_PC_status']&mask,'Fresh native protocol/capacity error')
        return ctrl
    os.chmod(software/'pose_demo_v1',0o700)
    argv=['python3',str(software/'board_guard.py'),'--stage','stress','--frames','52800',
          '--run-name','long-native','--session',str(host['session']),'--max-seconds','2100']
    save(out/'command.json',dict(argv=argv,SDK_Open_limit=1,automatic_retry=False))
    start=time.monotonic();run=software/'run-long-native'
    try:
        io=c.MMIO(evidence,identity);pc_snapshot() # Before SDK launch.
        with (out/'stdout.log').open('xb') as so,(out/'stderr.log').open('xb') as se:
            process=subprocess.Popen(argv,stdout=so,stderr=se,stdin=subprocess.DEVNULL,start_new_session=True)
            save(META/'long-process.json',dict(pid=process.pid,boot_id=identity,argv=argv))
            next_pc=start+10;next_report=start+30
            while process.poll() is None:
                now=time.monotonic()
                if failure is None and now>=next_pc:
                    try:
                        b.need(b.boot_id()==identity,'Runtime identity changed')
                        pc_snapshot()
                    except Exception as error:
                        failure=str(error);stop('long-native-protocol',failure);request_native_stop(process,run)
                    next_pc=now+10
                if now>=next_report:
                    print(json.dumps(dict(stage='long-test',guard_pid=process.pid,elapsed_seconds=now-start,protocol_snapshots=len(controls),error=failure)),flush=True)
                    next_report=now+30
                try:process.wait(timeout=1)
                except subprocess.TimeoutExpired:pass
            code=process.returncode
        if failure is None:
            try:pc_snapshot()
            except Exception as error:failure=str(error);stop('long-native-protocol-final',failure)
    finally:
        if io is not None:io.close()
        evidence.close()
    results=run/'results';summary=read(results/'summary.json') if (results/'summary.json').exists() else {}
    rows=[json.loads(x) for x in (results/'hdmi.jsonl').read_text().splitlines()] if (results/'hdmi.jsonl').exists() else []
    adopted=[x for x in rows if x.get('event')=='adopted']
    status=read(run/'guard-summary.json') if (run/'guard-summary.json').exists() else {}
    passed=(code==0 and failure is None and b.boot_id()==identity and not owners() and
            all(summary.get(k)==52800 for k in ('received','completed','sent','host_archived')) and
            summary.get('engine_destroyed') is True and len(adopted)==52800 and
            sum(x.get('event')=='stop_proved' for x in rows)==1 and
            sum(x.get('event')=='frames_released_after_stop' for x in rows)==1 and
            status.get('boot_id_unchanged') and status.get('SDK_unchanged') and not status.get('resource_danger'))
    result=dict(passed=bool(passed),valid=b.boot_id()==identity,boot_id=identity,native_exit=code,
        seconds=time.monotonic()-start,SDK_Open_attempts=1,startup_mode=admission['mode'],
        summary=summary,HDMI_adopted=len(adopted),protocol_snapshots=len(controls),
        all_fresh_native_protocol_checks_passed=failure is None,protocol_failure=failure,
        guard=status,physical_screen_verified=False,automatic_retry=False)
    save(META/'long-test.json',result)
    if not passed:stop('long-test',result)
    return result
def main(stage):
    authorize();original=cfg['original_boot_sha256'];candidate=cfg['files']['BOOT-candidate.bin']['sha256']
    if stage=='audit':return b.audit(original)
    if stage=='prepare':
        b.need(not stopped(),'Stopped package');b.audit(original,cfg['board']['pre_start_boot_id'])
        b.checked_backup()
        return save(META/'prepare.json',dict(passed=True,boot_id=b.boot_id()))
    if stage=='install':
        b.need(not stopped() and read(META/'prepare.json')['passed'],'Preparation absent')
        b.checked_backup() # replace_boot reserves install before its first mount/write.
        return b.replace_boot(PACKAGE/'BOOT-candidate.bin',original,candidate,'install','install.json')
    if stage=='candidate-reboot':
        b.need(not stopped() and read(META/'install.json')['passed'],'Install absent')
        return reboot(stage,candidate)
    if stage=='restore':
        prior=read(META/'candidate-reboot.attempt.json')['boot_id']
        b.need(prior!=b.boot_id() and read(META/'candidate-reboot-issued.json')['command_issued'],'Candidate not started')
        b.audit(candidate);return b.replace_boot(PACKAGE/'BOOT-original.readback.bin',candidate,original,'restore','restore.json')
    if stage=='startup':
        identity=restored();b.need(not stopped(),'Stopped package');reserve(stage,SDK=0)
        from bootstrap import bootstrap
        result=bootstrap(BASE,identity);return save(META/'startup.json',result)
    if stage=='long-test':
        b.need(not stopped(),'Stopped package');return long_stage()
    if stage=='fallback-reboot':restored();return reboot(stage,original)
    if stage=='close':
        prior=read(META/'fallback-reboot.attempt.json')['boot_id'];identity=b.boot_id()
        b.need(prior!=identity and read(META/'fallback-reboot-issued.json')['command_issued'],'Fallback not started')
        audit=b.audit(original,identity)
        b.need(len(audit['startup_files'])==9 and len(audit['SDK'])==6 and audit['fpga_state']=='operating' and not owners(),'Original runtime audit incomplete')
        save(META/'final-audit.json',audit)
        return save(META/'closed.json',dict(closed=True,boot_id=identity,candidate_starts=1,original_fallbacks=1,
            SDK_Open_attempts=int((META/'long-test.attempt.json').exists()),remaining=dict(candidate_starts=0,original_fallbacks=0,SDK_Open=0)))
    raise ValueError('Unknown explicit stage')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('audit','prepare','install','candidate-reboot','restore','startup','long-test','fallback-reboot','close'));p.add_argument('--cycle',type=int,default=1);a=p.parse_args()
    try:
        if a.cycle!=1:raise ValueError('Single candidate only')
        result=main(a.stage)
        if a.stage=='long-test':save(META/'long-controller-finished.json',dict(finished=True,passed=result.get('passed',False),result_file='metadata/long-test.json'))
        keys=('passed','valid','boot_id','mode','BOOT_sha256','closed','command_issued','helper_pid','native_exit','seconds','HDMI_adopted')
        print(json.dumps({k:result[k] for k in keys if k in result}),flush=True)
        if result.get('passed') is False:raise SystemExit(2)
    except Exception as error:
        if b is not None and a.stage not in ('audit','restore','fallback-reboot','close'):stop(a.stage,error)
        if b is not None and a.stage=='long-test' and not (META/'long-controller-finished.json').exists():
            save(META/'long-controller-finished.json',dict(finished=True,passed=False,error=str(error),automatic_retry=False))
        print(json.dumps(dict(error=str(error),automatic_retry=False)),file=sys.stderr);raise

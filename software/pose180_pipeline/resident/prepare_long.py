"""Prepare, but never authorize/run, the finite autonomous joint demo package."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[3]
SOURCE=Path(__file__).resolve().parent
ID='pose180-resident-long-20261025-r4'
OUT=ROOT/'.local'/ID
REMOTE='/root/demo-v1-20261022-r1/'+ID
CAPS=dict(candidate_starts=1,SDK_Open=1,original_fallbacks=1,runtime_seconds=1800,stop_request_seconds=1920)

def digest(path):
    return dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def pack(directory,target):
    executable={'pose180_demo','router_guard','nexutil','makecsiparams','capture-metadata','capture-metadata-stream'}
    with tarfile.open(target,'x:gz') as archive:
        for path in sorted(directory.rglob('*')):
            if path.is_file():
                info=archive.gettarinfo(str(path),arcname=path.relative_to(directory).as_posix())
                info.mode=0o755 if path.name in executable or path.suffix=='.sh' else 0o600
                with path.open('rb') as file:archive.addfile(info,file)

def main():
    global ID,OUT,REMOTE,CAPS
    parser=argparse.ArgumentParser(description=__doc__)
    selection=parser.add_mutually_exclusive_group()
    selection.add_argument('--stutter-r5',action='store_true',help='Prepare the r5 stutter-optimization package')
    selection.add_argument('--continuous-r6',action='store_true',help='Prepare the offline r6 renewable TX lease package; no device authorization')
    selection.add_argument('--window-r7',action='store_true',help='Prepare r7 bounded window diagnostics/recovery with qualified r6 TX; no device authorization')
    selection.add_argument('--phase-r8',action='store_true',help='Prepare r8 bounded causal clock tracking and atomic router heartbeat')
    selection.add_argument('--witness-r9',action='store_true',help='Prepare r9 phase tracking with strict passive three-witness corroboration')
    args=parser.parse_args()
    phase_features=args.phase_r8 or args.witness_r9
    continuous=args.continuous_r6 or args.window_r7 or phase_features
    short_run=args.window_r7 or phase_features
    incremental=args.stutter_r5 or continuous
    if args.stutter_r5:
        ID='pose180-resident-stutter-20261025-r5'
        OUT=ROOT/'.local'/ID
        REMOTE='/root/demo-v1-20261022-r1/'+ID
    if args.continuous_r6:
        ID='pose180-resident-continuous-20261025-r6'
        OUT=ROOT/'.local'/ID
        REMOTE='/root/demo-v1-20261022-r1/'+ID
    if args.window_r7:
        ID='pose180-resident-window-20261025-r7'
        OUT=ROOT/'.local'/ID
        REMOTE='/root/demo-v1-20261022-r1/'+ID
        CAPS=dict(candidate_starts=1,SDK_Open=1,original_fallbacks=1,runtime_seconds=600,stop_request_seconds=720)
    if args.phase_r8:
        ID='pose180-resident-phase-20261025-r8'
        OUT=ROOT/'.local'/ID
        REMOTE='/root/demo-v1-20261022-r1/'+ID
        CAPS=dict(candidate_starts=1,SDK_Open=1,original_fallbacks=1,runtime_seconds=600,stop_request_seconds=720)
    if args.witness_r9:
        ID='pose180-resident-witness-20261025-r9'
        OUT=ROOT/'.local'/ID
        REMOTE='/root/demo-v1-20261022-r1/'+ID
        CAPS=dict(candidate_starts=1,SDK_Open=1,original_fallbacks=1,runtime_seconds=600,stop_request_seconds=720)
    source_seconds=780 if short_run else 1980
    watchdog_seconds=900 if short_run else 2400
    helpers=('board_call.py','board_network.py','start_candidate.py','start_fallback.py','capture_uart.py','capture_hdmi_startup.ps1')
    # r5 may already contain its builds/test outputs. A prior package or helper
    # is never overwritten: preparing again needs a new package decision.
    if incremental:
        for name in ('board','software','prepared.json','board-package.tar.gz','radios',*helpers):
            if (OUT/name).exists():raise FileExistsError('Package output already exists: '+str(OUT/name))
    old=ROOT/'.local/pose180-resident-hdmi-20261025-r3'
    old_long=ROOT/'.local/pose180-resident-long-20261025-r4'
    native=OUT/'build/arm64/pose180_demo' if incremental else ROOT/'.local/pose180-resident-20261025/arm64/pose180_demo'
    guard=OUT/'build/router_guard' if incremental else ROOT/'.local/pose180-resident-long-20261025/build/router_guard'
    tx_module=(ROOT/'.local/pose180-resident-continuous-20261025-r6/firmware/dhd.ko') if short_run else OUT/'firmware/dhd.ko'
    if continuous and not tx_module.is_file():raise FileNotFoundError(tx_module)
    capture=ROOT/'.local/pose180-resident-long-20261025/build/capture-metadata-stream'
    for path in (native,guard,capture,old/'board/manifest.json'):
        if not path.is_file():raise FileNotFoundError('Required package input missing: '+str(path))
    OUT.mkdir(exist_ok=incremental)
    board=OUT/'board';board.mkdir();software=OUT/'software';software.mkdir()
    previous=json.loads((old/'board/manifest.json').read_text())
    protected={}
    for name,row in previous['files'].items():
        if name in ('software-package.tar.gz','controller.py'):continue
        target=board/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(old/'board'/name,target)
        if incremental:
            # Immutable qualified BOOT/SDK/support identities were already
            # recorded by r3. Reuse them; only new delivery software is hashed.
            protected[name]=dict(row)
        else:
            protected[name]=digest(target)
            if protected[name]!=row:raise ValueError('Existing qualified asset changed: '+name)
    if args.witness_r9:
        # Pure evidence corroboration only. Preserve the original seed and
        # consumption gates; no offset correction or extra hardware command.
        bootstrap=(board/'bootstrap.py').read_text()
        anchor="        c.fresh_json(run/'before-seed.json', seed)\n"
        if bootstrap.count(anchor)!=1:raise ValueError('Bootstrap integration point differs')
        bootstrap=bootstrap.replace(anchor,anchor+"        witness = _load(base/'witness.py', '_r9_witness')\n"
            "        coherence = witness.compare(before, trace_before, protocol_before)\n"
            "        c.fresh_json(run/'witness-coherence.json', coherence)\n"
            "        _need(coherence['consistent'], 'Native witnesses disagree: '+str(coherence['issues']))\n")
        (board/'bootstrap.py').write_text(bootstrap,newline='\n')
        protected.pop('bootstrap.py',None)
        shutil.copyfile(SOURCE/'witness.py',board/'witness.py')
    shutil.copyfile(native,software/'pose180_demo')
    for name in ('preflight.py','csi.conf'):shutil.copyfile(old/'software'/name,software/name)
    for name in ('run_hdmi_trial.py','service.py','bounded_log.py'):shutil.copyfile(SOURCE/name,software/name)
    identity=json.loads((old/'software/identity.json').read_text())
    identity.update(session=20261025050901 if args.witness_r9 else 20261025050801 if args.phase_r8 else 20261025050701 if args.window_r7 else 20261025050601 if args.continuous_r6 else 20261025050501 if args.stutter_r5 else 20261025050401,
                    seconds=CAPS['runtime_seconds'],detached_supervisor=True)
    identity['files']={p.name:digest(p)['sha256'] for p in software.iterdir()}
    (software/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
    pack(software,board/'software-package.tar.gz')
    controller=(old/'board/controller.py').read_text().replace("ID = 'pose180-resident-hdmi-20261025-r3'",'ID = '+repr(ID))
    start=controller.index('CAPS = ');end=controller.index('\ncfg =',start)
    controller=controller[:start]+'CAPS = '+repr(CAPS)+controller[end:]
    start=controller.index('def run(session):');end=controller.index('\n\ndef main(args):',start)
    controller=controller[:start]+'''def run(session):
    identity = restored()
    admission = read(BASE/'startup-admission.json')
    need(admission['passed'] and admission['boot_id'] == identity, 'Fresh same-boot admission absent')
    reserve('long-test', SDK_Open=1, runtime_seconds=CAPS['runtime_seconds'])
    result = subprocess.run([sys.executable,str(PIPELINE/'service.py'),'start'],
                            check=True,capture_output=True,text=True)
    return save(META/'long-started.json', dict(started=True,boot_id=identity,
                service=json.loads(result.stdout),actual_completion_not_yet_known=True))


def service_result():
    result = read(PIPELINE/'outcome.json')
    final = result.get('final_status',{})
    result['passed'] = bool(result.get('native_exit') == 0 and result.get('native_shutdown_complete')
        and not result.get('device_owners') and not owners()
        and b.boot_id() == read(BASE/'startup-admission.json')['boot_id']
        and final.get('inferred',0)>0 and 0<final.get('adopted',0)<=final.get('inferred',0))
    result.update(physical_screen_verified=False,PC_physical_offline_verified=False,
                  RX_physical_recovery_verified=False,long_duration_accepted=False)
    return save(META/'long-test.json',result)
''' + controller[end:]
    controller=controller.replace("if stage == 'run':\n        return run(args.session)",
        "if stage == 'run':\n        return run(args.session)\n    if stage in ('status','stop'):\n        result=subprocess.run([sys.executable,str(PIPELINE/'service.py'),stage],check=True,capture_output=True,text=True)\n        return json.loads(result.stdout)\n    if stage == 'result':\n        return service_result()")
    controller=controller.replace("'restore','startup','run','fallback-reboot','close'))", "'restore','startup','run','status','stop','result','fallback-reboot','close'))")
    controller=controller.replace("int((META/'long-test.attempt.json').exists())", "int((PIPELINE/'sdk-attempt.json').exists())")
    controller=controller.replace("print(json.dumps({key: result[key] for key in keys if key in result}), flush=True)",
        "print(json.dumps(result if args.stage in ('run','status','stop') else {key: result[key] for key in keys if key in result}), flush=True)")
    (board/'controller.py').write_text(controller,newline='\n')
    marker='POSE180_RESIDENT_WITNESS_R9_' if args.witness_r9 else 'POSE180_RESIDENT_PHASE_R8_' if args.phase_r8 else 'POSE180_RESIDENT_WINDOW_R7_' if args.window_r7 else 'POSE180_RESIDENT_CONTINUOUS_R6_' if args.continuous_r6 else 'POSE180_RESIDENT_STUTTER_R5_' if args.stutter_r5 else 'POSE180_RESIDENT_LONG_R4_'
    for name in helpers:
        text=(old/name).read_text(encoding='utf-8-sig').replace('pose180-resident-hdmi-20261025-r3',ID).replace('POSE180_RESIDENT_HDMI_R3_',marker)
        (OUT/name).write_text(text,encoding='utf-8',newline='\n')
    if short_run:
        # Reuse the actually exercised, identity-checked read-only UART entry,
        # replacing the obsolete generic script's unrelated output directory.
        previous_run=ROOT/'.local/pose180-resident-continuous-20261025-r6'
        for stage in ('candidate-1','fallback'):
            text=(previous_run/('uart-'+stage+'-reader.ps1')).read_text().replace(previous_run.name,ID)
            (OUT/('uart-'+stage+'-reader.ps1')).write_text(text,newline='\n')
        (OUT/'capture_hdmi_startup.ps1').write_text((OUT/'uart-candidate-1-reader.ps1').read_text(),newline='\n')
    shutil.copyfile(OUT/'board_network.py',board/'board_network.py')
    manifest={k:v for k,v in previous.items() if k not in ('files','source_reference')}
    manifest.update(package_id=ID,base=REMOTE,caps=CAPS,status='prepared_pending_explicit_BOOT_authorization',
                    source_reference='software/pose180_pipeline/resident; '+('strict passive three-witness corroboration; r8 causal phase tracking and atomic heartbeat' if args.witness_r9 else 'causal bounded grid phase tracking; atomic router heartbeat; qualified r6 TX and HDMI' if args.phase_r8 else 'bounded common-window rejection diagnostics and earlier alignment recovery; qualified r6 TX and HDMI' if args.window_r7 else 'renewable TX firmware lease, autonomous guard, PC-style HDMI view' if args.continuous_r6 else 'bounded recovery diagnostics, local RX recovery, TX handoff and HDMI waiting states' if args.stutter_r5 else 'lifecycle and capped logs')+', unchanged SDK/model preprocessing/RTL')
    if incremental:
        manifest['protected_identity_reference']='.local/pose180-resident-hdmi-20261025-r3/board/manifest.json'
    manifest['board']['remote_root']=REMOTE
    manifest['files']={**protected,**{p.relative_to(board).as_posix():digest(p) for p in board.rglob('*') if p.is_file() and p.relative_to(board).as_posix() not in protected}}
    (board/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (board/'authorization.json').write_text(json.dumps(dict(package_id=ID,active=False,caps=CAPS,user_confirmation=None),indent=2)+'\n')
    pack(board,OUT/'board-package.tar.gz')
    radios=OUT/'radios';radios.mkdir()
    if not args.stutter_r5:
        spec=importlib.util.spec_from_file_location('tx_job',ROOT/'tools/nexmon/host/router_tx_job.py')
        tx=importlib.util.module_from_spec(spec);spec.loader.exec_module(tx)
    # The same new guard/control files are copied to four devices; compute each
    # new source identity once and reuse it in each transfer manifest.
    shared_checks={'router_guard':digest(guard)['sha256'],
                   'router_ctl.sh':digest(SOURCE/'router_ctl.sh')['sha256'],
                   'watchdog.sh':digest(SOURCE/'router_watchdog.sh')['sha256']}
    for role in ('rx1','tx','rx2','rx3'):
        folder=radios/role;folder.mkdir()
        previous_root=ROOT/'.local/pose180-resident-20261025/direct'/role
        prior='/tmp/nexmon-direct-20261025-r2-'+role
        remote=('/tmp/nexmon-resident-witness-20261025-r9-' if args.witness_r9 else '/tmp/nexmon-resident-phase-20261025-r8-' if args.phase_r8 else '/tmp/nexmon-resident-window-20261025-r7-' if args.window_r7 else '/tmp/nexmon-resident-continuous-20261025-r6-' if args.continuous_r6 else '/tmp/nexmon-resident-stutter-20261025-r5-' if args.stutter_r5 else '/tmp/nexmon-resident-long-20261025-r4-')+role
        names=['dhd-csi.ko','nexutil'] if role=='tx' else ['dhd-csi.ko','nexutil','makecsiparams','capture-metadata']
        radio_source=old_long/'radios'/role if incremental else previous_root
        unchanged={}
        if incremental:
            recorded={name:sha for sha,name in (line.split(maxsplit=1) for line in (radio_source/'transfer.sha256').read_text().splitlines() if line.strip())}
            for name in names:unchanged[name]=recorded[name]
            if role!='tx':unchanged['capture-metadata-stream']=recorded['capture-metadata-stream']
        for name in names:shutil.copyfile(radio_source/name,folder/name)
        previous_tx_hash=unchanged.get('dhd-csi.ko')
        if continuous and role=='tx':
            shutil.copyfile(tx_module,folder/'dhd-csi.ko')
            unchanged['dhd-csi.ko']=digest(tx_module)['sha256']
            (folder/'tx.lease').write_text('mode3 / 60s lease / local renewal / no automatic restart\n',newline='\n')
        shutil.copyfile(guard,folder/'router_guard')
        if role!='tx':shutil.copyfile(capture,folder/'capture-metadata-stream')
        for name in ('stage.sh','load.sh','restore.sh'):
            text=(previous_root/name).read_text().replace(prior,remote)
            if phase_features and name=='load.sh':
                text=text.replace('cut -d. -f1 /proc/uptime > lease','cut -d. -f1 /proc/uptime > lease.load.tmp && mv lease.load.tmp lease')
            if continuous and role=='tx' and name=='load.sh':
                text=text.replace(previous_tx_hash,unchanged['dhd-csi.ko'])
            if name=='stage.sh':
                (radios/(role+'-stage.sh')).write_text(text,newline='\n');continue
            if name=='restore.sh':
                begin=text.index('if [ -f capture.pid ]');end=text.index('/usr/sbin/wl',begin)
                text=text[:begin]+'''touch stop.request
if [ -f capture.pid ]; then
 pid=$(cat capture.pid)
 if [ -r /proc/$pid/cmdline ] && [ "$(readlink /proc/$pid/cwd)" = "$PWD" ] && grep -q 'capture-metadata-stream' /proc/$pid/cmdline; then
  kill -TERM "$pid" 2>/dev/null || true
  sleep 1
 fi
fi
'''+text[end:]
                if role=='tx':
                    cleanup=('if [ ! -e tx.released ]; then\n ./nexutil -Ieth6 -s431 || true\n ./nexutil -Ieth6 -s432 || true\nfi\n'
                             if continuous else './nexutil -Ieth6 -s432 || true\n')
                    text=text.replace('/usr/sbin/wl -i eth6 monitor',cleanup+'/usr/sbin/wl -i eth6 monitor',1)
            (folder/name).write_text(text,newline='\n')
        shutil.copyfile(SOURCE/'router_watchdog.sh',folder/'watchdog.sh')
        if short_run:
            (folder/'watchdog.sh').write_text((folder/'watchdog.sh').read_text().replace('-gt 2400','-gt '+str(watchdog_seconds)),newline='\n')
        shutil.copyfile(SOURCE/'router_ctl.sh',folder/'router_ctl.sh')
        (folder/'guard.conf').write_text('GUARD_ROLE='+('tx' if role=='tx' else 'rx')+'\nGUARD_SECONDS='+str(source_seconds)+'\n',newline='\n')
        if role=='tx':
            if args.stutter_r5:
                # Exact r4 RF/frame contract, including its original payload
                # label. r5 only changes the host-side scheduling/diagnostics.
                shutil.copyfile(radio_source/'run.params',folder/'run.params')
                shutil.copyfile(old_long/'radios/tx-profile.json',radios/'tx-profile.json')
                unchanged['run.params']=recorded['run.params']
            else:
                job=tx.make_job('f0:2f:74:39:45:6c',300,60,'resident-r4',lease=continuous)
                if job['parameter_bytes']!=64:raise ValueError('TX parameter contract changed')
                (folder/'run.params').write_text(job['parameters_base64']+'\n')
                (radios/'tx-profile.json').write_text(json.dumps(job,indent=2)+'\n')
        checks={**unchanged,**shared_checks}
        if short_run:checks['watchdog.sh']=digest(folder/'watchdog.sh')['sha256']
        checks.update({p.name:digest(p)['sha256'] for p in folder.iterdir() if p.is_file() and p.name not in checks})
        (folder/'transfer.sha256').write_text(''.join(v+'  '+k+'\n' for k,v in checks.items()),newline='\n')
        pack(folder,radios/(role+'.tar.gz'))
        (radios/(role+'-extract.sh')).write_text('set -e\ncd '+remote+'\ntar xzf package.tar.gz\n'
            'tr -d \'\\r\' < transfer.sha256 | while read -r expected file; do actual=$(openssl dgst -sha256 "$file" | awk \'{print $NF}\'); '
            'test "$actual" = "$expected" || exit 1; printf "%s: OK\\n" "$file"; done\n',newline='\n')
    generated_python=[*(board.rglob('*.py')),*(software.rglob('*.py')),
                      *(OUT/name for name in helpers if name.endswith('.py'))]
    for path in generated_python:compile(path.read_text(encoding='utf-8-sig'),str(path),'exec')
    result=dict(package_id=ID,archive=digest(OUT/'board-package.tar.gz'),caps=CAPS,
                authorization_active=False,BOOT_writes=0,reboots=0,SDK=0,
                router_source_seconds=source_seconds,router_watchdog_hard_seconds=watchdog_seconds,
                native_logs_max_bytes=2097152,resource_logs_max_bytes=524288)
    if continuous:
        result.update(TX_mode=3,TX_lease_seconds=60,TX_renew_seconds=10,
                      hardware_tested=False)
        result['TX_firmware_sha256']=next(line.split()[0] for line in (radios/'tx/transfer.sha256').read_text().splitlines() if line.split()[1]=='dhd-csi.ko')
    (OUT/'prepared.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()

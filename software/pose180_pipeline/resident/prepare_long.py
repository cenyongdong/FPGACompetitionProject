"""Prepare, but never authorize/run, the finite autonomous joint demo package."""
from pathlib import Path
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
    OUT.mkdir();board=OUT/'board';board.mkdir();software=OUT/'software';software.mkdir()
    old=ROOT/'.local/pose180-resident-hdmi-20261025-r3'
    previous=json.loads((old/'board/manifest.json').read_text())
    protected={}
    for name,row in previous['files'].items():
        if name in ('software-package.tar.gz','controller.py'):continue
        target=board/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(old/'board'/name,target)
        protected[name]=digest(target)
        if protected[name]!=row:raise ValueError('Existing qualified asset changed: '+name)
    shutil.copyfile(ROOT/'.local/pose180-resident-20261025/arm64/pose180_demo',software/'pose180_demo')
    for name in ('preflight.py','csi.conf'):shutil.copyfile(old/'software'/name,software/name)
    for name in ('run_hdmi_trial.py','service.py','bounded_log.py'):shutil.copyfile(SOURCE/name,software/name)
    identity=json.loads((old/'software/identity.json').read_text())
    identity.update(session=20261025050401,seconds=CAPS['runtime_seconds'],detached_supervisor=True)
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
    for name in ('board_call.py','board_network.py','start_candidate.py','start_fallback.py','capture_uart.py','capture_hdmi_startup.ps1'):
        text=(old/name).read_text(encoding='utf-8-sig').replace('pose180-resident-hdmi-20261025-r3',ID).replace('POSE180_RESIDENT_HDMI_R3_','POSE180_RESIDENT_LONG_R4_')
        (OUT/name).write_text(text,encoding='utf-8',newline='\n')
    shutil.copyfile(OUT/'board_network.py',board/'board_network.py')
    manifest={k:v for k,v in previous.items() if k not in ('files','source_reference')}
    manifest.update(package_id=ID,base=REMOTE,caps=CAPS,status='prepared_pending_explicit_BOOT_authorization',
                    source_reference='software/pose180_pipeline/resident; lifecycle and capped logs, unchanged SDK/math/RTL')
    manifest['board']['remote_root']=REMOTE
    manifest['files']={**protected,**{p.relative_to(board).as_posix():digest(p) for p in board.rglob('*') if p.is_file() and p.relative_to(board).as_posix() not in protected}}
    (board/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (board/'authorization.json').write_text(json.dumps(dict(package_id=ID,active=False,caps=CAPS,user_confirmation=None),indent=2)+'\n')
    pack(board,OUT/'board-package.tar.gz')
    radios=OUT/'radios';radios.mkdir()
    spec=importlib.util.spec_from_file_location('tx_job',ROOT/'tools/nexmon/host/router_tx_job.py')
    tx=importlib.util.module_from_spec(spec);spec.loader.exec_module(tx)
    for role in ('rx1','tx','rx2','rx3'):
        folder=radios/role;folder.mkdir()
        previous_root=ROOT/'.local/pose180-resident-20261025/direct'/role
        prior='/tmp/nexmon-direct-20261025-r2-'+role
        remote='/tmp/nexmon-resident-long-20261025-r4-'+role
        names=['dhd-csi.ko','nexutil'] if role=='tx' else ['dhd-csi.ko','nexutil','makecsiparams','capture-metadata']
        for name in names:shutil.copyfile(previous_root/name,folder/name)
        shutil.copyfile(ROOT/'.local/pose180-resident-long-20261025/build/router_guard',folder/'router_guard')
        if role!='tx':shutil.copyfile(ROOT/'.local/pose180-resident-long-20261025/build/capture-metadata-stream',folder/'capture-metadata-stream')
        for name in ('stage.sh','load.sh','restore.sh'):
            text=(previous_root/name).read_text().replace(prior,remote)
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
                if role=='tx':text=text.replace('/usr/sbin/wl -i eth6 monitor', './nexutil -Ieth6 -s432 || true\n/usr/sbin/wl -i eth6 monitor',1)
            (folder/name).write_text(text,newline='\n')
        shutil.copyfile(SOURCE/'router_watchdog.sh',folder/'watchdog.sh')
        shutil.copyfile(SOURCE/'router_ctl.sh',folder/'router_ctl.sh')
        (folder/'guard.conf').write_text('GUARD_ROLE='+('tx' if role=='tx' else 'rx')+'\nGUARD_SECONDS=1980\n',newline='\n')
        if role=='tx':
            job=tx.make_job('f0:2f:74:39:45:6c',300,60,'resident-r4')
            if job['parameter_bytes']!=64:raise ValueError('TX parameter contract changed')
            (folder/'run.params').write_text(job['parameters_base64']+'\n')
            (radios/'tx-profile.json').write_text(json.dumps(job,indent=2)+'\n')
        checks={p.name:digest(p)['sha256'] for p in folder.iterdir() if p.is_file()}
        (folder/'transfer.sha256').write_text(''.join(v+'  '+k+'\n' for k,v in checks.items()),newline='\n')
        pack(folder,radios/(role+'.tar.gz'))
        (radios/(role+'-extract.sh')).write_text('set -e\ncd '+remote+'\ntar xzf package.tar.gz\n'
            'tr -d \'\\r\' < transfer.sha256 | while read -r expected file; do actual=$(openssl dgst -sha256 "$file" | awk \'{print $NF}\'); '
            'test "$actual" = "$expected" || exit 1; printf "%s: OK\\n" "$file"; done\n',newline='\n')
    for path in OUT.rglob('*.py'):compile(path.read_text(encoding='utf-8-sig'),str(path),'exec')
    result=dict(package_id=ID,archive=digest(OUT/'board-package.tar.gz'),caps=CAPS,
                authorization_active=False,BOOT_writes=0,reboots=0,SDK=0,
                router_source_seconds=1980,router_watchdog_hard_seconds=2400,
                native_logs_max_bytes=2097152,resource_logs_max_bytes=524288)
    (OUT/'prepared.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()

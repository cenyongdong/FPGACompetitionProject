"""Prepare a fresh, inactive HDMI package from qualified existing assets."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[3]
ID='pose180-resident-hdmi-20261025-r3'
REMOTE='/root/demo-v1-20261022-r1/'+ID
OUT=ROOT/'.local'/ID
CAPS=dict(candidate_starts=1,SDK_Open=1,original_fallbacks=1,runtime_seconds=180,stop_request_seconds=240)

def digest(path):return dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def archive(directory,target):
    with tarfile.open(target,'x:gz') as result:
        for path in sorted(directory.rglob('*')):
            if path.is_file():
                info=result.gettarinfo(str(path),arcname=path.relative_to(directory).as_posix())
                if path.name=='pose180_demo':info.mode=0o755
                with path.open('rb') as source:result.addfile(info,source)

def main():
    OUT.mkdir();board=OUT/'board';board.mkdir();software=OUT/'software';software.mkdir()
    old=ROOT/'.local/pose180-hdmi-20261025-r2'
    previous=json.loads((old/'board/manifest.json').read_text())
    # Qualified BOOT and existing admission/restore primitives are reused once.
    for relative in previous['files']:
        if relative=='software-package.tar.gz' or relative=='controller.py':continue
        target=board/relative;target.parent.mkdir(exist_ok=True,parents=True)
        shutil.copyfile(old/'board'/relative,target)
        if digest(target)!=previous['files'][relative]:raise ValueError('Qualified support asset differs: '+relative)
    trial=ROOT/'.local/pose180-resident-20261025/direct/sdk2'
    for name in ('pose180_demo','preflight.py','csi.conf'):shutil.copyfile(trial/name,software/name)
    shutil.copyfile(Path(__file__).with_name('run_hdmi_trial.py'),software/'run_board.py')
    (software/'pose180_demo').chmod(0o755)
    identity=json.loads((trial/'identity.json').read_text());identity.pop('boot_id',None)
    identity.update(session=20261025050301,seconds=180,hdmi=True,CSI_live=True)
    identity['files']={p.name:digest(p)['sha256'] for p in software.iterdir()}
    (software/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
    archive(software,board/'software-package.tar.gz')
    controller=(old/'board/controller.py').read_text().replace("ID = 'pose180-hdmi-20261025-r2'",'ID = '+repr(ID))
    start=controller.index('CAPS = dict(');end=controller.index('\ncfg =',start)
    controller=controller[:start]+'CAPS = '+repr(CAPS)+controller[end:]
    controller=controller.replace('archive.extractall(PIPELINE)',"archive.extractall(PIPELINE)\n    os.symlink("+repr(identity['model_package']+'/models')+", PIPELINE/'models')")
    start=controller.index('def run(session):');end=controller.index('\n\ndef main(args):',start)
    controller=controller[:start]+'''def run(session):
    identity = restored()
    admission = read(BASE/'startup-admission.json')
    need(admission['passed'] and admission['boot_id'] == identity
         and admission['observer_generation'] == 4, 'Same-boot startup admission absent')
    b.audit(cfg['original_boot_sha256'], identity)
    reserve('long-test', SDK_Open=1, runtime_seconds=180, stop_request_seconds=240)
    argv = [sys.executable, str(PIPELINE/'run_board.py')]
    save(META/'long-command.json', dict(argv=argv, boot_id=identity, automatic_retry=False))
    with (META/'long.stdout.log').open('xb') as stdout, (META/'long.stderr.log').open('xb') as stderr:
        child = subprocess.Popen(argv, stdout=stdout, stderr=stderr, start_new_session=True)
        save(META/'long-process.json', dict(pid=child.pid,
             start_ticks=Path('/proc/%d/stat'%child.pid).read_text().split()[21], boot_id=identity, argv=argv))
        while child.poll() is None:
            try: child.wait(timeout=30)
            except subprocess.TimeoutExpired: print(json.dumps(dict(stage='resident',pid=child.pid)),flush=True)
    outcome = read(PIPELINE/'outcome.json') if (PIPELINE/'outcome.json').exists() else {}
    status = outcome.get('final_status',{})
    passed = child.returncode == 0 and outcome.get('native_exit') == 0 and not outcome.get('stop_reason') \\
             and b.boot_id() == identity and not owners() and status.get('inferred',0)>0 \\
             and 0<status.get('adopted',0)<=status.get('inferred',0)
    return save(META/'long-test.json', dict(passed=bool(passed),native_exit=child.returncode,
        outcome=outcome,CSI_live=True,SDK_Open_attempts=1,physical_screen_verified=False,
        strict30Hz_required=False,numerical_accuracy_accepted=False,automatic_retry=False))
''' + controller[end:]
    (board/'controller.py').write_text(controller,newline='\n')
    for name in ('board_call.py','start_candidate.py','start_fallback.py','capture_uart.py','capture_hdmi_startup.ps1'):
        text=(old/name).read_text(encoding='utf-8-sig').replace('pose180-hdmi-20261025-r2',ID).replace('POSE180_HDMI_R2_','POSE180_RESIDENT_HDMI_R3_')
        (OUT/name).write_text(text,encoding='utf-8',newline='\n')
    manifest={k:v for k,v in previous.items() if k not in ('files','local_validation','prior_run_fact','precondition','source_commit')}
    manifest.update(package_id=ID,base=REMOTE,caps=CAPS,status='prepared_pending_explicit_BOOT_authorization',
        CSI_live=True,precondition='Fresh existing admission passes; unexpected shared-bus state ends this package. No D45 root-cause expansion.',
        source_reference='software/pose180_pipeline/resident; exact tested binary from direct/sdk2/identity.json')
    manifest['board']['remote_root']=REMOTE
    manifest['files']={p.relative_to(board).as_posix():digest(p) for p in board.rglob('*') if p.is_file()}
    (board/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (board/'authorization.json').write_text(json.dumps(dict(package_id=ID,active=False,caps=CAPS,user_confirmation=None),indent=2)+'\n')
    for path in OUT.rglob('*.py'):compile(path.read_text(encoding='utf-8-sig'),str(path),'exec')
    archive(board,OUT/'board-package.tar.gz')
    result=dict(package_id=ID,archive=digest(OUT/'board-package.tar.gz'),authorization_active=False,caps=CAPS,
        BOOT_writes=0,reboots=0,SDK=0)
    (OUT/'prepared.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()

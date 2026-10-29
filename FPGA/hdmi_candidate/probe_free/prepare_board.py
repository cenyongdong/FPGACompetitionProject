"""Prepare fresh, bounded probe-free rounds; no network or device operation."""
from pathlib import Path
import hashlib
import json
import py_compile
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
WORK = ROOT / '.local/hdmi-probe-free-20261025-r1'
OLD = ROOT / '.local/pose180-resident-witness-20261025-r9'
SOURCE = ROOT / 'software/pose180_pipeline/control'
REMOTE = '/root/demo-v1-20261022-r1/hdmi-probe-free-20261025-r1'


def put(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def digest(path):
    return dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def pack(folder, output):
    with tarfile.open(output, 'x:gz') as archive:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                info = archive.gettarinfo(str(path), arcname=path.relative_to(folder).as_posix())
                info.mode = 0o755 if path.name=='pose180_demo' or path.suffix=='.sh' else 0o600
                with path.open('rb') as stream:
                    archive.addfile(info, stream)


def main():
    qualification = json.loads((ROOT/'tools/pose-v1/evidence/hdmi-probe-free-20261025-r1/qualification.json').read_text())
    if not qualification['bit_generation_prerequisite_pass']:
        raise RuntimeError('Physical qualification has not passed')
    boot = WORK / 'boot-package/BOOT-probe-free-r1.bin'
    native = WORK / 'software-build/arm64/pose180_demo'
    review = json.loads((ROOT/'tools/pose-v1/evidence/hdmi-probe-free-20261025-r1/package-review.json').read_text())
    if digest(boot)['sha256'] != review['sha256'] or not review['all_bytes_outside_PL_identical']:
        raise RuntimeError('New BOOT differs from qualified package')
    bundle = WORK / 'board-bundle'
    bundle.mkdir()
    common = bundle / 'common'; common.mkdir()
    for name in ('board_support.py',):
        shutil.copyfile(OLD/'board'/name, common/name)
    shutil.copyfile(boot, common/'BOOT-candidate.bin')
    shutil.copyfile(OLD/'board/package/BOOT-original.bin', common/'BOOT-original.bin')
    software = WORK/'software'; software.mkdir()
    shutil.copyfile(native, software/'pose180_demo')
    for name in ('service.py', 'run_hdmi_trial.py', 'bounded_log.py'):
        shutil.copyfile(SOURCE/name, software/name)
    for name in ('preflight.py', 'csi.conf'):
        shutil.copyfile(OLD/'software'/name, software/name)

    old_controller = (OLD/'board/controller.py').read_text()
    old_manifest = json.loads((OLD/'board/manifest.json').read_text())
    for index, seconds in enumerate((120, 120, 1800), 1):
        name = 'round-'+str(index)
        folder = bundle/name; folder.mkdir()
        identifier = WORK.name+'-'+name
        base = REMOTE+'/'+name
        caps = dict(candidate_starts=1, SDK_Open=1, original_fallbacks=1, runtime_seconds=seconds, stop_request_seconds=seconds+120)
        controller = old_controller.replace("ID = 'pose180-resident-witness-20261025-r9'", 'ID = '+repr(identifier))
        controller = controller.replace('New bounded pose180 HDMI package; reuse qualified r53 BOOT/FAT primitives.',
            'Fresh probe-free reliability round; preserve the established FAT update primitives.')
        controller = controller.replace("CAPS = {'candidate_starts': 1, 'SDK_Open': 1, 'original_fallbacks': 1, 'runtime_seconds': 600, 'stop_request_seconds': 720}", 'CAPS = '+repr(caps))
        controller = controller.replace("BASE/'board_support.py'", "BASE.parent/'common/board_support.py'")
        controller = controller.replace("PACKAGE = BASE/'package'", "PACKAGE = BASE.parent/'common'")
        controller = controller.replace("    sys.path.insert(0, str(PACKAGE))\n    import capture_deferred\n    c = capture_deferred", '')
        controller = controller.replace('return b.owners() + c.owners()', "return b.owners() + [str(fd) for fd in Path('/proc').glob('[0-9]*/fd/*') if _axi_owner(fd)]")
        at = controller.index('\ndef owners():')
        controller = controller[:at] + '''\ndef _axi_owner(fd):
    try:
        return os.readlink(fd).startswith('/dev/axi')
    except OSError:
        return False

''' + controller[at:]
        controller = controller.replace("b.verify_file(BASE/name, row)", "b.verify_file(BASE/name, row)")
        begin = controller.index('def startup():')
        end = controller.index('\ndef run(', begin)
        controller = controller[:begin] + '''def startup():
    identity = restored()
    reserve('startup', SDK=0, diagnostic_MMIO=0)
    receipt = dict(passed=True, boot_id=identity, mode='probe_free', hardware_profile='probe_free',
        candidate_boot_sha256=cfg['candidate_boot_sha256'], diagnostic_MMIO=0,
        evidence_scope='BOOT installed/read back, fresh boot, original recovery file restored; no protocol health assertion')
    save(BASE/'startup-admission.json', receipt)
    save(PIPELINE/'startup-admission.json', receipt)
    (PIPELINE/'startup-mode.txt').write_text('probe_free\\n')
    return save(META/'startup.json', receipt)

''' + controller[end:]
        # Package files reside once in common; each round has its own metadata.
        controller = controller.replace("cfg['files']['package/BOOT-candidate.bin']['sha256']", "cfg['candidate_boot_sha256']")
        controller = controller.replace("cfg['files']['package/BOOT-original.bin']", "{'bytes':7023552,'sha256':cfg['original_boot_sha256']}")
        controller = controller.replace("and final.get('inferred',0)>0", "and result.get('seconds',0)>=CAPS['runtime_seconds'] and result.get('stop_reason') is None\n        and final.get('inferred',0)>0")
        controller = controller.replace('long_duration_accepted=False)', "long_duration_accepted=bool(result['passed'] and CAPS['runtime_seconds']>=1800))")
        anchor = "    if stage == 'fallback-reboot':"
        addition = '''    if stage in ('finish','promote'):
        identity=restored()
        outcome=read(META/'long-test.json')
        need(outcome['passed'] and not owners(), 'Safe successful business completion required')
        if stage=='promote':
            b.audit(original, identity)
            b.replace_boot(PACKAGE/'BOOT-candidate.bin', original, candidate, 'promote', 'promote.json')
        audit=b.audit(candidate if stage=='promote' else original, identity)
        save(META/'final-audit.json',audit)
        return save(META/'closed.json', dict(closed=True,boot_id=identity,candidate_starts=1,
            SDK_Open_attempts=1,original_fallbacks=0,running_candidate=True,
            startup_file='candidate' if stage=='promote' else 'original',
            remaining=dict(candidate_starts=0,SDK_Open=0,original_fallbacks=0)))
'''
        controller = controller.replace(anchor, addition+anchor)
        controller = controller.replace("'restore','startup','run','status','stop','result','fallback-reboot','close'))", "'restore','startup','run','status','stop','result','finish','promote','fallback-reboot','close'))")
        put(folder/'controller.py', controller)
        py_compile.compile(str(folder/'controller.py'), doraise=True, cfile=str(WORK/(name+'-controller.pyc')))
        identity = json.loads((OLD/'software/identity.json').read_text())
        identity.update(session=20261025100000+index, seconds=seconds, hardware_profile='probe_free', candidate_boot_sha256=review['sha256'],
            gain_profile='csi.conf: unchanged three frozen r9 coefficients; no new calibration')
        identity['files']={path.name:digest(path)['sha256'] for path in software.iterdir() if path.name!='identity.json'}
        put(software/'identity.json',json.dumps(identity,indent=2)+'\n')
        pack(software,folder/'software-package.tar.gz')
        manifest={key:value for key,value in old_manifest.items() if key not in ('files','source_reference','protected_identity_reference')}
        manifest.update(package_id=identifier,base=base,caps=caps,candidate_boot_sha256=review['sha256'],status='authorized_probe_free_reliability',hardware_profile='probe_free')
        manifest['board']=dict(manifest['board'],remote_root=base)
        manifest['files']={path.relative_to(folder).as_posix():digest(path) for path in folder.rglob('*') if path.is_file()}
        manifest['files'].update({'../common/'+path.name:digest(path) for path in common.iterdir()})
        put(folder/'manifest.json',json.dumps(manifest,indent=2)+'\n')
        put(folder/'authorization.json',json.dumps(dict(package_id=identifier,active=True,caps=caps,
            user_confirmation='2026-10-25 user explicitly requested removing all bitstream probes/protocol checkers, booting that design, and reliability verification. This fresh bounded round is within the standing autonomous board-test authorization; no failed SDK retry.'),indent=2)+'\n')
    pack(bundle,WORK/'board-package.tar.gz')
    print(json.dumps(dict(prepared=True,remote=REMOTE,rounds=3,runtime_seconds=[120,120,1800],SDK_max=3,original_fallback_max=1,BOOT_sha256=review['sha256'])))


if __name__=='__main__':
    main()

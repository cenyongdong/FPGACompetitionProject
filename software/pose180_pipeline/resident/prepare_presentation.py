"""Prepare a fresh finite presentation trial on the qualified probe-free/drain BOOT.

Reuses the current controller and recovery assets; never starts a board operation.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / '.local/hdmi-probe-free-drain-20261026-r1'

def digest(path):
    return dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def pack(folder, destination):
    with tarfile.open(destination, 'x:gz') as archive:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                info = archive.gettarinfo(str(path), arcname=path.relative_to(folder).as_posix())
                info.mode = 0o755 if path.name == 'pose180_demo' else 0o600
                with path.open('rb') as stream:
                    archive.addfile(info, stream)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=600)
    parser.add_argument('--hardware-work', type=Path, help='Qualified integrated PL-filter build and packaged BOOT')
    args = parser.parse_args()
    if not 1 <= args.seconds <= 1800:
        raise ValueError('Finite runtime required')
    work = args.work.resolve()
    work.mkdir(exist_ok=True)
    bundle = work / 'board-bundle'; bundle.mkdir()
    common = bundle / 'common'; shutil.copytree(BASE / 'board-bundle/common', common)
    profile='probe-free-drain-v1'
    qualification_reference=ROOT/'tools/pose-v1/evidence/hdmi-probe-free-drain-20261026-r1/qualification.json'
    if args.hardware_work:
        hardware=args.hardware_work.resolve();qualification_reference=hardware/'reports/qualification.json'
        qualified=json.loads(qualification_reference.read_text());review=json.loads((hardware/'reports/package-review.json').read_text())
        profile='probe-free-drain-filter-v1'
        if not (qualified.get('bit_generation_prerequisite_pass') and qualified.get('hardware_profile')==profile
                and review.get('all_bytes_outside_PL_identical') and review.get('PL_payload_matches_candidate_after_word_swap')):
            raise ValueError('Integrated hardware/BOOT not qualified')
        candidate=Path(review['BOOT_path'])
        if digest(candidate)['sha256']!=review['sha256']:raise ValueError('Qualified candidate BOOT changed')
        shutil.copyfile(candidate,common/'BOOT-candidate.bin')
    software = work / 'software'; software.mkdir()
    with tarfile.open(BASE / 'board-bundle/round-1/software-package.tar.gz') as archive:
        for member in archive.getmembers():
            if not member.isfile() or Path(member.name).name != member.name:
                raise ValueError('Unexpected software archive member')
        archive.extractall(software)
    shutil.copyfile(args.binary, software / 'pose180_demo')
    identity = json.loads((software / 'identity.json').read_text())
    identity['session'] = int(datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d%H%M%S'))
    identity['seconds'] = args.seconds
    identity['hardware_profile']=profile
    identity['candidate_boot_sha256']=digest(common/'BOOT-candidate.bin')['sha256']
    identity['files']['pose180_demo'] = digest(software / 'pose180_demo')['sha256']
    identity['presentation'] = dict(version='tracked-one-euro-v4', backend='cpu', port=39385,
                                   duplicate_centre=.3, duplicate_pose=.3,
                                   duplicate_translation=.7, duplicate_shape=.2,
                                   confirmation_hits=3, hold_ms=250, identity_ms=250, temporal_representative=True,
                                   shadow_support_margin=.25, interface='minimal-title-state-frame-views', skeleton_color='#3b9dff', PC_cursor='normal')
    if args.hardware_work:
        identity['presentation']['backend']='pl-with-isolated-cpu-fallback'
        for name in ('run_hdmi_trial.py','service.py'):
            path=software/name
            value=path.read_text().replace('probe-free-drain-v1',profile)
            # Every prepared invocation explicitly selects the matching hardware
            # and backend; the original scripts/archive stay untouched.
            value=value.replace("'--hdmi', '1'", "'--hardware-profile', '"+profile+"', '--filter-backend', 'pl', '--hdmi', '1'")
            value=value.replace("'--hdmi','1'", "'--hardware-profile','"+profile+"','--filter-backend','pl','--hdmi','1'")
            compile(value,name,'exec');path.write_text(value,newline='\n')
            identity['files'][name]=digest(path)['sha256']
    write(software / 'identity.json', identity)
    folder = bundle / 'round-1'; folder.mkdir()
    pack(software, folder / 'software-package.tar.gz')
    manifest = json.loads((BASE / 'board-bundle/round-1/manifest.json').read_text())
    old_caps = dict(manifest['caps'])
    caps = dict(candidate_starts=1, SDK_Open=1, original_fallbacks=1,
                runtime_seconds=args.seconds, stop_request_seconds=args.seconds + 120)
    remote = '/root/demo-v1-20261022-r1/' + work.name
    identifier = work.name + '-round-1'
    controller = (BASE / 'board-bundle/round-1/controller.py').read_text().replace(BASE.name, work.name)
    controller=controller.replace('probe-free-drain-v1',profile)
    controller = controller.replace('CAPS = ' + repr(old_caps), 'CAPS = ' + repr(caps))
    compile(controller, 'controller.py', 'exec')
    (folder / 'controller.py').write_text(controller, newline='\n')
    manifest.update(package_id=identifier, base=remote + '/round-1', caps=caps,
                    status='authorized_presentation_validation', hardware_rebuilt=bool(args.hardware_work),
                    hardware_profile=profile,candidate_boot_sha256=identity['candidate_boot_sha256'],
                    qualification_reference=str(qualification_reference))
    manifest['board']['remote_root'] = manifest['base']
    manifest['files'] = {p.name: digest(p) for p in folder.iterdir() if p.is_file()}
    manifest['files'].update({'../common/' + p.name: digest(p) for p in common.iterdir() if p.is_file()})
    write(folder / 'manifest.json', manifest)
    write(folder / 'authorization.json', dict(package_id=identifier, active=True, caps=caps,
          user_confirmation='2026-10-26 user explicitly requested latest qualified bitstream, investigation of HDMI flashing/overlap, fixes and integrated on-board validation. Fresh bounded package; no failed-load retry.'))
    pack(bundle, work / 'board-package.tar.gz')
    for name in ('board_call.py', 'capture_uart.py', 'capture_hdmi_startup.ps1', 'round-1-network.py'):
        target = work / name
        if not target.exists():
            target.write_text((BASE / name).read_text(encoding='utf-8-sig').replace(BASE.name, work.name), newline='\n')
    host = (ROOT / 'FPGA/hdmi_candidate/probe_free_drain/board_host.py').read_text()
    host = host.replace('parents[3]', 'parents[2]').replace(BASE.name, work.name).replace('DRAIN_R1_', 'PRESENTATION_R1_')
    (work / 'board_host.py').write_text(host, newline='\n')
    write(work / 'prepared.json', dict(package_id=identifier, caps=caps, hardware_profile=profile,
          BOOT_sha256=manifest['candidate_boot_sha256'], native_sha256=identity['files']['pose180_demo'],
          model_changed=False, hardware_rebuilt=bool(args.hardware_work), presentation=identity['presentation']))
    print(json.dumps(dict(prepared=True, package_id=identifier, caps=caps)))

if __name__ == '__main__':
    main()

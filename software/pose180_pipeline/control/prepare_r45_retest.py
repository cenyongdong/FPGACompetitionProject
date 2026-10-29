"""Prepare one explicitly requested r45 repeat using immutable successful assets."""
from pathlib import Path
import hashlib
import argparse
import json
import py_compile
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[3]
ID = 'pose180-r45-retest-20261025-r10'
OUT = ROOT / '.local' / ID
REMOTE = '/root/demo-v1-20261022-r1/' + ID
OLD = ROOT / '.local/pose180-resident-witness-20261025-r9'
GOOD = ROOT / '.local/pose180-resident-window-20261025-r7'
HOST = ROOT / '.local/hdmi-probe-free-20261025-r1'


def digest(path):
    return dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def pack(folder, target):
    with tarfile.open(target, 'x:gz') as archive:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                info = archive.gettarinfo(str(path), arcname=path.relative_to(folder).as_posix())
                info.mode = 0o755 if path.name == 'pose180_demo' else 0o600
                with path.open('rb') as source:
                    archive.addfile(info, source)


def main():
    global ID, OUT, REMOTE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--top3',action='store_true')
    parser.add_argument('--pc-top3',action='store_true')
    args=parser.parse_args()
    if args.pc_top3:args.top3=True
    if args.top3:
        ID='pose180-top3-pc-20261025-r12' if args.pc_top3 else 'pose180-top3-20261025-r11';OUT=ROOT/'.local'/ID
        REMOTE='/root/demo-v1-20261022-r1/'+ID
    OUT.mkdir(exist_ok=args.top3)
    board = OUT / 'board'; board.mkdir()
    software = OUT / 'software'; software.mkdir()
    manifest = json.loads((OLD / 'board/manifest.json').read_text())
    files = {}
    for name, expected in manifest['files'].items():
        if name in ('controller.py', 'software-package.tar.gz', 'board_network.py'):
            continue
        source = OLD / 'board' / name
        if digest(source) != expected:
            raise ValueError('Protected asset changed: ' + name)
        target = board / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        files[name] = expected
    good_manifest = json.loads((GOOD / 'board/manifest.json').read_text())
    if files['package/BOOT-candidate.bin'] != good_manifest['files']['package/BOOT-candidate.bin']:
        raise ValueError('BOOT is not the previously successful image')
    identity = json.loads((GOOD / 'software/identity.json').read_text())
    for name, expected in identity['files'].items():
        source = ROOT/'.local/pose180-top3-20261025-r11/build/arm64/pose180_demo' if args.top3 and name=='pose180_demo' else GOOD / 'software' / name
        actual=digest(source)['sha256']
        if not (args.top3 and name=='pose180_demo') and actual != expected:
            raise ValueError('Successful software asset changed: ' + name)
        shutil.copyfile(source, software / name)
        identity['files'][name]=actual
    old_caps=dict(manifest['caps'])
    if args.top3:
        manifest['caps'].update(runtime_seconds=300 if args.pc_top3 else 180,stop_request_seconds=420 if args.pc_top3 else 300)
        identity.update(seconds=manifest['caps']['runtime_seconds'],selection=dict(top_k=3,strict_score_threshold=0.2))
    identity['session'] = 20261025101201 if args.pc_top3 else 20261025101101 if args.top3 else 20261025101001
    write(software / 'identity.json', identity)
    pack(software, board / 'software-package.tar.gz')
    controller = (OLD / 'board/controller.py').read_text().replace(OLD.name, ID)
    controller=controller.replace('CAPS = '+repr(old_caps),'CAPS = '+repr(manifest['caps']))
    (board / 'controller.py').write_text(controller, newline='\n')
    # Keep current strict startup corroboration and all active-consumer guards.
    for name in ('controller.py', 'software-package.tar.gz'):
        files[name] = digest(board / name)
    network = (HOST / 'round-1-network.py').read_text().replace(HOST.name + '/round-1', ID)
    (board / 'board_network.py').write_text(network, newline='\n')
    files['board_network.py'] = digest(board / 'board_network.py')
    manifest.update(package_id=ID, base=REMOTE, files=files, status='authorized_r45_retest',
        source_reference=('Current resident native software with top3 and strict score >0.2; r7 service wrappers; ' if args.top3 else 'Exact successful r7 native software; ')+
        'exact r45 BOOT; existing r9 startup safety corroboration; reuse router autostart; no RTL or SDK changes')
    manifest['board']['remote_root'] = REMOTE
    write(board / 'manifest.json', manifest)
    write(board / 'authorization.json', dict(package_id=ID, active=True, caps=manifest['caps'],
        user_confirmation=('2026-10-25 user explicitly requested PC 3D display receiving simultaneous board inference with top3 and score >0.2. One candidate, at most one SDK, 300 seconds, one original BOOT fallback; no automatic retry.' if args.pc_top3 else
        '2026-10-25 user explicitly requested stopping current inference, selecting top3 then score >0.2 and running inference validation again. One candidate, at most one SDK, 180 seconds, one original BOOT fallback; no automatic retry.' if args.top3 else
        '2026-10-25 user explicitly requested retesting the previously successful bitstream. One candidate start, at most one SDK initialization, 600 seconds, one original BOOT fallback; no automatic retry.')))
    for name in ('board_call.py', 'capture_uart.py', 'capture_hdmi_startup.ps1'):
        text = (HOST / name).read_text(encoding='utf-8-sig').replace(HOST.name, ID)
        (OUT / name).write_text(text, newline='\n')
    for name in ('start_candidate.py', 'start_fallback.py'):
        text = (GOOD / name).read_text().replace(GOOD.name, ID).replace('POSE180_RESIDENT_WINDOW_R7_',
            'POSE180_TOP3_PC_R12_' if args.pc_top3 else 'POSE180_TOP3_R11_' if args.top3 else 'POSE180_R45_RETEST_R10_')
        (OUT / name).write_text(text, newline='\n')
    for path in board.glob('*.py'):
        py_compile.compile(str(path), cfile=str(OUT / (path.stem + '.pyc')), doraise=True)
    pack(board, OUT / 'board-package.tar.gz')
    receipt = dict(package_id=ID, caps=manifest['caps'], hardware_rebuilt=False,
        candidate=files['package/BOOT-candidate.bin'], native_sha256=identity['files']['pose180_demo'],
        source_software='current resident top3 build' if args.top3 else GOOD.name, startup_guards=OLD.name, router_operations=0,
        archive=digest(OUT / 'board-package.tar.gz'), actual_candidate_starts=0, actual_SDK=0)
    write(OUT / 'prepared.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()

"""Prepare a fresh finite presentation trial on the qualified probe-free/drain BOOT.

Reuses the current controller and recovery assets; never starts a board operation.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import math
import shutil
import tarfile
from dataset_input import validate_dataset

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / '.local/hdmi-probe-free-drain-20261026-r1'
DEFAULT_BOOT = ROOT / 'FPGA/hdmi_candidate/default_boot.json'

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
    parser.add_argument('--input-source', choices=('dataset','live-csi'), default='dataset')
    parser.add_argument('--csi-alignment', choices=('strict','adaptive'), default='strict',
                        help='Future explicit live-CSI package only; does not start capture')
    parser.add_argument('--dataset', type=Path, help='Directory prepared by dataset_input.py')
    parser.add_argument('--dataset-repetitions',type=int,default=1,help='Finite repeated inference, a fresh tracking epoch per pass')
    parser.add_argument('--filter-backend', choices=('cpu','pl'), default='cpu')
    parser.add_argument('--min-cutoff',type=float,default=.5)
    parser.add_argument('--beta',type=float,default=.3)
    parser.add_argument('--d-cutoff',type=float,default=1)
    parser.add_argument('--compare-ps',action='store_true',help='Time same-input CPU reference during a finite PL run')
    parser.add_argument('--hardware-work', type=Path, help='Qualified integrated PL-filter build and packaged BOOT')
    parser.add_argument('--reference-boot',type=Path,help='BOOT to preserve as this new package\'s startup/fallback baseline; defaults to the recorded deployed release')
    args = parser.parse_args()
    deployed=json.loads(DEFAULT_BOOT.read_text()) if DEFAULT_BOOT.is_file() else None
    if deployed:
        if not args.hardware_work:args.hardware_work=ROOT/deployed['hardware_work']
        if not args.reference_boot:
            args.reference_boot=ROOT/deployed['BOOT_path']
            if digest(args.reference_boot)['sha256']!=deployed['BOOT_sha256']:
                raise ValueError('Recorded default BOOT changed')
    if not (math.isfinite(args.min_cutoff) and args.min_cutoff>0 and math.isfinite(args.beta) and args.beta>=0 and math.isfinite(args.d_cutoff) and args.d_cutoff>0):
        raise ValueError('Invalid One Euro parameters')
    if args.filter_backend=='pl' and (args.min_cutoff,args.beta,args.d_cutoff)!=(1,.5,1):
        raise ValueError('Existing PL requires 1/0.5/1; use CPU for the tuned demonstration')
    if args.filter_backend=='pl' and not args.hardware_work:
        raise ValueError('PL filter needs the qualified integrated hardware')
    if args.compare_ps and args.filter_backend!='pl':
        raise ValueError('PS comparison requires PL backend')
    if not 1 <= args.seconds <= 1800:
        raise ValueError('Finite runtime required')
    if (args.input_source=='dataset') != bool(args.dataset):
        raise ValueError('Dataset mode requires --dataset; live-csi mode excludes it')
    dataset=validate_dataset(args.dataset) if args.dataset else None
    if dataset and args.csi_alignment!='strict':
        raise ValueError('Adaptive alignment applies only to an explicitly selected live-CSI source')
    if not 1<=args.dataset_repetitions<=30 or (not dataset and args.dataset_repetitions!=1):
        raise ValueError('Repetition requires an explicit finite dataset')
    if dataset and dataset['count']*args.dataset_repetitions>9000:
        raise ValueError('At most 9000 repeated dataset inputs')
    if dataset and args.seconds < args.dataset_repetitions*(dataset['count']/dataset['playback_hz']+.1)+2:
        raise ValueError('Runtime budget is shorter than the prepared clip')
    work = args.work.resolve()
    work.mkdir(exist_ok=True)
    bundle = work / 'board-bundle'; bundle.mkdir()
    common = bundle / 'common'; shutil.copytree(BASE / 'board-bundle/common', common)
    if args.reference_boot:
        # The historical reference stays in BASE. Only this fresh package's
        # fallback follows the installed release, avoiding an implicit downgrade.
        if args.reference_boot.stat().st_size!=7023552:raise ValueError('Unexpected reference BOOT size')
        shutil.copyfile(args.reference_boot,common/'BOOT-original.bin')
    reference_sha=digest(common/'BOOT-original.bin')['sha256']
    profile='probe-free-drain-v1'
    qualification_reference=ROOT/'tools/pose-v1/evidence/hdmi-probe-free-drain-20261026-r1/qualification.json'
    if args.hardware_work:
        hardware=args.hardware_work.resolve();qualification_reference=hardware/'reports/qualification.json'
        qualified=json.loads(qualification_reference.read_text());review=json.loads((hardware/'reports/package-review.json').read_text())
        profile=qualified.get('hardware_profile')
        if profile not in ('probe-free-drain-filter-v1','probe-free-drain-post-v2'):
            raise ValueError('Unsupported integrated hardware profile')
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
    identity['reference_boot_sha256']=reference_sha
    identity['files']['pose180_demo'] = digest(software / 'pose180_demo')['sha256']
    identity['input_source']='official_dataset' if dataset else 'live_csi'
    identity['CSI_live']=not bool(dataset)
    if not dataset:
        identity['csi_alignment']=args.csi_alignment
        if args.csi_alignment=='adaptive':
            csi_path=software/'csi.conf'
            lines=[line for line in csi_path.read_text().splitlines()
                   if line.split('=',1)[0] not in ('alignment','max_skew_us','max_sequence_skew')]
            csi_path.write_text('\n'.join(lines)+'\nalignment=adaptive\nmax_skew_us=5000\nmax_sequence_skew=1\n',newline='\n')
            identity['files']['csi.conf']=digest(csi_path)['sha256']
    identity['dataset_repetitions']=args.dataset_repetitions
    if dataset:
        for name in ('dataset.piwcsi2','dataset.json'):
            shutil.copyfile(args.dataset/name,software/name)
            identity['files'][name]=digest(software/name)['sha256']
    shutil.copyfile(Path(__file__).with_name('input_config.py'),software/'input_config.py')
    identity['files']['input_config.py']=digest(software/'input_config.py')['sha256']
    for name in ('run_hdmi_trial.py','service.py'):
        path=software/name
        value='from input_config import input_arguments\n'+path.read_text()
        value=value.replace("'--csi', str(root/'csi.conf')", '*input_arguments(root, identity)')
        value=value.replace("'--csi',str(root/'csi.conf')", '*input_arguments(root, identity)')
        value=value.replace('CSI_live=True', "CSI_live=identity['CSI_live']")
        value=value.replace('runtime_seconds=180', "runtime_seconds=identity['seconds']")
        value=value.replace("'--seconds','180'", "'--seconds',str(identity['seconds'])")
        value=value.replace('time.monotonic()-started>240', "time.monotonic()-started>identity['seconds']+120")
        value=value.replace('Stop requested after 240 seconds; observing original SDK call',
                            'Finite stop-request budget reached; observing original SDK call')
        filter_args=repr(['--min-cutoff',str(args.min_cutoff),'--beta',str(args.beta),'--d-cutoff',str(args.d_cutoff)])[1:-1]
        value=value.replace("'--hdmi', '1'",filter_args+", '--hdmi', '1'")
        value=value.replace("'--hdmi','1'",filter_args+", '--hdmi','1'")
        if "'--min-cutoff'" not in value:
            raise ValueError('Prepared invocation has no explicit filter parameters: '+name)
        if '*input_arguments(root, identity)' not in value:
            raise ValueError('Current controller has no recognized input selection: '+name)
        compile(value,name,'exec');path.write_text(value,newline='\n')
        identity['files'][name]=digest(path)['sha256']
    identity['presentation'] = dict(version='tracked-one-euro-v5', backend='cpu', port=39385,
                                   standby='seven-bars-before-first-result',
                                   min_cutoff=args.min_cutoff,beta=args.beta,d_cutoff=args.d_cutoff,tracking_cutoff=3,velocity_cutoff=1,local_quality_gate=True,
                                   duplicate_centre=.3, duplicate_pose=.3,
                                   duplicate_translation=.7, duplicate_shape=.2,
                                   confirmation_hits=3, hold_ms=250, identity_ms=250, temporal_representative=True,
                                   shadow_support_margin=.25, interface='minimal-title-state-frame-views', skeleton_color='#3b9dff', PC_cursor='normal')
    if args.hardware_work:
        identity['presentation']['backend']='pl-with-isolated-cpu-fallback' if args.filter_backend=='pl' else 'cpu'
        identity['presentation']['compare_ps']=args.compare_ps
        for name in ('run_hdmi_trial.py','service.py'):
            path=software/name
            value=path.read_text().replace('probe-free-drain-v1',profile)
            # Every prepared invocation explicitly selects the matching hardware
            # and backend; the original scripts/archive stay untouched.
            value=value.replace("'--hdmi', '1'", "'--hardware-profile', '"+profile+"', '--filter-backend', '"+args.filter_backend+"', '--hdmi', '1'")
            value=value.replace("'--hdmi','1'", "'--hardware-profile','"+profile+"','--filter-backend','"+args.filter_backend+"','--hdmi','1'")
            if args.compare_ps:
                value=value.replace("'--filter-backend',", "'--compare-ps','1','--filter-backend',")
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
    if dataset:
        controller=controller.replace("result.get('seconds',0)>=CAPS['runtime_seconds']",
            "(final.get('dataset_done') is True and final.get('input_source')=='official_dataset' and final.get('dataset_passes')=="+str(args.dataset_repetitions)+" and final.get('received')=="+str(dataset['count']*args.dataset_repetitions)+")")
        controller=controller.replace("long_duration_accepted=bool(result['passed'] and CAPS['runtime_seconds']>=1800)",
            "long_duration_accepted=False, dataset_clip_completed=bool(result['passed'])")
    compile(controller, 'controller.py', 'exec')
    (folder / 'controller.py').write_text(controller, newline='\n')
    manifest.update(package_id=identifier, base=remote + '/round-1', caps=caps,
                    original_boot_sha256=reference_sha,
                    status='authorized_presentation_validation', hardware_rebuilt=False,
                    input_source=identity['input_source'], CSI_live=identity['CSI_live'],
                    hardware_profile=profile,candidate_boot_sha256=identity['candidate_boot_sha256'],
                    qualification_reference=str(qualification_reference))
    manifest['board']['remote_root'] = manifest['base']
    manifest['files'] = {p.name: digest(p) for p in folder.iterdir() if p.is_file()}
    manifest['files'].update({'../common/' + p.name: digest(p) for p in common.iterdir() if p.is_file()})
    write(folder / 'manifest.json', manifest)
    write(folder / 'authorization.json', dict(package_id=identifier, active=True, caps=caps,
          user_confirmation='2026-10-27 user selected official dataset input for subsequent development/validation and demonstration, with live CSI input closed and both display layouts unchanged; existing autonomous finite board authorization applies. Fresh bounded package; no failed-load retry.'))
    pack(bundle, work / 'board-package.tar.gz')
    for name in ('board_call.py', 'capture_uart.py', 'capture_hdmi_startup.ps1', 'round-1-network.py'):
        target = work / name
        if not target.exists():
            target.write_text((BASE / name).read_text(encoding='utf-8-sig').replace(BASE.name, work.name), newline='\n')
    host = (ROOT / 'FPGA/hdmi_candidate/probe_free_drain/board_host.py').read_text()
    host = host.replace('parents[3]', 'parents[2]').replace(BASE.name, work.name).replace('DRAIN_R1_', 'PRESENTATION_R1_')
    if dataset:
        # Dataset input does not run the live-CSI network setup stage.
        host = host.replace(' boot-control pipeline network', ' boot-control pipeline startup-admission.json')
    (work / 'board_host.py').write_text(host, newline='\n')
    write(work / 'prepared.json', dict(package_id=identifier, caps=caps, hardware_profile=profile,
          BOOT_sha256=manifest['candidate_boot_sha256'], native_sha256=identity['files']['pose180_demo'],
          input_source=identity['input_source'], CSI_live=identity['CSI_live'],
          model_changed=False, hardware_rebuilt=False, presentation=identity['presentation']))
    print(json.dumps(dict(prepared=True, package_id=identifier, caps=caps)))

if __name__ == '__main__':
    main()

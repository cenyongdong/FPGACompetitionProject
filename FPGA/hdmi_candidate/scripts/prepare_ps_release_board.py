"""Bind actual qualified r26 BOOT and the bounded passive-only board scope."""
from pathlib import Path
import hashlib
import json
import shutil
import argparse
from prepare_ps_release_candidate import R,W,E


def identity(p):return dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--evidence',type=Path,default=E)
    parser.add_argument('--work',type=Path,default=W)
    parser.add_argument('--package-id',choices=['ps-release-r26','s01-isolation-r28','hp2-cycletrace-r30','hp2-protocol-r31'],default='ps-release-r26')
    parser.add_argument('--repository-root',type=Path,default=R)
    args=parser.parse_args();e=args.evidence.resolve();work=args.work.resolve()
    assets=args.repository_root.resolve()
    protocol=args.package_id=='hp2-protocol-r31'
    trace=args.package_id in ('hp2-cycletrace-r30','hp2-protocol-r31')
    isolated=args.package_id in ('s01-isolation-r28','hp2-cycletrace-r30','hp2-protocol-r31')
    qualification=json.loads((e/'qualification.json').read_text())
    review=json.loads((e/'package-review.json').read_text())
    uart=json.loads((e/'uart-resume/review.json').read_text())
    if not (qualification['bit_generation_prerequisite_pass'] and review['all_bytes_outside_PL_identical'] and
            review['PL_payload_matches_candidate_after_word_swap'] and uart['marker_received']):
        raise RuntimeError('Physical/package/UART prerequisites missing')
    prior=json.loads((assets/'tools/pose-v1/evidence/hdmi-startup-stability-20261020-r25/deploy/config.json').read_text())
    preflight=json.loads((e/'resume-preflight.json').read_text())
    remote='/root/hdmi-hp2-cycletrace-20261022-r30' if trace else ('/root/hdmi-s01-isolation-20261022-r28' if isolated else '/root/hdmi-ps-release-20261020-r26')
    if protocol:remote='/root/hdmi-protocol-checker-20261023-r31'
    caps=dict(candidate_starts=1 if isolated else 2,original_fallbacks=1,SDK_Open=0,DMA=False,inference=False,HDMI_START=False,physical_key=0,HDMI_long_term=False)
    files={'BOOT-candidate.bin':dict(bytes=review['bytes'],sha256=review['sha256'])}
    files.update({n:prior['files'][n] for n in ('BOOT-original.bin','BOOT-original.readback.bin','ai_preopen_monitor')})
    reuse={n:prior['asset_reuse'][n] for n in ('BOOT-original.bin','BOOT-original.readback.bin','ai_preopen_monitor')}
    deploy=e/'deploy';(deploy/'package').mkdir(parents=True,exist_ok=False)
    software=['capture_ps_release.py','decode_ps_release.py']
    if trace:software+=['capture_hp2_cycletrace.py','decode_hp2_cycletrace.py']
    if protocol:software+=['capture_hp2_protocol.py','decode_hp2_protocol.py','hp2_protocol_checks.py']
    for name in software:
        p=R/'FPGA/hdmi_candidate/software'/name;files[name]=identity(p);shutil.copyfile(p,deploy/'package'/name)
    shutil.copyfile(R/'FPGA/hdmi_candidate/scripts/ps_release_board.py',deploy/'ps_release_board.py')
    cfg=dict(package_id=args.package_id,base=remote,board=dict(prior['board'],remote_root=remote,
        pre_start_boot_id=preflight['boot_id']),original_boot_sha256=prior['original_boot_sha256'],
        known_FAT=prior['known_FAT'],caps=caps,files=files,asset_reuse=reuse,
        independent_host_backup=prior['independent_host_backup'],
        hardware_qualification='qualification.json',hardware_package='package-review.json',
        actual_host_BOOT=review['BOOT_path'])
    (deploy/'config.json').write_text(json.dumps(cfg,indent=2))
    auth=dict(active=True,scope='Passive HP2 consecutive cycle capture' if trace else ('S01 source isolation passive diagnosis' if isolated else 'PS reset/FIFO/release passive diagnosis'),caps=caps,caps_set_by_agent=True,
        user_authorization='User explicitly requests on-board waveform capture on 2026-10-22 and confirms board and UART restored; bounded one candidate and original fallback, no SDK/load.' if trace else ('User approved S01 isolation on 2026-10-22 after committed Git baseline/report; no SDK or HP port reassignment.' if isolated else 'Existing necessary PS reset/FIFO/release BOOT/reboot authorization, explicitly resumed 2026-10-21; UART restored by user and verified.'),
        no_SDK_or_functional_load=True,old_DATA='independently paused',HDMI_long_term=False)
    if protocol:
        auth.update(scope='Passive HP2 native protocol check and waveform capture',
            user_authorization='User approved native protocol checker plan and autonomous continuation on 2026-10-23; existing necessary passive PS reset/release diagnosis BOOT/reboot authorization applies. One candidate and original fallback, no SDK/load.')
    (deploy/'authorization.json').write_text(json.dumps(auth,indent=2))
    helper='''from pathlib import Path
import argparse,importlib.util,sys,json,contextlib,os
R=Path('D:/FPGACompetitionProject');E=R/'tools/pose-v1/evidence/hdmi-ps-release-20261020-r26'
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('mode',choices=['ssh','put','get']);p.add_argument('source');p.add_argument('destination',nargs='?');p.add_argument('--timeout',type=int,default=120);a=p.parse_args()
spec=importlib.util.spec_from_file_location('pinned_transport',R/'.local/hdmi-live-20261017-r3/secure_transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.REMOTE='/root/hdmi-ps-release-20261020-r26/'
log=E/(a.name+'.log');sys.argv=[str(m.__file__),a.mode,a.source]
if a.destination:sys.argv.append(a.destination)
sys.argv+=['--timeout',str(a.timeout),'--log',str(log)]
with open(os.devnull,'w') as null,contextlib.redirect_stdout(null):code=m.main()
print(json.dumps(dict(operation=a.name,exit_code=code,raw_log=str(log))))
if a.mode=='ssh' and log.exists():print(log.read_text(errors='replace')[-1800:])
raise SystemExit(code)
'''
    helper=helper.replace("R=Path('D:/FPGACompetitionProject')",'R=Path('+repr(str(assets))+')')
    helper=helper.replace("E=R/'tools/pose-v1/evidence/hdmi-ps-release-20261020-r26'",'E=Path('+repr(str(e))+')')
    helper=helper.replace("m.REMOTE='/root/hdmi-ps-release-20261020-r26/'",'m.REMOTE='+repr(remote+'/'))
    (work/'board_call.py').write_text(helper)
    print(json.dumps(dict(prepared=True,SDK=0,candidate_start_cap=caps['candidate_starts'],original_fallback_cap=1,BOOT_source=review['BOOT_path'])))


if __name__=='__main__':main()

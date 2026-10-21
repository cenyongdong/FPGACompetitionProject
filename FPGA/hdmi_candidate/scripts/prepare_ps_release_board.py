"""Bind actual qualified r26 BOOT and the bounded passive-only board scope."""
from pathlib import Path
import hashlib
import json
import shutil
from prepare_ps_release_candidate import R,W,E


def identity(p):return dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def main():
    qualification=json.loads((E/'qualification.json').read_text())
    review=json.loads((E/'package-review.json').read_text())
    uart=json.loads((E/'uart-resume/review.json').read_text())
    if not (qualification['bit_generation_prerequisite_pass'] and review['all_bytes_outside_PL_identical'] and
            review['PL_payload_matches_candidate_after_word_swap'] and uart['marker_received']):
        raise RuntimeError('Physical/package/UART prerequisites missing')
    prior=json.loads((R/'tools/pose-v1/evidence/hdmi-startup-stability-20261020-r25/deploy/config.json').read_text())
    preflight=json.loads((E/'resume-preflight.json').read_text())
    remote='/root/hdmi-ps-release-20261020-r26'
    caps=dict(candidate_starts=2,original_fallbacks=1,SDK_Open=0,DMA=False,inference=False,HDMI_START=False,physical_key=0,HDMI_long_term=False)
    files={'BOOT-candidate.bin':dict(bytes=review['bytes'],sha256=review['sha256'])}
    files.update({n:prior['files'][n] for n in ('BOOT-original.bin','BOOT-original.readback.bin','ai_preopen_monitor')})
    reuse={n:prior['asset_reuse'][n] for n in ('BOOT-original.bin','BOOT-original.readback.bin','ai_preopen_monitor')}
    deploy=E/'deploy';(deploy/'package').mkdir(parents=True,exist_ok=False)
    for name in ('capture_ps_release.py','decode_ps_release.py'):
        p=R/'FPGA/hdmi_candidate/software'/name;files[name]=identity(p);shutil.copyfile(p,deploy/'package'/name)
    shutil.copyfile(R/'FPGA/hdmi_candidate/scripts/ps_release_board.py',deploy/'ps_release_board.py')
    cfg=dict(package_id='ps-release-r26',base=remote,board=dict(prior['board'],remote_root=remote,
        pre_start_boot_id=preflight['boot_id']),original_boot_sha256=prior['original_boot_sha256'],
        known_FAT=prior['known_FAT'],caps=caps,files=files,asset_reuse=reuse,
        independent_host_backup=prior['independent_host_backup'],
        hardware_qualification='qualification.json',hardware_package='package-review.json',
        actual_host_BOOT=review['BOOT_path'])
    (deploy/'config.json').write_text(json.dumps(cfg,indent=2))
    auth=dict(active=True,scope='PS reset/FIFO/release passive diagnosis',caps=caps,caps_set_by_agent=True,
        user_authorization='Existing necessary PS reset/FIFO/release BOOT/reboot authorization, explicitly resumed 2026-10-21; UART restored by user and verified.',
        no_SDK_or_functional_load=True,old_DATA='independently paused',HDMI_long_term=False)
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
    (W/'board_call.py').write_text(helper)
    print(json.dumps(dict(prepared=True,SDK=0,candidate_start_cap=2,original_fallback_cap=1,BOOT_source=review['BOOT_path'])))


if __name__=='__main__':main()

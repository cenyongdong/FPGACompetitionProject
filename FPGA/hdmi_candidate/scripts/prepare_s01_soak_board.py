"""Bind the unchanged r28 image to the separately authorized r29 passive soak."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

R=Path(__file__).resolve().parents[3]


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def identity(p):return dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,value):
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--asset-root',type=Path,required=True);a=p.parse_args()
    assets=a.asset_root.resolve();old=assets/'tools/pose-v1/evidence/hdmi-s01-isolation-20261022-r28'
    e=old.with_name('hdmi-s01-soak-20261022-r29');deploy=e/'deploy'
    cfg=read(old/'deploy/config.json');pre=read(e/'preflight.json');build=read(e/'monitor-build.json')
    package=read(old/'package-review.json');q=read(old/'qualification.json')
    if not (q['bit_generation_prerequisite_pass'] and package['all_bytes_outside_PL_identical'] and
            package['PL_payload_matches_candidate_after_word_swap'] and not pre['device_owners'] and build['machine']=='aarch64'):
        raise RuntimeError('Actual image/platform/ownership prerequisite missing')
    for name in ('ai_preopen_monitor.cpp','dma_probe_evidence.hpp'):
        if identity(R/'FPGA/hdmi_candidate/software'/name)!=build['files'][name]:
            raise RuntimeError('Native monitor source differs: '+name)
    remote='/root/hdmi-s01-soak-20261022-r29'
    cfg.update(package_id='s01-soak-r29',base=remote,passive_soak_seconds=1800,
               actual_host_BOOT=package['BOOT_path'],hardware_qualification=str(old/'qualification.json'),
               hardware_package=str(old/'package-review.json'))
    cfg['board'].update(remote_root=remote,pre_start_boot_id=pre['boot_id'])
    cfg['files']['ai_preopen_monitor']=build['files']['ai_preopen_monitor']
    cfg['asset_reuse'].pop('ai_preopen_monitor')
    cfg['asset_reuse']['BOOT-candidate.bin']='/root/hdmi-s01-isolation-20261022-r28/package/BOOT-candidate.bin'
    deploy.mkdir();(deploy/'package').mkdir()
    for name in ('capture_ps_release.py','decode_ps_release.py'):
        source=R/'FPGA/hdmi_candidate/software'/name
        cfg['files'][name]=identity(source);shutil.copyfile(source,deploy/'package'/name)
    shutil.copyfile(R/'FPGA/hdmi_candidate/scripts/ps_release_board.py',deploy/'ps_release_board.py')
    save(deploy/'config.json',cfg)
    save(deploy/'authorization.json',dict(active=True,scope='S01 isolated 30 minute no-SDK soak',caps=cfg['caps'],
         user_authorization='2026-10-22 user explicitly authorized direct long-term stability validation of the isolated version.',
         execution_bounds='One unchanged isolated candidate, 1800 second passive observation, one original fallback; no SDK, AI load, HDMI START or physical keys.',
         old_r28='closed; image reused, authorization/counters not reused'))
    save(e/'state.json',dict(status='prepared_not_installed',as_of='2026-10-22',package_id='s01-soak-r29',
         user_authorized=True,passive_soak_seconds=1800,actual_candidate_starts=0,actual_original_fallbacks=0,
         caps=cfg['caps'],old_r28='closed',SDK=0,DMA=0,inference=0,HDMI_START=0,
         AI_four_HC_unchanged=True,BOOT_sha256=package['sha256'],code_root=str(R),
         background_tasks=[],remaining=dict(candidate_starts=1,original_fallbacks=1),
         next='Install only after native self-test, UART and preparation prerequisites.'))
    print(json.dumps(dict(prepared=True,seconds=1800,reused_actual_BOOT=package['sha256'],caps=cfg['caps'])))


if __name__=='__main__':main()

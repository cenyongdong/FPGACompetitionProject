"""Bounded same-bit startups, without a physical reset before Device::Open."""
from pathlib import Path
import argparse,json,os,shutil,subprocess,time,traceback
import reset_key_board as obs

BASE=obs.BASE;META=BASE/'metadata';cfg=obs.cfg;b=obs.b
ORIGINAL=obs.ORIGINAL;CANDIDATE=obs.CANDIDATE

def root_read(name):return b.read_json(META/(name+'.json'))
def root_save(name,value):b.save_new(META/(name+'.json'),value);return value
def cycle_read(n,name):return b.read_json(BASE/('run-'+str(n))/'metadata'/(name+'.json'))

def authorize():
 a=obs.authorize()
 b.need(cfg['contract']['candidate_starts_max']==3 and cfg['contract']['physical_reset_max']==0 and cfg['contract']['SDK_Open_per_boot_max']==1 and cfg['caps']['candidate_starts']==3 and cfg['caps']['SDK_Open']==3 and cfg['caps']['original_fallbacks']==1 and cfg['caps']['PL_KEY1_SW6_pulses']==0,'Unexpected startup package limits')
 b.need(not any(cfg['caps'][x] for x in ('DMA','inference','HDMI_START','HDMI_long_term')),'Startup-only package required')
 return a

def prior(n):
 if n==1:return cfg['board']['pre_start_boot_id']
 r=cycle_read(n-1,'restore');s=cycle_read(n-1,'software');w=cycle_read(n-1,'witness-software')
 b.need(r['passed'] and s['passed'] and w['valid'] and r['boot_id']==s['boot_id']==w['boot_id']==b.boot_id() and not (w['words'][1]&8),'Previous sample failed or runtime changed: no next startup')
 return r['boot_id']

def reboot(kind,n):
 if kind=='candidate':
  r=obs.read('install');b.need(r['passed'] and r['boot_id']==b.boot_id(),'Candidate install not verified')
  audit=b.audit(CANDIDATE,r['boot_id']);name='candidate-'+str(n)
 else:
  r=obs.runtime();audit=b.audit(ORIGINAL,r['boot_id']);name='original-fallback'
 # Exclusive durable record precedes the only reboot command. Never resend on timeout.
 root_save(name+'-attempt',dict(boot_id=audit['boot_id'],cycle=n,time_unix=time.time(),automatic_retry=False))
 p=subprocess.Popen(['/bin/sh','-c','sleep 2; exec /sbin/reboot'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 return root_save(name+'-issued',dict(boot_id=audit['boot_id'],helper_pid=p.pid,command_issued=True))

def main(stage,n):
 b.need(BASE==Path(__file__).resolve().parent and BASE.parent==Path('/root'),'Unexpected package location')
 if stage=='audit':return b.audit(ORIGINAL)
 a=authorize()
 if stage=='prepare':
  b.need(n==1,'Prepare once')
  audit=b.audit(ORIGINAL,cfg['board']['pre_start_boot_id'])
  for name,source in cfg['asset_reuse'].items():
   target=obs.PACKAGE/name;b.verify_file(Path(source),cfg['files'][name])
   if not target.exists():shutil.copyfile(source,target)
  b.checked_backup()
  for name,row in cfg['files'].items():b.verify_file(obs.PACKAGE/name,row)
  for name in ('ai_preopen_monitor','capture_boot_witness'):os.chmod(obs.PACKAGE/name,0o700)
  for row in cfg['software_assets'].values():b.verify_file(Path(row['path']),row)
  host=cfg['independent_host_backup'];b.need(host['verified'] and host['sha256']==ORIGINAL and host['bytes']==7023552,'Independent original backup absent')
  return root_save('prepare',dict(passed=True,boot_id=audit['boot_id']))
 run=obs.bind_sample(n)
 if stage=='install':
  b.need(root_read('prepare')['passed'],'Preparation not complete')
  expected=prior(n);b.audit(ORIGINAL,expected);b.checked_backup()
  run.mkdir(mode=0o700);obs.META.mkdir(mode=0o700);b.MOUNT.mkdir(mode=0o700)
  return b.replace_boot(obs.PACKAGE/'BOOT-ai-read-v3.bin',ORIGINAL,CANDIDATE,'install','install.json')
 if stage=='candidate-reboot':return reboot('candidate',n)
 if stage=='restore':
  b.need(root_read('candidate-'+str(n)+'-attempt')['boot_id']!=b.boot_id(),'No new candidate runtime')
  b.audit(CANDIDATE)
  return b.replace_boot(obs.PACKAGE/'BOOT-original.readback.bin',CANDIDATE,ORIGINAL,'restore','restore.json')
 if stage=='probe':return obs.observe('before')
 if stage=='software':return obs.software(require_physical_reset=False)
 if stage=='fallback-reboot':return reboot('original',n)
 if stage=='close':
  r=obs.read('restore');b.need(r['boot_id']!=b.boot_id(),'Candidate still running');root_read('original-fallback-attempt')
  final=b.audit(ORIGINAL);root_save('final-audit',final)
  a.update(active=False,remaining_candidate_starts=0,remaining_original_fallbacks=0,remaining_key_pulses=0,remaining_SDK_Open=0)
  (BASE/'authorization.json').write_text(json.dumps(a,indent=2))
  return dict(closed=True,boot_id=final['boot_id'])
 raise RuntimeError('Unknown stage')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['audit','prepare','install','candidate-reboot','restore','probe','software','fallback-reboot','close']);p.add_argument('--cycle',type=int,default=1);args=p.parse_args()
 try:print(json.dumps(main(args.stage,args.cycle),indent=2),flush=True)
 except BaseException:traceback.print_exc();raise SystemExit(1)
